# === src/tools/__init__.py ===

"""
工具模块

包含骰子系统等工具函数。
"""

from .dice_tools import roll_dice, roll_dice_tool, DiceResult

__all__ = ["roll_dice", "roll_dice_tool", "DiceResult"] 