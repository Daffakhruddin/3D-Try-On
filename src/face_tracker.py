"""
Face tracking module using MediaPipe Face Mesh.
Handles face detection, landmark extraction, and head pose estimation.
"""

import cv2
import numpy as np
import mediapipe as mp
import time
from typing import Optional, Tuple, List
from loguru import logger

from config import FaceTrackingConfig
from utils.math_utils import (
    create_camera_matrix,
    exponential_smoothing,
    compute_face_bounding_box
)


class FaceTracker:
    """
    Tracks face landmarks and estimates head pose using MediaPipe Face Mesh.
    """
    
    def __init__(self, config: FaceTrackingConfig, frame_width: int, frame_height: int):
        """
        Initialize face tracker.
        
        Args:
            config: Face tracking configuration
            frame_width: Video frame width
            frame_height: Video frame height
        """
        self.config = config
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Initialize MediaPipe Face Mesh
        logger.info("Initializing MediaPipe Face Mesh")
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None
        self._initialize_face_mesh()
        
        # Camera matrix for pose estimation
        self.camera_matrix = create_camera_matrix(frame_width, frame_height)
        self.dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
        
        # 3D model points for face landmarks (approximate)
        self.model_points_3d = self._get_3d_model_points()
        
        # State tracking
        self.last_successful_detection_time = time.time()
        self.last_rvec: Optional[np.ndarray] = None
        self.last_tvec: Optional[np.ndarray] = None
        self.smoothed_rvec: Optional[np.ndarray] = None
        self.smoothed_tvec: Optional[np.ndarray] = None
        self.frozen_rvec: Optional[np.ndarray] = None
        self.frozen_tvec: Optional[np.ndarray] = None
        self.is_pose_frozen = False
        
        logger.success("Face tracker initialized")
    
    def _initialize_face_mesh(self) -> None:
        """
        Initialize MediaPipe Face Mesh with error handling.
        """
        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=self.config.max_num_faces,
                refine_landmarks=True,
                min_detection_confidence=self.config.min_detection_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence
            )
            logger.info("MediaPipe Face Mesh initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Face Mesh: {e}")
            raise
    
    def _get_3d_model_points(self) -> np.ndarray:
        """
        Get approximate 3D model points for face landmarks.
        These are normalized coordinates centered at the nose.
        
        Returns:
            3D model points (6, 3) for the 6 key landmarks
        """
        # Approximate 3D positions (in arbitrary units, normalized)
        model_points = np.array([
            (0.0, 0.0, 0.0),          # Nose tip
            (0.0, -0.33, -0.07),      # Chin
            (-0.23, 0.17, -0.02),     # Left eye outer corner
            (0.23, 0.17, -0.02),      # Right eye outer corner
            (-0.15, -0.15, -0.03),    # Left mouth corner
            (0.15, -0.15, -0.03)      # Right mouth corner
        ], dtype=np.float64)
        
        return model_points
    
    def _extract_landmarks_2d(self, face_landmarks) -> Optional[np.ndarray]:
        """
        Extract 2D pixel coordinates for key landmarks.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            2D landmark coordinates (6, 2) or None if extraction fails
        """
        try:
            indices = [
                self.config.nose_tip_idx,
                self.config.chin_idx,
                self.config.left_eye_outer_idx,
                self.config.right_eye_outer_idx,
                self.config.left_mouth_idx,
                self.config.right_mouth_idx
            ]
            
            landmarks_2d = []
            for idx in indices:
                landmark = face_landmarks.landmark[idx]
                x = int(landmark.x * self.frame_width)
                y = int(landmark.y * self.frame_height)
                landmarks_2d.append([x, y])
            
            return np.array(landmarks_2d, dtype=np.float64)
        
        except Exception as e:
            logger.warning(f"Failed to extract 2D landmarks: {e}")
            return None
    
    def _solve_pose(self, landmarks_2d: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Solve for head pose using PnP.
        
        Args:
            landmarks_2d: 2D landmark coordinates
            
        Returns:
            Tuple of (rvec, tvec) or (None, None) if pose estimation fails
        """
        try:
            success, rvec, tvec = cv2.solvePnP(
                self.model_points_3d,
                landmarks_2d,
                self.camera_matrix,
                self.dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if success:
                return rvec, tvec
            else:
                logger.warning("solvePnP failed to converge")
                return None, None
                
        except Exception as e:
            logger.warning(f"Pose estimation error: {e}")
            return None, None
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
        """
        Process a frame to detect face and estimate pose.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Tuple of (rvec, tvec, face_detected)
            - rvec: Rotation vector (3, 1) or None
            - tvec: Translation vector (3, 1) or None
            - face_detected: True if face was detected in this frame
        """
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        try:
            results = self.face_mesh.process(frame_rgb)
        except Exception as e:
            logger.error(f"Face mesh processing error: {e}")
            # Try to reinitialize
            self._initialize_face_mesh()
            return self._get_fallback_pose()
        
        # Check if face detected
        if not results.multi_face_landmarks:
            return self._handle_no_detection()
        
        # Get first face
        face_landmarks = results.multi_face_landmarks[0]
        
        # Extract 2D landmarks
        landmarks_2d = self._extract_landmarks_2d(face_landmarks)
        if landmarks_2d is None:
            return self._handle_no_detection()
        
        # Estimate pose
        rvec, tvec = self._solve_pose(landmarks_2d)
        if rvec is None or tvec is None:
            return self._handle_no_detection()
        
        # Update state
        self.last_successful_detection_time = time.time()
        self.last_rvec = rvec
        self.last_tvec = tvec
        
        # Apply smoothing
        self.smoothed_rvec = exponential_smoothing(
            rvec, self.smoothed_rvec, self.config.smoothing_factor_rotation
        )
        self.smoothed_tvec = exponential_smoothing(
            tvec, self.smoothed_tvec, self.config.smoothing_factor_translation
        )
        
        # Update frozen pose
        self.frozen_rvec = self.smoothed_rvec.copy()
        self.frozen_tvec = self.smoothed_tvec.copy()
        self.is_pose_frozen = False
        
        return self.smoothed_rvec, self.smoothed_tvec, True
    
    def _handle_no_detection(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
        """
        Handle case when no face is detected.
        
        Returns:
            Tuple of (rvec, tvec, face_detected)
        """
        time_since_detection = (time.time() - self.last_successful_detection_time) * 1000
        
        # If detection lost for short time, freeze last good pose
        if time_since_detection < self.config.pose_freeze_timeout_ms:
            if not self.is_pose_frozen:
                logger.debug("Face lost, freezing last pose")
                self.is_pose_frozen = True
            return self.frozen_rvec, self.frozen_tvec, False
        
        # If detection lost for long time, hide helmet
        if time_since_detection > self.config.pose_lost_timeout_ms:
            if self.frozen_rvec is not None:
                logger.warning("Face lost for extended period, hiding helmet")
                self.frozen_rvec = None
                self.frozen_tvec = None
        
        return None, None, False
    
    def _get_fallback_pose(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], bool]:
        """
        Get fallback pose when processing fails.
        
        Returns:
            Tuple of (rvec, tvec, face_detected)
        """
        if self.frozen_rvec is not None and self.frozen_tvec is not None:
            return self.frozen_rvec, self.frozen_tvec, False
        return None, None, False
    
    def get_all_landmarks_2d(self, frame: np.ndarray) -> Optional[List[Tuple[int, int]]]:
        """
        Get all face landmarks for debug visualization.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of (x, y) coordinates or None
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        try:
            results = self.face_mesh.process(frame_rgb)
            if not results.multi_face_landmarks:
                return None
            
            face_landmarks = results.multi_face_landmarks[0]
            landmarks = []
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * self.frame_width)
                y = int(landmark.y * self.frame_height)
                landmarks.append((x, y))
            
            return landmarks
        except:
            return None
    
    def release(self) -> None:
        """
        Release MediaPipe resources.
        """
        if self.face_mesh is not None:
            logger.info("Releasing face mesh")
            self.face_mesh.close()
            self.face_mesh = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.release()
