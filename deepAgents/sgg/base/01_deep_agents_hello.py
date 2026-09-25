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
result = deep_agent.invoke({
    "messages":[
        {
            "role":"user",
            "content": "帮我查询下人型机器的新闻,买机器人etf还能不能发财！"
        }
    ]
})

# result -> state -> 1  ->  5 (经历几个对应的工具或者模型的处理)
for  index, message in enumerate(result["messages"],start=1):
    print(f"第{index}条,本次结果:{message}")


#print(f"结果:{result['messages'][-1].content}")