import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import dotenv from "dotenv";
import { RollDTool } from "./dist/tools/dice-tools.js";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { AgentExecutor, createToolCallingAgent } from "langchain/agents";
import { setGlobalDispatcher, ProxyAgent } from "undici";
// 只有在设置了代理的情况下才使用代理
if (process.env.https_proxy) {
  const dispatcher = new ProxyAgent({ uri: new URL(process.env.https_proxy).toString() });
  setGlobalDispatcher(dispatcher);
}
dotenv.config();

async function testAPI() {
  console.log("=== Google Gemini API 测试 ===");
  console.log("API Key:", process.env.GOOGLE_API_KEY ? "已设置" : "未设置");
  console.log("Model:", process.env.GEMINI_MODEL || "gemini-pro");
  
  if (!process.env.GOOGLE_API_KEY) {
    console.error("❌ 错误：未设置 GOOGLE_API_KEY");
    console.log("请检查 .env 文件");
    return;
  }

  try {
    const llm = new ChatGoogleGenerativeAI({
      model: "gemini-2.0-flash",
      apiKey: process.env.GOOGLE_API_KEY,
      temperature: 0.1,
    });

    const tools = [RollDTool];
    const prompt = ChatPromptTemplate.fromTemplate(`你是一位经验丰富的《克苏鲁的呼唤》守秘人(KP)。
      战斗时，需要先扔骰子判定命中，再判定对方的闪避或对抗。如果确实命中再投伤害骰子判定伤害。还有困难成功，极难成功，大成功等的效果加成。具体效果由你决定。
      
      重要：当你需要掷骰子时，必须使用roll_dice工具，伤害也要通过roll_dice工具计算。
      
      现在正在进行战斗轮，玩家输入的行动需要进行合法性判断。
      玩家输入的行动: {input}

      如果行为合法，需要把玩家输入的行为造成的结果完全描述出来放进description里。比如：玩家对怪物使用了武器，需要描述武器的命中，怪物的闪避或者对抗，怪物的血量变化，怪物的状态变化，怪物的死亡，等等。！！不要忘了带上掷骰子的动作和结果。
      如果行为不合法，需要把不合法的原因放进description里。
      如果玩家的行为造成了数值变化或者location变化，需要把把更新后的对应participant对象放进result数组里。如玩家对食尸鬼造成1点伤害，那么result数组里需要有食尸鬼的更新后的对象，hp比之前少1点。
      请分析玩家输入并返回结构化结果：
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
      maxIterations: 5, // 最大迭代次数
      agent,
      tools,
    });

    const { output } = await agentExecutor.invoke({
      input: "玩家使用手枪攻击食尸鬼",
    });
    console.log("✅ API 连接成功！");
    console.log("回复:", output);
    
  } catch (error) {
    console.error("❌ API 连接失败:");
    console.error("错误类型:", error.constructor.name);
    console.error("错误信息:", error.message);
    
    if (error.message.includes("fetch failed")) {
      console.log("\n💡 可能的解决方案:");
      console.log("1. 检查网络连接");
      console.log("2. 检查 API 密钥是否正确");
      console.log("3. 检查 API 配额是否用完");
      console.log("4. 尝试使用代理或 VPN");
    }
  }
}

testAPI(); 