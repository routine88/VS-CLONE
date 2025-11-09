#version 450 core

layout(location = 0) out vec4 out_color;

layout(binding = 0) uniform sampler2D u_albedo_buffer;
layout(binding = 1) uniform sampler2D u_normal_roughness_buffer;
layout(binding = 2) uniform sampler2D u_material_buffer;

struct DirectionalLight {
    vec3 direction;
    float intensity;
    vec3 color;
    float pad0;
};

layout(std140, binding = 0) uniform LightingBlock {
    vec3 u_ambient_color;
    float u_light_count;
    DirectionalLight u_lights[4];
};

vec3 apply_directional(in vec3 normal, DirectionalLight light, vec3 albedo) {
    float ndotl = max(dot(normal, -light.direction), 0.0);
    return albedo * light.color * (ndotl * light.intensity);
}

void main() {
    ivec2 texel = ivec2(gl_FragCoord.xy);
    vec4 albedo_sample = texelFetch(u_albedo_buffer, texel, 0);
    vec4 normal_sample = texelFetch(u_normal_roughness_buffer, texel, 0);
    vec4 material_sample = texelFetch(u_material_buffer, texel, 0);

    vec3 normal = normalize(normal_sample.xyz);
    float roughness = normal_sample.w;
    vec3 albedo = albedo_sample.rgb;
    vec3 emissive = material_sample.yzw;

    vec3 color = albedo * u_ambient_color;
    for (int index = 0; index < int(u_light_count); ++index) {
        color += apply_directional(normal, u_lights[index], albedo);
    }

    color = mix(color, color * roughness, 0.05);
    color += emissive;
    out_color = vec4(color, albedo_sample.a);
}
