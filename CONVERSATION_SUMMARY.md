# 对话需求与交付摘要

## 用户需求

用户要求编写一个五子棋程序，支持：

1. 单人对战；
2. 双人对战；
3. 内置 Rapfi 引擎；
4. 可借鉴 `dhbloo/gomoku-calculator`；
5. 整理本次对话内容并上传到 GitHub。

## 实现决定

- 使用 Python 标准库 Tkinter 构建 Windows 桌面界面，减少安装依赖。
- 单人模式通过 Gomocup/Yixin 扩展协议启动并调用官方 Rapfi，而非自行实现一个弱 AI。
- 内置 Rapfi 2025-06-15 Windows SSE 发行文件和自由规则权重，兼顾兼容性与仓库体积。
- 采用 15×15 自由规则：先形成五个或更多连续棋子的一方获胜。
- 支持选择执黑/执白、新对局、悔棋、棋谱、计时、最后一手和获胜线显示。
- 参考项目只用于确认协议与交互思路；本项目的代码和界面重新实现。

## 验收方式

- 运行 `python -m unittest discover -s tests -v` 检查规则与协议解析。
- 运行 `python run.py` 或双击 `run.bat` 启动应用。
