import { defaultState } from "@/state";
import { combatWorkflow } from "./coc-keeper";
import { GraphState, Participant } from "./types";
import * as readline from "readline";
import { CompiledStateGraph } from "@langchain/langgraph";

// ==================== 预设角色数据 ====================

const investigator1: Participant = {
  id: "艾米莉亚·克拉克",
  name: "艾米莉亚·克拉克",
  type: "investigator",
  stats: {
    HP: 12,
    max_HP: 12,
    SAN: 65,
    max_SAN: 65,
    DEX: 70,
    STR: 50,
    CON: 60,
    INT: 80,
    POW: 70,
    APP: 65,
    EDU: 75,
    SIZ: 55,
    fighting: 45,
    firearms: 60,
    dodge: 35,
    stealth: 40,
    spot_hidden: 50,
    listen: 45,
    psychology: 55,
    first_aid: 40
  },
  status: "active",
  effects: [],
  items: ["手枪", "医疗包", "手电筒"]
};

const investigator2: Participant = {
  id: "杰克·汤普森",
  name: "杰克·汤普森",
  type: "investigator",
  stats: {
    HP: 14,
    max_HP: 14,
    SAN: 60,
    max_SAN: 60,
    DEX: 65,
    STR: 70,
    CON: 65,
    INT: 70,
    POW: 65,
    APP: 60,
    EDU: 70,
    SIZ: 65,
    fighting: 60,
    firearms: 45,
    dodge: 30,
    stealth: 35,
    spot_hidden: 40,
    listen: 35,
    psychology: 45,
    first_aid: 50
  },
  status: "active",
  effects: [],
  items: ["猎刀", "绳索", "打火机"]
};

const ghoul1: Participant = {
  id: "ghoul_1",
  name: "食尸鬼A",
  type: "enemy",
  stats: {
    HP: 13,
    max_HP: 13,
    SAN: 0,
    max_SAN: 0,
    DEX: 65,
    STR: 60,
    CON: 70,
    INT: 40,
    POW: 50,
    APP: 20,
    EDU: 30,
    SIZ: 60,
    fighting: 55,
    firearms: 0,
    dodge: 25,
    stealth: 50,
    spot_hidden: 45,
    listen: 40,
    psychology: 0,
    first_aid: 0
  },
  status: "active",
  effects: [],
  items: []
};

const ghoul2: Participant = {
  id: "ghoul_2",
  name: "食尸鬼B",
  type: "enemy",
  stats: {
    HP: 11,
    max_HP: 11,
    SAN: 0,
    max_SAN: 0,
    DEX: 70,
    STR: 55,
    CON: 65,
    INT: 35,
    POW: 45,
    APP: 15,
    EDU: 25,
    SIZ: 55,
    fighting: 50,
    firearms: 0,
    dodge: 30,
    stealth: 55,
    spot_hidden: 40,
    listen: 35,
    psychology: 0,
    first_aid: 0
  },
  status: "active",
  effects: [],
  items: []
};

// ==================== 命令行界面 ====================

class CombatCLI {
  private rl: readline.Interface;
  private state: GraphState;
  private workflow: CompiledStateGraph<GraphState, any, any, any, any, any>;

  constructor() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    this.state = {
      ...defaultState,
      participants: [investigator1, investigator2, ghoul1, ghoul2]
    };
    
    this.workflow = combatWorkflow;
  }

  async start() {
    
    await this.pause();
    
    await this.runCombat();
  }

  private async pause(): Promise<void> {
    return new Promise((resolve) => {
      this.rl.question("按回车键继续...", () => {
        resolve();
      });
    });
  }

  private async getUserInput(prompt: string): Promise<string> {
    return new Promise((resolve) => {
      this.rl.question(prompt, (answer) => {
        resolve(answer.trim());
      });
    });
  }

  private async runCombat() {
    const messages = [];
    try {
      const config = {
        configurable: {
          thread_id: "combat_demo"
        }
      };

      let currentState = this.state;
      let stepCount = 0;
      const maxSteps = 50; // 防止无限循环

      while (stepCount < maxSteps && !currentState.fightEnded) {
        stepCount++;
        const playerInput = await this.handlePlayerInput(currentState);
        const playerMessage = `${currentState.initiativeOrder[currentState.currentActorIndex]}: ${playerInput}`;

        messages.push({
          role: "user",
          content: playerMessage
        });
        currentState = {
          participants: currentState.participants,
          map: currentState.map,
          fightEnded: currentState.fightEnded,
          roundEnded: currentState.roundEnded,
          roundNumber: currentState.roundNumber,
          currentActorIndex: currentState.currentActorIndex,
          combatLog: [],
          previousContext: currentState.normalCircleEnded ? messages.slice(-2).map(m => m.content ?? '') : currentState.previousContext,
          sender: null,
          playerInput: playerMessage || null,
          isValidAction: false,
          classifiedIntent: null,
          requiresPlayerInput: false,
          normalCircleEnded: false,
          llmOutput: "",
          initiativeOrder: currentState.initiativeOrder,
        }
        const result = await this.workflow.invoke(currentState, config);
        currentState = result as GraphState;
        messages.push({
          role: "assistant",
          content: currentState.llmOutput
        });
        console.log(currentState.llmOutput);
        
        // 短暂暂停
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      if (stepCount >= maxSteps) {
        console.log("\n⚠️ 达到最大步数限制，战斗强制结束");
      }
      
    } catch (error) {
      console.error("❌ 战斗运行出错:", error);
    }
  }

  private async handlePlayerInput(state: GraphState) {
    if (!state.requiresPlayerInput) return;
    
    const userInput = await this.getUserInput("你的输入: ");
    
    return userInput;
  }

  close() {
    this.rl.close();
  }
}

// ==================== 主函数 ====================

async function main() {
  const cli = new CombatCLI();
  
  try {
    await cli.start();
  } catch (error) {
    console.error("演示运行出错:", error);
  } finally {
    cli.close();
  }
}

// 如果直接运行此文件
main().catch(console.error);


export { CombatCLI, main };
