from typing import Literal

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv,find_dotenv
import os

# 加载 .env文件
load_dotenv(find_dotenv(),override = True)

# 创建tavily_client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# 定义搜索工具
@tool
def internet_search(
        query:str,
        max_results:int =10,
        topic:Literal["general","news","finance"] = "general",
        include_raw_content:bool = False):
    """
    互联网搜索工具！
    :param query: 搜索关键字
    :param max_results: 返回结果数量
    :param topic: 主题类型
    :param include_raw_content: False精简 True 返回详细结果
    :return: 搜索结果列表
    """
    print(f"进行网络搜索！搜索条件：{query},搜索主题类别:{topic},搜索最大的条数：{max_results}")
    return tavily_client.search(
        query=query,
        max_results=max_results,
        topic=topic,
        include_raw_content=include_raw_content
    )


# 极简初始化（自动读取OPENAI环境变量）
llm = init_chat_model(
    model=os.getenv("LLM_GLM-5.3-FLASH"),
    model_provider="openai"
)

# 目标: 创建深度代理的agent
# langchain  agent = create_agent(model,system_prompt,tools,...... )
deep_agent = create_deep_agent(
    model= llm,
    tools=[internet_search],
    system_prompt="你是一个高级研究助手! 你可以调用internet_search工具进行网络数据搜索!",
    subagents=[]  # 配置子代理的 子智能体
)

# 执行方法  invoke ainvoke  stream  astream
# langgraph -> 启动langgraph -> state  ->  {messages:[Message]}
for chunk in deep_agent.stream({
    "messages":[
        {
            "role":"user",
            "content": "帮我查询下人型机器的新闻,买机器人etf还能不能发财！"
        }
    ]
}):
    for node_name, state in chunk.items():
        # 我就获取有state 有messages属性
        if not state or "messages" not in state:
            continue
        # state {messages :[]}
        for message in state["messages"]:
            # AIMessage(content='', additional_kwa   模型的最终回答 模型决定调用哪个工具 模型决定调用哪个子代理
            # ToolMessage(content='{"query": "人型机器  工具的返回结果
            if node_name == "model":
                # 模型的最终回答 模型决定调用哪个工具 模型决定调用哪个子代理
                if message.content:
                    # content有值 [模型的最终回答]
                    print(f"[模型最终回答]:{message.content}")
                else:
                    # content没有值 [调用工具 / 调用子智能体]
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            if tool_call['name'] == "task":
                                # 调用子智能体
                                print(f"[模型决定调用子智能体],智能体:{tool_call['args']['subagent_type']}")
                            else:
                                # 调用了工具
                                print(f"[模型决定调用工具],工具:{tool_call['name']},传入参数:{tool_call['args']}")
            elif node_name == "tools":
                # 工具的最终返回结果
                content = message.content
                # 给前端返回结果
                print(f"[执行工具返回结果]:{content}")

# result -> state -> 1  ->  5 (经历几个对应的工具或者模型的处理)
# for  index, message in enumerate(result["messages"],start=1):
#     print(f"第{index}条,本次结果:{message}")


#print(f"结果:{result['messages'][-1].content}")