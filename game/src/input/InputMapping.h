#pragma once

#include "InputDevices.h"

#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace nightfall::input {

enum class BindingKind {
    Button,
    Axis,
    Pointer,
};

enum class AxisInterpretation {
    Analog,
    Digital,
};

struct BindingDescriptor {
    DeviceKind device{DeviceKind::Keyboard};
    BindingKind kind{BindingKind::Button};
    std::string control{};
    float scale{1.0f};
    float deadzone{0.1f};
    bool toggle{false};
    AxisInterpretation interpretation{AxisInterpretation::Analog};
};

struct ActionBindingSpec {
    std::string id{};
    std::vector<BindingDescriptor> bindings{};
    float smoothing_window{0.0f};
    float analog_threshold{0.2f};
};

struct InputMappingSpec {
    std::vector<ActionBindingSpec> actions{};

    static InputMappingSpec FromJson(std::string_view json_text);
};

struct ActionState {
    float value{0.0f};
    bool active{false};
    bool triggered{false};
    bool released{false};
};

class InputState {
public:
    void set_state(const std::string& action, const ActionState& state);
    [[nodiscard]] bool has_action(const std::string& action) const noexcept;
    [[nodiscard]] const ActionState& state_for(const std::string& action) const;
    [[nodiscard]] float value_or(const std::string& action, float fallback = 0.0f) const noexcept;

private:
    std::unordered_map<std::string, ActionState> _states{};
};

class InputMapping {
public:
    void load(const InputMappingSpec& spec);
    void rebind(const std::string& action, const std::vector<BindingDescriptor>& bindings);
    [[nodiscard]] InputState evaluate(const RawInputState& state) const;
    [[nodiscard]] ActionState evaluate_action(const std::string& action, const RawInputState& state) const;

private:
    struct RuntimeBinding {
        BindingDescriptor descriptor;
    };

    struct RuntimeAction {
        ActionBindingSpec spec;
        std::vector<RuntimeBinding> bindings;
        mutable float smoothed_value{0.0f};
        mutable float previous_value{0.0f};
        mutable bool previous_active{false};
        mutable bool toggle_state{false};
        mutable float toggle_scale{1.0f};
    };

    [[nodiscard]] ActionState compute_state(const RuntimeAction& action, const RawInputState& state) const;

    std::unordered_map<std::string, RuntimeAction> _actions{};
};

}  // namespace nightfall::input

