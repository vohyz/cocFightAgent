import { tool } from "@langchain/core/tools";
import { z } from "zod";

// 基础骰子工具
export interface DiceResult {
  dice: string; // 例如 "1d20", "2d6"
  rolls: number[]; // 实际掷出的数字
  total: number; // 总和
  modifier?: number; // 修正值
  finalResult: number; // 最终结果（包含修正值）
}

// 掷骰子函数
export function rollDice(diceNotation: string): DiceResult {
  // 解析骰子表示法，支持格式如 "1d20", "2d6+3", "1d100-5"
  const match = diceNotation.match(/^(\d+)d(\d+)([+-]\d+)?$/);
  if (!match) {
    throw new Error(`无效的骰子表示法: ${diceNotation}`);
  }

  const [, countStr, sidesStr, modifierStr] = match;
  const count = parseInt(countStr);
  const sides = parseInt(sidesStr);
  const modifier = modifierStr ? parseInt(modifierStr) : 0;

  if (count <= 0 || sides <= 0) {
    throw new Error(`无效的骰子参数: ${diceNotation}`);
  }

  // 掷骰子
  const rolls: number[] = [];
  for (let i = 0; i < count; i++) {
    rolls.push(Math.floor(Math.random() * sides) + 1);
  }

  const total = rolls.reduce((sum, roll) => sum + roll, 0);
  const finalResult = total + modifier;

  return {
    dice: diceNotation,
    rolls,
    total,
    modifier,
    finalResult
  };
}

// 投掷骰子工具
export const RollDTool = tool(
  async ({ diceNotation }: { diceNotation: string }) => {
    const roll = rollDice(diceNotation);
    return JSON.stringify(roll);
  },
  {
    name: "roll_dice",
    description: "在《克苏鲁的呼唤》游戏中投掷骰子进行各种判定。用于命中判定、闪避判定、伤害计算等。支持标准骰子表示法如1d20（1个20面骰）、2d6+3（2个6面骰加3点修正值）、1d100-5（1个100面骰减5点修正值）等。",
    schema: z.object({
      diceNotation: z.string().describe("骰子表示法，如'1d20'用于技能检定,'2d6+3'用于伤害计算,'1d100'用于百分骰等"),
    }),
  } as any
);