"""
Camera capture module for webcam video streaming.
Handles camera initialization, frame capture, and error recovery.
"""

import cv2
import numpy as np
import time
from typing import Optional, Tuple
from loguru import logger

from config import CameraConfig


class CameraError(Exception):
    """Custom exception for camera-related errors."""
    pass


class Camera:
    """
    Manages webcam capture with robust error handling and retry logic.
    """
    
    def __init__(self, config: CameraConfig):
        """
        Initialize camera capture.
        
        Args:
            config: Camera configuration
            
        Raises:
            CameraError: If camera cannot be initialized after all retries
        """
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False
        self.frame_count = 0
        self.last_frame: Optional[np.ndarray] = None
        
        self._initialize_camera()
    
    def _initialize_camera(self) -> None:
        """
        Initialize camera with retry logic.
        
        Raises:
            CameraError: If camera cannot be opened after all retries
        """
        logger.info(f"Initializing camera (device_id={self.config.device_id})")
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.cap = cv2.VideoCapture(self.config.device_id, cv2.CAP_DSHOW)
                
                if not self.cap.isOpened():
                    raise CameraError(f"Failed to open camera device {self.config.device_id}")
                
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
                
                # Verify settings
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                
                logger.info(f"Camera opened successfully: {actual_width}x{actual_height} @ {actual_fps}fps")
                
                # Test frame capture
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    raise CameraError("Camera opened but cannot read frames")
                
                self.is_opened = True
                self.last_frame = frame
                logger.success("Camera initialization complete")
                return
                
            except Exception as e:
                logger.warning(f"Camera initialization attempt {attempt + 1}/{self.config.retry_attempts} failed: {e}")
                
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay_ms / 1000.0)
        
        # All attempts failed
        error_msg = (
            f"Failed to initialize camera after {self.config.retry_attempts} attempts.\n"
            f"Possible solutions:\n"
            f"  1. Check if another application is using the camera\n"
            f"  2. Try a different device_id (current: {self.config.device_id})\n"
            f"  3. Verify camera drivers are installed\n"
            f"  4. Check camera permissions in Windows settings"
        )
        logger.error(error_msg)
        raise CameraError(error_msg)
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera with fallback logic.
        
        Returns:
            Tuple of (success, frame)
            - success: True if frame was read successfully
            - frame: The captured frame (BGR format) or None
        """
        if not self.is_opened or self.cap is None:
            logger.error("Camera is not opened")
            return False, None
        
        # Try to read frame with retries
        for attempt in range(3):
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                self.frame_count += 1
                self.last_frame = frame.copy()
                return True, frame
            
            if attempt < 2:
                logger.warning(f"Frame read failed, retrying... ({attempt + 1}/3)")
                time.sleep(0.01)
        
        # All read attempts failed - return last known good frame
        logger.error("Failed to read frame after 3 attempts, using last known frame")
        return False, self.last_frame
    
    def get_frame_size(self) -> Tuple[int, int]:
        """
        Get current frame dimensions.
        
        Returns:
            Tuple of (width, height)
        """
        if self.cap is not None and self.is_opened:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height
        return self.config.width, self.config.height
    
    def release(self) -> None:
        """
        Release camera resources.
        """
        if self.cap is not None:
            logger.info("Releasing camera")
            self.cap.release()
            self.cap = None
            self.is_opened = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.release()
