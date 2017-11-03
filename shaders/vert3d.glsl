#version 330
layout(location = 0) in vec3 position;      //important thing! pyglet push vertixes there
layout(location = 1) in vec3 textureCoords; //setted up in pyglet layout.py as ('1g3f/dynamic', tex_coords),
layout(location = 2) in vec4 vertColor;

uniform int coloring = 0;
uniform mat4 proj;
uniform mat4 view;
uniform mat4 rotation = mat4(
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);
uniform mat4 translation = mat4(
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);
uniform mat4 scale = mat4(
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);
uniform mat4 parent = mat4(
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);
uniform mat4 trfm = mat4 (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
);

out vec3 textures;
out vec4 color;


void main()
{
    gl_Position = proj * view * parent * trfm * translation * rotation * scale * vec4(position, 1.0f);
    //if (coloring == 0) {
        textures = textureCoords;
    //} else {
        color = vertColor;
    //}
}
