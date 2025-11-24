"""
Main application for AR Helmet Try-On system.
"""

import cv2
import numpy as np
import time
import sys
from typing import Optional
from loguru import logger

from config import config
from camera import Camera, CameraError
from face_tracker import FaceTracker
from renderer.gl_context import GLContext, GLContextError
from renderer.helmet_renderer import HelmetRenderer, ShaderCompileError
from utils.logging_utils import setup_logger, log_exception


class ARHelmetApp:
    """
    Main application class for AR Helmet Try-On.
    """
    
    def __init__(self):
        """Initialize the application."""
        # Setup logging
        setup_logger(config.log_level)
        logger.info("=" * 60)
        logger.info("AR Helmet Try-On System")
        logger.info("=" * 60)
        
        # Components
        self.camera: Optional[Camera] = None
        self.face_tracker: Optional[FaceTracker] = None
        self.gl_context: Optional[GLContext] = None
        self.helmet_renderer: Optional[HelmetRenderer] = None
        
        # State
        self.running = False
        self.frame_count = 0
        self.fps = 0.0
        self.last_fps_time = time.time()
    
    def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize camera
            logger.info("Initializing camera...")
            self.camera = Camera(config.camera)
            
            # Get camera frame size
            frame_width, frame_height = self.camera.get_frame_size()
            logger.info(f"Camera frame size: {frame_width}x{frame_height}")
            
            # Initialize face tracker
            logger.info("Initializing face tracker...")
            self.face_tracker = FaceTracker(
                config.face_tracking,
                frame_width,
                frame_height
            )
            
            # Initialize OpenGL context
            logger.info("Initializing OpenGL context...")
            self.gl_context = GLContext(
                config.render.window_width,
                config.render.window_height,
                config.render.window_title,
                visible=True
            )
            
            # Initialize helmet renderer
            logger.info("Initializing helmet renderer...")
            self.helmet_renderer = HelmetRenderer(
                self.gl_context,
                config.paths.helmet_model_path,
                config.paths.vertex_shader_path,
                config.paths.fragment_shader_path,
                config.render
            )
            
            logger.success("All components initialized successfully")
            return True
            
        except CameraError as e:
            logger.error(f"Camera initialization failed: {e}")
            return False
        except GLContextError as e:
            logger.error(f"OpenGL context creation failed: {e}")
            return False
        except ShaderCompileError as e:
            logger.error(f"Shader compilation failed: {e}")
            return False
        except Exception as e:
            log_exception(e, "Initialization failed")
            return False
    
    def process_frame(self) -> bool:
        """
        Process one frame.
        
        Returns:
            True if frame processed successfully, False otherwise
        """
        try:
            # Read camera frame
            success, frame = self.camera.read_frame()
            if not success or frame is None:
                logger.warning("Failed to read camera frame")
                return False
            
            # Process face tracking
            rvec, tvec, face_detected = self.face_tracker.process_frame(frame)
            
            # Render helmet
            helmet_visible = (rvec is not None and tvec is not None)
            rendered_helmet = self.helmet_renderer.render(rvec, tvec, helmet_visible)
            
            # Composite helmet onto camera frame
            composite_frame = self._composite_frames(frame, rendered_helmet)
            
            # Draw debug info
            if config.show_fps:
                self._draw_fps(composite_frame)
            
            if config.show_landmarks and face_detected:
                self._draw_landmarks(composite_frame, frame)
            
            # Display result
            cv2.imshow(config.render.window_title, composite_frame)
            
            # Update FPS
            self._update_fps()
            
            return True
            
        except Exception as e:
            log_exception(e, "Frame processing error")
            return False
    
    def _composite_frames(self, camera_frame: np.ndarray, helmet_frame: np.ndarray) -> np.ndarray:
        """
        Composite helmet rendering onto camera frame.
        
        Args:
            camera_frame: Camera frame (BGR)
            helmet_frame: Rendered helmet (RGBA)
            
        Returns:
            Composited frame (BGR)
        """
        # Resize helmet frame to match camera frame if needed
        if helmet_frame.shape[:2] != camera_frame.shape[:2]:
            helmet_frame = cv2.resize(
                helmet_frame,
                (camera_frame.shape[1], camera_frame.shape[0]),
                interpolation=cv2.INTER_LINEAR
            )
        
        # Extract alpha channel
        helmet_rgb = helmet_frame[:, :, :3]
        helmet_alpha = helmet_frame[:, :, 3:4] / 255.0
        
        # Alpha blending
        composite = (
            camera_frame * (1 - helmet_alpha) +
            helmet_rgb * helmet_alpha
        ).astype(np.uint8)
        
        return composite
    
    def _draw_fps(self, frame: np.ndarray) -> None:
        """
        Draw FPS counter on frame.
        
        Args:
            frame: Frame to draw on
        """
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(
            frame,
            fps_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )
    
    def _draw_landmarks(self, display_frame: np.ndarray, camera_frame: np.ndarray) -> None:
        """
        Draw face landmarks on frame for debugging.
        
        Args:
            display_frame: Frame to draw on
            camera_frame: Original camera frame
        """
        landmarks = self.face_tracker.get_all_landmarks_2d(camera_frame)
        if landmarks:
            for x, y in landmarks:
                cv2.circle(display_frame, (x, y), 1, (0, 255, 0), -1)
    
    def _update_fps(self) -> None:
        """Update FPS counter."""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def run(self) -> None:
        """
        Main application loop.
        """
        if not self.initialize():
            logger.error("Failed to initialize application")
            return
        
        logger.info("Starting main loop...")
        logger.info("Press 'q' or ESC to quit")
        
        self.running = True
        frame_skip_counter = 0
        
        try:
            while self.running:
                # Check if window should close
                if self.gl_context.should_close():
                    logger.info("Window close requested")
                    break
                
                # Poll events
                self.gl_context.poll_events()
                
                # Frame skipping for performance
                if config.render.frame_skip > 0:
                    frame_skip_counter += 1
                    if frame_skip_counter % (config.render.frame_skip + 1) != 0:
                        continue
                
                # Process frame
                if not self.process_frame():
                    logger.warning("Frame processing failed, continuing...")
                
                # Check for keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    logger.info("Quit key pressed")
                    break
                elif key == ord('d'):
                    # Toggle debug mode
                    config.show_landmarks = not config.show_landmarks
                    logger.info(f"Debug landmarks: {config.show_landmarks}")
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            log_exception(e, "Unexpected error in main loop")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        """
        logger.info("Cleaning up application...")
        
        self.running = False
        
        if self.helmet_renderer:
            self.helmet_renderer.cleanup()
        
        if self.gl_context:
            self.gl_context.cleanup()
        
        if self.face_tracker:
            self.face_tracker.release()
        
        if self.camera:
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        logger.success("Cleanup complete")
        logger.info("=" * 60)


def main():
    """
    Entry point.
    """
    try:
        app = ARHelmetApp()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        log_exception(e, "Application crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
