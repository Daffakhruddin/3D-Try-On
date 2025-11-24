"""
System test script to verify all dependencies and hardware.
Run this before starting the main application.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def test_python_version():
    print_header("Testing Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print("✓ Python version OK")
        return True
    else:
        print("✗ Python 3.10+ required")
        return False

def test_imports():
    print_header("Testing Python Dependencies")
    
    modules = {
        'cv2': 'opencv-python',
        'mediapipe': 'mediapipe',
        'numpy': 'numpy',
        'moderngl': 'moderngl',
        'glfw': 'glfw',
        'trimesh': 'trimesh',
        'pyrr': 'pyrr',
        'PIL': 'pillow',
        'loguru': 'loguru',
        'pydantic': 'pydantic'
    }
    
    all_ok = True
    for module, package in modules.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            all_ok = False
    
    return all_ok

def test_camera():
    print_header("Testing Camera Access")
    
    try:
        import cv2
        
        for device_id in range(3):
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✓ Camera {device_id}: {width}x{height}")
                    cap.release()
                    return True
                cap.release()
        
        print("✗ No working camera found")
        return False
        
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False

def test_opengl():
    print_header("Testing OpenGL Support")
    
    try:
        import glfw
        
        if not glfw.init():
            print("✗ GLFW initialization failed")
            return False
        
        # Set window hints for OpenGL 3.3
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        
        window = glfw.create_window(100, 100, "Test", None, None)
        if not window:
            print("✗ Failed to create OpenGL context")
            print("  → Update your GPU drivers")
            glfw.terminate()
            return False
        
        glfw.make_context_current(window)
        
        # Test ModernGL
        import moderngl
        ctx = moderngl.create_context()
        
        print(f"✓ OpenGL {ctx.version_code}")
        print(f"  Vendor: {ctx.info['GL_VENDOR']}")
        print(f"  Renderer: {ctx.info['GL_RENDERER']}")
        
        ctx.release()
        glfw.destroy_window(window)
        glfw.terminate()
        
        return True
        
    except Exception as e:
        print(f"✗ OpenGL test failed: {e}")
        try:
            glfw.terminate()
        except:
            pass
        return False

def test_mediapipe():
    print_header("Testing MediaPipe Face Mesh")
    
    try:
        import mediapipe as mp
        
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        print("✓ MediaPipe Face Mesh initialized")
        face_mesh.close()
        return True
        
    except Exception as e:
        print(f"✗ MediaPipe test failed: {e}")
        return False

def test_model_file():
    print_header("Testing Model File")
    
    model_path = os.path.join(os.path.dirname(__file__), 'assets', 'helmet.glb')
    
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✓ Model file found: {size_mb:.2f} MB")
        return True
    else:
        print(f"✗ Model file not found: {model_path}")
        print("  → Place a GLB model as 'assets/helmet.glb'")
        return False

def test_shaders():
    print_header("Testing Shader Files")
    
    shader_dir = os.path.join(os.path.dirname(__file__), 'shaders')
    vertex_shader = os.path.join(shader_dir, 'helmet.vert')
    fragment_shader = os.path.join(shader_dir, 'helmet.frag')
    
    all_ok = True
    
    if os.path.exists(vertex_shader):
        print(f"✓ Vertex shader found")
    else:
        print(f"✗ Vertex shader missing: {vertex_shader}")
        all_ok = False
    
    if os.path.exists(fragment_shader):
        print(f"✓ Fragment shader found")
    else:
        print(f"✗ Fragment shader missing: {fragment_shader}")
        all_ok = False
    
    return all_ok

def main():
    print("\n" + "=" * 70)
    print("  AR HELMET TRY-ON - SYSTEM TEST")
    print("=" * 70)
    
    results = {
        'Python Version': test_python_version(),
        'Dependencies': test_imports(),
        'Camera': test_camera(),
        'OpenGL': test_opengl(),
        'MediaPipe': test_mediapipe(),
        'Model File': test_model_file(),
        'Shaders': test_shaders()
    }
    
    print_header("TEST SUMMARY")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nYou can now run the application:")
        print("  python src/main.py")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease fix the issues above before running the application.")
        print("See README.md for troubleshooting help.")
    
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
