from deepagents import create_deep_agent
from deepagents.backends import StoreBackend, FilesystemBackend, CompositeBackend
from langgraph.store.memory import InMemoryStore
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
import os
from pathlib import Path  # 新增导入 Path 类

load_dotenv(find_dotenv())

# 1. 准备 Store
store = InMemoryStore()

# 2. 配置 LLM
llm = init_chat_model(
    model=os.getenv("LLM_GLM-5.3-FLASH"),
    model_provider="openai"
)

# 3. 定义混合后端工厂函数

workspace_dir = Path("./agent_workspace").resolve()
if not workspace_dir.exists():
    workspace_dir.mkdir(parents=True, exist_ok=True)
fs_backend = FilesystemBackend(root_dir=workspace_dir, virtual_mode=True)

# 3.2 实例化数据库后端（记得加上 namespace 参数）
store_backend = StoreBackend(namespace=lambda ctx: ("filesystem",))

composite_backend_instance = CompositeBackend(
    default=fs_backend,
    routes={
        "/store/": store_backend
    }
)


agent = create_deep_agent(
    model=llm,
    store=store,
    backend=composite_backend_instance,  # 传入工厂函数
    tools=[],
    system_prompt="""你是一个智能助手。
    - 重要记忆：写入 `/store/` 目录（如 `/store/profile.txt`），保存到store指定的存储方式中。
    """
)

# 4. 运行 Agent
print("\n=== 测试混合存储 ===")
config = {"configurable": {"thread_id": "thread_composite"}}

# 任务：同时触发两种存储路径
# user_input = "1. 创建本地文件 local.txt，内容'本地文件'。\n2. 创建记忆文件 /store/memory.txt，内容'重要记忆'。"
user_input = "你好，我叫yjh"
print(f"用户指令: {user_input}")

result = agent.invoke({
    "messages": [{"role": "user", "content": user_input}]
}, config=config)

print("Agent 回复:", result["messages"][-1].content)

# 5. 验证结果
print("\n=== 验证本地文件 (Filesystem) ===")
# 替换 os.path.join + os.path.exists 为 Path 写法
local_path = Path("agent_workspace") / "local.txt"  # Path 拼接路径
if local_path.exists():  # Path 内置 exists 方法
    print(f"本地文件存在: {local_path}")
else:
    print("本地文件缺失")

print("\n=== 验证数据库存储 (Store) ===")
# CompositeBackend 会自动剥离路由前缀，所以 /store/memory.txt 在 Store 中的 Key 为 /memory.txt
items = store.search(("filesystem",))
for item in items:
    print(item)