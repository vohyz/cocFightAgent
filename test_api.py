# === test_api.py ===

import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.dice_tools import roll_dice_tool, roll_dice

# 加载环境变量
load_dotenv()

async def test_gemini_connection():
    """测试Gemini API连接"""
    print("🔍 测试Gemini API连接...")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1,
        )
        
        response = await llm.ainvoke("你好，请简单回复'连接成功'")
        print(f"✅ Gemini API连接成功: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API连接失败: {e}")
        return False

def test_dice_system():
    """测试骰子系统"""
    print("\n🎲 测试骰子系统...")
    
    test_cases = [
        "1d20",
        "2d6+3", 
        "1d100-5",
        "3d4",
        "1d10"
    ]
    
    for dice in test_cases:
        try:
            result = roll_dice(dice)
            print(f"✅ {dice}: {result}")
        except Exception as e:
            print(f"❌ {dice}: 错误 - {e}")

async def test_dice_tool():
    """测试骰子工具"""
    print("\n🔧 测试骰子工具...")
    
    try:
        result = await roll_dice_tool.ainvoke({"dice_notation": "2d6+3"})
        print(f"✅ 骰子工具测试成功: {result}")
        return True
    except Exception as e:
        print(f"❌ 骰子工具测试失败: {e}")
        return False

async def test_agents():
    """测试智能体系统"""
    print("\n🤖 测试智能体系统...")
    
    try:
        from classes import GraphState, Participant, ParticipantStatus
        from src.agents import player_input_triage_agent
        
        # 创建测试状态
        test_participant = Participant(
            id="test_player",
            name="测试玩家",
            type="investigator",
            stats={"HP": 10, "DEX": 50},
            status=ParticipantStatus.ACTIVE,
            effects=[],
            items=[]
        )
        
        test_state = GraphState(
            participants=[test_participant],
            initiative_order=["test_player"],
            current_actor_index=0,
            player_input="我使用手枪攻击"
        )
        
        # 测试意图分类
        result = player_input_triage_agent(test_state)
        print(f"✅ 意图分类测试成功: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 智能体测试失败: {e}")
        return False

async def test_workflow():
    """测试工作流"""
    print("\n🔄 测试工作流...")
    
    try:
        from src.coc_keeper import combat_workflow
        from classes import GraphState, Participant, ParticipantStatus
        
        # 创建测试状态
        test_participant = Participant(
            id="test_player",
            name="测试玩家",
            type="investigator",
            stats={"HP": 10, "DEX": 50},
            status=ParticipantStatus.ACTIVE,
            effects=[],
            items=[]
        )
        
        test_state = GraphState(
            participants=[test_participant],
            initiative_order=["test_player"],
            current_actor_index=0,
            player_input="我使用手枪攻击"
        )
        
        config = {
            "configurable": {
                "thread_id": "test_workflow"
            }
        }
        
        # 运行工作流
        result = await combat_workflow.ainvoke(test_state, config)
        print(f"✅ 工作流测试成功: 状态更新完成")
        return True
        
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 开始API和系统测试...")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ 未找到GOOGLE_API_KEY环境变量")
        print("请确保在.env文件中设置了正确的API密钥")
        return
    
    # 运行测试
    tests = [
        ("Gemini API连接", test_gemini_connection),
        ("骰子系统", lambda: test_dice_system()),
        ("骰子工具", test_dice_tool),
        ("智能体系统", test_agents),
        ("工作流", test_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出错: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
    else:
        print("⚠️ 部分测试失败，请检查配置和依赖。")

if __name__ == "__main__":
    asyncio.run(main()) 