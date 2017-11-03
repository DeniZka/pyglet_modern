#version 330
in vec4 color;
in vec3 textures;

uniform sampler2D sampTexture;
uniform int coloring = 0;
uniform float time = 0.0f;

#define color_none 0
#define color_sum 1
uniform int colorize = color_none;
uniform vec4 clr_clr = vec4(0.0, 0.0, 0.0, 0.0);

out vec4 outColor;


#define iterations 17
#define formuparam 0.53

#define volsteps 20
#define stepsize 0.1

#define zoom   0.800
#define tile   0.850
#define speed  0.010

#define brightness 0.0015
#define darkmatter 0.300
#define distfading 0.730
#define saturation 0.850


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
    if (coloring == 1) {
    	//get coords and direction
        vec2 uv=gl_FragCoord.xy/vec2(800.0,600.0)-.001;
        uv.y*=600.0/800.0;
        vec3 dir=vec3(uv*zoom,1.);
        float rtime=time*speed+.25;
        vec3 from=vec3(1.,.5,0.5);
        from+=vec3(rtime*2.,rtime,-2.);

        //volumetric rendering
        float s=0.2,fade=1.5;
        vec3 v=vec3(0.);
        for (int r=0; r<volsteps; r++) {
            vec3 p=from+s*dir*.5;
            p = abs(vec3(tile)-mod(p,vec3(tile*1.5))); // tiling fold
            float pa,a=pa=1.;
            for (int i=0; i<iterations; i++) {
                p=abs(p)/dot(p,p)-formuparam; // the magic formula
                a+=abs(length(p)-pa); // absolute sum of average change
                pa=length(p);
            }
            float dm=max(0.183764372039847189,darkmatter-a*a*.1); //dark matter
            a*=a*a; // add contrast
            if (r>6) fade*=1.2-dm; // dark matter, don't render near
            //v+=vec3(dm,dm*.5,0.);
            //v+=fade;
            v+=vec3(s,s*s,s*s*s*s)*a*brightness*fade; // coloring based on distance
            fade*=distfading; // distance fading
            s+=stepsize;
        }
        v=mix(vec3(length(v)),v,saturation); //color adjust
        outColor = vec4(v*.006,1000.);
        //outColor = vec4(color.r * sin(time), color.gba);
        outColor = color;
    } else {
        vec4 clr = texture(sampTexture, textures.xy);
        if (colorize == 0) {
            outColor = clr;
        } else {
            outColor = vec4(vec3(clr.rgb + color.rgb), clr.a*color.a);
        }
    }
}
