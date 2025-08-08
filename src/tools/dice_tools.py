# === src/tools/dice_tools.py ===

import random
import re
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain.tools import tool

# 基础骰子结果类
class DiceResult(BaseModel):
    dice: str  # 例如 "1d20", "2d6"
    rolls: List[int]  # 实际掷出的数字
    total: int  # 总和
    modifier: int = 0  # 修正值
    final_result: int  # 最终结果（包含修正值）

# 掷骰子函数
def roll_dice(dice_notation: str) -> DiceResult:
    """掷骰子函数
    
    Args:
        dice_notation: 骰子表示法，如 "1d20", "2d6+3", "1d100-5"
        
    Returns:
        DiceResult: 骰子结果
        
    Raises:
        ValueError: 无效的骰子表示法
    """
    # 解析骰子表示法，支持格式如 "1d20", "2d6+3", "1d100-5"
    match = re.match(r'^(\d+)d(\d+)([+-]\d+)?$', dice_notation)
    if not match:
        raise ValueError(f"无效的骰子表示法: {dice_notation}")

    count_str, sides_str, modifier_str = match.groups()
    count = int(count_str)
    sides = int(sides_str)
    modifier = int(modifier_str) if modifier_str else 0

    if count <= 0 or sides <= 0:
        raise ValueError(f"无效的骰子参数: {dice_notation}")

    # 掷骰子
    rolls = []
    for _ in range(count):
        rolls.append(random.randint(1, sides))

    total = sum(rolls)
    final_result = total + modifier

    return DiceResult(
        dice=dice_notation,
        rolls=rolls,
        total=total,
        modifier=modifier,
        final_result=final_result
    )

# 投掷骰子工具
@tool
def roll_dice_tool(dice_notation: str) -> str:
    """在《克苏鲁的呼唤》游戏中投掷骰子进行各种判定。
    
    用于命中判定、闪避判定、伤害计算等。支持标准骰子表示法如1d20（1个20面骰）、
    2d6+3（2个6面骰加3点修正值）、1d100-5（1个100面骰减5点修正值）等。
    
    Args:
        dice_notation: 骰子表示法，如'1d20'用于技能检定,'2d6+3'用于伤害计算,'1d100'用于百分骰等
        
    Returns:
        str: JSON格式的骰子结果
    """
    try:
        result = roll_dice(dice_notation)
        return result.model_dump_json()
    except ValueError as e:
        return f"错误: {str(e)}"

# 示例用法
if __name__ == "__main__":
    # 测试骰子系统
    test_cases = ["1d20", "2d6+3", "1d100-5", "3d4"]
    
    for dice in test_cases:
        try:
            result = roll_dice(dice)
            print(f"{dice}: {result}")
        except ValueError as e:
            print(f"错误: {e}") 