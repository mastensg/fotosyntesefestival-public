uniform vec2 resolution;
uniform vec2 offset;
uniform float order;

attribute vec2 position;
attribute vec2 texcoord;

varying vec2 frag_texcoord;

void
main(void)
{
    vec2 outpos;

    outpos.x = -1.0 + 2.0 * (position.x + offset.x) / 1280.0;
    outpos.y =  1.0 - 2.0 * (position.y + offset.y) / 768.0;

    gl_Position = vec4(outpos, 0.0, 1.0);

    frag_texcoord = texcoord;
}
