#version 450 core

layout(location = 0) out vec4 out_color;

layout(binding = 0) uniform sampler2D u_lighting_buffer;
layout(binding = 1) uniform sampler2D u_bloom_buffer;

layout(push_constant) uniform ToneMappingParams {
    float exposure;
    float bloom_intensity;
    int operator_id;
} u_params;

vec3 tone_map(vec3 color) {
    if (u_params.operator_id == 1) {
        return color / (color + vec3(1.0));
    }
    if (u_params.operator_id == 2) {
        return clamp(color, 0.0, 1.0);
    }
    const float A = 2.51;
    const float B = 0.03;
    const float C = 2.43;
    const float D = 0.59;
    const float E = 0.14;
    vec3 x = color;
    return clamp((x * (A * x + B)) / (x * (C * x + D) + E), 0.0, 1.0);
}

void main() {
    ivec2 texel = ivec2(gl_FragCoord.xy);
    vec3 lighting = texelFetch(u_lighting_buffer, texel, 0).rgb;
    vec3 bloom = texelFetch(u_bloom_buffer, texel, 0).rgb * u_params.bloom_intensity;
    vec3 color = (lighting + bloom) * u_params.exposure;
    out_color = vec4(tone_map(color), 1.0);
}
