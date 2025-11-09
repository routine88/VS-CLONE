#pragma once

#include <optional>
#include <string>
#include <unordered_map>

namespace nightfall::input {

enum class DeviceKind {
    Keyboard,
    Mouse,
    Gamepad,
};

struct ButtonState {
    bool pressed{false};
    bool was_pressed{false};

    [[nodiscard]] bool just_pressed() const noexcept { return pressed && !was_pressed; }
    [[nodiscard]] bool just_released() const noexcept { return !pressed && was_pressed; }
};

struct RawKeyboardState {
    std::unordered_map<std::string, ButtonState> keys{};

    [[nodiscard]] const ButtonState& get(const std::string& key) const noexcept;
    [[nodiscard]] bool is_down(const std::string& key) const noexcept;
};

struct RawMouseState {
    std::unordered_map<std::string, ButtonState> buttons{};
    float position_x{0.0f};
    float position_y{0.0f};
    float delta_x{0.0f};
    float delta_y{0.0f};
    float wheel_delta{0.0f};

    [[nodiscard]] const ButtonState& get(const std::string& button) const noexcept;
    [[nodiscard]] bool is_down(const std::string& button) const noexcept;
};

struct RawGamepadState {
    std::unordered_map<std::string, ButtonState> buttons{};
    std::unordered_map<std::string, float> axes{};
    std::unordered_map<std::string, float> previous_axes{};

    [[nodiscard]] const ButtonState& get_button(const std::string& button) const noexcept;
    [[nodiscard]] bool button_down(const std::string& button) const noexcept;
    [[nodiscard]] float axis_value(const std::string& axis, float default_value = 0.0f) const noexcept;
};

struct RawInputState {
    RawKeyboardState keyboard{};
    RawMouseState mouse{};
    RawGamepadState gamepad{};
    float delta_time{0.0f};
};

}  // namespace nightfall::input

