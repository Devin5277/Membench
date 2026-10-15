"""membench —— 智能体长期记忆可解释评测框架。

一个零依赖(除图表可选依赖 matplotlib)的可复现评测框架:
- 通过统一 AgentAdapter 接口接入任意智能体(KylinBot / Hermes Agent / kylin-agent / OpenClaw ...)
- 以"对话 + 记忆记录 + 行动轨迹 + 文件"为证据,自动评估六项长期记忆能力
- 确定性、可解释的自动评分,一键产出 JSON / Markdown 报告与多维对比雷达图
"""

__version__ = "0.1.0"
