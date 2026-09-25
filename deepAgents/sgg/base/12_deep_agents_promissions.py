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
    model=os.getenv("LLM_GLM-5.3-FLASH"),
    model_provider="openai"
)


# 2. 定义权限：禁止所有写入操作
agent = create_deep_agent(
    model=llm,
    backend=backend,
    permissions=[
        # 权限匹配自上而下! 匹配到了以后就会停止匹配!!
        # 越详细的越靠上写!!
        FilesystemPermission(
            operations=["write"],
            paths=["/**"],
            mode="deny"
        ),
        FilesystemPermission(
            operations=["write"],
            paths=["/xx/**"],
            mode="deny"
        )
    ]
)

# ==============================
# 正确方式：直接 invoke 运行！
# 让智能体自己执行文件操作，权限自动生效
# ==============================
print("=== 测试：智能体只读权限（invoke 执行）===")

# 测试1：让智能体执行【写入文件】→ 应该被拒绝

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "请在根目录创建test.txt，内容为hello"
    }]
})

print(f"写入结果：{result['messages'][-1].content}")


# 测试2：让智能体执行【读取文件】→ 应该允许
result1 = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "读取java.txt文件内容"
    }]
})
print(f"读取结果：{result1['messages'][-1].content}")
