// === src/agents.ts ===

import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { z } from "zod";
import { GraphState, ClassifiedIntent, Participant } from "./types";
import { RollDTool } from "./tools/dice-tools";
import { AgentExecutor, createToolCallingAgent } from "langchain/agents";

import dotenv from "dotenv";
dotenv.config();

const IS_DEBUG = process.env.IS_DEBUG === "true";
const llm = new ChatGoogleGenerativeAI({
  model: process.env.GEMINI_MODEL || "gemini-2.0-flash",
  apiKey: process.env.GOOGLE_API_KEY,
  temperature: 0.1,
  maxRetries: 3,
  maxConcurrency: 1,
  streaming: false,
});

// --- Agent 1: Player Input Triage Agent ---

// TODO：如果玩家一句话里有多种不同意图，需要进行多意图分类
const triageSchema = z.object({
  intent: z.enum(["direct_action", "query", "ooc", "fuzzy_intent"]).describe("玩家输入的意图分类"),
});

export async function playerInputTriageAgent(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("--- 调用: Player Input Triage Agent ---");
  }
  const triageLlm = llm.withStructuredOutput(triageSchema) as unknown as any;
  const prompt = ChatPromptTemplate.fromMessages([
    ["system", "你是一个游戏助手，负责将玩家在《克苏鲁的呼唤》游戏中的输入进行意图分类。根据玩家输入和当前上下文进行判断"],
    ["human", `当前场景: 战斗在第{roundNumber}轮，轮到玩家 {playerId} 行动。
    玩家输入: "{input}"
    请对以上输入进行分类和解析。
    如果玩家输入是关于他的行动的，比如，"我使用武器攻击"，“闪避”，“对抗”，请返回 "direct_action"。
    如果玩家输入是关于规则和状态的，请返回 "query"。
    如果玩家输入是关于OOC的，请返回 "ooc"。
    如果玩家输入是模糊的，请返回 "fuzzy_intent"。`],
  ]);

  const chain = prompt.pipe(triageLlm);
  const result = await chain.invoke({
    roundNumber: state.roundNumber,
    playerId: state.initiativeOrder[state.currentActorIndex],
    input: state.playerInput,
  }) as unknown as { intent: ClassifiedIntent };

  return { classifiedIntent: result.intent as ClassifiedIntent };
}


// --- Agent 2: Monster AI Agent ---

export async function monsterAiAgent(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("--- 调用: Monster AI Agent ---");
  }
  
  const contextInfo = state.previousContext.join("\n");
  const currentActorId = state.initiativeOrder[state.currentActorIndex] || "unknown";
  const combatLogText = state.combatLog.join("\n");
  const mapInfo = state.map ? JSON.stringify(state.map) : "无地图信息";
  const participantsInfo = JSON.stringify(state.participants);
  const currentActorInfo = JSON.stringify(state.participants.find(p => p.id === state.initiativeOrder[state.currentActorIndex]));
  
  const prompt = ChatPromptTemplate.fromTemplate(`你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    重要：当你需要掷骰子时，必须使用roll_dice工具，尤其是伤害，在判定命中后需要投伤害骰，通过roll_dice工具计算。不可以跳过掷骰子，一定要用roll_dice工具。
    现在正在进行战斗轮，你正在扮演怪物。
    之前的上下文信息: {contextInfo}
    当前游戏状态: 轮到怪物 {currentActorId} 行动。
    最近的log: "{combatLogText}",
    地图信息：{mapInfo},
    所有角色状态：{participantsInfo}
    你的状态：{currentActorInfo}
    
    决定你控制的怪物的行动，并把行动造成的结果完全描述出来放进description里,如果需要玩家补充信息，请也放进description里（如选择闪避或者对抗）。
    比如：食尸鬼使用了爪击，需要描述命中，对方的闪避或者对抗，对方的血量变化，对方的状态变化，对方的死亡，等等。！！不要忘了带上掷骰子的动作和结果。
    如果行动造成了数值变化或者location变化，需要把把更新后的对应participant对象放进result数组里。如玩家对食尸鬼造成1点伤害，那么result数组里需要有食尸鬼的更新后的对象，hp比之前少1点。
    如果需要玩家补充信息,requiresPlayerInput = true。
    返回JSON blob的结构化结果：
    {{
      description: 行动信息(具体做了什么，造成了什么影响，),
      result: participants中发生数据变化的对象[],
      requiresPlayerInput: 是否需要玩家补充信息,
  }}
    agent_scratchpad: {agent_scratchpad}
    `);
  const tools = [RollDTool];

  const agent = await createToolCallingAgent({
    llm,
    tools,
    prompt,
  });

  const agentExecutor = new AgentExecutor({
    agent,
    tools,
  });

  const {output} = await agentExecutor.invoke({
    contextInfo,
    currentActorId,
    combatLogText,
    mapInfo,
    participantsInfo,
    currentActorInfo
  });
  
  let result = null;
  // 处理 LLM 返回的内容，可能包含在代码块中
  if (output.includes('```json')) {
    // 提取 JSON 代码块中的内容
    const jsonMatch = output.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      result = JSON.parse(jsonMatch[1]);
    }
  } 

  const updatedParticipants = state.participants.map(participant => {
    const updatedParticipant = result.result.find((p: Participant) => p.id === participant.id);
    return updatedParticipant ? updatedParticipant : participant;
  });
  return { 
    combatLog: [`[守秘人]: ${result.description}`],
    participants: updatedParticipants,
    requiresPlayerInput: result.requiresPlayerInput,
  };
}
// --- Agent 3: OOC Agent ---

export async function oocAgent(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("--- 调用: ooc Agent ---");
  }
  if(state.classifiedIntent !== ClassifiedIntent.OOC) return {};
  
  const prompt = ChatPromptTemplate.fromTemplate(`你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    当前游戏状态: 轮到玩家 {playerId} 行动。
    玩家的输入: "{input}"，
    最近的log: {combatLog}
    请根据规则和常识，以KP的口吻清晰地回答玩家的问题，并引导他做出最终决定。注意，玩家可能会发表一些ooc，请合理的回复ooc即可`);
  
  const chain = prompt.pipe(llm);
  const result = await chain.invoke({
      playerId: state.initiativeOrder[state.currentActorIndex],
      input: state.playerInput,
      combatLog: state.combatLog.slice(-5).join("\n"),
  });
  return { combatLog: [`[守秘人]: ${result.content}`], llmOutput: result.content as string };
}

// --- Agent 4: Rules Keeper Agent ---

export async function rulesKeeperAgent(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("--- 调用: Rules Keeper Agent ---");
  }
  if(state.classifiedIntent !== ClassifiedIntent.Query) return {};
  
  const prompt = ChatPromptTemplate.fromTemplate(`你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
  当前游戏状态: 轮到玩家 {playerId} 行动。
  玩家的输入: "{input}"，
  最近的log: {combatLog}
  请根据规则和常识，以KP的口吻清晰地回答玩家的问题，并引导他做出最终决定。`);
  
  const chain = prompt.pipe(llm);
  const result = await chain.invoke({
      playerId: state.initiativeOrder[state.currentActorIndex],
      input: state.playerInput,
      combatLog: state.combatLog.slice(-7).join("\n"),
  });
  return { combatLog: [`[守秘人]: ${result.content}`], llmOutput: result.content as string };
}

// --- Agent 5: 玩家行动 ---
export async function playerActionAgent(state: GraphState): Promise<Partial<GraphState>> {
  if (IS_DEBUG) {
    console.log("--- 调用: Player Action Agent ---");
  }
  if(state.classifiedIntent !== ClassifiedIntent.DirectAction) return {};
  const tools = [RollDTool];
  const prompt = ChatPromptTemplate.fromTemplate(`你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
    重要：当你需要掷骰子时，必须使用roll_dice工具，尤其是伤害，在判定命中后需要投伤害骰，也要通过roll_dice工具计算。不可以跳过掷骰子，一定要用roll_dice工具。
    
    现在正在进行战斗轮，玩家输入的行动需要进行合法性判断。
    之前的上下文信息: {contextInfo}
    当前游戏状态: 轮到玩家 {currentActorId} 行动。
    玩家的输入: "{input}"，
    最近的log: "{combatLogText}",
    地图信息：{mapInfo},
    所有角色状态：{participantsInfo}
    当前玩家状态：{currentActorInfo}
    
    如果行为合法，需要把玩家输入的行为造成的结果完全描述出来放进description里。比如：玩家对怪物使用了武器，需要描述武器的命中，怪物的闪避或者对抗，怪物的血量变化，怪物的状态变化，怪物的死亡，等等。！！不要忘了带上掷骰子的动作和结果。
    如果行为不合法，需要把不合法的原因放进description里。
    如果玩家的行为造成了数值变化或者location变化，需要把把更新后的对应participant对象放进result数组里。如玩家对食尸鬼造成1点伤害，那么result数组里需要有食尸鬼的更新后的对象，hp比之前少1点。
    请分析玩家输入并返回JSON blob的结构化结果：
    {{
      isValid: 输入是否合法,
      description: 不合法的原因，或者合法的行动信息(具体做了什么，造成了什么影响，),
      result: participants中发生数据变化的对象[],
    }}
    agent_scratchpad: {agent_scratchpad}
    `);
  const agent = await createToolCallingAgent({
    llm,
    tools,
    prompt,
  });

  const agentExecutor = new AgentExecutor({
    agent,
    tools,
  });

  const { output } = await agentExecutor.invoke({
    contextInfo: state.previousContext.join("\n"),
    currentActorId: state.initiativeOrder[state.currentActorIndex],
    combatLogText: state.combatLog.join("\n"),
    mapInfo: state.map ? JSON.stringify(state.map) : "无地图信息",
    participantsInfo: JSON.stringify(state.participants),
    currentActorInfo: JSON.stringify(state.participants.find(p => p.id === state.initiativeOrder[state.currentActorIndex])),
    input: state.playerInput,
  });
  let result = null;
  // 处理 LLM 返回的内容，可能包含在代码块中
  if (output.includes('```json')) {
    // 提取 JSON 代码块中的内容
    const jsonMatch = output.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      result = JSON.parse(jsonMatch[1]);
    }
  } 
  if (!result.isValid) {
    return { 
      combatLog: [`[守秘人]: ${result.description}`],
      isValidAction: false,
    };
  }

  // 更新participants
  const updatedParticipants = state.participants.map(participant => {
    const updatedParticipant = result.result.find((p: Participant) => p.id === participant.id);
    return updatedParticipant ? updatedParticipant : participant;
  });

  return { 
    combatLog: [`[守秘人]: ${result.description}`],
    isValidAction: true,
    participants: updatedParticipants,
  };
}

// --- Agent 6: Keeper Narrator Agent ---

export async function keeperNarratorAgent(state: GraphState): Promise<Partial<GraphState>> {
    if (IS_DEBUG) {
      console.log("--- 调用: Keeper Narrator Agent ---", state.combatLog);
    }

    const prompt = ChatPromptTemplate.fromTemplate(`你是一位《克苏鲁的呼唤》的守秘人，擅长营造恐怖氛围。
      所有角色：{participantsInfo}，
      地图：{mapInfo}
      请根据以下发生的事件，生成一段生动的战斗描述。给玩家反馈，或者告诉玩家轮到他行动。不要给玩家行动建议。也不要在输出里带上[守秘人]。
      描述时要包括投骰子的命令和投骰子的结果，把它们融合进描述中。
      描述中要区分不同的玩家，不要混淆称呼。
      战斗描述要包含战斗的场景，战斗的参与者，战斗的行动，战斗的结果(如玩家对怪物造成1点伤害，怪物hp减少1点)。
      描述里要把每个角色都带到，比如大致位置等。
      发生的事: {event_data}`);
    
    const chain = prompt.pipe(llm);
    const result = await chain.invoke({
        event_data: JSON.stringify(state.combatLog.join("\n")),
        participantsInfo: JSON.stringify(state.participants),
        mapInfo: JSON.stringify(state.map),
    });

    return { llmOutput: result.content as string };
}