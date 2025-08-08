# === demo.py ===

"""
CoC战斗系统演示脚本

这是一个简化的演示脚本，可以直接运行来测试系统功能。
"""

import asyncio
import os
from dotenv import load_dotenv
from src.types import GraphState, Participant, ParticipantStatus

# 加载环境变量
load_dotenv()

async def simple_demo():
    """简单演示"""
    print("🎲 CoC战斗系统 - Python版本演示")
    print("=" * 50)
    
    # 检查API密钥
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ 未找到GOOGLE_API_KEY环境变量")
        print("请确保在.env文件中设置了正确的API密钥")
        return
    
    try:
        # 测试骰子系统
        print("\n🎲 测试骰子系统...")
        from src.tools.dice_tools import roll_dice
        
        test_dice = ["1d20", "2d6+3", "1d100-5"]
        for dice in test_dice:
            result = roll_dice(dice)
            print(f"✅ {dice}: {result}")
        
        # 测试智能体
        print("\n🤖 测试智能体...")
        from src.agents import player_input_triage_agent
        
        test_participant = Participant(
            id="demo_player",
            name="演示玩家",
            type="investigator",
            stats={"HP": 10, "DEX": 50},
            status=ParticipantStatus.ACTIVE,
            effects=[],
            items=[]
        )
        
        test_state = GraphState(
            participants=[test_participant],
            initiative_order=["demo_player"],
            current_actor_index=0,
            player_input="我使用手枪攻击"
        )
        
        result = await player_input_triage_agent(test_state)
        print(f"✅ 意图分类: {result}")
        
        print("\n🎉 演示完成！系统运行正常。")
        
    except Exception as e:
        print(f"❌ 演示出错: {e}")
        print("请检查依赖安装和API配置")

if __name__ == "__main__":
    asyncio.run(simple_demo()) 