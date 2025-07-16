import { StateGraph, START, END } from "@langchain/langgraph";
import { StateAnnotation } from "./state";
import { ClassifiedIntent, GraphState } from "./types";
import {
  playerInputTriageAgent,
  monsterAiAgent,
  rulesKeeperAgent,
  keeperNarratorAgent,
  oocAgent,
  playerActionAgent
} from "./agents";
import dotenv from "dotenv";
import { setGlobalDispatcher, ProxyAgent } from "undici";
// 只有在设置了代理的情况下才使用代理
if (process.env.https_proxy) {
  const dispatcher = new ProxyAgent({ uri: new URL(process.env.https_proxy).toString() });
  setGlobalDispatcher(dispatcher);
}
dotenv.config();

const IS_DEBUG = process.env.IS_DEBUG === "true";
/**
 * 战斗开始节点
 */
async function routeInput(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("=== 路由输入 ===");
  }
  if (state.roundNumber === 0) {
    return {
      combatLog: ["战斗开始！空气中弥漫着不祥的气息..."]
    };
  }
  const intentResult = await playerInputTriageAgent(state);
  
  return {
    classifiedIntent: intentResult.classifiedIntent,
  };
}
async function initializeCombat(state: GraphState): Promise<Partial<GraphState>> {
  const combatResult = await rollInitiative(state);
  return {
    ...combatResult,
    roundNumber: state.roundNumber + 1,
    currentActorIndex: -1,
    requiresPlayerInput: false,
    classifiedIntent: null,
    isValidAction: false,
    playerInput: null,
    sender: null,
    roundEnded: false,
    fightEnded: false,
  };
}

// TODO: 添加effect处理， 比如毒dot，眩晕x回合进度等
// async function effectEvent(state: GraphState): Promise<Partial<GraphState>> {
//   return {
//     ...effectResult,
//   };
// }

async function rollInitiative(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("=== 重投先攻 ===");
  }

  const activeParticipants = state.participants.filter(p => p.status === "active");

  const initiativeResults = activeParticipants.map(p => ({
    id: p.id,
    initiative: Math.floor(Math.random() * 100) + (p.stats.DEX || 50) // TODO: 需要根据角色类型和技能调整先攻
  }));

  initiativeResults.sort((a, b) => a.initiative - b.initiative);

  const initiativeOrder = initiativeResults.map(r => r.id);

  const eventMessage = "参与者们根据先攻重新确定行动顺序: " + initiativeOrder.join(", ");
  return {
    initiativeOrder,
    combatLog: [eventMessage],
  };
}

/**
 * 回合处理
 */
async function determineNextStep(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("=== 确定下一步 ===");
  }
  if(state.participants.filter(p => p.type === "investigator").every(p => p.stats.HP <= 0 || p.status !== "active")) {
    return {
      combatLog: ["所有调查员都已倒下，战斗结束！"],
      fightEnded: true,
    };
  } else if(state.participants.filter(p => p.type === "enemy").every(p => p.stats.HP <= 0 || p.status !== "active")) {
    return {
      combatLog: ["所有敌人都已倒下，调查员们获胜！"],
      fightEnded: true,
    };
  }
  const currentActorIndex = state.currentActorIndex + 1;
  if(currentActorIndex >= state.initiativeOrder.length) {
    return {
      combatLog: ["本轮结束，准备开始下一轮"],
      roundEnded: true,
      currentActorIndex: -1, // 重置为-1，这样下一轮会从0开始
    };
  }
  const currentActor = state.participants.find(p => p.id === state.initiativeOrder[currentActorIndex]);

  if (!currentActor) {
    return {
      combatLog: ["错误：找不到当前行动者"],
      roundEnded: true,
    };
  }
  
  if(currentActor.type === "investigator") {
    return {
      currentActorIndex,
      normalCircleEnded: true,
      requiresPlayerInput: true,
      combatLog: [`轮到 ${currentActor.name} 行动`]
    }
  }
  return {
    currentActorIndex,
    requiresPlayerInput: false,
    combatLog: [`轮到 ${currentActor.name} 行动`]
  };
}

async function prepareForNextInput(state: GraphState): Promise<Partial<GraphState>> {
  const keeperNarratorResult = await keeperNarratorAgent(state);
  return {
    ...keeperNarratorResult,
  };
}
async function combatEnd(state: GraphState): Promise<Partial<GraphState>> {
  const keeperNarratorResult = await keeperNarratorAgent(state);
  return {
    ...keeperNarratorResult,
  };
}

// ==================== 构建工作流图 ====================

const workflow = new StateGraph(StateAnnotation);

// 添加节点
workflow
  .addNode("route_input", routeInput)
  .addNode("handle_ooc", oocAgent)
  .addNode("handle_query", rulesKeeperAgent)
  .addNode("direct_action", playerActionAgent)
  .addNode("initialize_combat", initializeCombat)
  .addNode("determine_next_step", determineNextStep)
  .addNode("prepare_for_next_input", prepareForNextInput)
  .addNode("combat_end", combatEnd)
  .addNode("monster_ai", monsterAiAgent)
  .addEdge(START, "route_input")
  .addEdge("handle_ooc", END)
  .addEdge("handle_query", END)
  .addEdge("combat_end", END)
  .addEdge("prepare_for_next_input", END)
  .addConditionalEdges("route_input", (state) => {
    if (state.roundNumber === 0) {
      return "initialize_combat";
    }
    if (state.classifiedIntent === ClassifiedIntent.DirectAction) {
      return "direct_action";
    } else if (state.classifiedIntent === ClassifiedIntent.Query) {
      return "handle_query";
    } 
    return "handle_ooc";
  }, {
    "direct_action": "direct_action",
    "handle_query": "handle_query",
    "handle_ooc": "handle_ooc",
    "initialize_combat": "initialize_combat"
  })
  .addConditionalEdges("direct_action", (state) => {
    if(state.isValidAction) {
      return "determine_next_step";
    }
    return "prepare_for_next_input";
  }, {
    "prepare_for_next_input": "prepare_for_next_input",
    "determine_next_step": "determine_next_step"
  })
  .addConditionalEdges("determine_next_step", (state) => {
    if(state.requiresPlayerInput) {
      return "prepare_for_next_input";
    }
    if(state.roundEnded) {
      return "initialize_combat";
    }
    if(state.fightEnded) {
      return "combat_end";
    }
    return "monster_ai";
  }, {
    "prepare_for_next_input": "prepare_for_next_input",
    "initialize_combat": "initialize_combat",
    "combat_end": "combat_end",
    "monster_ai": "monster_ai"
  })
  .addEdge("monster_ai", "determine_next_step")
  .addEdge("initialize_combat", "determine_next_step")

// ==================== 导出工作流 ====================

export const combatWorkflow = workflow.compile();
const mermaidSyntax = combatWorkflow.getGraph().drawMermaid();
console.log(mermaidSyntax);
