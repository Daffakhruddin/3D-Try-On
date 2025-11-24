"""
3D model loader for GLB/GLTF files using trimesh.
"""

import os
import numpy as np
import trimesh
from typing import Optional, Dict, List, Tuple
from loguru import logger
from PIL import Image


class ModelLoadError(Exception):
    """Custom exception for model loading errors."""
    pass


class ModelData:
    """
    Container for 3D model data.
    """
    
    def __init__(self):
        self.vertices: Optional[np.ndarray] = None
        self.normals: Optional[np.ndarray] = None
        self.texcoords: Optional[np.ndarray] = None
        self.indices: Optional[np.ndarray] = None
        self.texture_image: Optional[np.ndarray] = None
        self.has_texture: bool = False
        self.bounding_box_min: Optional[np.ndarray] = None
        self.bounding_box_max: Optional[np.ndarray] = None
        self.center: Optional[np.ndarray] = None
        self.scale: float = 1.0


class ModelLoader:
    """
    Loads 3D models from GLB/GLTF files.
    """
    
    @staticmethod
    def load_glb(file_path: str) -> ModelData:
        """
        Load a GLB model file.
        
        Args:
            file_path: Path to the GLB file
            
        Returns:
            ModelData object containing all mesh data
            
        Raises:
            ModelLoadError: If model cannot be loaded
        """
        if not os.path.exists(file_path):
            error_msg = f"Model file not found: {file_path}"
            logger.error(error_msg)
            raise ModelLoadError(error_msg)
        
        try:
            logger.info(f"Loading GLB model: {file_path}")
            
            # Load scene using trimesh
            scene = trimesh.load(file_path, force='scene')
            
            if scene is None:
                raise ModelLoadError("Failed to load model scene")
            
            # Combine all geometries in the scene
            if isinstance(scene, trimesh.Scene):
                mesh = scene.dump(concatenate=True)
            else:
                mesh = scene
            
            if mesh is None or not isinstance(mesh, trimesh.Trimesh):
                raise ModelLoadError("Model does not contain valid geometry")
            
            # Create model data
            model_data = ModelData()
            
            # Extract vertices
            model_data.vertices = np.array(mesh.vertices, dtype=np.float32)
            logger.info(f"Loaded {len(model_data.vertices)} vertices")
            
            # Extract normals
            if hasattr(mesh, 'vertex_normals') and mesh.vertex_normals is not None:
                model_data.normals = np.array(mesh.vertex_normals, dtype=np.float32)
            else:
                # Compute normals if not present
                mesh.fix_normals()
                model_data.normals = np.array(mesh.vertex_normals, dtype=np.float32)
            
            # Extract texture coordinates
            if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
                model_data.texcoords = np.array(mesh.visual.uv, dtype=np.float32)
                logger.info(f"Loaded {len(model_data.texcoords)} texture coordinates")
            else:
                # Create dummy texture coordinates
                model_data.texcoords = np.zeros((len(model_data.vertices), 2), dtype=np.float32)
                logger.warning("No texture coordinates found, using default")
            
            # Extract indices
            model_data.indices = np.array(mesh.faces, dtype=np.uint32).flatten()
            logger.info(f"Loaded {len(mesh.faces)} faces")
            
            # Extract texture image
            model_data.texture_image = ModelLoader._extract_texture(mesh)
            model_data.has_texture = model_data.texture_image is not None
            
            # Compute bounding box and center
            model_data.bounding_box_min = mesh.bounds[0]
            model_data.bounding_box_max = mesh.bounds[1]
            model_data.center = mesh.centroid
            
            # Compute scale to normalize model
            extents = mesh.extents
            model_data.scale = 1.0 / max(extents)
            
            logger.success(f"Model loaded successfully: {file_path}")
            logger.info(f"  - Vertices: {len(model_data.vertices)}")
            logger.info(f"  - Faces: {len(mesh.faces)}")
            logger.info(f"  - Has texture: {model_data.has_texture}")
            logger.info(f"  - Bounds: {model_data.bounding_box_min} to {model_data.bounding_box_max}")
            
            return model_data
            
        except Exception as e:
            error_msg = f"Failed to load GLB model '{file_path}': {str(e)}"
            logger.error(error_msg)
            raise ModelLoadError(error_msg)
    
    @staticmethod
    def _extract_texture(mesh: trimesh.Trimesh) -> Optional[np.ndarray]:
        """
        Extract texture image from mesh.
        
        Args:
            mesh: Trimesh object
            
        Returns:
            Texture image as numpy array (RGBA) or None
        """
        try:
            if hasattr(mesh.visual, 'material'):
                material = mesh.visual.material
                
                # Try to get base color texture
                if hasattr(material, 'baseColorTexture') and material.baseColorTexture is not None:
                    texture = material.baseColorTexture
                    if isinstance(texture, Image.Image):
                        # Convert PIL Image to numpy array
                        texture_array = np.array(texture.convert('RGBA'), dtype=np.uint8)
                        logger.info(f"Extracted texture: {texture_array.shape}")
                        return texture_array
                
                # Try to get image from visual
                if hasattr(mesh.visual, 'to_texture') and callable(mesh.visual.to_texture):
                    texture_visual = mesh.visual.to_texture()
                    if hasattr(texture_visual, 'image') and texture_visual.image is not None:
                        texture_array = np.array(texture_visual.image.convert('RGBA'), dtype=np.uint8)
                        logger.info(f"Extracted texture from visual: {texture_array.shape}")
                        return texture_array
            
            logger.warning("No texture found in model")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract texture: {e}")
            return None
    
    @staticmethod
    def create_fallback_texture() -> np.ndarray:
        """
        Create a fallback texture (white color).
        
        Returns:
            White texture as numpy array (RGBA)
        """
        texture = np.ones((256, 256, 4), dtype=np.uint8) * 255
        logger.info("Created fallback white texture")
        return texture
