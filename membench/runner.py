"""评测运行器:加载数据集 -> 逐个智能体跑全部用例 -> 聚合六维指标。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from membench.agents import get_agent
from membench.dataset import load, validate
from membench.metrics import aggregate
from membench.models import AgentReport, Episode
from membench.scorer import score_episode
from membench.scorer_semantic import score_episode_semantic

_SCORERS = {
    "keyword": score_episode,
    "semantic": score_episode_semantic,
}


def run_benchmark(
    dataset_path: str | Path,
    agent_names: List[str],
    scorer: str = "keyword",
) -> Tuple[List[Episode], List[AgentReport]]:
    """运行完整评测,返回 (用例列表, 每个智能体的报告)。

    scorer: "keyword"(默认,确定性关键词) 或 "semantic"(字符 n-gram 语义基线)。
    """
    if scorer not in _SCORERS:
        raise ValueError(f"未知评分器 {scorer!r},可选: {', '.join(_SCORERS)}")
    score_fn = _SCORERS[scorer]

    episodes = load(dataset_path)

    errors = validate(episodes)
    if errors:
        raise ValueError("数据集校验失败:\n" + "\n".join(f"  - {e}" for e in errors))

    reports: List[AgentReport] = []
    for name in agent_names:
        agent = get_agent(name)  # 每个智能体用全新实例
        results = [score_fn(ep, agent) for ep in episodes]
        reports.append(aggregate(name, results))

    return episodes, reports
