# Quick Start Guide

## Installation (5 minutes)

### Windows Quick Setup

1. **Open PowerShell** (as regular user, not admin)

2. **Navigate to project**
   ```powershell
   cd "C:\Users\VICTUS 15\Music\project"
   ```

3. **Create virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

4. **Install dependencies**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Get a helmet model**
   - Download a free GLB model from Sketchfab
   - OR use a test cube from Blender
   - Place as `assets\helmet.glb`

6. **Run the application**
   ```powershell
   python src\main.py
   ```

### Linux Quick Setup

```bash
cd ~/project
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Place your model
# mv /path/to/your/model.glb assets/helmet.glb

python src/main.py
```

## First Run Checklist

Before running:
- [ ] Python 3.10+ installed
- [ ] Webcam connected and working
- [ ] GPU drivers updated
- [ ] `assets/helmet.glb` exists
- [ ] Virtual environment activated
- [ ] All dependencies installed

## Testing Installation

### Test 1: Check Python Version
```bash
python --version
# Should output: Python 3.10.x or higher
```

### Test 2: Check Dependencies
```bash
pip list | grep -E "(opencv|mediapipe|moderngl|glfw|trimesh)"
```

Should show:
- opencv-python
- mediapipe
- moderngl
- glfw
- trimesh

### Test 3: Test Camera
```python
python -c "import cv2; cap = cv2.VideoCapture(0); ret, frame = cap.read(); print('Camera OK' if ret else 'Camera FAIL'); cap.release()"
```

### Test 4: Test OpenGL
```python
python -c "import glfw; print('GLFW OK' if glfw.init() else 'GLFW FAIL')"
```

### Test 5: Test MediaPipe
```python
python -c "import mediapipe; print('MediaPipe OK')"
```

## Running the Application

### Standard Run
```bash
# Activate virtual environment first!
# Windows:
.\venv\Scripts\activate
# Linux:
source venv/bin/activate

# Run application
python src\main.py  # Windows
python src/main.py  # Linux
```

### With Debug Output
Edit `src/config.py`:
```python
config.log_level = "DEBUG"
config.show_landmarks = True
```

Then run normally.

## Common First-Time Issues

### Issue 1: "No module named 'cv2'"
**Cause**: Dependencies not installed
**Fix**: 
```bash
pip install -r requirements.txt
```

### Issue 2: "Failed to initialize camera"
**Cause**: Camera in use or wrong device ID
**Fix**: 
1. Close other camera apps (Zoom, Teams, etc.)
2. Try different device ID in `src/config.py`:
   ```python
   config.camera.device_id = 1  # Try 0, 1, 2
   ```

### Issue 3: "Model file not found"
**Cause**: No helmet.glb in assets folder
**Fix**: Download a GLB model and place in `assets/helmet.glb`

### Issue 4: "Failed to create GLFW window"
**Cause**: Outdated GPU drivers or no OpenGL support
**Fix**: 
1. Update GPU drivers
2. Check OpenGL support:
   - Windows: Download OpenGL Extensions Viewer
   - Linux: `glxinfo | grep "OpenGL version"`

### Issue 5: Application freezes or crashes
**Cause**: GPU/driver issues
**Fix**:
1. Update GPU drivers
2. Try integrated GPU instead of dedicated
3. Lower resolution in config:
   ```python
   config.camera.width = 640
   config.camera.height = 480
   ```

## Configuration for First Run

Create `src/config_override.py` (optional):
```python
from config import config

# Lower resolution for slower PCs
config.camera.width = 640
config.camera.height = 480

# Reduce render quality for better performance
config.render.frame_skip = 1

# Increase smoothing for stability
config.face_tracking.smoothing_factor_rotation = 0.5
config.face_tracking.smoothing_factor_translation = 0.5
```

Then import in `main.py`:
```python
from config import config
import config_override  # Your custom settings
```

## Performance Tips for First Run

**For slow computers:**
1. Lower camera resolution: 640x480
2. Enable frame skipping: `frame_skip = 1`
3. Disable lighting: `enable_lighting = False`
4. Use simpler helmet model (< 10,000 polygons)

**For fast computers:**
1. Use 1080p camera: 1920x1080
2. No frame skipping: `frame_skip = 0`
3. Enable all features
4. Use high-quality helmet model

## What to Expect

**First successful run:**
1. Console shows initialization messages
2. Window opens showing webcam feed
3. Face detection starts immediately
4. Helmet appears on your head (if face detected)
5. Helmet follows your head movements
6. FPS counter in top-left corner

**Controls:**
- `Q` or `ESC`: Quit
- `D`: Toggle debug landmarks

**Normal behavior:**
- Helmet may take 1-2 seconds to appear initially
- Helmet freezes briefly if face not detected
- FPS: 25-60 depending on hardware
- Slight delay in movement is normal (smoothing)

## Getting Help

If you're stuck:
1. Check this guide again
2. Review README.md troubleshooting section
3. Check console error messages
4. Enable debug logging (log_level = "DEBUG")
5. Create GitHub issue with:
   - Your OS and version
   - Python version
   - GPU model
   - Complete error message
   - What you tried

## Next Steps

After first successful run:
1. Experiment with different helmet models
2. Adjust configuration for your preference
3. Try different camera angles
4. Test in various lighting conditions
5. Adjust smoothing and scaling parameters

Enjoy your AR Helmet Try-On system! 🎭
