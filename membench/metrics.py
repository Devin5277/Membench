"""六维指标聚合:把单个用例得分汇总为每项能力的 0-100 分与总分。"""
from __future__ import annotations

from collections import defaultdict
from typing import List

from membench.models import CAPABILITY_ORDER, AgentReport, EpisodeResult


def aggregate(agent_name: str, results: List[EpisodeResult]) -> AgentReport:
    """按能力维度聚合用例得分,产出 AgentReport。"""
    report = AgentReport(agent_name=agent_name, results=results)

    by_cap: dict[str, list[float]] = defaultdict(list)
    for r in results:
        by_cap[r.capability].append(r.score)

    for cap in CAPABILITY_ORDER:
        scores = by_cap.get(cap, [])
        report.capability_scores[cap] = round(sum(scores) / len(scores), 1) if scores else 0.0

    report.overall = round(sum(report.capability_scores.values()) / len(CAPABILITY_ORDER), 1)
    return report
