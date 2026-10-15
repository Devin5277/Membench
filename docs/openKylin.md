# membench × openKylin 集成与安装说明

membench 是一套**面向 openKylin 操作系统**的智能体长期记忆能力可解释评测框架。本文说明它与
openKylin 的关系、如何在 openKylin 上安装运行,以及如何对接 openKylin 生态内的智能体框架。

## 1. 与 openKylin 的关系(三层)

| 层面 | 说明 |
| --- | --- |
| 评测对象 | openKylin 生态内的智能体框架:KylinBot、Hermes Agent、OpenClaw 等 |
| 运行环境 | 以 `.deb` 原生安装到 openKylin(Debian 系),复用其 Python 3 运行时 |
| 数据场景 | 内置用例围绕 openKylin 开发者日常设计:软件源路径、构建服务器凭据、UKUI 桌面、社区贡献、风险操作 |

内置样例数据集直接使用 openKylin 真实语境:

- `discrimination-02` —— 区分开发/生产**软件源路径** `/etc/apt/sources.list.d/openkylin-{dev,prod}.list`;
- `discrimination-01` —— 区分 openKylin **构建服务器**的开发/生产密码;
- `reuse` —— 复用 KylinBot 的「openKylin 适配进展日报」「openKylin 社区贡献周报」模板;
- `boundary-03` —— 排除「删除 openKylin 软件源生产仓库」这类风险指令;
- `retention-02` —— 无关对话穿插 `apt` 升级内核、UKUI 换主题等 openKylin 操作。

## 2. 在 openKylin 上安装

openKylin(Debian 系)自带 Python 3;雷达图依赖 `python3-matplotlib`。

### 方式一:.deb 安装(推荐,满足"在 openKylin 上编译运行、产出 .deb")

```bash
# 在 openKylin 上执行
bash scripts/build_deb.sh          # 生成 dist/membench_0.1.0_all.deb
sudo dpkg -i dist/membench_0.1.0_all.deb
sudo apt -f install -y             # 若有依赖(如 python3-matplotlib)自动补齐
membench run                       # 立即可用
```

### 方式二:源码安装

```bash
sudo apt update
sudo apt install -y python3 python3-matplotlib
pip install .
membench run
```

### 校验安装

```bash
membench agents     # 列出已注册智能体(模拟 + KylinBot/HermesAgent 骨架)
membench run        # 一键运行评测,产出 results/report.json · report.md · radar.png
```

## 3. 对接 openKylin 智能体框架

评测逻辑与智能体完全解耦,接入 KylinBot / Hermes Agent 只需实现 `AgentAdapter` 的 4 个方法:

```python
from membench.agent import AgentAdapter

class KylinBotAdapter(AgentAdapter):
    name = "kylinbot"

    def reset(self):
        # 清空 KylinBot 会话与记忆
        ...

    def on_user(self, message: str) -> str:
        # 调用 KylinBot 本地服务 / API,返回回复
        ...

    def memory_snapshot(self) -> dict:
        # 从 KylinBot 的记忆存储(向量库/知识库/配置)读出当前"可回忆"的键值
        # 契约:返回 dict[str, str],键为事实键、值为其内容
        return {row.key: row.value for row in self.kylinbot.memory_store.all()}

    def action_trace(self) -> list[str]:
        # 返回 KylinBot 的工具调用 / 动作轨迹
        ...
```

登记到 `membench/agents/__init__.py` 的 `REGISTRY` 后,即可 `membench run --agents kylinbot,...` 参与评测。

已内置 **OpenAI 兼容 HTTP 适配器骨架**(`membench/agents/http_agent.py`),登记名为 `kylinbot` / `hermes_agent`。
设置环境变量指向真实服务地址即可接入:

```bash
export MEMBENCH_BASE_URL="http://127.0.0.1:8000"   # KylinBot / Hermes Agent 服务地址
export MEMBENCH_API_KEY="..."                       # 可选
export MEMBENCH_MODEL="kylinbot"                    # 可选
membench run --agents kylinbot,hermes_agent
```

`memory_snapshot` 需按各框架的实际记忆存储层覆盖实现(这是接入真实智能体唯一待定制点)。

## 4. 与 openKylin 生态的对应关系

| openKylin 元素 | membench 中的对应用例 |
| --- | --- |
| 软件源路径 `/etc/apt/sources.list.d/` | `discrimination-02` 相近区分 |
| 构建服务器 / 部署凭据 | `discrimination-01` 相近区分 |
| UKUI 桌面 / 麒麟软件商店 | `retention-02` 无关对话 |
| 社区贡献 / 适配工作模板 | `reuse-01` / `reuse-02` 任务复用 |
| 删软件源等风险操作 | `boundary-03` 边界识别 |
| 开发者个人信息(姓名/偏好/地址) | `retention` / `recall` / `update` 用例 |

## 5. 已知边界(如实注明)

- 真实智能体的 `memory_snapshot()` 需按各框架版本的实际存储层实现,完成度约 70%(见 `docs/DESIGN.md` 第 13 章)。
- 默认评分采用确定性关键词/键匹配,不依赖外部大模型,保证可复现、可解释;语义判分为可选通道。
