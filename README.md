# 斗弈 · Rapfi 五子棋

一款支持 iPhone、Android 和 Windows 的离线五子棋。支持本地双人和单人 AI 对战；移动端优先加载 Rapfi WebAssembly，在引擎产物缺失或 WebView 不支持时自动切换到内置离线策略 AI。

## 功能

- 单人对战：可选择执黑或执白；Rapfi 可用时通过 Gomocup/Yixin 协议计算落点
- 双人对战：同一设备轮流落子
- 15×15 自适应棋盘、最后一手标记、获胜连线
- 新对局、悔棋、棋谱坐标和对局计时
- iPhone 安全区、Retina 棋盘和仅竖屏布局
- 完全离线；应用不会请求网络权限

## iPhone 运行

要求 macOS、Xcode 16 或更新版本，以及 iOS 16 或更新版本。

1. 在 Xcode 中打开 `ios/DouYi.xcodeproj`。
2. 选择 `DouYi` target，在 **Signing & Capabilities** 中选择自己的 Team。
3. 连接 iPhone，选择该设备后点击 **Run**；也可以先在 iPhone 模拟器中运行。

个人 Apple Account 可用于真机开发签名；Xcode 默认的自动签名会创建所需开发描述文件。真机首次运行时可能还需要在 iPhone 上启用开发者模式。

未预先构建 Rapfi WASM 时，工程仍可直接运行和单人对战（使用内置策略 AI）。若要把 Rapfi WASM 一并打进应用，可在配置好 Emscripten 的 macOS/Linux 环境运行：

```bash
./scripts/build-rapfi-wasm.sh
```

脚本会同时把产物放入 Android 和 iOS 的离线资源目录。

## 下载即玩

在 GitHub [Releases](https://github.com/MrDouZheng/rapfi-gomoku/releases) 下载对应文件：

- iPhone：`DouYi-iOS-Simulator.zip` 是模拟器构建，用于快速验收；真机安装需在 Xcode 中用自己的 Team 签名，或由维护者另行发布 TestFlight/App Store 版本。
- Windows：`RapfiGomoku-Windows-x64.exe`，双击运行，无需安装 Python。
- Android：`DouYi-Android.apk`，允许浏览器安装未知来源应用后直接安装。
- `SHA256SUMS.txt` 可用于核对下载文件完整性。

> iOS 模拟器包不能直接安装到 iPhone；这是 Apple 代码签名和 CPU 平台要求，不是 IPA。

## 从源码运行 Windows 版

要求 Windows 10/11 和 Python 3.10+（安装 Python 时建议勾选 `Add Python to PATH`）。

双击 `run.bat`，或在项目目录运行：

```powershell
python run.py
```

项目本身不依赖 pip 包；界面使用 Python 标准库 Tkinter。

## 测试

```powershell
python -m unittest discover -s tests -v
node --check android/app/src/main/assets/app.js
node tests/test_mobile_ai.mjs
```

iOS 编译验证（macOS）：

```bash
xcodebuild -project ios/DouYi.xcodeproj \
  -scheme DouYi \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO build
```

## 目录

```text
gomoku/       游戏规则、Rapfi 适配器和 Windows 桌面界面
engine/       Rapfi 2025-06-15 Windows SSE 引擎及自由规则权重
android/      Android WebView 应用及离线移动端界面
ios/          SwiftUI + WKWebView iPhone 工程
scripts/      Rapfi WASM 构建脚本
tests/        规则和协议解析测试
tools/        可复现的图标生成工具
```

## 实现说明

项目借鉴了 [gomoku-calculator](https://github.com/dhbloo/gomoku-calculator) 的协议集成思路：使用 `START`、`INFO`、`YXBOARD`、`YXNBEST` 等命令与 Rapfi 通信。界面、规则状态机和进程适配器均为本项目重新实现，没有复制该仓库的界面代码。

引擎来自 [Rapfi 2025-06-15](https://github.com/dhbloo/rapfi/releases/tag/250615)，使用自由规则 Mix9 网络。Windows 使用原生 SSE 引擎；Android/iOS 构建流水线使用官方源码生成单线程 WebAssembly。详情见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 版权与许可证

Copyright © 2026 MrDouZheng and contributors.

原创源文件使用 SPDX 版权与许可证头标记。本项目采用 GNU GPL v3.0；Rapfi 及其随附模型同样按 GPL v3.0 分发。完整信息见 [COPYRIGHT.md](COPYRIGHT.md)、[LICENSE](LICENSE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
