# 弈境 · Rapfi 五子棋

一款零第三方 Python 依赖的 Windows 桌面五子棋，支持本地双人和真正由 Rapfi 驱动的单人对战。

## 功能

- 单人对战：可选择执黑或执白，AI 通过 Gomocup/Yixin 协议调用内置 Rapfi
- 双人对战：同一台电脑轮流落子
- 15×15 自适应棋盘、落子序号、最后一手标记、获胜连线
- 新对局、悔棋、棋谱坐标和对局计时
- 完全离线运行，Rapfi SSE 版本兼容大多数 64 位 Windows 电脑

## 运行

要求 Windows 10/11 和 Python 3.10+（安装 Python 时建议勾选 `Add Python to PATH`）。

双击 `run.bat`，或在项目目录运行：

```powershell
python run.py
```

项目本身不依赖 pip 包；界面使用 Python 标准库 Tkinter。

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 目录

```text
gomoku/       游戏规则、Rapfi 适配器和桌面界面
engine/       内置 Rapfi 2025-06-15 Windows SSE 引擎及自由规则权重
tests/        规则和协议解析测试
run.py        程序入口
run.bat       Windows 双击启动器
```

## 实现说明

项目借鉴了 [gomoku-calculator](https://github.com/dhbloo/gomoku-calculator) 的协议集成思路：使用 `START`、`INFO`、`YXBOARD`、`YXNBEST` 等命令与 Rapfi 通信。界面、规则状态机和 Python 进程适配器均为本项目重新实现，没有复制该仓库的界面代码。

内置引擎来自 [Rapfi 2025-06-15](https://github.com/dhbloo/rapfi/releases/tag/250615)，使用自由规则 Mix9 网络。详情见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 许可证

本项目采用 GNU GPL v3.0。Rapfi 及其随附模型同样按 GPL v3.0 分发。
