#pragma once

#include <cstdint>
#include <string_view>

struct ID3D12GraphicsCommandList;
struct ID3D12CommandQueue;

namespace vs::engine::render::diagnostics {

using CpuBeginCallback = void (*)(std::string_view label, std::uint32_t color);
using CpuEndCallback = void (*)();
using GpuBeginCallback = void (*)(void* command_context, std::string_view label, std::uint32_t color);
using GpuEndCallback = void (*)(void* command_context);

void initialize();
void shutdown();

void set_cpu_callbacks(CpuBeginCallback begin, CpuEndCallback end);
void set_gpu_callbacks(GpuBeginCallback begin, GpuEndCallback end);

void begin_renderdoc_capture(ID3D12CommandQueue* queue = nullptr);
void end_renderdoc_capture(ID3D12CommandQueue* queue = nullptr);

class ScopedCpuZone {
public:
    explicit ScopedCpuZone(std::string_view label, std::uint32_t color = 0xff00ffff);
    ~ScopedCpuZone();

    ScopedCpuZone(const ScopedCpuZone&) = delete;
    ScopedCpuZone& operator=(const ScopedCpuZone&) = delete;

    ScopedCpuZone(ScopedCpuZone&&) = delete;
    ScopedCpuZone& operator=(ScopedCpuZone&&) = delete;

private:
    std::string_view _label;
    std::uint32_t _color;
    bool _active;
};

class ScopedGpuZone {
public:
    ScopedGpuZone(
        ID3D12GraphicsCommandList* command_list,
        std::string_view label,
        std::uint32_t color = 0xff00ffff
    );
    ~ScopedGpuZone();

    ScopedGpuZone(const ScopedGpuZone&) = delete;
    ScopedGpuZone& operator=(const ScopedGpuZone&) = delete;

    ScopedGpuZone(ScopedGpuZone&&) = delete;
    ScopedGpuZone& operator=(ScopedGpuZone&&) = delete;

private:
    ID3D12GraphicsCommandList* _command_list;
    std::string_view _label;
    std::uint32_t _color;
    bool _active;
};

}  // namespace vs::engine::render::diagnostics

