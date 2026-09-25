# -*- coding: utf-8 -*-
"""
DeepAgents stream 模式下的 HITL（人工审批）示例
核心功能：
1. 高危工具调用前触发人工审批
2. 使用 stream() 流式获取执行过程
3. 使用 Command(resume=...) 恢复执行
"""

import os
from dotenv import load_dotenv, find_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# 加载环境变量
load_dotenv(find_dotenv())


# ======================== 1. 定义工具 ========================

@tool
def delete_database(table_name: str):
    """高危操作：删除数据库表"""
    print(f"[工具执行] 删除数据库表: {table_name}")
    return f"已成功删除数据库表：{table_name}"


@tool
def delete_file(file_name: str):
    """高危操作：删除文件"""
    print(f"[工具执行] 删除文件: {file_name}")
    return f"已成功删除文件：{file_name}"


@tool
def select_data(table_name: str):
    """普通操作：查询表数据（无需审批）"""
    print(f"[工具执行] 查询表数据: {table_name}")
    return f"查询成功，表名：{table_name}"


# ======================== 2. 初始化 Agent ========================

checkpointer = InMemorySaver()

llm = init_chat_model(
    model=os.getenv("LLM_GLM-5.3-FLASH"),  # 模型名称（从环境变量读取）
    model_provider="openai"
)

deep_agent = create_deep_agent(
    model=llm,
    tools=[delete_database, delete_file, select_data],
    interrupt_on={
        "delete_database": True,
        "delete_file": True,
    },
    checkpointer=checkpointer,
    system_prompt="你是一个数据库与文件管理助手，所有回答都使用中文。"
)

# 会话配置：必须固定 thread_id，才能恢复执行
thread_config = {"configurable": {"thread_id": "stream_hitl_demo_1"}}


# ======================== 3. 第一次流式执行：触发中断 ========================

print("\n=== 第一阶段：开始流式执行 ===")

interrupts = None

for chunk in deep_agent.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "先删除 users 表，再查询 product 表的数据，最后删除 user.txt 文件。"
            }
        ]
    },
    config=thread_config
):
    print("stream chunk =>", chunk)

    # 关键：stream 模式下，中断信息会出现在某个 chunk 中
    if "__interrupt__" in chunk:
        interrupts = chunk["__interrupt__"]
        print("\n当前状态：智能体已暂停，等待人工审批。")
        break


# ======================== 4. 解析中断信息并模拟人工审批 ========================

if interrupts:
    # action_requests: [{name:工具名,args:{xx} , {}}]
    action_requests = interrupts[0].value["action_requests"]

    print("\n=== 审批信息 ===")
    print(f"需要审批的操作数量：{len(action_requests)}")
    print("待审批操作名称：", [item["name"] for item in action_requests])

    # 模拟人工审批结果
    # 顺序必须与 action_requests 一一对应
    decisions = [
        {"type": "approve"},  # 同意 delete_database
        {"type": "reject"}    # 拒绝 delete_file
    ]


    # ======================== 5. 恢复执行 ========================

    print("\n=== 第二阶段：恢复流式执行 ===")

    for chunk in deep_agent.stream(
        Command(
            resume={
                "decisions": decisions
            }
        ),
        config=thread_config   # 必须使用同一个 thread_id
    ):
        print("resume chunk =>", chunk)