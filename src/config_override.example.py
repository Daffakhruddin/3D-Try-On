"""
Example configuration override file.
Copy this to config_override.py and customize as needed.
"""

from config import config

# ============================================================================
# EXAMPLE 1: PERFORMANCE MODE (for slower computers)
# ============================================================================
# config.camera.width = 640
# config.camera.height = 480
# config.render.frame_skip = 1
# config.render.enable_lighting = False
# config.render.helmet_scale = 1.2

# ============================================================================
# EXAMPLE 2: QUALITY MODE (for powerful computers)
# ============================================================================
# config.camera.width = 1920
# config.camera.height = 1080
# config.render.frame_skip = 0
# config.render.enable_lighting = True
# config.render.helmet_scale = 1.4
# config.render.ambient_strength = 0.3
# config.render.diffuse_strength = 0.7

# ============================================================================
# EXAMPLE 3: SMOOTH MODE (reduce jitter)
# ============================================================================
# config.face_tracking.smoothing_factor_rotation = 0.6
# config.face_tracking.smoothing_factor_translation = 0.6
# config.render.helmet_scale = 1.3

# ============================================================================
# EXAMPLE 4: RESPONSIVE MODE (faster reaction)
# ============================================================================
# config.face_tracking.smoothing_factor_rotation = 0.1
# config.face_tracking.smoothing_factor_translation = 0.1
# config.render.helmet_scale = 1.35

# ============================================================================
# EXAMPLE 5: DEBUG MODE
# ============================================================================
# config.log_level = "DEBUG"
# config.show_fps = True
# config.show_landmarks = True
# config.debug_mode = True

# ============================================================================
# CUSTOM HELMET POSITION
# ============================================================================
# Adjust these if helmet doesn't align properly with your face:
# config.render.helmet_scale = 1.5        # Bigger helmet
# config.render.helmet_offset_y = 0.12    # Move up (+) or down (-)
# config.render.helmet_offset_z = -0.05   # Move forward (-) or back (+)

# ============================================================================
# CUSTOM CAMERA
# ============================================================================
# If using external USB camera:
# config.camera.device_id = 1  # Try 0, 1, 2, etc.

# ============================================================================
# CUSTOM MODEL PATH
# ============================================================================
# If your model is named differently:
# import os
# config.paths.project_root = os.path.dirname(os.path.abspath(__file__))
# config.paths.helmet_model_path = os.path.join(config.paths.assets_dir, "ironman.glb")
