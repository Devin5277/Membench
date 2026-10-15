"""语义判分器(可选、可插拔)。

默认评分路径(scorer.keyword)使用确定性关键词匹配,从根本上避免"语义偏移"。
本模块提供一条可选的语义判分通道,作为对命题"自动评分易语义偏移"痛点的进阶应对:

- `CharNgramJudge`:基于字符 n-gram 的"语义包含度"零依赖基线。它把"关键词是否被回答
  语义包含"量化为 0–1,能容忍轻微措辞差异,又无需任何外部模型/网络。
- 如需更强的释义级语义(paraphrase),可在 `score_episode_semantic` 中传入自定义 judge,
  例如嵌入向量余弦相似度,或 LLM-as-judge(见 docs/DESIGN.md 第 6 节)。

用法:
    membench run --scorer semantic
"""
from __future__ import annotations

from typing import List

from membench.agent import AgentAdapter
from membench.models import CheckResult, Episode, EpisodeResult

DEFAULT_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# 字符 n-gram 相似度
# ---------------------------------------------------------------------------
def char_ngrams(text: str, n: int = 3) -> set[str]:
    t = text.strip()
    if len(t) < n:
        return {t} if t else set()
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def containment(needle: str, haystack: str, n: int = 3) -> float:
    """关键字 needle 被 haystack 覆盖的比例(0–1)。

    衡量"回答在多大程度上包含了该关键词的字符特征",是对子串匹配的平滑推广,
    可容忍轻微空格/标点差异。对短于 n 的关键词自动降级 n,避免 2 字中文词漏判。
    """
    needle = needle.strip()
    if not needle:
        return 0.0
    n_eff = max(1, min(n, len(needle)))
    N, H = char_ngrams(needle, n_eff), char_ngrams(haystack, n_eff)
    if not N:
        return 0.0
    return len(N & H) / len(N)


def similarity(a: str, b: str, n: int = 3) -> float:
    """对称的 Jaccard 相似度(备用)。"""
    A, B = char_ngrams(a, n), char_ngrams(b, n)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


class Judge:
    """语义判分器接口。自定义实现可替换为嵌入/LLM-as-judge。"""

    def containment(self, needle: str, haystack: str) -> float:
        raise NotImplementedError

    def similarity(self, a: str, b: str) -> float:
        raise NotImplementedError


class CharNgramJudge(Judge):
    """零依赖的字符 n-gram 判分基线。"""

    def __init__(self, n: int = 3) -> None:
        self.n = n

    def containment(self, needle: str, haystack: str) -> float:
        return containment(needle, haystack, self.n)

    def similarity(self, a: str, b: str) -> float:
        return similarity(a, b, self.n)


# ---------------------------------------------------------------------------
# 语义评分
# ---------------------------------------------------------------------------
def score_episode_semantic(
    episode: Episode,
    agent: AgentAdapter,
    judge: Judge | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> EpisodeResult:
    """语义判分:should_contain / should_not_contain 用语义包含度,记忆检查保持精确。"""
    judge = judge or CharNgramJudge()
    probe = episode.probe

    agent.reset()
    for turn in episode.turns:
        agent.on_user(turn.content)

    answer = agent.on_user(probe.query) if probe else ""
    snapshot = agent.memory_snapshot()
    trace = agent.action_trace()

    checks: List[CheckResult] = []

    if probe is not None:
        for kw in probe.should_contain:
            c = judge.containment(kw, answer)
            passed = c >= threshold
            detail = f"回答对「{kw}」的语义包含度 {c:.2f}(阈值 {threshold})"
            checks.append(CheckResult(
                "should_contain", kw, passed, detail,
                "正确记忆" if passed else "遗漏误记",
            ))

        for kw in probe.should_not_contain:
            c = judge.containment(kw, answer)
            passed = c < threshold
            detail = f"回答对不应包含的「{kw}」语义包含度 {c:.2f}(阈值 {threshold})"
            checks.append(CheckResult(
                "should_not_contain", kw, passed, detail,
                "正确记忆" if passed else "误记混淆",
            ))

        for key in probe.expected_memory_present:
            passed = key in snapshot and bool(snapshot.get(key))
            detail = (f"记忆中正确保留了「{key}」" if passed
                      else f"记忆中缺少应保留的「{key}」")
            checks.append(CheckResult(
                "memory_present", key, passed, detail,
                "正确记忆" if passed else "遗漏误记",
            ))

        for key in probe.expected_memory_absent:
            passed = key not in snapshot
            detail = (f"记忆中正确排除了「{key}」" if passed
                      else f"记忆中错误保留了不应记忆的「{key}」")
            checks.append(CheckResult(
                "memory_absent", key, passed, detail,
                "正确记忆" if passed else "越界记忆",
            ))

    total = len(checks)
    passed_count = sum(1 for c in checks if c.passed)
    score = round(passed_count / total * 100, 1) if total else 100.0
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
