# Assets Directory

Place your 3D helmet model here as `helmet.glb`.

## Where to Get Helmet Models

### Free Sources:
1. **Sketchfab** (https://sketchfab.com/)
   - Search for "helmet", "iron man helmet", or "sci-fi helmet"
   - Filter by: Free, Downloadable, GLTF/GLB format
   - Download and rename to `helmet.glb`

2. **Poly Pizza** (https://poly.pizza/)
   - Free 3D models
   - Download in GLB format

3. **CGTrader Free** (https://www.cgtrader.com/free-3d-models)
   - Look for GLB format models
   - Free account required

### Creating Your Own:
1. **Blender** (free, open-source)
   - Model or import your helmet
   - File → Export → glTF 2.0 (.glb)
   - Settings:
     - Format: GLB (binary)
     - Include: Selected Objects, Normals, UVs, Vertex Colors
     - Material: Export Materials and Textures

## Example Model Specifications

**Recommended:**
- Format: GLB (binary GLTF 2.0)
- Polygons: 5,000 - 50,000 triangles
- Size: < 10 MB
- Textures: Embedded in GLB
- Texture resolution: 1024x1024 or 2048x2048
- Proper UV unwrapping
- Normals computed

**Iron Man Helmet Example:**
You can find Iron Man helmet models on Sketchfab:
- Search: "Iron Man Helmet"
- Filter: Downloadable, Free
- Download as GLB format
- Place as: `assets/helmet.glb`

## Quick Test Model

If you don't have a model yet, you can create a simple test cube in Blender:
1. Open Blender
2. Default cube is already there
3. File → Export → glTF 2.0
4. Save as `helmet.glb` in this directory

**Note:** The application will show an error if `helmet.glb` is not found.
Update the path in `src/config.py` if using a different filename.
