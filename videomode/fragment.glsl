uniform sampler2D texture;
uniform float fade;
uniform float darken;
uniform float opacity;

varying vec2 frag_texcoord;

void
main(void)
{
    vec4 color = texture2D(texture, frag_texcoord);

    float l = 0.333 * length(color.xyz);

    vec4 bw = vec4(l, l, l, color.w);

    //gl_FragColor = vec4(frag_texcoord.x, frag_texcoord.y, 1.0, 1.0);
    //gl_FragColor = vec4(lighten, lighten, lighten, 1.0);

    //gl_FragColor = vec4(mix(bw, color, fade).xyz - vec3(darken, darken, darken), color.w);
    gl_FragColor = vec4(mix(bw, color, fade).xyz, clamp(color.w, 0.0, opacity));
    //gl_FragColor = vec4(mix(bw, color, fade).xyz, 0.5);
    //gl_FragColor = vec4(color.w, color.w, color.w, 1.0);
}
