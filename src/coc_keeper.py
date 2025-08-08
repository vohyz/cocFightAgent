# === src/coc_keeper.py ===

import os
import random
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.types import ClassifiedIntent, GraphState, ParticipantStatus

from .agents import (
    player_input_triage_agent,
    monster_ai_agent,
    rules_keeper_agent,
    keeper_narrator_agent,
    ooc_agent,
    player_action_agent
)

# 加载环境变量
load_dotenv()

IS_DEBUG = os.getenv("IS_DEBUG", "false").lower() == "true"

# ==================== 战斗流程节点 ====================

async def route_input(state: GraphState) -> GraphState:
    """战斗开始节点"""
    if IS_DEBUG:
        print("=== 路由输入 ===")
    
    if state["round_number"] == 0:
        state["combat_log"].append("战斗开始！空气中弥漫着不祥的气息...")
    
    # 如果有玩家输入，进行意图分类
    if state["player_input"]:
        triage_result = await player_input_triage_agent(state)
        state["classified_intent"] = triage_result.get("classified_intent")
    
    return state

def initialize_combat(state: GraphState) -> GraphState:
    """初始化战斗"""
    combat_result = roll_initiative(state)
    
    state["round_number"] += 1
    state["current_actor_index"] = -1
    state["requires_player_input"] = False
    state["classified_intent"] = None
    state["is_valid_action"] = False
    state["player_input"] = None
    state["round_ended"] = False
    state["fight_ended"] = False
    
    # 合并战斗结果
    if "initiative_order" in combat_result:
        state["initiative_order"] = combat_result["initiative_order"]
    if "combat_log" in combat_result:
        state["combat_log"].extend(combat_result["combat_log"])
    
    return state

def roll_initiative(state: GraphState) -> Dict[str, Any]:
    """重投先攻"""
    if IS_DEBUG:
        print("=== 重投先攻 ===")

    active_participants = [p for p in state["participants"] if p["status"] == ParticipantStatus.ACTIVE]

    initiative_results = []
    for participant in active_participants:
        initiative = random.randint(1, 100) + (100 - (participant["stats"].get("DEX", 50)))
        initiative_results.append({
            "id": participant["id"],
            "initiative": initiative
        })

    # 按先攻值排序（数值越小越先行动）
    initiative_results.sort(key=lambda x: x["initiative"])
    initiative_order = [r["id"] for r in initiative_results]

    event_message = f"参与者们根据先攻重新确定行动顺序: {', '.join(initiative_order)}"
    
    return {
        "initiative_order": initiative_order,
        "combat_log": [event_message],
    }

def determine_next_step(state: GraphState) -> GraphState:
    """回合处理"""
    if IS_DEBUG:
        print("=== 确定下一步 ===")
    
    # 检查战斗是否结束
    investigators = [p for p in state["participants"] if p["type"] == "investigator"]
    enemies = [p for p in state["participants"] if p["type"] == "enemy"]
    
    if all(p["stats"].get("HP", 0) <= 0 or p["status"] != ParticipantStatus.ACTIVE for p in investigators):
        state["combat_log"].append("所有调查员都已倒下，战斗结束！")
        state["fight_ended"] = True
        return state
    elif all(p["stats"].get("HP", 0) <= 0 or p["status"] != ParticipantStatus.ACTIVE for p in enemies):
        state["combat_log"].append("所有敌人都已倒下，调查员们获胜！")
        state["fight_ended"] = True
        return state
    
    current_actor_index = state["current_actor_index"]
    if state["temp_player_actor"] is None:
        current_actor_index = state["current_actor_index"] + 1
        # 确定下一个行动者
        if current_actor_index >= len(state["initiative_order"]):
            state["combat_log"].append("本轮结束，准备开始下一轮")
            state["round_ended"] = True
            state["current_actor_index"] = -1  # 重置为-1，这样下一轮会从0开始
            return state
    
    current_actor = next((p for p in state["participants"] if p["id"] == state["initiative_order"][current_actor_index]), None)
    
    if not current_actor:
        state["combat_log"].append("错误：找不到当前行动者")
        state["round_ended"] = True
        return state
    
    state["current_actor_index"] = current_actor_index
    
    if current_actor["type"] == "investigator":
        state["requires_player_input"] = True
        state["combat_log"].append(f"轮到 {current_actor['name']} 行动")
    else:
        state["requires_player_input"] = False
        state["combat_log"].append(f"轮到 {current_actor['name']} 行动")
    
    return state

async def prepare_for_next_input(state: GraphState) -> GraphState:
    """准备下一个输入"""
    keeper_narrator_result = await keeper_narrator_agent(state)
    if "llm_output" in keeper_narrator_result:
        state["llm_output"] = keeper_narrator_result["llm_output"]
    return state

async def combat_end(state: GraphState) -> GraphState:
    """战斗结束"""
    keeper_narrator_result = await keeper_narrator_agent(state)
    if "llm_output" in keeper_narrator_result:
        state["llm_output"] = keeper_narrator_result["llm_output"]
    return state

# ==================== 智能体节点 ====================

async def handle_ooc(state: GraphState) -> GraphState:
    """处理OOC对话"""
    ooc_result = await ooc_agent(state)
    
    if "combat_log" in ooc_result:
        state["combat_log"].extend(ooc_result["combat_log"])
    if "llm_output" in ooc_result:
        state["llm_output"] = ooc_result["llm_output"]
    
    return state

async def handle_query(state: GraphState) -> GraphState:
    """处理规则查询"""
    rules_result = await rules_keeper_agent(state)
    
    if "combat_log" in rules_result:
        state["combat_log"].extend(rules_result["combat_log"])
    if "llm_output" in rules_result:
        state["llm_output"] = rules_result["llm_output"]
    
    return state

async def direct_action(state: GraphState) -> GraphState:
    """处理直接行动"""
    action_result = await player_action_agent(state)
    
    if "combat_log" in action_result:
        state["combat_log"].extend(action_result["combat_log"])
    if "is_valid_action" in action_result:
        state["is_valid_action"] = action_result["is_valid_action"]
    if "participants" in action_result:
        state["participants"] = action_result["participants"]
    if "temp_player_actor" in action_result:
        state["temp_player_actor"] = action_result["temp_player_actor"]
    return state

async def monster_ai(state: GraphState) -> GraphState:
    """怪物AI"""
    monster_result = await monster_ai_agent(state)
    
    if "combat_log" in monster_result:
        state["combat_log"].extend(monster_result["combat_log"])
    if "participants" in monster_result:
        state["participants"] = monster_result["participants"]
    if "requires_player_input" in monster_result:
        state["requires_player_input"] = monster_result["requires_player_input"]
    if "temp_player_actor" in monster_result:
        state["temp_player_actor"] = monster_result["temp_player_actor"]
    return state

# ==================== 条件函数 ====================

def route_input_condition(state: GraphState) -> str:
    """路由输入条件"""
    if state["round_number"] == 0:
        return "initialize_combat"
    if state["classified_intent"] == ClassifiedIntent.DIRECT_ACTION:
        return "direct_action"
    elif state["classified_intent"] == ClassifiedIntent.QUERY:
        return "handle_query"
    return "handle_ooc"

def direct_action_condition(state: GraphState) -> str:
    """直接行动条件"""
    if state["is_valid_action"]:
        if state["requires_player_input"]:
            return "prepare_for_next_input"
        return "determine_next_step"
    return "prepare_for_next_input"

def determine_next_step_condition(state: GraphState) -> str:
    """确定下一步条件"""
    if state["requires_player_input"]:
        return "prepare_for_next_input"
    if state["round_ended"]:
        return "initialize_combat"
    if state["fight_ended"]:
        return "combat_end"
    return "monster_ai"

def monster_ai_condition(state: GraphState) -> str:
    """怪物AI条件"""
    if state["requires_player_input"]:
        return "prepare_for_next_input"
    return "determine_next_step"

# ==================== 构建工作流图 ====================

def create_combat_workflow() -> StateGraph:
    """创建战斗工作流"""
    workflow = StateGraph(GraphState)
    
    # 添加节点
    workflow.add_node("route_input", route_input)
    workflow.add_node("handle_ooc", handle_ooc)
    workflow.add_node("handle_query", handle_query)
    workflow.add_node("direct_action", direct_action)
    workflow.add_node("initialize_combat", initialize_combat)
    workflow.add_node("determine_next_step", determine_next_step)
    workflow.add_node("prepare_for_next_input", prepare_for_next_input)
    workflow.add_node("combat_end", combat_end)
    workflow.add_node("monster_ai", monster_ai)
    
    # 添加边
    workflow.add_edge(START, "route_input")
    workflow.add_edge("handle_ooc", END)
    workflow.add_edge("handle_query", END)
    workflow.add_edge("combat_end", END)
    workflow.add_edge("prepare_for_next_input", END)
    
    # 添加条件边
    workflow.add_conditional_edges(
        "route_input",
        route_input_condition,
        {
            "direct_action": "direct_action",
            "handle_query": "handle_query",
            "handle_ooc": "handle_ooc",
            "initialize_combat": "initialize_combat"
        }
    )
    
    workflow.add_conditional_edges(
        "direct_action",
        direct_action_condition,
        {
            "prepare_for_next_input": "prepare_for_next_input",
            "determine_next_step": "determine_next_step"
        }
    )
    
    workflow.add_conditional_edges(
        "determine_next_step",
        determine_next_step_condition,
        {
            "prepare_for_next_input": "prepare_for_next_input",
            "initialize_combat": "initialize_combat",
            "combat_end": "combat_end",
            "monster_ai": "monster_ai"
        }
    )
    
    workflow.add_conditional_edges(
        "monster_ai",
        monster_ai_condition,
        {
            "determine_next_step": "determine_next_step",
            "prepare_for_next_input": "prepare_for_next_input"
        }
    )
    
    workflow.add_edge("initialize_combat", "determine_next_step")
    
    return workflow

# ==================== 导出工作流 ====================

combat_workflow = create_combat_workflow().compile(checkpointer=MemorySaver()) 