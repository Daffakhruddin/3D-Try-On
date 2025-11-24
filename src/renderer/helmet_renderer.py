"""
Helmet renderer that combines 3D rendering with webcam feed.
"""

import numpy as np
import moderngl
from typing import Optional, Tuple
from loguru import logger
import os

from renderer.model_loader import ModelData, ModelLoader
from renderer.gl_context import GLContext
from utils.math_utils import create_transformation_matrix, create_projection_matrix
from config import RenderConfig


class ShaderCompileError(Exception):
    """Custom exception for shader compilation errors."""
    pass


class HelmetRenderer:
    """
    Renders 3D helmet model with head pose transformation.
    """
    
    def __init__(
        self,
        gl_context: GLContext,
        model_path: str,
        vertex_shader_path: str,
        fragment_shader_path: str,
        config: RenderConfig
    ):
        """
        Initialize helmet renderer.
        
        Args:
            gl_context: OpenGL context
            model_path: Path to helmet GLB file
            vertex_shader_path: Path to vertex shader
            fragment_shader_path: Path to fragment shader
            config: Render configuration
        """
        self.gl_context = gl_context
        self.ctx = gl_context.ctx
        self.config = config
        
        # Load model
        self.model_data: Optional[ModelData] = None
        self._load_model(model_path)
        
        # Load and compile shaders
        self.program: Optional[moderngl.Program] = None
        self._load_shaders(vertex_shader_path, fragment_shader_path)
        
        # Create GPU buffers
        self.vbo: Optional[moderngl.Buffer] = None
        self.ibo: Optional[moderngl.Buffer] = None
        self.vao: Optional[moderngl.VertexArray] = None
        self.texture: Optional[moderngl.Texture] = None
        self._create_buffers()
        
        # Create projection matrix
        aspect_ratio = config.window_width / config.window_height
        self.projection_matrix = create_projection_matrix(
            config.fov_degrees,
            aspect_ratio,
            config.near_plane,
            config.far_plane
        )
        
        logger.success("Helmet renderer initialized")
    
    def _load_model(self, model_path: str) -> None:
        """
        Load 3D model.
        
        Args:
            model_path: Path to GLB file
        """
        try:
            self.model_data = ModelLoader.load_glb(model_path)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _load_shaders(self, vertex_path: str, fragment_path: str) -> None:
        """
        Load and compile shaders.
        
        Args:
            vertex_path: Path to vertex shader
            fragment_path: Path to fragment shader
            
        Raises:
            ShaderCompileError: If shader compilation fails
        """
        try:
            # Read shader sources
            if not os.path.exists(vertex_path):
                raise ShaderCompileError(f"Vertex shader not found: {vertex_path}")
            if not os.path.exists(fragment_path):
                raise ShaderCompileError(f"Fragment shader not found: {fragment_path}")
            
            with open(vertex_path, 'r') as f:
                vertex_source = f.read()
            
            with open(fragment_path, 'r') as f:
                fragment_source = f.read()
            
            logger.info("Compiling shaders...")
            
            # Compile shader program
            try:
                self.program = self.ctx.program(
                    vertex_shader=vertex_source,
                    fragment_shader=fragment_source
                )
                logger.success("Shaders compiled successfully")
            except Exception as e:
                # Extract and log GLSL error
                error_msg = str(e)
                logger.error(f"Shader compilation failed:\n{error_msg}")
                raise ShaderCompileError(f"Shader compilation error: {error_msg}")
                
        except ShaderCompileError:
            raise
        except Exception as e:
            logger.error(f"Failed to load shaders: {e}")
            raise ShaderCompileError(str(e))
    
    def _create_buffers(self) -> None:
        """
        Create GPU buffers for vertex data.
        """
        try:
            # Interleave vertex data: position (3) + normal (3) + texcoord (2)
            vertices = self.model_data.vertices
            normals = self.model_data.normals
            texcoords = self.model_data.texcoords
            
            # Ensure all arrays have same length
            num_vertices = len(vertices)
            if len(normals) != num_vertices:
                logger.warning(f"Normal count mismatch: {len(normals)} vs {num_vertices}")
                normals = np.zeros((num_vertices, 3), dtype=np.float32)
            if len(texcoords) != num_vertices:
                logger.warning(f"Texcoord count mismatch: {len(texcoords)} vs {num_vertices}")
                texcoords = np.zeros((num_vertices, 2), dtype=np.float32)
            
            # Interleave data
            vertex_data = np.hstack([vertices, normals, texcoords]).astype(np.float32)
            
            # Create vertex buffer
            self.vbo = self.ctx.buffer(vertex_data.tobytes())
            
            # Create index buffer
            self.ibo = self.ctx.buffer(self.model_data.indices.tobytes())
            
            # Create vertex array object
            self.vao = self.ctx.vertex_array(
                self.program,
                [
                    (self.vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_texcoord')
                ],
                self.ibo
            )
            
            # Create texture
            if self.model_data.has_texture:
                texture_data = self.model_data.texture_image
            else:
                texture_data = ModelLoader.create_fallback_texture()
            
            self.texture = self.ctx.texture(
                (texture_data.shape[1], texture_data.shape[0]),
                components=4,
                data=texture_data.tobytes()
            )
            self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.texture.build_mipmaps()
            
            logger.info("GPU buffers created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create GPU buffers: {e}")
            raise
    
    def render(
        self,
        rvec: Optional[np.ndarray],
        tvec: Optional[np.ndarray],
        helmet_visible: bool = True
    ) -> np.ndarray:
        """
        Render helmet with given pose.
        
        Args:
            rvec: Rotation vector (3, 1)
            tvec: Translation vector (3, 1)
            helmet_visible: Whether to render helmet
            
        Returns:
            Rendered image as numpy array (RGBA)
        """
        # Begin offscreen rendering
        self.gl_context.begin_offscreen_render()
        
        # Only render if helmet should be visible and pose is valid
        if helmet_visible and rvec is not None and tvec is not None:
            try:
                # Create model transformation matrix
                model_matrix = create_transformation_matrix(
                    rvec,
                    tvec,
                    scale=self.config.helmet_scale * self.model_data.scale,
                    offset_y=self.config.helmet_offset_y,
                    offset_z=self.config.helmet_offset_z
                )
                
                # Set uniforms
                self.program['model'].write(model_matrix.T.astype('f4').tobytes())
                self.program['projection'].write(self.projection_matrix.T.astype('f4').tobytes())
                
                # Lighting uniforms
                if self.config.enable_lighting:
                    self.program['ambientStrength'].value = self.config.ambient_strength
                    self.program['diffuseStrength'].value = self.config.diffuse_strength
                    self.program['lightPos'].value = (0.0, 1.0, 1.0)
                    self.program['lightColor'].value = (1.0, 1.0, 1.0)
                else:
                    self.program['ambientStrength'].value = 1.0
                    self.program['diffuseStrength'].value = 0.0
                
                self.program['opacity'].value = self.config.helmet_opacity
                
                # Bind texture
                self.texture.use(0)
                self.program['textureSampler'].value = 0
                self.program['useTexture'].value = 1 if self.model_data.has_texture else 0
                
                # Draw
                self.vao.render(moderngl.TRIANGLES)
                
            except Exception as e:
                logger.error(f"Rendering error: {e}")
        
        # End offscreen rendering
        self.gl_context.end_offscreen_render()
        
        # Read pixels from framebuffer
        rendered_image = self.gl_context.read_pixels()
        
        return rendered_image
    
    def cleanup(self) -> None:
        """
        Release GPU resources.
        """
        logger.info("Cleaning up helmet renderer")
        
        if self.vao:
            self.vao.release()
        if self.vbo:
            self.vbo.release()
        if self.ibo:
            self.ibo.release()
        if self.texture:
            self.texture.release()
        if self.program:
            self.program.release()
        
        logger.info("Helmet renderer cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass
