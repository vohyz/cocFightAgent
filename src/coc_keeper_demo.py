# === src/coc_keeper_demo.py ===

import asyncio
from typing import cast
try:
    from .types import GraphState, Participant, ParticipantStatus, Map
    from .coc_keeper import combat_workflow
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.types import GraphState, Participant, ParticipantStatus, Map
    from src.coc_keeper import combat_workflow

# ==================== 预设角色数据 ====================

def create_investigator1() -> Participant:
    """创建调查员1"""
    return {
        "id": "艾米莉亚·克拉克",
        "name": "艾米莉亚·克拉克",
        "type": "investigator",
        "stats": {
            "HP": 12,
            "max_HP": 12,
            "SAN": 65,
            "max_SAN": 65,
            "DEX": 30,
            "STR": 30,
            "CON": 40,
            "INT": 50,
            "POW": 50,
            "APP": 65,
            "EDU": 75,
            "SIZ": 55,
            "fighting": 45,
            "firearms": 60,
            "dodge": 35,
            "stealth": 40,
            "spot_hidden": 50,
            "listen": 45,
            "psychology": 55,
            "first_aid": 40
        },
        "status": ParticipantStatus.ACTIVE,
        "effects": [],
        "items": ["手枪", "医疗包", "手电筒"]
    }

def create_investigator2() -> Participant:
    """创建调查员2"""
    return {
        "id": "杰克·汤普森",
        "name": "杰克·汤普森",
        "type": "investigator",
        "stats": {
            "HP": 14,
            "max_HP": 14,
            "SAN": 60,
            "max_SAN": 60,
            "DEX": 65,
            "STR": 70,
            "CON": 65,
            "INT": 70,
            "POW": 65,
            "APP": 60,
            "EDU": 70,
            "SIZ": 65,
            "fighting": 60,
            "firearms": 45,
            "dodge": 30,
            "stealth": 35,
            "spot_hidden": 40,
            "listen": 35,
            "psychology": 45,
            "first_aid": 50
        },
        "status": ParticipantStatus.ACTIVE,
        "effects": [],
        "items": ["猎刀", "绳索", "打火机"]
    }

def create_ghoul1() -> Participant:
    """创建食尸鬼1"""
    return {
        "id": "ghoul_1",
        "name": "食尸鬼A",
        "type": "enemy",
        "stats": {
            "HP": 13,
            "max_HP": 13,
            "SAN": 0,
            "max_SAN": 0,
            "DEX": 85,
            "STR": 80,
            "CON": 80,
            "INT": 80,
            "POW": 80,
            "APP": 20,
            "EDU": 30,
            "SIZ": 60,
            "fighting": 100,
            "firearms": 0,
            "dodge": 25,
            "stealth": 50,
            "spot_hidden": 45,
            "listen": 40,
            "psychology": 0,
            "first_aid": 0
        },
        "status": ParticipantStatus.ACTIVE,
        "effects": [],
        "items": []
    }

def create_ghoul2() -> Participant:
    """创建食尸鬼2"""
    return {
        "id": "ghoul_2",
        "name": "食尸鬼B",
        "type": "enemy",
        "stats": {
            "HP": 11,
            "max_HP": 11,
            "SAN": 0,
            "max_SAN": 0,
            "DEX": 90,
            "STR": 55,
            "CON": 65,
            "INT": 35,
            "POW": 45,
            "APP": 15,
            "EDU": 25,
            "SIZ": 55,
            "fighting": 50,
            "firearms": 0,
            "dodge": 30,
            "stealth": 55,
            "spot_hidden": 40,
            "listen": 35,
            "psychology": 0,
            "first_aid": 0
        },
        "status": ParticipantStatus.ACTIVE,
        "effects": [],
        "items": []
    }

# ==================== 命令行界面 ====================

class CombatCLI:
    """战斗命令行界面"""
    
    def __init__(self):
        default_map: Map = {
            "name": "禁忌图书馆",
            "zones": {
                "entrance": {
                    "description": "图书馆的入口，一扇巨大的橡木门敞开着。",
                    "adjacent_zones": ["main_hall"],
                    "properties": ["has_light"]
                }
            }
        }
        
        self.state: GraphState = {
            "participants": [create_investigator1(), create_ghoul1()],
            "map": default_map,
            "fight_ended": False,
            "round_ended": False,
            "round_number": 0,
            "current_actor_index": 0,
            "temp_player_actor": None,
            "combat_log": [],
            "previous_context": [],
            "player_input": None,
            "is_valid_action": False,
            "classified_intent": None,
            "requires_player_input": False,
            "llm_output": "",
            "initiative_order": []
        }
        self.workflow = combat_workflow
        self.messages = []

    async def start(self):
        """开始战斗演示"""
        print("🎲 欢迎来到《克苏鲁的呼唤》战斗系统！")
        print("=" * 50)
        
        await self.pause()
        await self.run_combat()

    async def pause(self):
        """暂停等待用户输入"""
        input("按回车键继续...")

    async def get_user_input(self, prompt: str) -> str:
        """获取用户输入"""
        return input(prompt).strip()

    async def run_combat(self):
        """运行战斗"""
        config = {
            "configurable": {
                "thread_id": "combat_demo"
            }
        }

        current_state = self.state
        step_count = 0
        max_steps = 50  # 防止无限循环

        while step_count < max_steps and not current_state["fight_ended"]:
            step_count += 1
            
            # 处理玩家输入
            player_input = await self.handle_player_input(current_state)
            current_actor_index = current_state["current_actor_index"]
            initiative_order = current_state["initiative_order"]
            temp_player_actor = current_state["temp_player_actor"]
            current_actor_name = initiative_order[current_actor_index] if current_actor_index < len(initiative_order) else 'unknown'
            if temp_player_actor:
                current_actor_name = temp_player_actor
            player_message = f"{current_actor_name}: {player_input}"

            self.messages.append({
                "role": "user",
                "content": player_message
            })

            # 更新状态
            previous_messages = [msg["content"] for msg in self.messages[-4:]]
            
            current_state = cast(GraphState, {
                "participants": current_state["participants"],
                "map": current_state["map"],
                "fight_ended": current_state["fight_ended"],
                "round_ended": current_state["round_ended"],
                "round_number": current_state["round_number"],
                "current_actor_index": current_state["current_actor_index"],
                "temp_player_actor": temp_player_actor,
                "combat_log": [],
                "previous_context": previous_messages,
                "player_input": player_message if player_input else None,
                "is_valid_action": False,
                "classified_intent": None,
                "requires_player_input": False,
                "llm_output": "",
                "initiative_order": current_state["initiative_order"],
            })
            
            # 运行工作流
            result = await self.workflow.ainvoke(current_state, config)
            current_state = cast(GraphState, result)
            
            self.messages.append({
                "role": "assistant",
                "content": current_state["llm_output"]
            })
            
            print(current_state["llm_output"])
            
            # 短暂暂停
            await asyncio.sleep(1)
        
        if step_count >= max_steps:
            print("\n⚠️ 达到最大步数限制，战斗强制结束")

    async def handle_player_input(self, state: GraphState) -> str:
        """处理玩家输入"""
        if not state["requires_player_input"]:
            return ""
        
        user_input = await self.get_user_input("你的输入: ")
        return user_input

# ==================== 主函数 ====================

async def main():
    """主函数"""
    cli = CombatCLI()
    await cli.start()
    
# 如果直接运行此文件
if __name__ == "__main__":
    asyncio.run(main())

# 导出类和函数
__all__ = ["CombatCLI", "main", "create_investigator1", "create_investigator2", "create_ghoul1", "create_ghoul2"] 