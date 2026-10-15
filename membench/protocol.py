"""事实协议与别名表(供模拟智能体与样例数据集共用)。

为了让评测结果确定、可复现、低人工介入,样例数据集使用一套简洁的"事实协议"来
向智能体播种信息,模拟智能体据此解析。真实智能体适配器无需遵循此协议——它只需
实现 AgentAdapter 接口即可;这里的协议仅服务于离线可复现的演示。

协议格式(用户消息前缀):
    [记住] key = value      长期记忆
    [更新] key = value      覆盖更新
    [敏感] key = value      敏感信息(不应记忆)
    [临时] key = value      临时信息(不应长期保留)
    [模板] name => action   任务模板(可被复用)
    (普通文本)              忽略

别名表用于把探针的自然语言问题映射回记忆键,从而让回答生成与评分都确定化。
"""
from __future__ import annotations

import re
from typing import Dict, List

# 各类事实语句的正则
RE_REMEMBER = re.compile(r"^\[记住\]\s*(.+?)\s*=\s*(.+)$")
RE_UPDATE = re.compile(r"^\[更新\]\s*(.+?)\s*=\s*(.+)$")
RE_SENSITIVE = re.compile(r"^\[敏感\]\s*(.+?)\s*=\s*(.+)$")
RE_TEMP = re.compile(r"^\[临时\]\s*(.+?)\s*=\s*(.+)$")
RE_RISK = re.compile(r"^\[风险\]\s*(.+?)\s*=\s*(.+)$")
RE_TEMPLATE = re.compile(r"^\[模板\]\s*(.+?)\s*=>\s*(.+)$")

# 记忆键 -> 探针中可能出现的自然语言别名
ALIASES: Dict[str, List[str]] = {
    "name": ["名字", "叫什么", "称呼", "怎么称呼", "姓名", "贵姓"],
    "preference": ["偏好", "喜欢", "爱喝"],
    "project_path": ["项目路径", "工程路径", "路径"],
    "address": ["地址", "住在", "住哪", "住在哪里"],
    "dev_password": ["开发密码", "开发环境密码", "dev密码", "开发环境"],
    "prod_password": ["生产密码", "生产环境密码", "prod密码", "生产环境"],
    "dev_path": ["开发路径", "dev路径"],
    "prod_path": ["生产路径", "prod路径"],
    # 粗粒度键(弱智能体把相似信息归一化后的键)
    "password": ["密码", "password"],
    "path": ["路径", "部署"],
    # 边界类键
    "bank_password": ["银行卡密码", "银行卡", "银行密码"],
    "temp_note": ["下午", "在哪里", "会议室", "临时"],
    "instruction": ["指令", "复述"],
    # 模板键
    "template:日报": ["日报"],
    "template:周报": ["周报"],
}


def match_alias(key: str, query: str) -> bool:
    """判断探针 query 是否命中记忆键 key 的别名。"""
    aliases = ALIASES.get(key, [key])
    return any(a in query for a in aliases)
