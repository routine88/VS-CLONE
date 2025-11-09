#include "HudRenderer.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <utility>

namespace nightfall::ui {

namespace {
constexpr float kEpsilon = 1e-4f;

float smooth_step(float current, float target, float speed, float delta_time) {
    if (speed <= kEpsilon || delta_time <= 0.0f) {
        return target;
    }
    float alpha = 1.0f - std::exp(-speed * delta_time);
    return current + (target - current) * alpha;
}

}  // namespace

HudElement::HudElement(std::string id, int z_index) : id_(std::move(id)), z_index_(z_index) {}

std::pair<float, float> HudElement::resolve_anchor(float width, float height, const LayoutTransform& transform, Anchor anchor) {
    float scaled_width = width * transform.scale_x;
    float scaled_height = height * transform.scale_y;
    float x = transform.offset_x;
    float y = transform.offset_y;
    switch (anchor) {
        case Anchor::TopLeft:
            break;
        case Anchor::TopRight:
            x += transform.viewport_width - scaled_width;
            break;
        case Anchor::BottomLeft:
            y += transform.viewport_height - scaled_height;
            break;
        case Anchor::BottomRight:
            x += transform.viewport_width - scaled_width;
            y += transform.viewport_height - scaled_height;
            break;
        case Anchor::Center:
            x += (transform.viewport_width - scaled_width) * 0.5f;
            y += (transform.viewport_height - scaled_height) * 0.5f;
            break;
    }
    return {x, y};
}

HealthBarElement::HealthBarElement(std::string id, Anchor anchor, float width, float height)
    : HudElement(std::move(id), 10), anchor_(anchor), width_(width), height_(height) {}

void HealthBarElement::update(const HudContext& context, float delta_time) {
    float max_health = std::max(context.player_max_health, 1.0f);
    float target_ratio = std::clamp(context.player_health / max_health, 0.0f, 1.0f);
    displayed_ratio_ = smooth_step(displayed_ratio_, target_ratio, smoothing_, delta_time);
}

void HealthBarElement::build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const {
    (void)context;
    float scaled_width = width_ * transform.scale_x;
    float scaled_height = height_ * transform.scale_y;
    auto [base_x, base_y] = resolve_anchor(width_, height_, transform, anchor_);
    float margin = 24.0f;
    base_x += margin * transform.scale_x;
    base_y += margin * transform.scale_y;

    OverlayInstruction background;
    background.id = id() + ":background";
    background.layer = "ui_overlay";
    background.x = base_x;
    background.y = base_y;
    background.width = scaled_width;
    background.height = scaled_height;
    background.opacity = 0.8f;
    background.color = {0.08f, 0.09f, 0.12f, 0.8f};
    background.z_index = z_index();
    background.anchor = anchor_;
    out.push_back(background);

    OverlayInstruction fill;
    fill.id = id() + ":fill";
    fill.layer = "ui_overlay";
    fill.x = base_x + 4.0f * transform.scale_x;
    fill.y = base_y + 4.0f * transform.scale_y;
    fill.width = (scaled_width - 8.0f * transform.scale_x) * displayed_ratio_;
    fill.height = scaled_height - 8.0f * transform.scale_y;
    fill.opacity = 0.95f;
    fill.color = {0.86f, 0.23f, 0.31f, 1.0f};
    fill.z_index = z_index() + 1;
    fill.anchor = anchor_;
    out.push_back(fill);
}

UltimateMeterElement::UltimateMeterElement(std::string id, Anchor anchor, float width, float height)
    : HudElement(std::move(id), 15), anchor_(anchor), width_(width), height_(height) {}

void UltimateMeterElement::update(const HudContext& context, float delta_time) {
    float target_charge = std::clamp(context.ultimate_charge, 0.0f, 1.0f);
    charge_ = smooth_step(charge_, target_charge, smoothing_, delta_time);
}

void UltimateMeterElement::build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const {
    (void)context;
    float scaled_width = width_ * transform.scale_x;
    float scaled_height = height_ * transform.scale_y;
    auto [base_x, base_y] = resolve_anchor(width_, height_, transform, anchor_);
    float margin_x = 24.0f;
    float margin_y = (anchor_ == Anchor::BottomLeft || anchor_ == Anchor::BottomRight) ? 96.0f : 72.0f;
    base_x += margin_x * transform.scale_x;
    base_y += margin_y * transform.scale_y;

    OverlayInstruction frame;
    frame.id = id() + ":frame";
    frame.layer = "ui_overlay";
    frame.x = base_x;
    frame.y = base_y;
    frame.width = scaled_width;
    frame.height = scaled_height;
    frame.opacity = 0.85f;
    frame.color = {0.1f, 0.14f, 0.2f, 0.85f};
    frame.z_index = z_index();
    frame.anchor = anchor_;
    out.push_back(frame);

    OverlayInstruction charge_bar;
    charge_bar.id = id() + ":charge";
    charge_bar.layer = "ui_overlay";
    charge_bar.x = base_x + 6.0f * transform.scale_x;
    charge_bar.y = base_y + 6.0f * transform.scale_y;
    charge_bar.width = (scaled_width - 12.0f * transform.scale_x) * charge_;
    charge_bar.height = scaled_height - 12.0f * transform.scale_y;
    charge_bar.opacity = 0.95f;
    charge_bar.color = {0.21f, 0.72f, 0.98f, 1.0f};
    charge_bar.z_index = z_index() + 1;
    charge_bar.anchor = anchor_;
    out.push_back(charge_bar);
}

TextLabelElement::TextLabelElement(std::string id, Anchor anchor, std::string prefix, float font_scale)
    : HudElement(std::move(id), 20), anchor_(anchor), prefix_(std::move(prefix)), font_scale_(font_scale) {}

void TextLabelElement::update(const HudContext& context, float delta_time) {
    (void)delta_time;
    std::ostringstream stream;
    stream << prefix_ << context.salvage;
    cached_text_ = stream.str();
}

void TextLabelElement::build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const {
    (void)context;
    auto [base_x, base_y] = resolve_anchor(0.0f, 0.0f, transform, anchor_);
    float margin = 28.0f;
    if (anchor_ == Anchor::TopRight || anchor_ == Anchor::BottomRight) {
        base_x -= margin * transform.scale_x;
    } else {
        base_x += margin * transform.scale_x;
    }
    if (anchor_ == Anchor::BottomLeft || anchor_ == Anchor::BottomRight) {
        base_y -= margin * transform.scale_y;
    } else {
        base_y += margin * transform.scale_y;
    }

    OverlayInstruction label;
    label.id = id() + ":label";
    label.layer = "ui_overlay";
    label.x = base_x;
    label.y = base_y;
    label.width = 0.0f;
    label.height = 0.0f;
    label.opacity = 1.0f;
    label.color = {0.95f, 0.95f, 0.9f, 1.0f};
    label.text = cached_text_;
    label.font_scale = font_scale_ * std::min(transform.scale_x, transform.scale_y);
    label.z_index = z_index();
    label.anchor = anchor_;
    out.push_back(label);
}

HudRenderer::HudRenderer() = default;

void HudRenderer::set_viewport(int width, int height) {
    viewport_width_ = std::max(width, 1);
    viewport_height_ = std::max(height, 1);
}

void HudRenderer::set_resolution_config(const ResolutionConfig& config) {
    config_ = config;
}

void HudRenderer::add_element(const std::shared_ptr<HudElement>& element) {
    elements_.push_back(element);
    dirty_ = true;
}

void HudRenderer::remove_element(const std::string& id) {
    elements_.erase(
        std::remove_if(
            elements_.begin(),
            elements_.end(),
            [&](const std::shared_ptr<HudElement>& element) { return element && element->id() == id; }),
        elements_.end());
    dirty_ = true;
}

void HudRenderer::clear() {
    elements_.clear();
    sorted_cache_.clear();
    dirty_ = true;
}

std::vector<OverlayInstruction> HudRenderer::build_frame(const HudContext& context, float delta_time) {
    rebuild_cache();
    LayoutTransform transform = compute_transform();
    std::vector<OverlayInstruction> instructions;
    for (const auto& element : sorted_cache_) {
        if (!element) {
            continue;
        }
        element->update(context, delta_time);
        element->build_instructions(context, transform, instructions);
    }
    std::stable_sort(instructions.begin(), instructions.end(), [](const OverlayInstruction& lhs, const OverlayInstruction& rhs) {
        return lhs.z_index < rhs.z_index;
    });
    return instructions;
}

LayoutTransform HudRenderer::compute_transform() const {
    LayoutTransform transform;
    transform.viewport_width = static_cast<float>(viewport_width_);
    transform.viewport_height = static_cast<float>(viewport_height_);
    float sx = transform.viewport_width / std::max(config_.reference_width, 1.0f);
    float sy = transform.viewport_height / std::max(config_.reference_height, 1.0f);
    if (config_.maintain_aspect) {
        float uniform = std::min(sx, sy);
        transform.scale_x = uniform;
        transform.scale_y = uniform;
        float scaled_width = config_.reference_width * uniform;
        float scaled_height = config_.reference_height * uniform;
        transform.offset_x = (transform.viewport_width - scaled_width) * 0.5f;
        transform.offset_y = (transform.viewport_height - scaled_height) * 0.5f;
    } else {
        transform.scale_x = sx;
        transform.scale_y = sy;
        transform.offset_x = 0.0f;
        transform.offset_y = 0.0f;
    }
    return transform;
}

void HudRenderer::rebuild_cache() const {
    if (!dirty_) {
        return;
    }
    sorted_cache_ = elements_;
    std::stable_sort(sorted_cache_.begin(), sorted_cache_.end(), [](const std::shared_ptr<HudElement>& lhs, const std::shared_ptr<HudElement>& rhs) {
        if (!lhs) {
            return false;
        }
        if (!rhs) {
            return true;
        }
        if (lhs->z_index() == rhs->z_index()) {
            return lhs->id() < rhs->id();
        }
        return lhs->z_index() < rhs->z_index();
    });
    dirty_ = false;
}

}  // namespace nightfall::ui

