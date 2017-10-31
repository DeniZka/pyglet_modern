#version 330
layout(location = 0) in vec2 position;
layout(location = 1) in vec4 color;

uniform mat4 view;
uniform mat4 proj; //some problem when name is projection... last symbol is lost
uniform mat4 trfm = mat4 (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);

out vec4 newColor;

void main()
{

    gl_Position = proj * view * trfm * vec4(position, 0.0f, 1.0f);

    newColor = color;
}