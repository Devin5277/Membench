"""报告生成:把评测结果序列化为 JSON 与可读 Markdown。"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from membench.models import CAPABILITIES, CAPABILITY_ORDER, AgentReport, Episode


def reports_to_dict(reports: List[AgentReport]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in reports]


def build_payload(
    episodes: List[Episode],
    reports: List[AgentReport],
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """构建可持久化的 JSON 载荷。"""
    return {
        "meta": meta or {},
        "capabilities": {k: CAPABILITIES[k] for k in CAPABILITY_ORDER},
        "episodes": [
            {"id": ep.id, "capability": ep.capability, "title": ep.title} for ep in episodes
        ],
        "reports": reports_to_dict(reports),
    }


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Markdown 报告
# ---------------------------------------------------------------------------
def render_markdown(reports: List[AgentReport]) -> str:
    agents = [r.agent_name for r in reports]
    header = "| 能力维度 | " + " | ".join(agents) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(agents)) + " |"

    rows: List[str] = []
    for cap in CAPABILITY_ORDER:
        label = CAPABILITIES[cap]["label"]
        scores = " | ".join(f"{r.capability_scores.get(cap, 0.0)}" for r in reports)
        rows.append(f"| {label} | {scores} |")
    overall = " | ".join(f"{r.overall}" for r in reports)
    rows.append(f"| **综合** | {overall} |")

    lines: List[str] = [
        "# 智能体长期记忆能力评测报告",
        "",
        "## 六维能力得分总览",
        "",
        header,
        sep,
        *rows,
        "",
        "> 分数为 0–100,按该能力下所有用例的平均得分计算。",
        "",
    ]

    for report in reports:
        lines += ["", f"## 智能体:{report.agent_name}", ""]
        for r in report.results:
            status = "✅" if r.score >= 100 else ("⚠️" if r.score >= 50 else "❌")
            lines.append(f"### {status} {r.episode_id} · {r.title} —— {r.score} 分")
            lines.append("")
            lines.append(f"- **能力**:{CAPABILITIES[r.capability]['label']}")
            lines.append(f"- **探针回答**:{r.probe_answer}")
            lines.append(f"- **记忆快照**:{r.memory_snapshot or '(空)'}")
            lines.append(f"- **行动轨迹**:{r.action_trace or '(空)'}")
            if r.reasons:
                lines.append("- **未通过原因**:")
                for reason in r.reasons:
                    lines.append(f"  - {reason}")
            else:
                lines.append("- **未通过原因**:无(全部通过)")
            lines.append("")

    return "\n".join(lines) + "\n"


def write_markdown(path: str | Path, reports: List[AgentReport]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_markdown(reports), encoding="utf-8")
