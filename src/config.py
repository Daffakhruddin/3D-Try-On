"""
Configuration module for AR Helmet Try-On system.
Contains all configurable parameters and settings.
"""

from dataclasses import dataclass, field
from typing import Tuple
import os


@dataclass
class CameraConfig:
    """Camera capture configuration."""
    device_id: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    retry_attempts: int = 3
    retry_delay_ms: int = 100


@dataclass
class FaceTrackingConfig:
    """Face tracking and pose estimation configuration."""
    max_num_faces: int = 1
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    
    # Pose estimation landmarks (MediaPipe Face Mesh indices)
    nose_tip_idx: int = 1
    chin_idx: int = 152
    left_eye_outer_idx: int = 263
    right_eye_outer_idx: int = 33
    left_mouth_idx: int = 61
    right_mouth_idx: int = 291
    
    # Fallback and stability
    pose_freeze_timeout_ms: int = 800
    pose_lost_timeout_ms: int = 2000
    
    # Smoothing factors (0.0 = no smoothing, 1.0 = infinite smoothing)
    smoothing_factor_rotation: float = 0.3
    smoothing_factor_translation: float = 0.3


@dataclass
class RenderConfig:
    """3D rendering configuration."""
    window_width: int = 1280
    window_height: int = 720
    window_title: str = "AR Helmet Try-On"
    
    # Performance
    target_fps: int = 30
    frame_skip: int = 0  # 0 = no skip, 1 = render every 2nd frame, etc.
    render_resolution_scale: float = 1.0  # 1.0 = native, 0.5 = half res
    
    # Helmet scaling and positioning
    helmet_scale: float = 1.35
    helmet_offset_y: float = 0.08  # Vertical offset (up = positive)
    helmet_offset_z: float = 0.02  # Forward offset (forward = negative)
    
    # Visual settings
    fov_degrees: float = 60.0
    near_plane: float = 0.1
    far_plane: float = 100.0
    
    # Background alpha blending
    helmet_opacity: float = 1.0
    enable_lighting: bool = True
    ambient_strength: float = 0.4
    diffuse_strength: float = 0.6


@dataclass
class PathConfig:
    """File and directory paths."""
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    @property
    def assets_dir(self) -> str:
        return os.path.join(self.project_root, "assets")
    
    @property
    def shaders_dir(self) -> str:
        return os.path.join(self.project_root, "shaders")
    
    @property
    def helmet_model_path(self) -> str:
        return os.path.join(self.assets_dir, "helmet.glb")
    
    @property
    def vertex_shader_path(self) -> str:
        return os.path.join(self.shaders_dir, "helmet.vert")
    
    @property
    def fragment_shader_path(self) -> str:
        return os.path.join(self.shaders_dir, "helmet.frag")


@dataclass
class AppConfig:
    """Main application configuration."""
    camera: CameraConfig = field(default_factory=CameraConfig)
    face_tracking: FaceTrackingConfig = field(default_factory=FaceTrackingConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    
    # Debug settings
    debug_mode: bool = False
    show_fps: bool = True
    show_landmarks: bool = False
    log_level: str = "INFO"


# Global configuration instance
config = AppConfig()
