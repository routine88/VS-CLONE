#include "InputMapping.h"

#include <algorithm>
#include <cmath>
#include <cctype>
#include <stdexcept>
#include <string>
#include <utility>
#include <variant>
#include <vector>
#include <unordered_map>
#include <string_view>

namespace nightfall::input {

namespace {

struct JsonValue;
using JsonArray = std::vector<JsonValue>;
using JsonObject = std::unordered_map<std::string, JsonValue>;

struct JsonValue {
    std::variant<std::nullptr_t, bool, double, std::string, JsonArray, JsonObject> data;

    [[nodiscard]] bool is_null() const noexcept { return std::holds_alternative<std::nullptr_t>(data); }
    [[nodiscard]] bool is_bool() const noexcept { return std::holds_alternative<bool>(data); }
    [[nodiscard]] bool is_number() const noexcept { return std::holds_alternative<double>(data); }
    [[nodiscard]] bool is_string() const noexcept { return std::holds_alternative<std::string>(data); }
    [[nodiscard]] bool is_array() const noexcept { return std::holds_alternative<JsonArray>(data); }
    [[nodiscard]] bool is_object() const noexcept { return std::holds_alternative<JsonObject>(data); }

    [[nodiscard]] bool as_bool(bool fallback = false) const {
        if (is_bool()) {
            return std::get<bool>(data);
        }
        if (is_number()) {
            return std::get<double>(data) != 0.0;
        }
        if (is_string()) {
            const auto& text = std::get<std::string>(data);
            return text == "true" || text == "1";
        }
        return fallback;
    }

    [[nodiscard]] double as_number(double fallback = 0.0) const {
        if (is_number()) {
            return std::get<double>(data);
        }
        if (is_bool()) {
            return std::get<bool>(data) ? 1.0 : 0.0;
        }
        if (is_string()) {
            try {
                return std::stod(std::get<std::string>(data));
            } catch (...) {
                return fallback;
            }
        }
        return fallback;
    }

    [[nodiscard]] const std::string& as_string() const {
        if (!is_string()) {
            throw std::runtime_error("expected JSON string");
        }
        return std::get<std::string>(data);
    }

    [[nodiscard]] const JsonArray& as_array() const {
        if (!is_array()) {
            throw std::runtime_error("expected JSON array");
        }
        return std::get<JsonArray>(data);
    }

    [[nodiscard]] const JsonObject& as_object() const {
        if (!is_object()) {
            throw std::runtime_error("expected JSON object");
        }
        return std::get<JsonObject>(data);
    }
};

class JsonParser {
public:
    explicit JsonParser(std::string_view text) : text_(text) {}

    JsonValue parse() {
        skip_whitespace();
        JsonValue value = parse_value();
        skip_whitespace();
        if (position_ != text_.size()) {
            throw std::runtime_error("unexpected characters after JSON document");
        }
        return value;
    }

private:
    [[noreturn]] void raise_error(const char* message) const {
        throw std::runtime_error(message);
    }

    void skip_whitespace() {
        while (position_ < text_.size()) {
            char c = text_[position_];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') {
                ++position_;
            } else {
                break;
            }
        }
    }

    char peek() const {
        if (position_ >= text_.size()) {
            return '\0';
        }
        return text_[position_];
    }

    char consume() {
        if (position_ >= text_.size()) {
            raise_error("unexpected end of input");
        }
        return text_[position_++];
    }

    JsonValue parse_value() {
        skip_whitespace();
        char c = peek();
        if (c == '{') {
            return parse_object();
        }
        if (c == '[') {
            return parse_array();
        }
        if (c == '"') {
            return parse_string();
        }
        if (c == '-' || std::isdigit(static_cast<unsigned char>(c))) {
            return parse_number();
        }
        if (text_.substr(position_, 4) == "true") {
            position_ += 4;
            return JsonValue{true};
        }
        if (text_.substr(position_, 5) == "false") {
            position_ += 5;
            return JsonValue{false};
        }
        if (text_.substr(position_, 4) == "null") {
            position_ += 4;
            return JsonValue{nullptr};
        }
        raise_error("unexpected token in JSON");
    }

    JsonValue parse_object() {
        JsonObject object;
        consume();  // skip '{'
        skip_whitespace();
        if (peek() == '}') {
            consume();
            return JsonValue{object};
        }
        while (true) {
            skip_whitespace();
            if (peek() != '"') {
                raise_error("expected string key in object");
            }
            std::string key = std::get<std::string>(parse_string().data);
            skip_whitespace();
            if (consume() != ':') {
                raise_error("expected ':' after key");
            }
            skip_whitespace();
            JsonValue value = parse_value();
            object.emplace(std::move(key), std::move(value));
            skip_whitespace();
            char separator = consume();
            if (separator == '}') {
                break;
            }
            if (separator != ',') {
                raise_error("expected ',' or '}' in object");
            }
        }
        return JsonValue{object};
    }

    JsonValue parse_array() {
        JsonArray array;
        consume();  // skip '['
        skip_whitespace();
        if (peek() == ']') {
            consume();
            return JsonValue{array};
        }
        while (true) {
            JsonValue value = parse_value();
            array.emplace_back(std::move(value));
            skip_whitespace();
            char separator = consume();
            if (separator == ']') {
                break;
            }
            if (separator != ',') {
                raise_error("expected ',' or ']' in array");
            }
            skip_whitespace();
        }
        return JsonValue{array};
    }

    JsonValue parse_string() {
        if (consume() != '"') {
            raise_error("expected string");
        }
        std::string result;
        while (position_ < text_.size()) {
            char c = consume();
            if (c == '"') {
                return JsonValue{std::move(result)};
            }
            if (c == '\\') {
                char next = consume();
                switch (next) {
                    case '"':
                        result.push_back('"');
                        break;
                    case '\\':
                        result.push_back('\\');
                        break;
                    case '/':
                        result.push_back('/');
                        break;
                    case 'b':
                        result.push_back('\b');
                        break;
                    case 'f':
                        result.push_back('\f');
                        break;
                    case 'n':
                        result.push_back('\n');
                        break;
                    case 'r':
                        result.push_back('\r');
                        break;
                    case 't':
                        result.push_back('\t');
                        break;
                    default:
                        raise_error("unsupported escape sequence");
                }
            } else {
                result.push_back(c);
            }
        }
        raise_error("unterminated string");
    }

    JsonValue parse_number() {
        std::string number;
        if (peek() == '-') {
            number.push_back(consume());
        }
        while (std::isdigit(static_cast<unsigned char>(peek()))) {
            number.push_back(consume());
        }
        if (peek() == '.') {
            number.push_back(consume());
            while (std::isdigit(static_cast<unsigned char>(peek()))) {
                number.push_back(consume());
            }
        }
        if (peek() == 'e' || peek() == 'E') {
            number.push_back(consume());
            if (peek() == '+' || peek() == '-') {
                number.push_back(consume());
            }
            while (std::isdigit(static_cast<unsigned char>(peek()))) {
                number.push_back(consume());
            }
        }
        try {
            return JsonValue{std::stod(number)};
        } catch (...) {
            raise_error("invalid numeric literal");
        }
    }

    std::string_view text_;
    std::size_t position_{0};
};

BindingKind parse_binding_kind(const std::string& text) {
    if (text == "axis") {
        return BindingKind::Axis;
    }
    if (text == "pointer") {
        return BindingKind::Pointer;
    }
    return BindingKind::Button;
}

AxisInterpretation parse_interpretation(const std::string& text) {
    if (text == "digital" || text == "binary") {
        return AxisInterpretation::Digital;
    }
    return AxisInterpretation::Analog;
}

DeviceKind parse_device_kind(const std::string& text) {
    if (text == "mouse") {
        return DeviceKind::Mouse;
    }
    if (text == "gamepad" || text == "controller") {
        return DeviceKind::Gamepad;
    }
    return DeviceKind::Keyboard;
}

float extract_axis_value(const BindingDescriptor& descriptor, const RawInputState& state) {
    switch (descriptor.device) {
        case DeviceKind::Keyboard: {
            const auto& button = state.keyboard.get(descriptor.control);
            return button.pressed ? descriptor.scale : 0.0f;
        }
        case DeviceKind::Mouse: {
            if (descriptor.control == "x" || descriptor.control == "delta_x") {
                return state.mouse.delta_x * descriptor.scale;
            }
            if (descriptor.control == "y" || descriptor.control == "delta_y") {
                return state.mouse.delta_y * descriptor.scale;
            }
            if (descriptor.control == "wheel" || descriptor.control == "scroll") {
                return state.mouse.wheel_delta * descriptor.scale;
            }
            if (descriptor.control == "position_x") {
                return state.mouse.position_x * descriptor.scale;
            }
            if (descriptor.control == "position_y") {
                return state.mouse.position_y * descriptor.scale;
            }
            return 0.0f;
        }
        case DeviceKind::Gamepad: {
            return state.gamepad.axis_value(descriptor.control) * descriptor.scale;
        }
    }
    return 0.0f;
}

bool extract_toggle_transition(const BindingDescriptor& descriptor, const RawInputState& state) {
    if (!descriptor.toggle) {
        return false;
    }
    switch (descriptor.device) {
        case DeviceKind::Keyboard:
            return state.keyboard.get(descriptor.control).just_pressed();
        case DeviceKind::Mouse:
            return state.mouse.get(descriptor.control).just_pressed();
        case DeviceKind::Gamepad:
            return state.gamepad.get_button(descriptor.control).just_pressed();
    }
    return false;
}

bool extract_button_pressed(const BindingDescriptor& descriptor, const RawInputState& state) {
    switch (descriptor.device) {
        case DeviceKind::Keyboard:
            return state.keyboard.get(descriptor.control).pressed;
        case DeviceKind::Mouse:
            return state.mouse.get(descriptor.control).pressed;
        case DeviceKind::Gamepad:
            return state.gamepad.get_button(descriptor.control).pressed;
    }
    return false;
}

bool extract_button_triggered(const BindingDescriptor& descriptor, const RawInputState& state) {
    switch (descriptor.device) {
        case DeviceKind::Keyboard:
            return state.keyboard.get(descriptor.control).just_pressed();
        case DeviceKind::Mouse:
            return state.mouse.get(descriptor.control).just_pressed();
        case DeviceKind::Gamepad:
            return state.gamepad.get_button(descriptor.control).just_pressed();
    }
    return false;
}

bool extract_button_released(const BindingDescriptor& descriptor, const RawInputState& state) {
    switch (descriptor.device) {
        case DeviceKind::Keyboard:
            return state.keyboard.get(descriptor.control).just_released();
        case DeviceKind::Mouse:
            return state.mouse.get(descriptor.control).just_released();
        case DeviceKind::Gamepad:
            return state.gamepad.get_button(descriptor.control).just_released();
    }
    return false;
}

}  // namespace

void InputState::set_state(const std::string& action, const ActionState& state) {
    _states[action] = state;
}

bool InputState::has_action(const std::string& action) const noexcept {
    return _states.find(action) != _states.end();
}

const ActionState& InputState::state_for(const std::string& action) const {
    auto it = _states.find(action);
    if (it == _states.end()) {
        static const ActionState kEmpty{};
        return kEmpty;
    }
    return it->second;
}

float InputState::value_or(const std::string& action, float fallback) const noexcept {
    auto it = _states.find(action);
    if (it == _states.end()) {
        return fallback;
    }
    return it->second.value;
}

InputMappingSpec InputMappingSpec::FromJson(std::string_view json_text) {
    JsonParser parser(json_text);
    JsonValue root = parser.parse();
    const JsonObject& object = root.as_object();
    auto actions_it = object.find("actions");
    if (actions_it == object.end()) {
        throw std::runtime_error("input mapping JSON missing 'actions' array");
    }
    const JsonArray& actions_array = actions_it->second.as_array();
    InputMappingSpec spec;
    spec.actions.reserve(actions_array.size());
    for (const JsonValue& value : actions_array) {
        const JsonObject& action_object = value.as_object();
        ActionBindingSpec action;
        if (auto id_it = action_object.find("id"); id_it != action_object.end()) {
            action.id = id_it->second.as_string();
        } else if (auto name_it = action_object.find("action"); name_it != action_object.end()) {
            action.id = name_it->second.as_string();
        } else {
            throw std::runtime_error("action entry missing 'id'");
        }
        if (auto smoothing_it = action_object.find("smoothing"); smoothing_it != action_object.end()) {
            action.smoothing_window = static_cast<float>(smoothing_it->second.as_number(0.0));
        }
        if (auto threshold_it = action_object.find("analog_threshold"); threshold_it != action_object.end()) {
            action.analog_threshold = static_cast<float>(threshold_it->second.as_number(0.2));
        }
        auto bindings_it = action_object.find("bindings");
        if (bindings_it == action_object.end()) {
            throw std::runtime_error("action entry missing 'bindings'");
        }
        const JsonArray& binding_array = bindings_it->second.as_array();
        action.bindings.reserve(binding_array.size());
        for (const JsonValue& binding_value : binding_array) {
            const JsonObject& binding_object = binding_value.as_object();
            BindingDescriptor descriptor;
            if (auto device_it = binding_object.find("device"); device_it != binding_object.end()) {
                descriptor.device = parse_device_kind(device_it->second.as_string());
            }
            if (auto kind_it = binding_object.find("kind"); kind_it != binding_object.end()) {
                descriptor.kind = parse_binding_kind(kind_it->second.as_string());
            }
            if (auto control_it = binding_object.find("control"); control_it != binding_object.end()) {
                descriptor.control = control_it->second.as_string();
            } else {
                throw std::runtime_error("binding missing 'control'");
            }
            if (auto scale_it = binding_object.find("scale"); scale_it != binding_object.end()) {
                descriptor.scale = static_cast<float>(scale_it->second.as_number(1.0));
            }
            if (auto deadzone_it = binding_object.find("deadzone"); deadzone_it != binding_object.end()) {
                descriptor.deadzone = static_cast<float>(deadzone_it->second.as_number(0.1));
            }
            if (auto toggle_it = binding_object.find("toggle"); toggle_it != binding_object.end()) {
                descriptor.toggle = toggle_it->second.as_bool(false);
            }
            if (auto interpretation_it = binding_object.find("interpretation"); interpretation_it != binding_object.end()) {
                descriptor.interpretation = parse_interpretation(interpretation_it->second.as_string());
            }
            action.bindings.emplace_back(std::move(descriptor));
        }
        spec.actions.emplace_back(std::move(action));
    }
    return spec;
}

void InputMapping::load(const InputMappingSpec& spec) {
    _actions.clear();
    for (const auto& action : spec.actions) {
        RuntimeAction runtime;
        runtime.spec = action;
        runtime.bindings.reserve(action.bindings.size());
        for (const auto& descriptor : action.bindings) {
            runtime.bindings.push_back(RuntimeBinding{descriptor});
        }
        _actions.emplace(action.id, std::move(runtime));
    }
}

void InputMapping::rebind(const std::string& action, const std::vector<BindingDescriptor>& bindings) {
    auto it = _actions.find(action);
    if (it == _actions.end()) {
        throw std::runtime_error("unknown action: " + action);
    }
    it->second.bindings.clear();
    it->second.bindings.reserve(bindings.size());
    for (const auto& descriptor : bindings) {
        it->second.bindings.push_back(RuntimeBinding{descriptor});
    }
}

InputState InputMapping::evaluate(const RawInputState& state) const {
    InputState result;
    for (const auto& [id, action] : _actions) {
        result.set_state(id, compute_state(action, state));
    }
    return result;
}

ActionState InputMapping::evaluate_action(const std::string& action, const RawInputState& state) const {
    auto it = _actions.find(action);
    if (it == _actions.end()) {
        return ActionState{};
    }
    return compute_state(it->second, state);
}

ActionState InputMapping::compute_state(const RuntimeAction& action, const RawInputState& state) const {
    float value = 0.0f;
    bool any_pressed = false;
    bool any_triggered = false;
    bool any_released = false;

    bool has_toggle = false;
    bool toggle_value = action.toggle_state;
    float toggle_scale = action.toggle_scale;
    bool toggle_turned_on = false;
    bool toggle_turned_off = false;

    for (const auto& runtime_binding : action.bindings) {
        const auto& descriptor = runtime_binding.descriptor;
        if (descriptor.kind == BindingKind::Button) {
            bool pressed = extract_button_pressed(descriptor, state);
            any_pressed = any_pressed || pressed;
            any_triggered = any_triggered || extract_button_triggered(descriptor, state);
            any_released = any_released || extract_button_released(descriptor, state);
            if (descriptor.toggle) {
                has_toggle = true;
                toggle_scale = descriptor.scale;
                if (extract_toggle_transition(descriptor, state)) {
                    bool previous_toggle = toggle_value;
                    toggle_value = !toggle_value;
                    if (!previous_toggle && toggle_value) {
                        toggle_turned_on = true;
                    }
                    if (previous_toggle && !toggle_value) {
                        toggle_turned_off = true;
                    }
                }
            } else {
                value += pressed ? descriptor.scale : 0.0f;
            }
        } else {
            float axis_value = extract_axis_value(descriptor, state);
            if (std::fabs(axis_value) <= descriptor.deadzone) {
                axis_value = 0.0f;
            }
            if (descriptor.interpretation == AxisInterpretation::Digital) {
                bool active = std::fabs(axis_value) > descriptor.deadzone;
                any_pressed = any_pressed || active;
                if (active && std::fabs(action.previous_value) <= descriptor.deadzone) {
                    any_triggered = true;
                }
                if (!active && std::fabs(action.previous_value) > descriptor.deadzone) {
                    any_released = true;
                }
                if (active) {
                    value += descriptor.scale * (axis_value >= 0.0f ? 1.0f : -1.0f);
                }
            } else {
                value += axis_value;
                if (std::fabs(axis_value) > descriptor.deadzone) {
                    any_pressed = true;
                }
            }
        }
    }

    if (has_toggle) {
        action.toggle_state = toggle_value;
        action.toggle_scale = toggle_scale;
        if (toggle_value) {
            value += toggle_scale;
            any_pressed = true;
        }
        if (toggle_turned_on) {
            any_triggered = true;
        }
        if (toggle_turned_off) {
            any_released = true;
        }
    } else {
        action.toggle_state = false;
        action.toggle_scale = 1.0f;
    }

    value = std::clamp(value, -1.0f, 1.0f);

    float smoothed = value;
    if (action.spec.smoothing_window > 0.0f && state.delta_time > 0.0f) {
        float t = state.delta_time / action.spec.smoothing_window;
        t = std::clamp(t, 0.0f, 1.0f);
        smoothed = action.previous_value + (value - action.previous_value) * t;
    }

    bool active = any_pressed || std::fabs(smoothed) > 1e-3f;
    bool triggered = any_triggered;
    bool released = any_released;

    if (!triggered && action.spec.analog_threshold > 0.0f) {
        triggered = (std::fabs(smoothed) >= action.spec.analog_threshold) &&
                    (std::fabs(action.previous_value) < action.spec.analog_threshold);
    }
    if (!released && action.spec.analog_threshold > 0.0f) {
        released = (std::fabs(smoothed) <= action.spec.analog_threshold * 0.5f) &&
                   (std::fabs(action.previous_value) > action.spec.analog_threshold * 0.5f);
    }

    action.previous_value = smoothed;
    action.previous_active = active;

    return ActionState{smoothed, active, triggered, released};
}

}  // namespace nightfall::input

