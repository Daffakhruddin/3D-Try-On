#version 330 core

// Input from vertex shader
in vec3 fragPosition;
in vec3 fragNormal;
in vec2 fragTexCoord;

// Output color
out vec4 fragColor;

// Uniforms
uniform sampler2D textureSampler;
uniform int useTexture;
uniform float opacity;

// Lighting uniforms
uniform vec3 lightPos;
uniform vec3 lightColor;
uniform float ambientStrength;
uniform float diffuseStrength;

void main()
{
    // Base color from texture or default white
    vec4 baseColor;
    if (useTexture == 1) {
        baseColor = texture(textureSampler, fragTexCoord);
    } else {
        baseColor = vec4(0.8, 0.8, 0.8, 1.0);  // Default gray
    }
    
    // Ambient lighting
    vec3 ambient = ambientStrength * lightColor;
    
    // Diffuse lighting
    vec3 norm = normalize(fragNormal);
    vec3 lightDir = normalize(lightPos - fragPosition);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diffuseStrength * diff * lightColor;
    
    // Combine lighting with base color
    vec3 result = (ambient + diffuse) * baseColor.rgb;
    
    // Apply opacity
    fragColor = vec4(result, baseColor.a * opacity);
    
    // Discard fully transparent fragments
    if (fragColor.a < 0.01) {
        discard;
    }
}
