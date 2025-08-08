# === src/types.py ===

from enum import Enum
from typing import List, Dict, Optional, TypedDict, Literal

# 定义参与者的状态
class ParticipantStatus(str, Enum):
    UNCONSCIOUS = "unconscious"
    DEAD = "dead"
    INSANE = "insane"
    FLED = "fled"
    ACTIVE = "active"

# 定义战斗中的一个参与者（调查员或敌人）
class ParticipantStats(TypedDict, total=False):
    HP: int
    max_HP: int
    SAN: int
    max_SAN: int
    DEX: int
    STR: int
    CON: int
    INT: int
    POW: int
    APP: int
    EDU: int
    SIZ: int
    fighting: int
    firearms: int
    dodge: int
    stealth: int
    spot_hidden: int
    listen: int
    psychology: int
    first_aid: int

class Participant(TypedDict):
    id: str
    type: Literal["investigator", "enemy"]
    name: str
    stats: ParticipantStats
    status: ParticipantStatus
    effects: List[str]
    items: List[str]

# Triage Agent分类后的意图
class ClassifiedIntent(str, Enum):
    DIRECT_ACTION = "direct_action"
    QUERY = "query"
    OOC = "ooc"
    FUZZY_INTENT = "fuzzy_intent"

# 地图区域定义
class MapZone(TypedDict):
    description: str
    adjacent_zones: List[str]
    properties: List[str]

class Map(TypedDict):
    name: str
    zones: Dict[str, MapZone]

# LangGraph 的核心 State 定义
class GraphState(TypedDict, total=False):
    # 之前的上下文信息
    previous_context: List[str]
    round_ended: bool  # 本轮是否结束
    fight_ended: bool  # 战斗是否结束

    participants: List[Participant]
    initiative_order: List[str]  # 本轮的行动顺序，是角色ID列表
    round_number: int  # 战斗轮数，0表示战斗尚未开始
    current_actor_index: int  # 当前行动者在 turn_order 中的索引
    temp_player_actor: str | None  # 临时行动者（玩家）的名字
    map: Map
    # 用于叙事的战斗日志
    combat_log: List[str]
    # 玩家交互相关的状态
    player_input: Optional[str]
    is_valid_action: bool
    classified_intent: Optional[ClassifiedIntent]
    requires_player_input: bool
    # 最终结果
    llm_output: str 