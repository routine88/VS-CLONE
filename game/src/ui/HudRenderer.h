#pragma once

#include <array>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace nightfall::ui {

struct HudContext {
    float player_health{100.0f};
    float player_max_health{100.0f};
    float ultimate_charge{0.0f};
    int salvage{0};
    int wave{1};
    int score{0};
};

struct ResolutionConfig {
    float reference_width{1920.0f};
    float reference_height{1080.0f};
    bool maintain_aspect{true};
};

struct LayoutTransform {
    float scale_x{1.0f};
    float scale_y{1.0f};
    float offset_x{0.0f};
    float offset_y{0.0f};
    float viewport_width{1920.0f};
    float viewport_height{1080.0f};
};

enum class Anchor {
    TopLeft,
    TopRight,
    BottomLeft,
    BottomRight,
    Center,
};

struct OverlayInstruction {
    std::string id{};
    std::string layer{"overlay"};
    float x{0.0f};
    float y{0.0f};
    float width{0.0f};
    float height{0.0f};
    float opacity{1.0f};
    std::array<float, 4> color{1.0f, 1.0f, 1.0f, 1.0f};
    std::string text{};
    float font_scale{1.0f};
    int z_index{0};
    Anchor anchor{Anchor::TopLeft};
};

class HudElement {
public:
    explicit HudElement(std::string id, int z_index = 0);
    virtual ~HudElement() = default;

    [[nodiscard]] const std::string& id() const noexcept { return id_; }
    [[nodiscard]] int z_index() const noexcept { return z_index_; }

    virtual void update(const HudContext& context, float delta_time) = 0;
    virtual void build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const = 0;

protected:
    static std::pair<float, float> resolve_anchor(float width, float height, const LayoutTransform& transform, Anchor anchor);

private:
    std::string id_;
    int z_index_;
};

class HealthBarElement final : public HudElement {
public:
    HealthBarElement(std::string id, Anchor anchor, float width, float height);

    void update(const HudContext& context, float delta_time) override;
    void build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const override;

private:
    Anchor anchor_;
    float width_;
    float height_;
    float displayed_ratio_{1.0f};
    float smoothing_{6.0f};
};

class UltimateMeterElement final : public HudElement {
public:
    UltimateMeterElement(std::string id, Anchor anchor, float width, float height);

    void update(const HudContext& context, float delta_time) override;
    void build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const override;

private:
    Anchor anchor_;
    float width_;
    float height_;
    float charge_{0.0f};
    float smoothing_{4.0f};
};

class TextLabelElement final : public HudElement {
public:
    TextLabelElement(std::string id, Anchor anchor, std::string prefix, float font_scale = 1.0f);

    void update(const HudContext& context, float delta_time) override;
    void build_instructions(const HudContext& context, const LayoutTransform& transform, std::vector<OverlayInstruction>& out) const override;

private:
    Anchor anchor_;
    std::string prefix_;
    float font_scale_;
    std::string cached_text_;
};

class HudRenderer {
public:
    HudRenderer();

    void set_viewport(int width, int height);
    void set_resolution_config(const ResolutionConfig& config);
    void add_element(const std::shared_ptr<HudElement>& element);
    void remove_element(const std::string& id);
    void clear();

    std::vector<OverlayInstruction> build_frame(const HudContext& context, float delta_time);

private:
    LayoutTransform compute_transform() const;
    void rebuild_cache() const;

    int viewport_width_{1920};
    int viewport_height_{1080};
    ResolutionConfig config_{};
    std::vector<std::shared_ptr<HudElement>> elements_{};
    mutable std::vector<std::shared_ptr<HudElement>> sorted_cache_{};
    mutable bool dirty_{true};
};

}  // namespace nightfall::ui

