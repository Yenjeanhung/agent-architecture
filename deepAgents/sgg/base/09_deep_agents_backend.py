from pathlib import Path  # 导入Path类
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

# 1. 准备本地工作目录（用Path改写）
workspace_dir = Path("./agent_workspace").resolve()  # resolve() 等价于 os.path.abspath()，获取绝对路径
if not workspace_dir.exists():  # 等价于 os.path.exists()
    workspace_dir.mkdir(parents=True, exist_ok=True)  # 等价于 os.makedirs()

print(f"Agent 的工作目录已设置为: {workspace_dir}")

# todo fileSystembackend指定文件输出的位置
# 1. 创建文件系统后端
file_system_backend = FilesystemBackend(root_dir = workspace_dir , virtual_mode= True)
# 2. 创建deep_agent的时候指定backend

llm = init_chat_model(
    model=os.getenv("LLM_GLM-5.3-FLASH"),  # 模型名称（从环境变量读取）
    model_provider="openai"
)

deep_agent = create_deep_agent(
    model=llm,
    tools=[],
    system_prompt="你是一个智能助手。你可以使用文件工具来读写文件，但只有在用户明确要求时才创建文件。",
    subagents=[],
    backend=file_system_backend # 指定了文件存储方式 file_system存储 -> 存储位置   [你主动]
)

result_1 = deep_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "帮我查询下,python语言的发展历史!!"
        }
    ]
})

print(f"第一次调用结果: {result_1['messages'][-1].content}")

result_2 = deep_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "帮我查询下,java语言的发展历史,并且写到java.txt文件中!!"
        }
    ]
})

print(f"第二次调用结果: {result_2['messages'][-1].content}")


result_3 = deep_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "帮我读取java.txt文件中内容!!"
        }
    ]
})

print(f"第三次调用结果: {result_3['messages'][-1].content}")