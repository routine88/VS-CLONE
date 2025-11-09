#include "CameraSystem.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace nightfall::camera {

namespace {
constexpr float kEpsilon = 1e-4f;

float clamp01(float value) {
    return std::clamp(value, 0.0f, 1.0f);
}

Vec3 subtract(const Vec3& a, const Vec3& b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

Vec3 add(const Vec3& a, const Vec3& b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}

Vec3 multiply(const Vec3& value, float scalar) {
    return {value.x * scalar, value.y * scalar, value.z * scalar};
}

float length_squared(const Vec3& value) {
    return dot(value, value);
}

}  // namespace

Vec3 operator+(const Vec3& lhs, const Vec3& rhs) {
    return add(lhs, rhs);
}

Vec3 operator-(const Vec3& lhs, const Vec3& rhs) {
    return subtract(lhs, rhs);
}

Vec3 operator*(const Vec3& value, float scalar) {
    return multiply(value, scalar);
}

Vec3 operator*(float scalar, const Vec3& value) {
    return multiply(value, scalar);
}

Vec3 operator/(const Vec3& value, float scalar) {
    if (std::fabs(scalar) <= kEpsilon) {
        return {0.0f, 0.0f, 0.0f};
    }
    return {value.x / scalar, value.y / scalar, value.z / scalar};
}

Vec3 lerp(const Vec3& a, const Vec3& b, float t) {
    return a + (b - a) * clamp01(t);
}

Vec3 clamp_vec(const Vec3& value, const Vec3& min, const Vec3& max) {
    return {
        std::clamp(value.x, min.x, max.x),
        std::clamp(value.y, min.y, max.y),
        std::clamp(value.z, min.z, max.z),
    };
}

float dot(const Vec3& lhs, const Vec3& rhs) {
    return lhs.x * rhs.x + lhs.y * rhs.y + lhs.z * rhs.z;
}

float length(const Vec3& value) {
    return std::sqrt(dot(value, value));
}

Vec3 normalize(const Vec3& value) {
    float len = length(value);
    if (len <= kEpsilon) {
        return {0.0f, 0.0f, 0.0f};
    }
    return value / len;
}

CollisionResolver::CollisionResolver(float radius) : radius_(std::max(radius, 0.0f)) {}

Vec3 CollisionResolver::resolve(const Vec3& desired_position, const std::vector<AABB>& obstacles) const {
    Vec3 corrected = desired_position;
    float radius_sq = radius_ * radius_;
    for (const AABB& box : obstacles) {
        Vec3 clamped = clamp_vec(corrected, box.min, box.max);
        Vec3 delta = corrected - clamped;
        float distance_sq = length_squared(delta);
        if (distance_sq < radius_sq) {
            if (distance_sq > kEpsilon) {
                Vec3 push = normalize(delta) * radius_;
                corrected = clamped + push;
            } else {
                // Degenerate case: camera center is inside the box without direction information.
                corrected.y = box.max.y + radius_;
            }
        }
    }
    return corrected;
}

PlayerCamera::PlayerCamera() {
    rig_.position = follow_offset_;
    rig_.look_at = {0.0f, 0.0f, 0.0f};
    rig_.up = {0.0f, 1.0f, 0.0f};
}

void PlayerCamera::set_follow_offset(const Vec3& offset) {
    follow_offset_ = offset;
}

void PlayerCamera::set_look_offset(const Vec3& offset) {
    look_offset_ = offset;
}

void PlayerCamera::set_stiffness(float position_stiffness, float look_stiffness) {
    position_stiffness_ = std::max(position_stiffness, 0.0f);
    look_stiffness_ = std::max(look_stiffness, 0.0f);
}

void PlayerCamera::set_target(const Vec3& position, const Vec3& velocity) {
    target_position_ = position;
    target_velocity_ = velocity;
}

void PlayerCamera::update(float delta_time, const CollisionResolver& resolver, const std::vector<AABB>& obstacles) {
    Vec3 desired_position = target_position_ + follow_offset_;
    Vec3 resolved_position = resolver.resolve(desired_position, obstacles);
    float position_alpha = 1.0f - std::exp(-position_stiffness_ * std::max(delta_time, 0.0f));
    rig_.position = lerp(rig_.position, resolved_position, position_alpha);

    Vec3 desired_look = target_position_ + look_offset_;
    float look_alpha = 1.0f - std::exp(-look_stiffness_ * std::max(delta_time, 0.0f));
    rig_.look_at = lerp(rig_.look_at, desired_look, look_alpha);
    rig_.up = {0.0f, 1.0f, 0.0f};
}

void CinematicCamera::play(std::vector<CinematicKeyframe> keyframes, bool loop) {
    keyframes_ = std::move(keyframes);
    std::sort(keyframes_.begin(), keyframes_.end(), [](const CinematicKeyframe& a, const CinematicKeyframe& b) {
        return a.time < b.time;
    });
    elapsed_ = 0.0f;
    loop_ = loop;
    active_ = !keyframes_.empty();
}

void CinematicCamera::stop() {
    active_ = false;
    elapsed_ = 0.0f;
    keyframes_.clear();
    loop_ = false;
}

void CinematicCamera::update(float delta_time) {
    if (!active_) {
        return;
    }
    if (keyframes_.empty()) {
        active_ = false;
        return;
    }
    elapsed_ += std::max(delta_time, 0.0f);
    float end_time = keyframes_.back().time;
    if (loop_ && end_time > 0.0f) {
        while (elapsed_ > end_time) {
            elapsed_ -= end_time;
        }
    } else if (elapsed_ > end_time) {
        elapsed_ = end_time;
        if (!loop_) {
            // Leave the cinematic active so callers can blend out smoothly.
        }
    }
}

CameraRig CinematicCamera::rig() const {
    CameraRig rig{};
    if (keyframes_.empty()) {
        return rig;
    }
    float time = std::clamp(elapsed_, keyframes_.front().time, keyframes_.back().time);
    const CinematicKeyframe* start = &keyframes_.front();
    const CinematicKeyframe* end = start;
    for (const CinematicKeyframe& keyframe : keyframes_) {
        if (keyframe.time <= time) {
            start = &keyframe;
        }
        if (keyframe.time >= time) {
            end = &keyframe;
            break;
        }
    }
    if (start == end) {
        rig.position = start->position;
        rig.look_at = start->look_at;
        rig.field_of_view = start->field_of_view;
        return rig;
    }
    float segment_duration = std::max(end->time - start->time, kEpsilon);
    float t = (time - start->time) / segment_duration;
    rig.position = lerp(start->position, end->position, t);
    rig.look_at = lerp(start->look_at, end->look_at, t);
    rig.field_of_view = start->field_of_view + (end->field_of_view - start->field_of_view) * t;
    return rig;
}

CameraSystem::CameraSystem(float collision_radius) : resolver_(collision_radius) {
    active_rig_ = player_.rig();
    previous_rig_ = active_rig_;
}

void CameraSystem::set_player_target(const Vec3& position, const Vec3& velocity) {
    player_.set_target(position, velocity);
}

void CameraSystem::configure_player_offsets(const Vec3& follow_offset, const Vec3& look_offset) {
    player_.set_follow_offset(follow_offset);
    player_.set_look_offset(look_offset);
}

void CameraSystem::configure_player_stiffness(float position_stiffness, float look_stiffness) {
    player_.set_stiffness(position_stiffness, look_stiffness);
}

void CameraSystem::play_cinematic(std::vector<CinematicKeyframe> keyframes, float blend_duration, bool loop) {
    previous_rig_ = active_rig_;
    cinematic_.play(std::move(keyframes), loop);
    blend_duration_ = std::max(blend_duration, 0.0f);
    blend_timer_ = 0.0f;
    blending_ = blend_duration_ > 0.0f;
}

void CameraSystem::stop_cinematic(float blend_duration) {
    if (cinematic_.is_active()) {
        previous_rig_ = cinematic_.rig();
        active_rig_ = previous_rig_;
    } else {
        previous_rig_ = active_rig_;
    }
    cinematic_.stop();
    blend_duration_ = std::max(blend_duration, 0.0f);
    blend_timer_ = 0.0f;
    blending_ = blend_duration_ > 0.0f;
}

CameraState CameraSystem::update(float delta_time, const std::vector<AABB>& obstacles) {
    player_.update(delta_time, resolver_, obstacles);
    cinematic_.update(delta_time);

    CameraRig target_rig = player_.rig();
    bool cinematic_active = cinematic_.is_active();
    if (cinematic_active) {
        CameraRig cinematic_rig = cinematic_.rig();
        cinematic_rig.position = resolver_.resolve(cinematic_rig.position, obstacles);
        target_rig = cinematic_rig;
    }

    if (blending_) {
        blend_timer_ += delta_time;
        float t = blend_duration_ > 0.0f ? clamp01(blend_timer_ / blend_duration_) : 1.0f;
        active_rig_.position = lerp(previous_rig_.position, target_rig.position, t);
        active_rig_.look_at = lerp(previous_rig_.look_at, target_rig.look_at, t);
        active_rig_.up = lerp(previous_rig_.up, target_rig.up, t);
        active_rig_.field_of_view = previous_rig_.field_of_view + (target_rig.field_of_view - previous_rig_.field_of_view) * t;
        active_rig_.near_clip = previous_rig_.near_clip + (target_rig.near_clip - previous_rig_.near_clip) * t;
        active_rig_.far_clip = previous_rig_.far_clip + (target_rig.far_clip - previous_rig_.far_clip) * t;
        if (t >= 1.0f - kEpsilon) {
            blending_ = false;
            previous_rig_ = target_rig;
        }
    } else {
        active_rig_ = target_rig;
        previous_rig_ = target_rig;
    }

    return CameraState{active_rig_, cinematic_active};
}

}  // namespace nightfall::camera

