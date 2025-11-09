#include "InputDevices.h"

#include <stdexcept>

namespace nightfall::input {

namespace {
const ButtonState kEmptyButton{};
}

const ButtonState& RawKeyboardState::get(const std::string& key) const noexcept {
    auto it = keys.find(key);
    if (it == keys.end()) {
        return kEmptyButton;
    }
    return it->second;
}

bool RawKeyboardState::is_down(const std::string& key) const noexcept {
    return get(key).pressed;
}

const ButtonState& RawMouseState::get(const std::string& button) const noexcept {
    auto it = buttons.find(button);
    if (it == buttons.end()) {
        return kEmptyButton;
    }
    return it->second;
}

bool RawMouseState::is_down(const std::string& button) const noexcept {
    return get(button).pressed;
}

const ButtonState& RawGamepadState::get_button(const std::string& button) const noexcept {
    auto it = buttons.find(button);
    if (it == buttons.end()) {
        return kEmptyButton;
    }
    return it->second;
}

bool RawGamepadState::button_down(const std::string& button) const noexcept {
    return get_button(button).pressed;
}

float RawGamepadState::axis_value(const std::string& axis, float default_value) const noexcept {
    auto it = axes.find(axis);
    if (it == axes.end()) {
        return default_value;
    }
    return it->second;
}

}  // namespace nightfall::input

