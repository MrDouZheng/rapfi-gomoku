# 第三方软件说明

## Rapfi

- 项目：https://github.com/dhbloo/rapfi
- 内置版本：Rapfi 2025-06-15（发行标签 `250615`）
- 发行包：https://github.com/dhbloo/rapfi/releases/tag/250615
- 许可证：GNU General Public License v3.0
- 内置文件：Windows SSE 可执行文件、自由规则 Mix9 权重、配置、作者名单，以及 Android/iOS 发布构建中的 WebAssembly 产物
- 对应源代码：https://github.com/dhbloo/rapfi/tree/250615
- 源码归档：https://github.com/dhbloo/rapfi/archive/refs/tags/250615.zip

Rapfi 的作者信息保留在 `engine/AUTHORS`。完整 GPL v3.0 条款见仓库根目录 `LICENSE`。

移动端 Rapfi WebAssembly 不提交二进制构建产物到源码树；发布流水线从上述固定标签源码构建，并把相同产物分别打包进 Android 和 iOS 应用。若产物缺失或 WebView 无法启动它，应用会使用本项目原创的轻量离线策略 AI。

## gomoku-calculator

本项目参考了其公开文档中描述的 Rapfi WebAssembly/Gomocup 协议集成方式，但未复制其源代码或视觉资源。

- 项目：https://github.com/dhbloo/gomoku-calculator
