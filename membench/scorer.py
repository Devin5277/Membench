"""自动评分引擎:确定性、可解释、低人工介入。

针对每个用例,驱动智能体完成播种与探针,然后逐条检查并给出可解释结论。

四类检查:
- should_contain      —— 回答中应包含关键词(命中 = 正确记忆/调用)
- should_not_contain  —— 回答中不应包含关键词(命中 = 误记/混淆/残留)
- memory_present      —— 记忆快照中应存在该键(命中 = 长期保持/正确更新)
- memory_absent       —— 记忆快照中不应存在该键(命中 = 边界越界)

每条检查附 classification,对应命题强调的三类判定:
- 正确记忆   —— 记住了且调用了
- 遗漏误记   —— 记不住 / 漏答
- 误记混淆   —— 误记了(混淆、残留旧值)
- 越界记忆   —— 不该记却记了
"""
from __future__ import annotations

from typing import List

from membench.agent import AgentAdapter
from membench.models import CheckResult, Episode, EpisodeResult, Probe


def _contains(text: str, kw: str) -> bool:
    return kw in text


def _mk(check_type: str, target: str, passed: bool, detail: str) -> CheckResult:
    if check_type == "should_contain":
        classification = "正确记忆" if passed else "遗漏误记"
    elif check_type == "should_not_contain":
        classification = "正确记忆" if passed else "误记混淆"
    elif check_type == "memory_present":
        classification = "正确记忆" if passed else "遗漏误记"
    elif check_type == "memory_absent":
        classification = "正确记忆" if passed else "越界记忆"
    else:
        classification = "正确记忆" if passed else "未通过"
    return CheckResult(
        check_type=check_type,
        target=target,
        passed=passed,
        detail=detail,
        classification=classification,
    )


def score_episode(episode: Episode, agent: AgentAdapter) -> EpisodeResult:
    """对单个用例,在一个全新重置的智能体上完成评测并评分。"""
    probe: Probe | None = episode.probe

    # 1) 重置
    agent.reset()

    # 2) 播种阶段
    for turn in episode.turns:
        agent.on_user(turn.content)

    # 3) 探针阶段
    answer = agent.on_user(probe.query) if probe else ""
    snapshot = agent.memory_snapshot()
    trace = agent.action_trace()

    checks: List[CheckResult] = []

    if probe is not None:
        for kw in probe.should_contain:
            passed = _contains(answer, kw)
            detail = (f"回答中包含关键词「{kw}」" if passed
                      else f"回答中未出现应包含的关键词「{kw}」")
            checks.append(_mk("should_contain", kw, passed, detail))

        for kw in probe.should_not_contain:
            present = _contains(answer, kw)
            passed = not present
            detail = (f"回答中未出现不应包含的关键词「{kw}」" if passed
                      else f"回答中错误出现不应包含的关键词「{kw}」")
            checks.append(_mk("should_not_contain", kw, passed, detail))

        for key in probe.expected_memory_present:
            passed = key in snapshot and bool(snapshot.get(key))
            detail = (f"记忆中正确保留了「{key}」" if passed
                      else f"记忆中缺少应保留的「{key}」")
            checks.append(_mk("memory_present", key, passed, detail))

        for key in probe.expected_memory_absent:
            passed = key not in snapshot
            detail = (f"记忆中正确排除了「{key}」" if passed
                      else f"记忆中错误保留了不应记忆的「{key}」")
            checks.append(_mk("memory_absent", key, passed, detail))

    total = len(checks)
    passed_count = sum(1 for c in checks if c.passed)
    score = round(passed_count / total * 100, 1) if total else 100.0

    # 失败项汇总为可读原因
    reasons = [c.detail for c in checks if not c.passed]

    return EpisodeResult(
        episode_id=episode.id,
        capability=episode.capability,
        title=episode.title,
        score=score,
        passed_checks=passed_count,
        total_checks=total,
        checks=checks,
        probe_answer=answer,
        memory_snapshot=snapshot,
        action_trace=trace,
        reasons=reasons,
    )
