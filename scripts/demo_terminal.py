#!/usr/bin/env python3
"""实机演示录屏脚本(自动带节奏)。

用于录制"实机演示视频":脚本按固定顺序,逐段 (1) 在终端打印该段的口播提示与等价命令,
(2) 等待你按下回车(或 --auto 模式下自动计时), (3) 真正执行命令并把真实输出打到终端,
(4) 可选打开结果图片/报告。你只需对着录屏按提示口播即可,无需记忆命令。

用法:
    python scripts/demo_terminal.py             # 手动节奏:每段结束后按回车进入下一段(推荐)
    python scripts/demo_terminal.py --auto 8    # 自动节奏:每段结束额外停留 8 秒(不含命令输出时间)

录制前准备(避免中文乱码):
    Windows: 用 Windows Terminal 当终端,或先执行  chcp 65001 && set PYTHONUTF8=1
    Linux/openKylin: 终端默认 UTF-8,无需处理。
    然后在项目根目录用 venv 的 python 运行本脚本(见 README「快速开始」)。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# 强制 UTF-8 输出,避免 Windows 控制台中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

ROOT = Path(__file__).resolve().parent.parent

# 每个子进程都带上 UTF-8 环境,保证 membench 的中文输出正常
_CHILD_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

# ---------------------------------------------------------------------------
# 演示分镜:每段 = (标题, 口播提示, 等价命令展示, 实际执行 argv 或 None, 要打开的文件或 None)
# ---------------------------------------------------------------------------
STEPS = [
    (
        "开场介绍",
        "面向 openKylin 的智能体长期记忆可解释评测框架 membench",
        None,
        None,
        None,
    ),
    (
        "列出智能体",
        "评测与智能体解耦;内置强/中/弱三档模拟智能体 + KylinBot/HermesAgent 骨架",
        "membench agents",
        [sys.executable, "-m", "membench", "agents"],
        None,
    ),
    (
        "一键运行评测",
        "13 个用例覆盖六项能力,三个智能体得分拉开层次(满分/82/20)",
        "membench run",
        [sys.executable, "-m", "membench", "run"],
        None,
    ),
    (
        "六维雷达图",
        "六维对比:强智能体满分,拟真智能体在措辞简化/边界识别失分,弱智能体塌陷",
        "start results/radar.png",
        None,
        str(ROOT / "results" / "radar.png"),
    ),
    (
        "语义判分",
        "判分器可插拔;切换字符 n-gram 语义基线,同样确定可复现",
        "membench run --scorer semantic --out results_semantic",
        [sys.executable, "-m", "membench", "run", "--scorer", "semantic", "--out", "results_semantic"],
        None,
    ),
    (
        "数据可扩展",
        "确定性生成器一键扩到 120 例(六维各 20),自动校验后重跑",
        "python scripts/gen_dataset.py --per 20",
        [sys.executable, "scripts/gen_dataset.py", "--per", "20"],
        None,
    ),
    (
        "可复现 + 可解释",
        "测试全过;报告里每条检查附原因与证据,结构化区分记住/误记/越界",
        "python tests/test_scorer.py",
        [sys.executable, "tests/test_scorer.py"],
        str(ROOT / "results" / "report.md"),
    ),
]


def _banner(idx: int, total: int, title: str, cue: str) -> None:
    print()
    print("═" * 62)
    print(f"  第 {idx} / {total} 段 · {title}")
    print(f"  口播要点:{cue}")
    print("═" * 62)


def _run(show: str, argv: list[str]) -> None:
    print(f"\n  $ {show}")
    print("  " + "─" * 56)
    subprocess.run(argv, cwd=str(ROOT), env=_CHILD_ENV)
    print("  " + "─" * 56)


def _open(path: str) -> None:
    p = Path(path)
    if not p.exists():
        print(f"  [未找到 {path},请手动打开]")
        return
    print(f"  [已打开 {path}]")
    try:
        if sys.platform == "win32":
            os.startfile(str(p))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(p)], check=False)
        else:
            subprocess.run(["xdg-open", str(p)], check=False)
    except OSError as exc:  # 打开查看器失败不中断演示
        print(f"  [打开失败:{exc},请手动打开]")





def _wait(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
        return
    input("  >>> 按回车进入下一段 …")


def main() -> int:
    parser = argparse.ArgumentParser(description="实机演示录屏脚本(自动带节奏)")
    parser.add_argument("--auto", type=float, default=0.0,
                        help="每段结束额外停留的秒数;缺省 0 表示手动回车推进(推荐)")
    args = parser.parse_args()

    print("membench · 实机演示录屏")
    print("提示:请先确认终端为 UTF-8(Windows 用 Windows Terminal 或 chcp 65001)。")
    print("节奏:", "自动(每段停留 %.1f 秒)" % args.auto if args.auto > 0 else "手动(每段按回车推进)")
    print()

    total = len(STEPS)
    for idx, (title, cue, show, argv, open_path) in enumerate(STEPS, start=1):
        _banner(idx, total, title, cue)
        if show and argv:
            _run(show, argv)
        if open_path:
            _open(open_path)
        _wait(args.auto)

    print()
    print("═" * 62)
    print("  演示结束。如需更短,可裁剪 STEPS 中任意段后重录。")
    print("═" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
