#pragma once

#include <optional>
#include <vector>

namespace nightfall::camera {

struct Vec3 {
    float x{0.0f};
    float y{0.0f};
    float z{0.0f};
};

struct AABB {
    Vec3 min;
    Vec3 max;
};

struct CameraRig {
    Vec3 position{};
    Vec3 look_at{};
    Vec3 up{0.0f, 1.0f, 0.0f};
    float field_of_view{60.0f};
    float near_clip{0.1f};
    float far_clip{500.0f};
};

struct CameraState {
    CameraRig rig{};
    bool cinematic{false};
};

struct CinematicKeyframe {
    float time{0.0f};
    Vec3 position{};
    Vec3 look_at{};
    float field_of_view{60.0f};
};

class CollisionResolver {
public:
    explicit CollisionResolver(float radius = 0.5f);

    [[nodiscard]] Vec3 resolve(const Vec3& desired_position, const std::vector<AABB>& obstacles) const;

private:
    float radius_;
};

class PlayerCamera {
public:
    PlayerCamera();

    void set_follow_offset(const Vec3& offset);
    void set_look_offset(const Vec3& offset);
    void set_stiffness(float position_stiffness, float look_stiffness);
    void set_target(const Vec3& position, const Vec3& velocity);
    void update(float delta_time, const CollisionResolver& resolver, const std::vector<AABB>& obstacles);

    [[nodiscard]] const CameraRig& rig() const noexcept { return rig_; }

private:
    Vec3 target_position_{};
    Vec3 target_velocity_{};
    Vec3 follow_offset_{0.0f, 4.0f, -9.0f};
    Vec3 look_offset_{0.0f, 2.0f, 0.0f};
    CameraRig rig_{};
    float position_stiffness_{6.0f};
    float look_stiffness_{8.0f};
};

class CinematicCamera {
public:
    void play(std::vector<CinematicKeyframe> keyframes, bool loop = false);
    void stop();
    void update(float delta_time);

    [[nodiscard]] bool is_active() const noexcept { return active_; }
    [[nodiscard]] CameraRig rig() const;

private:
    std::vector<CinematicKeyframe> keyframes_{};
    float elapsed_{0.0f};
    bool active_{false};
    bool loop_{false};
};

class CameraSystem {
public:
    explicit CameraSystem(float collision_radius = 0.5f);

    void set_player_target(const Vec3& position, const Vec3& velocity);
    void configure_player_offsets(const Vec3& follow_offset, const Vec3& look_offset);
    void configure_player_stiffness(float position_stiffness, float look_stiffness);

    void play_cinematic(std::vector<CinematicKeyframe> keyframes, float blend_duration, bool loop = false);
    void stop_cinematic(float blend_duration = 0.25f);

    CameraState update(float delta_time, const std::vector<AABB>& obstacles);

private:
    CollisionResolver resolver_;
    PlayerCamera player_{};
    CinematicCamera cinematic_{};
    float blend_timer_{0.0f};
    float blend_duration_{0.0f};
    CameraRig previous_rig_{};
    CameraRig active_rig_{};
    bool blending_{false};
};

Vec3 lerp(const Vec3& a, const Vec3& b, float t);
Vec3 clamp_vec(const Vec3& value, const Vec3& min, const Vec3& max);
Vec3 operator+(const Vec3& lhs, const Vec3& rhs);
Vec3 operator-(const Vec3& lhs, const Vec3& rhs);
Vec3 operator*(const Vec3& value, float scalar);
Vec3 operator*(float scalar, const Vec3& value);
Vec3 operator/(const Vec3& value, float scalar);
float dot(const Vec3& lhs, const Vec3& rhs);
float length(const Vec3& value);
Vec3 normalize(const Vec3& value);

}  // namespace nightfall::camera

