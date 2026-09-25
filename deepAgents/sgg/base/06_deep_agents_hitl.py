# -*- coding: utf-8 -*-
"""
DeepAgents 中断审批机制示例
核心功能：演示高危工具调用前的人工审批流程，支持删除数据库表/文件的审批控制
"""
import os
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver  # 内存检查点，用于保存中断状态
from langgraph.types import Command  # 恢复执行的指令类型
from dotenv import load_dotenv, find_dotenv

# 加载环境变量（DASHSCOPE_API_KEY等），优先查找当前目录的.env文件
load_dotenv(find_dotenv())


# ======================== 1. 定义工具函数 ========================
# 装饰器@tool将普通函数转为LangChain可调用工具，函数文档字符串会作为工具描述给Agent
@tool
def delete_database(table_name: str):
    """
    高危操作：删除数据库表
    :param table_name: 要删除的表名
    :return: 操作结果提示
    """
    print(f"[工具执行] 删除表: {table_name}")
    return f"已成功删除表: {table_name}"


@tool
def select_data(table_name: str):
    """
    普通操作：查询指定表名的数据（无需审批）
    :param table_name: 要查询的表名
    :return: 操作结果提示
    """
    print(f"[工具执行] 查询指定表名数据: {table_name}")
    return f"查询数据成功：{table_name}"


@tool
def delete_file(file_name: str):
    """
    高危操作：删除文件
    :param file_name: 要删除的文件路径/名称
    :return: 操作结果提示
    """
    print(f"[工具执行] 删除文件: {file_name}")
    return f"已成功删除文件: {file_name}"



# ======================== 2. 核心配置 ========================
# 配置检查点（必须）：保存Agent中断时的状态，确保恢复执行时能衔接上下文
# 注意：InMemorySaver仅用于测试，生产环境建议使用RedisCheckpointer等持久化方案
checkpointer = InMemorySaver()

# 初始化大模型（通义千问）
llm = init_chat_model(
    model=os.getenv("LLM_GLM-5.3-FLASH"),          # 模型名称（从环境变量读取）
    model_provider="openai"                   # 兼容OpenAI格式的接口
)

# 重要前提: 1. checkpointer=checkpointer  2. 两次的线程id必须相同

# 创建deep_agent 配置三个工具以及设置人机交互
deep_agent = create_deep_agent(
    model=llm,
    tools = [delete_database, select_data, delete_file],
    system_prompt="你是一个高级数据处理助手，你只能调用delete_database,select_data,delete_file工具，请勿调用其他工具。",
    checkpointer=checkpointer , #配置短期记忆,一次会话内 (执行的thread_id相同)可以共享数据,第一次拦截以后,第二次还能继续执行..
    interrupt_on={
        # 工具名 : 是否打断  False 不打断,执行放行  True 打断 , 有三个动作  {"allowed_decisions": ["approve", "reject"]}
        # approve 放行  reject 拒绝  edit 放行,修改工具的参数
        "delete_database": True,
        "delete_file": True,
        "select_data": False
    }
)


# 只要调用深度代理触发,工具的使用,看有没有拦截 (第一次调用)

# ======================== 3. 执行流程 ========================
# 会话配置：通过thread_id绑定会话，确保中断/恢复在同一个会话中执行
thread_config = {"configurable": {"thread_id": "safe_thread_1"}}

print("\n=== 第一阶段：触发工具调用（规划阶段）===")
# 第一次调用：Agent会规划操作序列，但触发中断后不会执行任何工具
result_1 = deep_agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "先查询product表数据！再把用户表(users)删了！最后把 user.txt 文件也删除了！"
            }
        ]
    },
    config=thread_config  # 绑定会话ID，确保状态可追溯
)


# 怎么看有没有打断  1. 看工具的调用  2. 打断了 result __interrupt__
# todo: 只要本次有打断内容参与,整体都先不会执行(包括放行的函数),只有判断放行规则才会执行!
print(f"第一次调用结果: {result_1.get("__interrupt__")}")
interrupt = result_1.get("__interrupt__")

# 如何进行放行处理
if interrupt:
    # 不为空,触发了一些拦截工具
    print(f"本地打断了{len(interrupt[0].value['action_requests'])}个工具,分别是:{[  tool_item['name'] for tool_item in interrupt[0].value['action_requests']]}")
    # [Interrupt(value={'action_requests': [{'name': 'delete_database', 'args': {'table_name': 'users'}, 'description': "Tool execution requires approval\n\nTool: delete_database\nArgs: {'table_name': 'users'}"}, {'name': 'delete_file', 'args': {'file_name': 'user.txt'}, 'description': "Tool execution requires approval\n\nTool: delete_file\nArgs: {'file_name': 'user.txt'}"}], 'review_configs': [{'action_name': 'delete_database', 'allowed_decisions': ['approve', 'edit', 'reject', 'respond']}, {'action_name': 'delete_file', 'allow
    # action_requests 本次触发的打断的工具  [ {name="工具的名字",args:{工具的参数}},{name="工具的名字",args:{工具的参数}}  ]4
    # review_configs  本次触发的打断的工具可选项  [{'action_name': 'delete_database', 'allowed_decisions': ['approve'
    # 固定工具是否放行   delete_database 放行  delete_file 我们拦截
    decisions = []  # 存放放行动作 , 顺序 ==  action_requests的顺序

    for action in interrupt[0].value['action_requests']:
        if action['name'] == 'delete_database':
            # 放行
            decisions.append({
                "type":"approve"
            })
        elif action['name'] == 'delete_file':
            # 修改参数 放行的,我要删除 文件不是你说的文件
            decisions.append({
                "type": "edit",
                "edited_action": {
                    "name": action["name"],  # Must include the tool name
                    "args": {"file_name": "erdaye.pdf"}
                }
            })

    # 做好决定了
    # 第二次执行即可
    result2 =  deep_agent.invoke(
        Command(
            resume={
                "decisions":decisions
            }
        ),
        config=thread_config
    )

    print(f"最终执行结果:{result2['messages'][-1].content}")