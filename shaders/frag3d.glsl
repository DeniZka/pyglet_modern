#version 330
in vec2 textures;

//out vec4 outColor;
uniform sampler2D sampTexture;


float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

int get(vec2 offset) {
    vec4 tex = texture(sampTexture, (gl_FragCoord.xy + offset) / 1.2f);
    int ret = 0;
    if (rand(tex.ra) > 0.5) {
        ret = 1;
    }

    return ret;
}

void main()
{
    int sum =
        get(vec2(-1.0, -1.0)) +
        get(vec2(-1.0,  0.0)) +
        get(vec2(-1.0,  1.0)) +
        get(vec2( 0.0, -1.0)) +
        get(vec2( 0.0,  1.0)) +
        get(vec2( 1.0, -1.0)) +
        get(vec2( 1.0,  0.0)) +
        get(vec2( 1.0,  1.0));
    if (sum == 3) {
        gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
    } else if (sum == 2) {
        float current = float(get(vec2(0.0, 0.0)));
        gl_FragColor = vec4(current, current, current, 1.0);
    } else {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        gl_FragColor = texture(sampTexture, textures.xy);
    }
}
