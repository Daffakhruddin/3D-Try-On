#version 330 core

// Input vertex attributes
in vec3 in_position;
in vec3 in_normal;
in vec2 in_texcoord;

// Output to fragment shader
out vec3 fragPosition;
out vec3 fragNormal;
out vec2 fragTexCoord;

// Uniform matrices
uniform mat4 model;
uniform mat4 projection;

void main()
{
    // Transform position to clip space
    vec4 worldPosition = model * vec4(in_position, 1.0);
    gl_Position = projection * worldPosition;
    
    // Pass world position to fragment shader
    fragPosition = worldPosition.xyz;
    
    // Transform normal to world space
    // Note: For non-uniform scaling, should use transpose(inverse(model))
    mat3 normalMatrix = mat3(model);
    fragNormal = normalize(normalMatrix * in_normal);
    
    // Pass texture coordinates
    fragTexCoord = in_texcoord;
}
