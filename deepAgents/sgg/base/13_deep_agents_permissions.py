# 独立可运行 🔥 官方标准写法：invoke 执行
import os

from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import FilesystemBackend
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

load_dotenv(find_dotenv())

# 1. 准备本地工作目录（用Path改写）
workspace_dir = Path("./agent_workspace").resolve()  # resolve() 等价于 os.path.abspath()，获取绝对路径
if not workspace_dir.exists():  # 等价于 os.path.exists()
    workspace_dir.mkdir(parents=True, exist_ok=True)  # 等价于 os.makedirs()

print(f"Agent 的工作目录已设置为: {workspace_dir}")

# 2. 配置本地文件系统后端
# virtual_mode=True 开启安全沙箱模式，限制 Agent 只能访问 workspace_dir
backend = FilesystemBackend(root_dir=workspace_dir, virtual_mode=True)

llm = init_chat_model(
    model=os.getenv("LLM_QWEN_MAX"),
    model_provider="openai"
)

# ========== 案例2：目录隔离 ==========
agent = create_deep_agent(
    model=llm,
    backend=backend,
    permissions=[
        # 1. 允许工作区读写
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/agent_workspace/**"],
            mode="allow"
        ),
        # 2. 拒绝其他所有路径
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/**"],
            mode="deny"
        ),
    ]
)

print("=" * 50)
print("【案例2】测试：目录隔离权限")
print("=" * 50)

# 测试1：允许目录 → 成功

result1 = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "在 /agent_workspace 下创建 data.txt"
    }]
})

print(f"第一次执行结果: {result1['messages'][-1].content}")


# 测试2：禁止外部目录 → 拒绝

result2 = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "在系统根目录 / 创建 secret.txt"
    }]
})

print(f"第二次执行结果: {result2['messages'][-1].content}")
