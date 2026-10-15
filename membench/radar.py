"""多维对比雷达图:六项能力 × 多个智能体。

依赖 matplotlib(可选)。若未安装,评测仍会产出 JSON / Markdown 报告,
仅跳过雷达图生成。
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import List

from membench.models import CAPABILITIES, CAPABILITY_ORDER, AgentReport


def _setup_cjk_font() -> None:
    try:
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError:
        return

    candidates = [
        "Microsoft YaHei", "SimHei", "PingFang SC",
        "Noto Sans CJK SC", "Noto Sans SC", "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei", "Source Han Sans SC", "DejaVu Sans",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name] + list(plt.rcParams.get("font.sans-serif", []))
            break
    plt.rcParams["axes.unicode_minus"] = False


def draw_radar(reports: List[AgentReport], out_path: str | Path, title: str = "智能体长期记忆能力对比") -> str:
    """绘制六维雷达图,返回输出文件路径。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _setup_cjk_font()

    labels = [CAPABILITIES[c]["label"] for c in CAPABILITY_ORDER]
    n = len(labels)
    angles = [i * 2 * math.pi / n for i in range(n)]
    angles += angles[:1]

    fig = plt.figure(figsize=(7.5, 7.5))
    ax = fig.add_subplot(111, polar=True)

    for report in reports:
        values = [report.capability_scores.get(c, 0.0) for c in CAPABILITY_ORDER]
        values += values[:1]
        ax.plot(angles, values, linewidth=2, label=report.agent_name)
        ax.fill(angles, values, alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8)
    ax.set_rlabel_position(0)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.12), fontsize=10)
    ax.set_title(title, pad=22, fontsize=13)

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return str(p)
