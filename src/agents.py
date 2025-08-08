# === src/agents.py ===

import os
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from src.types import ClassifiedIntent, GraphState, Participant

from .tools.dice_tools import roll_dice_tool

# 加载环境变量
load_dotenv()

IS_DEBUG = os.getenv("IS_DEBUG", "false").lower() == "true"

# 根据环境变量选择LLM
def get_llm():
    """根据环境变量选择使用Claude还是Google Gemini"""
    anthropic_api_key = os.getenv("CLAUDE_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    # 优先使用Claude
    if anthropic_api_key:
        return ChatAnthropic(
            anthropic_api_key=anthropic_api_key,
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            temperature=0.1,
            max_retries=3,
            streaming=False,
        )
    elif google_api_key:
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=google_api_key,
            temperature=0.1,
            max_retries=3,
        )
    else:
        raise ValueError("需要设置 ANTHROPIC_API_KEY 或 GOOGLE_API_KEY")

# 初始化LLM
llm = get_llm()

# --- Agent 1: Player Input Triage Agent ---

async def player_input_triage_agent(state: GraphState) -> Dict[str, Any]:
    """玩家输入意图分类智能体"""
    if IS_DEBUG:
        print("--- 调用: Player Input Triage Agent ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个游戏助手，负责将玩家在《克苏鲁的呼唤》游戏中的输入进行意图分类。根据玩家输入和当前上下文进行判断"),
        ("human", """当前场景: 战斗在第{round_number}轮，轮到玩家 {player_id} 行动。
        玩家输入: "{input}"
        请对以上输入进行分类和解析。
        如果玩家输入是关于他的行动的，比如，"我使用武器攻击"，"闪避"，"对抗"，请返回 "direct_action"。
        如果玩家输入是关于规则和状态的，请返回 "query"。
        如果玩家输入是关于OOC的，请返回 "ooc"。
        如果玩家输入是模糊的，请返回 "fuzzy_intent"。
        
        请只返回意图分类，不要其他内容。""")
    ])

    chain = prompt.pipe(llm)
    result = await chain.ainvoke({
        "round_number": state["round_number"],
        "player_id": state["initiative_order"][state["current_actor_index"]] if state["current_actor_index"] < len(state["initiative_order"]) else "unknown",
        "input": state["player_input"] or "",
    })

    # 解析结果
    intent_text = result.content.strip().lower()
    if "direct_action" in intent_text:
        classified_intent = ClassifiedIntent.DIRECT_ACTION
    elif "query" in intent_text:
        classified_intent = ClassifiedIntent.QUERY
    elif "ooc" in intent_text:
        classified_intent = ClassifiedIntent.OOC
    else:
        classified_intent = ClassifiedIntent.FUZZY_INTENT

    return {"classified_intent": classified_intent}

# --- Agent 2: Monster AI Agent ---

async def monster_ai_agent(state: GraphState) -> Dict[str, Any]:
    """怪物AI智能体"""
    if IS_DEBUG:
        print("--- 调用: Monster AI Agent ---")
    
    context_info = "\n".join(state["previous_context"])
    current_actor_id = state["initiative_order"][state["current_actor_index"]] if state["current_actor_index"] < len(state["initiative_order"]) else "unknown"
    combat_log_text = "\n".join(state["combat_log"])
    map_info = json.dumps(state["map"]) if state["map"] else "无地图信息"
    participants_info = json.dumps(state["participants"])
    current_actor_info = json.dumps(next((p for p in state["participants"] if p["id"] == current_actor_id), {}))
    
    prompt = ChatPromptTemplate.from_template("""你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    重要：当你需要掷骰子时，必须使用roll_dice_tool工具，尤其是伤害，在判定命中后需要投伤害骰，通过roll_dice_tool工具计算。不可以跳过掷骰子，一定要用roll_dice_tool工具。
    现在正在进行战斗轮，你正在扮演怪物。
    之前的上下文信息: {context_info}
    当前游戏状态: 轮到怪物 {current_actor_id} 行动。
    最近的log: "{combat_log_text}",
    地图信息：{map_info},
    所有角色状态：{participants_info}
    你的状态：{current_actor_info}
    
    决定你控制的怪物的行动，并把行动造成的结果完全描述出来放进description里,如果需要玩家补充信息，请也放进description里（如选择闪避或者对抗）。
    比如：食尸鬼使用了爪击，需要描述命中，对方的闪避或者对抗，对方的血量变化，对方的状态变化，对方的死亡，等等。！！不要忘了带上掷骰子的动作和结果。
    如果行动造成了数值变化或者location变化，需要把把更新后的对应participant对象放进result数组里。如玩家对食尸鬼造成1点伤害，那么result数组里需要有食尸鬼的更新后的对象，hp比之前少1点。
    如果需要某玩家补充信息,请把requiresPlayerInput设置为true，请把temp_player_actor设置为目标玩家的名字。
    返回JSON blob的结构化结果：
    {{
      "description": "行动信息(具体做了什么，造成了什么影响，)",
      "result": "participants中发生数据变化的对象[]",
      "requiresPlayerInput": "是否需要玩家补充信息",
      "temp_player_actor": "需要补充信息的玩家的名字"
    }}

    {agent_scratchpad}
    """)
    
    tools = [roll_dice_tool]
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    result = await agent_executor.ainvoke({
        "context_info": context_info,
        "current_actor_id": current_actor_id,
        "combat_log_text": combat_log_text,
        "map_info": map_info,
        "participants_info": participants_info,
        "current_actor_info": current_actor_info
    })
    
    # 解析结果
    output = result["output"]
    parsed_result = None
    
    # 处理 LLM 返回的内容，可能包含在代码块中
    if "```json" in output:
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", output)
        if json_match:
            parsed_result = json.loads(json_match.group(1))
    else:
        # 尝试直接解析JSON
        try:
            parsed_result = json.loads(output)
        except:
            parsed_result = {"description": output, "result": [], "requiresPlayerInput": False}

    # 更新参与者
    updated_participants = state["participants"].copy()
    if parsed_result and "result" in parsed_result:
        for updated_participant_data in parsed_result["result"]:
            for i, participant in enumerate(updated_participants):
                if participant["id"] == updated_participant_data.get("id"):
                    updated_participants[i] = updated_participant_data
                    break
    return {
        "combat_log": [f"[守秘人]: {parsed_result.get('description', '')}"],
        "participants": updated_participants,
        "requires_player_input": parsed_result.get("requiresPlayerInput", False) if parsed_result else False,
        "temp_player_actor": parsed_result.get("temp_player_actor", None) if parsed_result else None,
    }

# --- Agent 3: OOC Agent ---

async def ooc_agent(state: GraphState) -> Dict[str, Any]:
    """OOC对话智能体"""
    if IS_DEBUG:
        print("--- 调用: ooc Agent ---")
    
    prompt = ChatPromptTemplate.from_template("""你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    当前游戏状态: 轮到玩家 {player_id} 行动。
    玩家的输入: "{input}"，
    最近的log: {combat_log}
    请根据规则和常识，以KP的口吻清晰地回答玩家的问题，并引导他做出最终决定。注意，玩家可能会发表一些ooc，请合理的回复ooc即可""")
    
    chain = prompt.pipe(llm)
    result = await chain.ainvoke({
        "player_id": state["initiative_order"][state["current_actor_index"]] if state["current_actor_index"] < len(state["initiative_order"]) else "unknown",
        "input": state["player_input"] or "",
        "combat_log": "\n".join(state["combat_log"][-5:]),
    })
    
    return {
        "combat_log": [f"[守秘人]: {result.content}"],
        "llm_output": result.content
    }

# --- Agent 4: Rules Keeper Agent ---

async def rules_keeper_agent(state: GraphState) -> Dict[str, Any]:
    """规则查询智能体"""
    if IS_DEBUG:
        print("--- 调用: Rules Keeper Agent ---")
    
    if state["classified_intent"] != ClassifiedIntent.QUERY:
        return {}
    
    prompt = ChatPromptTemplate.from_template("""你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    当前游戏状态: 轮到玩家 {player_id} 行动。
    玩家的输入: "{input}"，
    最近的log: {combat_log}
    请根据规则和常识，以KP的口吻清晰地回答玩家的问题，并引导他做出最终决定。""")
    
    chain = prompt.pipe(llm)
    result = await chain.ainvoke({
        "player_id": state["initiative_order"][state["current_actor_index"]] if state["current_actor_index"] < len(state["initiative_order"]) else "unknown",
        "input": state["player_input"] or "",
        "combat_log": "\n".join(state["combat_log"][-7:]),
    })
    
    return {
        "combat_log": [f"[守秘人]: {result.content}"],
        "llm_output": result.content
    }

# --- Agent 5: Player Action Agent ---

async def player_action_agent(state: GraphState) -> Dict[str, Any]:
    """玩家行动智能体"""
    if IS_DEBUG:
        print("--- 调用: Player Action Agent ---")
    
    if state["classified_intent"] != ClassifiedIntent.DIRECT_ACTION:
        return {}
    
    tools = [roll_dice_tool]
    prompt = ChatPromptTemplate.from_template("""你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    重要：当你需要掷骰子时，必须使用roll_dice_tool工具，尤其是伤害，在判定命中后需要投伤害骰，也要通过roll_dice_tool工具计算。不可以跳过掷骰子，一定要用roll_dice_tool工具。
    
    现在正在进行战斗轮，玩家输入的行动需要进行合法性判断。
    当前是否为玩家的临时行动: {is_temp}, 如果是临时行动，玩家只能选择闪避或者对抗，其他的行为不允许。
    之前的上下文信息: {context_info}
    当前游戏状态: 轮到玩家 {current_actor_id} 行动。
    玩家的输入: "{input}"，
    最近的log: "{combat_log_text}",
    地图信息：{map_info},
    所有角色状态：{participants_info}
    当前玩家状态：{current_actor_info}
    
    如果行为合法，需要把玩家输入的行为造成的结果完全描述出来放进description里。比如：玩家对怪物使用了武器，需要描述武器的命中，怪物的闪避或者对抗，怪物的血量变化，怪物的状态变化，怪物的死亡，等等。！！不要忘了带上掷骰子的动作和结果。
    如果行为不合法，需要把不合法的原因放进description里。
    如果玩家的行为造成了数值变化或者location变化，需要把把更新后的对应participant对象放进result数组里。如玩家对食尸鬼造成1点伤害，那么result数组里需要有食尸鬼的更新后的对象，hp比之前少1点。
    如果需要某玩家补充信息,请把requiresPlayerInput设置为true，请把temp_player_actor设置为目标玩家的名字。
    请分析玩家输入并返回JSON blob的结构化结果：
    {{
      "isValid": "输入是否合法",
      "description": "不合法的原因，或者合法的行动信息(具体做了什么，造成了什么影响，)",
      "result": "participants中发生数据变化的对象[]",
      "requiresPlayerInput": "是否需要玩家补充信息",
      "temp_player_actor": "需要补充信息的玩家名"
    }}

    {agent_scratchpad}
    """)
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    result = await agent_executor.ainvoke({
        "context_info": "\n".join(state["previous_context"]),
        "current_actor_id": state["initiative_order"][state["current_actor_index"]] if state["current_actor_index"] < len(state["initiative_order"]) else "unknown",
        "combat_log_text": "\n".join(state["combat_log"]),
        "map_info": json.dumps(state["map"]) if state["map"] else "无地图信息",
        "participants_info": json.dumps(state["participants"]),
        "current_actor_info": json.dumps(next((p for p in state["participants"] if p["id"] == state["initiative_order"][state["current_actor_index"]]), {})),
        "input": state["player_input"] or "",
        "is_temp": state["temp_player_actor"] is not None,
    })
    
    output = result["output"]
    parsed_result = None
    
    # 处理 LLM 返回的内容，可能包含在代码块中
    if "```json" in output:
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", output)
        if json_match:
            parsed_result = json.loads(json_match.group(1))
    else:
        # 尝试直接解析JSON
        try:
            parsed_result = json.loads(output)
        except:
            parsed_result = {"isValid": False, "description": output, "result": []}

    if IS_DEBUG:
        print(f"Player Action Result: {parsed_result}")

    if not parsed_result.get("isValid", False):
        return {
            "combat_log": [f"[守秘人]: {parsed_result.get('description', '')}"],
            "is_valid_action": False,
        }

    # 更新participants
    updated_participants = state["participants"].copy()
    if "result" in parsed_result:
        for updated_participant_data in parsed_result["result"]:
            for i, participant in enumerate(updated_participants):
                if participant["id"] == updated_participant_data.get("id"):
                    updated_participants[i] = updated_participant_data
                    break

    return {
        "combat_log": [f"[守秘人]: {parsed_result.get('description', '')}"],
        "is_valid_action": True,
        "participants": updated_participants,
        "requires_player_input": parsed_result.get("requiresPlayerInput", False) if parsed_result else False,
        "temp_player_actor": parsed_result.get("temp_player_actor", None) if parsed_result else None,
    }

# --- Agent 6: Keeper Narrator Agent ---

async def keeper_narrator_agent(state: GraphState) -> Dict[str, Any]:
    """守秘人叙述智能体"""
    if IS_DEBUG:
        print("--- 调用: Keeper Narrator Agent ---", state["combat_log"])

    prompt = ChatPromptTemplate.from_template("""你是一位《克苏鲁的呼唤》的守秘人，擅长营造恐怖氛围。
      所有角色：{participants_info}，
      地图：{map_info}
      请根据以下发生的事件，生成一段生动的战斗描述。给玩家反馈，或者告诉玩家轮到他行动。不要给玩家行动建议。也不要在输出里带上[守秘人]。
      描述时要包括投骰子的命令和投骰子的结果，把它们融合进描述中。
      描述中要区分不同的玩家，不要混淆称呼。
      战斗描述要包含战斗的场景，战斗的参与者，战斗的行动，战斗的结果(如玩家对怪物造成1点伤害，怪物hp减少1点)。
      描述里要把每个角色都带到，比如大致位置等。
      发生的事: {event_data}""")
    
    chain = prompt.pipe(llm)
    result = await chain.ainvoke({
        "event_data": json.dumps("\n".join(state["combat_log"])),
        "participants_info": json.dumps(state["participants"]),
        "map_info": json.dumps(state["map"]) if state["map"] else "{}",
    })

    return {"llm_output": result.content} 