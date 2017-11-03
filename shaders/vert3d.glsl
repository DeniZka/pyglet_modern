#version 330

#define m_identity mat4 ( \
    1.0, 0.0, 0.0, 0.0,   \
    0.0, 1.0, 0.0, 0.0,   \
    0.0, 0.0, 1.0, 0.0,   \
    0.0, 0.0, 0.0, 1.0    \
);

layout(location = 0) in vec3 position;      //0 is static for vertixes
layout(location = 1) in vec3 textureCoords; //1 is static for texture uvw
layout(location = 2) in vec4 vertColor;     //2 is static for colors

uniform int coloring = 0;
uniform mat4 proj = m_identity;
uniform mat4 view = m_identity;
uniform mat4 trfm = m_identity;

out vec3 textures;
out vec4 color;

void main()
{
    gl_Position = proj * view * trfm * vec4(position, 1.0f);
    textures = textureCoords;
    color = vertColor;
}
