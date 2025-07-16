// === src/types.ts ===

import { MessageContent, MessageFieldWithRole } from "@langchain/core/messages";

// 定义参与者的状态
export type ParticipantStatus = "unconscious" | "dead" | "insane" | "fled" | "active";

// 定义战斗中的一个参与者（调查员或敌人）
export interface Participant {
  id: string;
  type: "investigator" | "enemy";
  name: string;
  stats: Record<string, any>; // e.g., { HP: 12, SAN: 50, DEX: 60, Firearms: 45 }
  status: ParticipantStatus;
  effects: string[]; // e.g., ["prone", "reloading"]
  items: string[];
}

// Triage Agent分类后的意图
export enum ClassifiedIntent {
  DirectAction = "direct_action",
  Query = "query",
  OOC = "ooc",
  FuzzyIntent = "fuzzy_intent"
}

// LangGraph 的核心 State 定义
export interface GraphState {
  // 之前的上下文信息
  previousContext: string[];
  roundEnded: boolean; // 本轮是否结束
  fightEnded: boolean; // 战斗是否结束
  sender: string | null; // 上一个节点

  participants: Participant[];
  initiativeOrder: string[]; // 本轮的行动顺序，是角色ID列表，例如 ["ghoul_1", "player_Alex", "cultist_1"]
  roundNumber: number; // 战斗轮数，0表示战斗尚未开始
  currentActorIndex: number; // 当前行动者在 turn_order 中的索引
  map: {
    name: string;
    zones: {
      [key: string]: {
        description: string;
        adjacent_zones: string[];
        properties: string[];
      }
    }
  }
  // 用于叙事的战斗日志
  combatLog: string[];
  // 玩家交互相关的状态
  playerInput: string | null;
  isValidAction: boolean;
  classifiedIntent: ClassifiedIntent | null;
  requiresPlayerInput: boolean;
  normalCircleEnded: boolean;
  // 最终结果
  llmOutput: string;
}