#version 450 core

layout(location = 0) in vec3 v_world_position;
layout(location = 1) in vec3 v_normal;
layout(location = 2) in vec2 v_uv;
layout(location = 3) in vec4 v_color;

layout(location = 0) out vec4 out_albedo;
layout(location = 1) out vec4 out_normal_roughness;
layout(location = 2) out vec4 out_metallic_emissive;

layout(binding = 0) uniform sampler2D u_albedo_map;
layout(binding = 1) uniform sampler2D u_emissive_map;

struct MaterialUniforms {
    vec3 albedo;
    float roughness;
    vec3 emissive;
    float metallic;
};

layout(std140, binding = 1) uniform MaterialBlock {
    MaterialUniforms u_material;
};

void main() {
    vec4 sampled = texture(u_albedo_map, v_uv) * v_color;
    vec3 albedo = sampled.rgb * u_material.albedo;
    vec3 emissive = texture(u_emissive_map, v_uv).rgb + u_material.emissive;

    out_albedo = vec4(albedo, 1.0);
    out_normal_roughness = vec4(normalize(v_normal), u_material.roughness);
    out_metallic_emissive = vec4(u_material.metallic, emissive);
}
