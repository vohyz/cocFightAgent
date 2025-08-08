# === src/__init__.py ===

"""
CoC战斗系统 - Python版本

这是一个使用Python LangGraph和Google Gemini构建的《克苏鲁的呼唤》(Call of Cthulhu) 战斗系统。
"""

__version__ = "1.0.0"
__author__ = "CoC Fight Team"

# 导出主要类和函数
from .types import (
    GraphState,
    Participant,
    ParticipantStatus,
    ClassifiedIntent,
    Map,
    MapZone
)

from .coc_keeper import combat_workflow

from .agents import (
    player_input_triage_agent,
    monster_ai_agent,
    rules_keeper_agent,
    keeper_narrator_agent,
    ooc_agent,
    player_action_agent
)

from .tools.dice_tools import (
    roll_dice,
    roll_dice_tool,
    DiceResult
)

__all__ = [
    # 类型
    "GraphState",
    "Participant", 
    "ParticipantStatus",
    "ClassifiedIntent",
    "Map",
    "MapZone",
    
    # 工作流
    "combat_workflow",
    
    # 智能体
    "player_input_triage_agent",
    "monster_ai_agent", 
    "rules_keeper_agent",
    "keeper_narrator_agent",
    "ooc_agent",
    "player_action_agent",
    
    # 工具
    "roll_dice",
    "roll_dice_tool",
    "DiceResult"
] 