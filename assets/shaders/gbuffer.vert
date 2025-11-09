#version 450 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;
layout(location = 3) in vec4 in_color;

layout(location = 0) out vec3 v_world_position;
layout(location = 1) out vec3 v_normal;
layout(location = 2) out vec2 v_uv;
layout(location = 3) out vec4 v_color;

layout(std140, binding = 0) uniform FrameUniforms {
    mat4 u_view_projection;
    mat4 u_model;
};

void main() {
    vec4 world = u_model * vec4(in_position, 1.0);
    v_world_position = world.xyz;
    v_normal = mat3(u_model) * in_normal;
    v_uv = in_uv;
    v_color = in_color;
    gl_Position = u_view_projection * world;
}
