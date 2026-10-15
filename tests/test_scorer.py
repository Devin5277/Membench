"""membench 基础测试(纯标准库断言,可直接 `python tests/test_scorer.py` 运行)。"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from membench.dataset import DEFAULT_DATASET, load, validate  # noqa: E402
from membench.models import CAPABILITY_ORDER  # noqa: E402
from membench.runner import run_benchmark  # noqa: E402


def test_dataset_valid() -> None:
    eps = load(DEFAULT_DATASET)
    assert len(eps) == 13, f"期望 13 个用例,实际 {len(eps)}"
    assert set(e.capability for e in eps) == set(CAPABILITY_ORDER), "六项能力应全部覆盖"
    assert validate(eps) == [], "样例数据集应通过校验"


def test_good_beats_weak() -> None:
    _, reports = run_benchmark(DEFAULT_DATASET, ["mock_good", "mock_weak"])
    by_name = {r.agent_name: r for r in reports}
    assert by_name["mock_good"].overall > by_name["mock_weak"].overall, \
        "记忆强智能体总分应高于弱智能体"


def test_reports_are_explainable() -> None:
    _, reports = run_benchmark(DEFAULT_DATASET, ["mock_good", "mock_weak"])
    for r in reports:
        for res in r.results:
            assert res.total_checks > 0, f"{res.episode_id} 无检查项"
            assert all(c.detail and c.classification for c in res.checks), \
                f"{res.episode_id} 存在无解释的检查项"


def test_semantic_scorer() -> None:
    _, reports = run_benchmark(DEFAULT_DATASET, ["mock_good", "mock_weak"], scorer="semantic")
    by_name = {r.agent_name: r for r in reports}
    assert by_name["mock_good"].overall > by_name["mock_weak"].overall, \
        "语义判分下,记忆强智能体总分仍应高于弱智能体"


def test_agents_registered() -> None:
    from membench.agents import list_agents
    names = list_agents().keys()
    assert {"mock_good", "mock_weak", "kylinbot", "hermes_agent"} <= set(names), \
        "应注册模拟智能体与真实智能体骨架"


if __name__ == "__main__":
    tests = [
        test_dataset_valid,
        test_good_beats_weak,
        test_reports_are_explainable,
        test_semantic_scorer,
        test_agents_registered,
    ]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print("全部测试通过 [OK]")
