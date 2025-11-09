#include "../camera/CameraSystem.h"
#include "../input/InputMapping.h"
#include "../ui/HudRenderer.h"

#include <algorithm>
#include <cmath>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace nightfall::scenes {

using nightfall::camera::AABB;
using nightfall::camera::CameraState;
using nightfall::camera::CameraSystem;
using nightfall::camera::CinematicKeyframe;
using nightfall::camera::Vec3;
using nightfall::input::InputMapping;
using nightfall::input::InputMappingSpec;
using nightfall::input::InputState;
using nightfall::input::RawInputState;
using nightfall::ui::Anchor;
using nightfall::ui::HealthBarElement;
using nightfall::ui::HudContext;
using nightfall::ui::HudRenderer;
using nightfall::ui::OverlayInstruction;
using nightfall::ui::ResolutionConfig;
using nightfall::ui::TextLabelElement;
using nightfall::ui::UltimateMeterElement;

namespace {

constexpr std::string_view kInputManifest = R"json(
{
  "actions": [
    {
      "id": "move_horizontal",
      "bindings": [
        {"device": "keyboard", "control": "KeyA", "scale": -1.0},
        {"device": "keyboard", "control": "KeyD", "scale": 1.0},
        {"device": "gamepad", "kind": "axis", "control": "left_x", "deadzone": 0.25},
        {"device": "mouse", "kind": "axis", "control": "x", "deadzone": 0.25, "interpretation": "digital"}
      ],
      "smoothing": 0.08,
      "analog_threshold": 0.15
    },
    {
      "id": "move_vertical",
      "bindings": [
        {"device": "keyboard", "control": "KeyW", "scale": -1.0},
        {"device": "keyboard", "control": "KeyS", "scale": 1.0},
        {"device": "gamepad", "kind": "axis", "control": "left_y", "deadzone": 0.25}
      ],
      "smoothing": 0.08,
      "analog_threshold": 0.15
    },
    {
      "id": "dash",
      "bindings": [
        {"device": "keyboard", "control": "Space"},
        {"device": "gamepad", "control": "south"},
        {"device": "mouse", "control": "Button4", "toggle": false}
      ]
    },
    {
      "id": "ultimate",
      "bindings": [
        {"device": "keyboard", "control": "KeyQ"},
        {"device": "gamepad", "control": "west"},
        {"device": "mouse", "control": "Button5"}
      ]
    }
  ]
}
)json";

Vec3 make_vec(float x, float y, float z) {
    return Vec3{x, y, z};
}

}  // namespace

class DemoLevel {
public:
    DemoLevel();

    void load();
    void handle_input(const RawInputState& input_state);
    void tick(float delta_time);
    void play_cinematic(const std::vector<CinematicKeyframe>& keyframes, float blend_duration);

    [[nodiscard]] const std::vector<OverlayInstruction>& hud_instructions() const noexcept { return hud_instructions_; }
    [[nodiscard]] const CameraState& camera_state() const noexcept { return camera_state_; }

private:
    void update_player(float delta_time);
    void update_hud(float delta_time);
    void update_camera(float delta_time);

    InputMapping input_mapping_{};
    InputState last_input_state_{};
    CameraSystem camera_system_{};
    HudRenderer hud_renderer_{};
    HudContext hud_context_{};
    CameraState camera_state_{};
    std::vector<AABB> world_geometry_{};
    std::vector<OverlayInstruction> hud_instructions_{};

    Vec3 player_position_{0.0f, 0.0f, 0.0f};
    Vec3 player_velocity_{0.0f, 0.0f, 0.0f};
    float dash_cooldown_{0.0f};
    float ultimate_charge_{0.0f};
};

DemoLevel::DemoLevel() {
    ResolutionConfig config;
    config.reference_width = 1920.0f;
    config.reference_height = 1080.0f;
    hud_renderer_.set_resolution_config(config);
    hud_renderer_.set_viewport(1920, 1080);
}

void DemoLevel::load() {
    InputMappingSpec spec = InputMappingSpec::FromJson(kInputManifest);
    input_mapping_.load(spec);

    hud_renderer_.add_element(std::make_shared<HealthBarElement>("hud.health", Anchor::TopLeft, 460.0f, 32.0f));
    hud_renderer_.add_element(std::make_shared<UltimateMeterElement>("hud.ultimate", Anchor::BottomLeft, 320.0f, 28.0f));
    hud_renderer_.add_element(std::make_shared<TextLabelElement>("hud.salvage", Anchor::TopRight, "Salvage: ", 1.2f));

    world_geometry_ = {
        {make_vec(-6.0f, -1.0f, -6.0f), make_vec(-2.0f, 3.0f, 2.0f)},
        {make_vec(4.0f, -1.0f, -4.0f), make_vec(8.0f, 2.0f, 3.0f)},
        {make_vec(-1.0f, -1.0f, 6.0f), make_vec(2.0f, 4.0f, 9.0f)},
    };
}

void DemoLevel::handle_input(const RawInputState& input_state) {
    last_input_state_ = input_mapping_.evaluate(input_state);
}

void DemoLevel::tick(float delta_time) {
    dash_cooldown_ = std::max(dash_cooldown_ - delta_time, 0.0f);
    update_player(delta_time);
    update_camera(delta_time);
    update_hud(delta_time);
}

void DemoLevel::play_cinematic(const std::vector<CinematicKeyframe>& keyframes, float blend_duration) {
    camera_system_.play_cinematic(keyframes, blend_duration, false);
}

void DemoLevel::update_player(float delta_time) {
    float move_x = last_input_state_.value_or("move_horizontal", 0.0f);
    float move_y = last_input_state_.value_or("move_vertical", 0.0f);
    Vec3 direction = make_vec(move_x, 0.0f, move_y);
    float magnitude = nightfall::camera::length(direction);
    if (magnitude > 1.0f) {
        direction = nightfall::camera::normalize(direction);
    }

    float speed = 6.0f;
    if (dash_cooldown_ <= 0.0f && last_input_state_.state_for("dash").triggered) {
        speed = 14.0f;
        dash_cooldown_ = 2.0f;
    }

    player_velocity_ = direction * speed;
    player_position_ = player_position_ + player_velocity_ * delta_time;

    bool ultimate_pressed = last_input_state_.state_for("ultimate").triggered;
    ultimate_charge_ = std::clamp(ultimate_charge_ + delta_time * 0.15f, 0.0f, 1.0f);
    if (ultimate_pressed && ultimate_charge_ >= 1.0f) {
        ultimate_charge_ = 0.0f;
        hud_context_.score += 250;
    }

    hud_context_.player_health = std::clamp(hud_context_.player_health - delta_time * 3.0f, 0.0f, hud_context_.player_max_health);
    if (hud_context_.player_health <= 5.0f) {
        hud_context_.player_health = hud_context_.player_max_health;
    }
    hud_context_.salvage = static_cast<int>(hud_context_.salvage + delta_time * 3.0f);
}

void DemoLevel::update_hud(float delta_time) {
    hud_context_.ultimate_charge = ultimate_charge_;
    hud_instructions_ = hud_renderer_.build_frame(hud_context_, delta_time);
}

void DemoLevel::update_camera(float delta_time) {
    camera_system_.set_player_target(player_position_, player_velocity_);
    camera_state_ = camera_system_.update(delta_time, world_geometry_);
}

}  // namespace nightfall::scenes

