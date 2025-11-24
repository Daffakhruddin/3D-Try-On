"""
OpenGL context management using moderngl and GLFW.
"""

import glfw
import moderngl
import numpy as np
from typing import Optional, Tuple
from loguru import logger


class GLContextError(Exception):
    """Custom exception for OpenGL context errors."""
    pass


class GLContext:
    """
    Manages OpenGL context, window creation, and framebuffer objects.
    """
    
    def __init__(self, width: int, height: int, title: str = "AR Helmet Try-On", visible: bool = True):
        """
        Initialize OpenGL context and window.
        
        Args:
            width: Window width
            height: Window height
            title: Window title
            visible: Whether window should be visible
            
        Raises:
            GLContextError: If context creation fails
        """
        self.width = width
        self.height = height
        self.title = title
        self.window: Optional[glfw._GLFWwindow] = None
        self.ctx: Optional[moderngl.Context] = None
        self.fbo: Optional[moderngl.Framebuffer] = None
        self.render_texture: Optional[moderngl.Texture] = None
        self.depth_buffer: Optional[moderngl.Renderbuffer] = None
        
        self._initialize(visible)
    
    def _initialize(self, visible: bool) -> None:
        """
        Initialize GLFW and create OpenGL context.
        
        Args:
            visible: Whether window should be visible
            
        Raises:
            GLContextError: If initialization fails
        """
        try:
            # Initialize GLFW
            if not glfw.init():
                raise GLContextError("Failed to initialize GLFW")
            
            logger.info("GLFW initialized successfully")
            
            # Set window hints
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
            glfw.window_hint(glfw.VISIBLE, glfw.TRUE if visible else glfw.FALSE)
            glfw.window_hint(glfw.SAMPLES, 4)  # 4x MSAA
            
            # Create window
            self.window = glfw.create_window(self.width, self.height, self.title, None, None)
            if not self.window:
                glfw.terminate()
                raise GLContextError(
                    "Failed to create GLFW window.\n"
                    "Possible solutions:\n"
                    "  1. Update your GPU drivers\n"
                    "  2. Check if your GPU supports OpenGL 3.3+\n"
                    "  3. Try running with integrated graphics if you have multiple GPUs"
                )
            
            logger.info(f"GLFW window created: {self.width}x{self.height}")
            
            # Make context current
            glfw.make_context_current(self.window)
            glfw.swap_interval(1)  # Enable vsync
            
            # Create moderngl context
            self.ctx = moderngl.create_context()
            if not self.ctx:
                raise GLContextError("Failed to create ModernGL context")
            
            logger.info(f"ModernGL context created: OpenGL {self.ctx.version_code}")
            
            # Enable depth testing and face culling
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.enable(moderngl.CULL_FACE)
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            
            # Create framebuffer for offscreen rendering
            self._create_framebuffer()
            
            logger.success("OpenGL context initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL context: {e}")
            self.cleanup()
            raise GLContextError(str(e))
    
    def _create_framebuffer(self) -> None:
        """
        Create framebuffer object for offscreen rendering.
        """
        try:
            # Create render texture
            self.render_texture = self.ctx.texture(
                (self.width, self.height),
                components=4,
                dtype='f1'
            )
            self.render_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            
            # Create depth buffer
            self.depth_buffer = self.ctx.depth_renderbuffer(
                (self.width, self.height)
            )
            
            # Create framebuffer
            self.fbo = self.ctx.framebuffer(
                color_attachments=[self.render_texture],
                depth_attachment=self.depth_buffer
            )
            
            logger.info("Framebuffer created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create framebuffer: {e}")
            raise GLContextError(f"Framebuffer creation failed: {e}")
    
    def resize(self, width: int, height: int) -> None:
        """
        Resize the framebuffer.
        
        Args:
            width: New width
            height: New height
        """
        if width == self.width and height == self.height:
            return
        
        self.width = width
        self.height = height
        
        # Recreate framebuffer with new size
        if self.fbo:
            self.fbo.release()
        if self.render_texture:
            self.render_texture.release()
        if self.depth_buffer:
            self.depth_buffer.release()
        
        self._create_framebuffer()
        logger.info(f"Framebuffer resized to {width}x{height}")
    
    def begin_offscreen_render(self) -> None:
        """
        Begin rendering to the offscreen framebuffer.
        """
        self.fbo.use()
        self.fbo.clear(0.0, 0.0, 0.0, 0.0)  # Clear with transparent background
    
    def end_offscreen_render(self) -> None:
        """
        End offscreen rendering.
        """
        # Bind default framebuffer
        self.ctx.screen.use()
    
    def read_pixels(self) -> np.ndarray:
        """
        Read pixels from the framebuffer.
        
        Returns:
            RGBA image as numpy array (height, width, 4)
        """
        data = self.fbo.read(components=4, dtype='f1')
        image = np.frombuffer(data, dtype=np.uint8).reshape((self.height, self.width, 4))
        
        # Flip vertically (OpenGL origin is bottom-left)
        image = np.flipud(image)
        
        return image
    
    def should_close(self) -> bool:
        """
        Check if window should close.
        
        Returns:
            True if window should close
        """
        return glfw.window_should_close(self.window) if self.window else True
    
    def swap_buffers(self) -> None:
        """
        Swap front and back buffers.
        """
        if self.window:
            glfw.swap_buffers(self.window)
    
    def poll_events(self) -> None:
        """
        Process pending events.
        """
        glfw.poll_events()
    
    def cleanup(self) -> None:
        """
        Clean up OpenGL resources.
        """
        logger.info("Cleaning up OpenGL context")
        
        if self.fbo:
            self.fbo.release()
            self.fbo = None
        
        if self.render_texture:
            self.render_texture.release()
            self.render_texture = None
        
        if self.depth_buffer:
            self.depth_buffer.release()
            self.depth_buffer = None
        
        if self.ctx:
            self.ctx.release()
            self.ctx = None
        
        if self.window:
            glfw.destroy_window(self.window)
            self.window = None
        
        glfw.terminate()
        logger.info("OpenGL cleanup complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
