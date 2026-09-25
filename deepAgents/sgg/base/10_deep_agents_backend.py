from deepagents import create_deep_agent
from deepagents.backends import StoreBackend, StateBackend
from langgraph.store.memory import InMemoryStore
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
import os
load_dotenv(find_dotenv())

# 生产环境建议使用 RedisStore: from langgraph.store.redis import RedisStore
# 1. 配置 Store 后端
llm = init_chat_model(
    model=os.getenv("LLM_QWEN_MAX"),
    model_provider="openai"
)

store = InMemoryStore()
# todo 目标 使用长期记忆进行虚拟文件存储! 长期以及的好处就是可以跨进程
# 步骤1: store [存储虚拟文件]  步骤2: 指定storebackend
deep_agent = create_deep_agent(
    model=llm,
    tools=[],
    store=store,
    backend=StoreBackend(namespace=lambda x : ("filesystem",)),
    system_prompt="请把用户的重要信息保存到 user_profile.txt"
    # 需要存储到文件的内容 -> 存储到 store ->  namespace ("filesystem",) -> erdaye.txt  哈哈哈哈哈  桀桀
)

result1 = deep_agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "我叫大风哥,我的幸运数字是7号! 我喜欢点38号!!!"
            }
        ]
    }
)

print(f"第一次执行:{result1['messages'][-1].content}")


result2 = deep_agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "我是谁?我平时去红浪漫喜欢点多少号?"
            }
        ]
    }
)

print(f"第二次执行:{result2['messages'][-1].content}")


# 我想自己从store取值
result3 = store.search(("filesystem",))
# {文件名 : 存储的值 }
for item in result3:
    print(f"key:{item.key} -- value:{item.value}")