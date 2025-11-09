#include "diagnostics.h"

#include <chrono>
#include <mutex>
#include <ostream>
#include <string>
#include <utility>
#include <vector>

#if defined(ENABLE_PIX)
#include <pix3.h>
#endif

#if defined(ENABLE_RENDERDOC)
#include "renderdoc_app.h"
#endif

namespace vs::engine::render::diagnostics {

namespace {
std::mutex g_cpu_mutex;
CpuBeginCallback g_cpu_begin = nullptr;
CpuEndCallback g_cpu_end = nullptr;

std::mutex g_gpu_mutex;
GpuBeginCallback g_gpu_begin = nullptr;
GpuEndCallback g_gpu_end = nullptr;

#if defined(ENABLE_RENDERDOC)
RENDERDOC_API_1_6_0* g_renderdoc_api = nullptr;
#endif

#if defined(ENABLE_PIX)
bool g_pix_available = true;

std::wstring to_wstring(std::string_view label) {
    return std::wstring(label.begin(), label.end());
}
#endif

class StdoutCpuLogger {
public:
    void begin(std::string_view label, std::uint32_t color) {
        (void)color;
        auto now = std::chrono::steady_clock::now();
        std::lock_guard<std::mutex> lock(_mutex);
        _stack_depth++;
        _timeline.emplace_back(now, std::string(label), true);
    }

    void end() {
        auto now = std::chrono::steady_clock::now();
        std::lock_guard<std::mutex> lock(_mutex);
        if (_stack_depth > 0) {
            _timeline.emplace_back(now, std::string{}, false);
            _stack_depth--;
        }
    }

    void flush(std::ostream& out) {
        std::lock_guard<std::mutex> lock(_mutex);
        auto it = _timeline.begin();
        std::vector<std::pair<std::chrono::steady_clock::time_point, std::string>> stack;
        while (it != _timeline.end()) {
            if (it->opening) {
                stack.emplace_back(it->timestamp, it->label);
            } else if (!stack.empty()) {
                auto begin = stack.back().first;
                auto label = stack.back().second;
                stack.pop_back();
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
                    it->timestamp - begin
                );
                out << "[CPU] " << label << " took " << duration.count() << " us" << '\n';
            }
            ++it;
        }
        _timeline.clear();
    }

private:
    struct Marker {
        std::chrono::steady_clock::time_point timestamp;
        std::string label;
        bool opening;
    };

    std::mutex _mutex;
    std::vector<Marker> _timeline;
    std::size_t _stack_depth = 0;
};

StdoutCpuLogger& cpu_logger() {
    static StdoutCpuLogger logger;
    return logger;
}

void default_cpu_begin(std::string_view label, std::uint32_t color) {
#if defined(ENABLE_PIX)
    if (g_pix_available) {
        auto label_w = to_wstring(label);
        PIXBeginEvent(PIX_COLOR(color), label_w.c_str());
    }
#endif
    cpu_logger().begin(label, color);
}

void default_cpu_end() {
#if defined(ENABLE_PIX)
    if (g_pix_available) {
        PIXEndEvent();
    }
#endif
    cpu_logger().end();
}

void default_gpu_begin(void* command_context, std::string_view label, std::uint32_t color) {
#if defined(ENABLE_PIX)
    if (g_pix_available && command_context != nullptr) {
        auto label_w = to_wstring(label);
        PIXBeginEvent(
            static_cast<ID3D12GraphicsCommandList*>(command_context),
            PIX_COLOR(color),
            label_w.c_str()
        );
    }
#else
    (void)command_context;
    (void)label;
    (void)color;
#endif
}

void default_gpu_end(void* command_context) {
#if defined(ENABLE_PIX)
    if (g_pix_available && command_context != nullptr) {
        PIXEndEvent(static_cast<ID3D12GraphicsCommandList*>(command_context));
    }
#else
    (void)command_context;
#endif
}

}  // namespace

void initialize() {
    std::lock_guard<std::mutex> cpu_lock(g_cpu_mutex);
    if (!g_cpu_begin) {
        g_cpu_begin = &default_cpu_begin;
    }
    if (!g_cpu_end) {
        g_cpu_end = &default_cpu_end;
    }

    std::lock_guard<std::mutex> gpu_lock(g_gpu_mutex);
    if (!g_gpu_begin) {
        g_gpu_begin = &default_gpu_begin;
    }
    if (!g_gpu_end) {
        g_gpu_end = &default_gpu_end;
    }

#if defined(ENABLE_RENDERDOC)
    if (g_renderdoc_api == nullptr) {
        auto status = RENDERDOC_GetAPI(RENDERDOC_Version_1_6_0, reinterpret_cast<void**>(&g_renderdoc_api));
        if (status != 1) {
            g_renderdoc_api = nullptr;
        }
    }
#endif
}

void shutdown() {
    std::lock_guard<std::mutex> cpu_lock(g_cpu_mutex);
    g_cpu_begin = nullptr;
    g_cpu_end = nullptr;

    std::lock_guard<std::mutex> gpu_lock(g_gpu_mutex);
    g_gpu_begin = nullptr;
    g_gpu_end = nullptr;
}

void set_cpu_callbacks(CpuBeginCallback begin, CpuEndCallback end) {
    std::lock_guard<std::mutex> lock(g_cpu_mutex);
    g_cpu_begin = begin ? begin : &default_cpu_begin;
    g_cpu_end = end ? end : &default_cpu_end;
}

void set_gpu_callbacks(GpuBeginCallback begin, GpuEndCallback end) {
    std::lock_guard<std::mutex> lock(g_gpu_mutex);
    g_gpu_begin = begin ? begin : &default_gpu_begin;
    g_gpu_end = end ? end : &default_gpu_end;
}

void begin_renderdoc_capture(ID3D12CommandQueue* queue) {
#if defined(ENABLE_RENDERDOC)
    if (g_renderdoc_api != nullptr) {
        g_renderdoc_api->StartFrameCapture(queue, nullptr);
    }
#else
    (void)queue;
#endif
}

void end_renderdoc_capture(ID3D12CommandQueue* queue) {
#if defined(ENABLE_RENDERDOC)
    if (g_renderdoc_api != nullptr) {
        g_renderdoc_api->EndFrameCapture(queue, nullptr);
    }
#else
    (void)queue;
#endif
}

ScopedCpuZone::ScopedCpuZone(std::string_view label, std::uint32_t color)
    : _label(label), _color(color), _active(false) {
    std::lock_guard<std::mutex> lock(g_cpu_mutex);
    if (g_cpu_begin != nullptr) {
        g_cpu_begin(label, color);
        _active = true;
    }
}

ScopedCpuZone::~ScopedCpuZone() {
    if (!_active) {
        return;
    }
    std::lock_guard<std::mutex> lock(g_cpu_mutex);
    if (g_cpu_end != nullptr) {
        g_cpu_end();
    }
}

ScopedGpuZone::ScopedGpuZone(
    ID3D12GraphicsCommandList* command_list,
    std::string_view label,
    std::uint32_t color
) : _command_list(command_list), _label(label), _color(color), _active(false) {
    std::lock_guard<std::mutex> lock(g_gpu_mutex);
    if (g_gpu_begin != nullptr) {
        g_gpu_begin(command_list, label, color);
        _active = true;
    }
}

ScopedGpuZone::~ScopedGpuZone() {
    if (!_active) {
        return;
    }
    std::lock_guard<std::mutex> lock(g_gpu_mutex);
    if (g_gpu_end != nullptr) {
        g_gpu_end(_command_list);
    }
}

}  // namespace vs::engine::render::diagnostics

