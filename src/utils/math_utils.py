"""
Mathematical utilities for 3D transformations and pose estimation.
"""

import numpy as np
import cv2
from typing import Tuple, Optional
import pyrr


def rodrigues_to_matrix(rvec: np.ndarray) -> np.ndarray:
    """
    Convert rotation vector to rotation matrix.
    
    Args:
        rvec: Rotation vector (3,) from solvePnP
        
    Returns:
        Rotation matrix (3, 3)
    """
    rotation_matrix, _ = cv2.Rodrigues(rvec)
    return rotation_matrix


def create_transformation_matrix(
    rvec: np.ndarray,
    tvec: np.ndarray,
    scale: float = 1.0,
    offset_y: float = 0.0,
    offset_z: float = 0.0
) -> np.ndarray:
    """
    Create a 4x4 transformation matrix from rotation vector, translation vector, and scale.
    
    Args:
        rvec: Rotation vector (3,)
        tvec: Translation vector (3,)
        scale: Uniform scale factor
        offset_y: Vertical offset
        offset_z: Forward/backward offset
        
    Returns:
        Transformation matrix (4, 4)
    """
    # Convert rotation vector to matrix
    rotation_matrix = rodrigues_to_matrix(rvec)
    
    # Create 4x4 transformation matrix
    transform = np.eye(4, dtype=np.float32)
    transform[:3, :3] = rotation_matrix * scale
    transform[:3, 3] = tvec.flatten()
    
    # Apply offsets
    transform[1, 3] += offset_y  # Y offset
    transform[2, 3] += offset_z  # Z offset
    
    return transform


def create_projection_matrix(
    fov_degrees: float,
    aspect_ratio: float,
    near: float,
    far: float
) -> np.ndarray:
    """
    Create a perspective projection matrix.
    
    Args:
        fov_degrees: Field of view in degrees
        aspect_ratio: Width / height
        near: Near clipping plane
        far: Far clipping plane
        
    Returns:
        Projection matrix (4, 4)
    """
    return pyrr.matrix44.create_perspective_projection(
        fov_degrees, aspect_ratio, near, far, dtype=np.float32
    )


def create_camera_matrix(width: int, height: int, fov_degrees: float = 60.0) -> np.ndarray:
    """
    Create camera intrinsic matrix for OpenCV.
    
    Args:
        width: Image width
        height: Image height
        fov_degrees: Field of view in degrees
        
    Returns:
        Camera matrix (3, 3)
    """
    focal_length = width / (2 * np.tan(np.radians(fov_degrees) / 2))
    camera_matrix = np.array([
        [focal_length, 0, width / 2],
        [0, focal_length, height / 2],
        [0, 0, 1]
    ], dtype=np.float64)
    return camera_matrix


def exponential_smoothing(
    current_value: np.ndarray,
    previous_value: Optional[np.ndarray],
    smoothing_factor: float
) -> np.ndarray:
    """
    Apply exponential smoothing to reduce jitter.
    
    Args:
        current_value: Current measurement
        previous_value: Previous smoothed value (None for first frame)
        smoothing_factor: Smoothing factor (0 = no smoothing, 1 = infinite smoothing)
        
    Returns:
        Smoothed value
    """
    if previous_value is None:
        return current_value
    
    smoothing_factor = np.clip(smoothing_factor, 0.0, 0.99)
    return smoothing_factor * previous_value + (1 - smoothing_factor) * current_value


def compute_face_bounding_box(landmarks_2d: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Compute bounding box from 2D landmarks.
    
    Args:
        landmarks_2d: Array of 2D landmarks (N, 2)
        
    Returns:
        Tuple of (x_min, y_min, width, height)
    """
    x_coords = landmarks_2d[:, 0]
    y_coords = landmarks_2d[:, 1]
    
    x_min, x_max = np.min(x_coords), np.max(x_coords)
    y_min, y_max = np.min(y_coords), np.max(y_coords)
    
    width = x_max - x_min
    height = y_max - y_min
    
    return x_min, y_min, width, height


def normalize_vector(v: np.ndarray) -> np.ndarray:
    """
    Normalize a vector.
    
    Args:
        v: Input vector
        
    Returns:
        Normalized vector
    """
    norm = np.linalg.norm(v)
    if norm < 1e-10:
        return v
    return v / norm
