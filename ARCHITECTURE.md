# Architecture Documentation

## System Overview

The AR Helmet Try-On system is a real-time computer vision and 3D rendering application that overlays virtual 3D helmet models onto live webcam footage with proper head tracking and pose estimation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Main Application                        │
│                         (main.py)                               │
└────────────┬────────────────────────────────────────────────────┘
             │
    ┌────────┴─────────┬──────────────┬──────────────┬────────────┐
    │                  │              │              │            │
┌───▼────┐      ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌──▼──┐
│Camera  │      │Face       │  │GL Context │  │Helmet     │  │Utils│
│Module  │      │Tracker    │  │           │  │Renderer   │  │     │
└───┬────┘      └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┘
    │                 │              │              │
    │  Frame          │  Landmarks   │  Render      │  Composite
    │  (BGR)          │  Pose        │  (RGBA)      │  (BGR)
    │                 │  (rvec,tvec) │              │
    └─────────────────┴──────────────┴──────────────┘
```

## Component Breakdown

### 1. Camera Module (`camera.py`)

**Purpose**: Capture video frames from webcam with robust error handling.

**Key Features**:
- OpenCV VideoCapture wrapper
- Automatic retry logic (3 attempts)
- Frame fallback when read fails
- Configurable resolution and FPS

**Flow**:
```
Initialize Camera
    ↓
Set Properties (width, height, fps)
    ↓
Test Frame Capture
    ↓
Main Loop: Read Frame
    ↓ (if fail)
Retry (3x) → Use Last Good Frame
```

**Error Handling**:
- Camera not available → Detailed error with solutions
- Frame read failure → Retry then fallback to last frame
- Resource cleanup on exit

---

### 2. Face Tracker (`face_tracker.py`)

**Purpose**: Detect face and estimate 6DOF head pose.

**Technology**: MediaPipe Face Mesh (468 landmarks)

**Pipeline**:
```
Input Frame (BGR)
    ↓
Convert to RGB
    ↓
MediaPipe Face Mesh Processing
    ↓
Extract Key Landmarks (6 points):
  - Nose tip (1)
  - Chin (152)
  - Left eye outer (263)
  - Right eye outer (33)
  - Left mouth (61)
  - Right mouth (291)
    ↓
solvePnP (2D-3D correspondence)
    ↓
Output: rvec (rotation), tvec (translation)
    ↓
Apply Exponential Smoothing
    ↓
Freeze Pose if Face Lost < 800ms
```

**Key Algorithms**:

1. **PnP Solver**: 
   - Maps 2D image landmarks to 3D model points
   - Uses camera intrinsic matrix
   - Returns rotation vector and translation vector

2. **Pose Smoothing**:
   ```
   smoothed = α * previous + (1-α) * current
   where α = smoothing_factor (0-1)
   ```

3. **Pose Freezing**:
   - If face lost < 800ms: use last good pose
   - If face lost > 2000ms: hide helmet

**Error Recovery**:
- MediaPipe crash → Auto-reinitialize
- solvePnP failure → Use frozen pose
- No detection → Intelligent fallback

---

### 3. GL Context (`renderer/gl_context.py`)

**Purpose**: Manage OpenGL context, window, and framebuffers.

**Technology**: 
- GLFW for window management
- ModernGL for OpenGL bindings

**Setup**:
```
Initialize GLFW
    ↓
Create Window (OpenGL 3.3 Core)
    ↓
Create ModernGL Context
    ↓
Enable: Depth Test, Culling, Blending
    ↓
Create Offscreen Framebuffer (FBO)
    - Render Texture (RGBA)
    - Depth Buffer
```

**Rendering Flow**:
```
Begin Offscreen Render
    ↓
Clear FBO (transparent)
    ↓
Render 3D Content
    ↓
End Offscreen Render
    ↓
Read Pixels from FBO
    ↓
Return RGBA Image
```

**Why Offscreen FBO?**
- Render 3D helmet to texture
- Composite with camera frame using alpha blending
- Avoid Z-fighting with background

---

### 4. Model Loader (`renderer/model_loader.py`)

**Purpose**: Load 3D models from GLB files.

**Technology**: Trimesh library

**Loading Process**:
```
Load GLB File
    ↓
Parse Scene
    ↓
Combine Geometries
    ↓
Extract:
  - Vertices (positions)
  - Normals (lighting)
  - Texture Coordinates (UVs)
  - Indices (triangles)
  - Textures (images)
    ↓
Compute Bounding Box & Scale
    ↓
Return ModelData
```

**Data Structure**:
```python
class ModelData:
    vertices: np.ndarray        # (N, 3) positions
    normals: np.ndarray         # (N, 3) normals
    texcoords: np.ndarray       # (N, 2) UVs
    indices: np.ndarray         # (M,) triangle indices
    texture_image: np.ndarray   # (H, W, 4) RGBA
    bounding_box_min/max
    center
    scale
```

**Fallback**:
- Missing textures → White fallback texture
- Missing normals → Auto-compute from geometry

---

### 5. Helmet Renderer (`renderer/helmet_renderer.py`)

**Purpose**: Render 3D helmet with transformations and lighting.

**Shader Pipeline**:
```
Vertex Shader (helmet.vert)
    ↓
Transform vertices:
  gl_Position = projection * model * position
    ↓
Pass to Fragment Shader:
  - World position
  - Normal (for lighting)
  - Texture coordinates
    ↓
Fragment Shader (helmet.frag)
    ↓
Sample texture
    ↓
Compute Lighting:
  - Ambient (base light)
  - Diffuse (directional light)
    ↓
Combine: color = (ambient + diffuse) * texture
    ↓
Output RGBA with alpha
```

**Transformation Matrix**:
```
Model Matrix = T * R * S

Where:
  T = Translation (from tvec + offsets)
  R = Rotation (from rvec via Rodrigues)
  S = Scale (helmet_scale * model_scale)
```

**GPU Buffers**:
- VBO (Vertex Buffer): Interleaved vertex data
- IBO (Index Buffer): Triangle indices
- VAO (Vertex Array): Attribute bindings
- Texture: 2D RGBA texture with mipmaps

---

### 6. Math Utils (`utils/math_utils.py`)

**Key Functions**:

1. **rodrigues_to_matrix**: Convert OpenCV rotation vector to 3x3 matrix
2. **create_transformation_matrix**: Build 4x4 model matrix
3. **create_projection_matrix**: Perspective projection matrix
4. **create_camera_matrix**: OpenCV camera intrinsic matrix
5. **exponential_smoothing**: Reduce jitter in pose
6. **compute_face_bounding_box**: For adaptive scaling

---

## Data Flow

### Main Loop Flow

```
1. Read Camera Frame
   ↓ (BGR image)
   
2. Process Face Tracking
   ↓ (rvec, tvec, detected)
   
3. Render Helmet
   ↓ (RGBA image with transparency)
   
4. Composite
   result = camera * (1-alpha) + helmet * alpha
   ↓ (BGR image)
   
5. Draw UI (FPS, debug)
   ↓
   
6. Display Frame
```

### Coordinate Systems

**Camera Space**: OpenCV convention
- Origin: Camera center
- +X: Right
- +Y: Down
- +Z: Forward (into scene)

**OpenGL Space**: Right-handed
- Origin: Camera center
- +X: Right
- +Y: Up
- +Z: Backward (toward camera)

**Transformation**: 
- OpenCV rvec/tvec → Model matrix handles conversion
- Projection matrix handles perspective

---

## Performance Optimizations

### 1. Frame Skipping
```python
if frame_skip > 0:
    if frame_count % (frame_skip + 1) != 0:
        continue  # Skip rendering
```

### 2. Pose Smoothing
- Reduces computation by stabilizing pose
- Fewer sudden movements = less GPU work

### 3. Offscreen Rendering
- Render once to FBO
- Efficient alpha compositing

### 4. Mipmapping
- Generate texture mipmaps for better quality and performance
- Hardware-accelerated texture filtering

### 5. Early Exit
- If face not detected → Skip rendering
- Transparent FBO → No overdraw

---

## Error Handling Strategy

### Graceful Degradation

1. **Camera Failure**:
   - Retry 3 times
   - Use last good frame
   - Show detailed error

2. **Face Detection Failure**:
   - Freeze pose (< 800ms)
   - Hide helmet (> 2000ms)
   - Auto-recover when face returns

3. **OpenGL Failure**:
   - Check drivers
   - Suggest solutions
   - Clean up resources

4. **Model Loading Failure**:
   - Clear error message with path
   - Fallback textures
   - Continue with default materials

5. **Shader Compilation Failure**:
   - Print GLSL error log
   - Suggest shader issues
   - Fail safely

---

## Configuration System

**Hierarchical Configuration**:
```
config.py (defaults)
    ↓
config_override.py (user overrides)
    ↓
Runtime modifications
```

**Configuration Categories**:
- Camera: Resolution, FPS, device
- Face Tracking: Confidence, smoothing, timeouts
- Rendering: Quality, lighting, scaling
- Paths: Model, shader locations

---

## Threading Model

**Single-threaded design** for simplicity and stability:
- Main thread handles all operations sequentially
- No race conditions
- Predictable performance
- Easy debugging

**Future Enhancement**: Could parallelize:
- Face detection (separate thread)
- Frame capture (separate thread)
- UI rendering (GPU async)

---

## Memory Management

**Resource Cleanup**:
```
Application Exit
    ↓
Cleanup Helmet Renderer
  - Release VAO, VBO, IBO
  - Release texture
  - Release shader program
    ↓
Cleanup GL Context
  - Release FBO
  - Release ModernGL context
  - Destroy GLFW window
    ↓
Cleanup Face Tracker
  - Close MediaPipe Face Mesh
    ↓
Cleanup Camera
  - Release VideoCapture
    ↓
Destroy OpenCV windows
```

**Automatic Cleanup**:
- Context managers (`__enter__`, `__exit__`)
- Destructors (`__del__`)
- Exception handling ensures cleanup

---

## Testing Strategy

**System Test** (`test_system.py`):
1. Python version check
2. Dependency verification
3. Camera availability
4. OpenGL support
5. MediaPipe initialization
6. Model file presence
7. Shader file presence

**Manual Testing Checklist**:
- [ ] Different lighting conditions
- [ ] Various head rotations
- [ ] Face temporarily occluded
- [ ] Multiple camera angles
- [ ] Different helmet models
- [ ] Performance under load

---

## Extension Points

**Easy to Extend**:

1. **Multiple Helmets**: Add helmet selector UI
2. **Recording**: Add OpenCV VideoWriter
3. **Screenshots**: Add cv2.imwrite on key press
4. **Multi-face**: Increase max_num_faces in config
5. **Custom Shaders**: Swap shader files
6. **Different Models**: Change model_path in config

---

## Troubleshooting Guide

See README.md for detailed troubleshooting.

**Quick Diagnostic**:
```bash
python test_system.py
```

**Common Issues**:
- Camera: Check device_id
- OpenGL: Update drivers
- Model: Verify GLB format
- Performance: Lower resolution or enable frame_skip

---

## Future Enhancements

**Planned Features**:
1. Occlusion handling (hands in front of face)
2. Expression-based animations
3. Multiple helmet library
4. Cloud-based model streaming
5. Mobile port (iOS/Android)
6. WebGL version
7. Multi-user support
8. Recording and playback
9. Social media integration
10. Real-time lighting matching

---

## License

MIT License - See LICENSE file

---

**Built with modern Python practices and production-quality standards** ✨
