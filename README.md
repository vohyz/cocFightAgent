# LangGraph + Gemini TypeScript 项目

这是一个使用 LangGraph 和 Google Gemini 构建的 TypeScript 项目示例。

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

将 `env.example` 文件复制为 `.env` 并配置你的 Google API 密钥：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```env
GOOGLE_API_KEY=your_actual_google_api_key_here
GEMINI_MODEL=gemini-pro
DEBUG=false
```

### 3. 获取 Google API 密钥

1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 创建一个新的 API 密钥
3. 将密钥复制到 `.env` 文件中

### 4. 运行项目

```bash
# 运行基本示例
npm start

# 或者使用开发模式（自动重启）
npm run dev

# 运行高级示例
npm run advanced

# 或者使用开发模式运行高级示例
npm run advanced:dev

# 运行CoC战斗演示
npm run coc-demo

# 运行基础CoC演示（不需要API密钥）
npm run coc-basic

# 构建 TypeScript 项目
npm run build
```

## 📁 项目结构

```
├── package.json              # 项目配置和依赖
├── tsconfig.json             # TypeScript 配置
├── src/
│   ├── index.ts              # 基本示例：简单的聊天机器人
│   ├── advanced-example.ts   # 高级示例：多节点工作流
│   ├── types.ts              # TypeScript 类型定义
│   ├── coc-combat-types.ts   # CoC战斗相关类型定义
│   ├── coc-combat-utils.ts   # CoC战斗工具函数
│   ├── coc-combat-agent.ts   # CoC战斗守秘人Agent（完整版）
│   └── coc-combat-demo.ts    # CoC战斗演示程序
├── dist/                     # 编译输出目录
├── env.example               # 环境变量模板
├── README.md                # 项目说明文档
└── .env                     # 环境变量文件（需要创建）
```

## 🔧 功能特性

### 基本示例 (src/index.ts)
- 简单的 LangGraph 状态图
- 与 Gemini 模型的基本交互
- 错误处理和连接测试
- 完整的 TypeScript 类型支持

### 高级示例 (src/advanced-example.ts)
- 多节点工作流
- 意图识别和路由
- 条件逻辑和状态管理
- 复杂的对话处理
- 严格的类型检查和接口定义

### CoC战斗系统 (src/coc-combat-*.ts)
- 完整的克苏鲁的呼唤战斗轮状态机
- 包含先攻、行动解析、状态更新的完整流程
- 支持调查员和敌人的AI行为
- 包含SAN检定、伤害计算、状态效果
- 模块化设计，易于扩展

## 🎯 TypeScript 优势

### 类型安全
- 编译时类型检查，减少运行时错误
- 自动补全和智能提示
- 重构时的类型保证

### 更好的开发体验
- 强类型的状态管理
- 明确的接口定义
- 完整的类型推断

### 可维护性
- 清晰的代码结构
- 自文档化的类型信息
- 更容易的团队协作

## 🎲 CoC战斗系统

### 系统架构

CoC战斗系统是一个基于LangGraph的状态机，完整实现了克苏鲁的呼唤战斗轮的所有逻辑。

### 核心组件

#### 1. 类型定义 (coc-combat-types.ts)
- **Participant**: 参与者（调查员/敌人）
- **ActionChoice**: 行动选择
- **ActionResult**: 行动结果
- **CombatStatus**: 战斗状态
- **ParticipantStatus**: 参与者状态

#### 2. 工具函数 (coc-combat-utils.ts)
- **DiceRoller**: 骰子系统（1d100、技能检定、对抗检定）
- **SanityChecker**: SAN检定和疯狂状态
- **DamageCalculator**: 伤害计算
- **CombatStateChecker**: 战斗状态检查
- **AIBehavior**: AI行为逻辑
- **CombatDescriber**: 战斗描述生成

#### 3. 状态机节点
- **start_combat**: 战斗开始，执行SAN检定
- **roll_initiative**: 投掷先攻，确定行动顺序
- **process_turn**: 处理当前回合，选择行动
- **resolve_action**: 解析行动，计算结果
- **update_state**: 更新状态，应用效果
- **start_new_round**: 开始新轮次
- **end_combat**: 战斗结束

### 战斗流程

```
开始战斗 → 投掷先攻 → 处理回合 → 解析行动 → 更新状态 → 检查结束条件
    ↓           ↑                                    ↓
  结束战斗 ← 开始新轮次 ← ← ← ← ← ← ← ← ← ← ← ← ← ← 继续战斗
```

### 使用示例

```bash
# 运行基础CoC战斗演示（不需要API密钥）
npm run demo

# 运行交互式CoC战斗演示（支持玩家输入）
npm run demo:interactive
```

### 演示内容

基础演示包含：
- **骰子系统演示**: 1d100、技能检定、对抗检定、统计分析
- **伤害计算演示**: 不同武器的伤害计算和状态变化
- **SAN检定演示**: 理智值损失和疯狂状态管理
- **完整战斗轮**: 调查员 vs 食尸鬼的实际对战

### 实际演示结果

```
🎲 骰子系统演示
格斗(50): 失败 (投掷: 65, 目标: 50)
闪避(30): 大成功! (投掷: 5, 目标: 30)
统计演示 - 格斗技能(50) 100次投掷:
成功率: 49% (期望: ~50%)

💥 伤害计算演示
手枪 (1d10): 9 点伤害
步枪 (2d6+4): 11 点伤害

🧠 SAN检定演示
目击食尸鬼: 失去2点理智
直视克苏鲁: 失去4点理智 (成功检定)

⚔️ 战斗轮演示
第1轮: 调查员攻击成功，食尸鬼受伤
第2轮: 调查员攻击失败，食尸鬼反击
第3轮: 调查员失去意识，食尸鬼获胜
```

### 可扩展功能

- **添加新的行动类型**: 在ActionType中添加新类型
- **自定义敌人**: 扩展ENEMY_TEMPLATES
- **复杂状态效果**: 扩展StatusEffect系统
- **高级AI行为**: 改进AIBehavior类
- **多人战斗**: 扩展参与者系统

## 🎯 LangGraph 核心概念

### 1. 状态管理

```typescript
interface State {
  messages: BaseMessage[];
  userIntent: UserIntent | null;
  needsMoreInfo: boolean;
}

const StateAnnotation = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (left: BaseMessage[], right: BaseMessage[]): BaseMessage[] => left.concat(right),
    default: (): BaseMessage[] => [],
  }),
  userIntent: Annotation<UserIntent | null>({
    reducer: (left: UserIntent | null, right: UserIntent | null): UserIntent | null => right || left,
    default: (): UserIntent | null => null,
  }),
});
```

### 2. 节点定义

```typescript
async function callModel(state: State): Promise<{ messages: BaseMessage[] }> {
  const messages = state.messages;
  const response = await model.invoke(messages);
  return {
    messages: [response],
  };
}
```

### 3. 图形构建

```typescript
const workflow = new StateGraph(StateAnnotation)
  .addNode("agent", callModel)
  .addEdge(START, "agent")
  .addEdge("agent", END);
```

### 4. 条件路由

```typescript
function routeByIntent(state: State): string {
  switch (state.userIntent) {
    case "greeting":
      return "greeting_handler";
    case "question":
      return "question_handler";
    default:
      return "other_handler";
  }
}
```

## 🔄 工作流示例

高级示例中的工作流程：

```
用户输入 → 意图分析 → 根据意图路由 → 处理节点 → 检查是否需要更多信息 → 结束或返回
```

## 📚 可扩展性

基于这个项目，你可以：

1. **添加更多节点类型**
   - 数据库查询节点
   - 外部 API 调用节点
   - 文件处理节点

2. **实现更复杂的路由逻辑**
   - 基于上下文的路由
   - 动态路由选择
   - 并行处理节点

3. **集成不同的接口**
   - Web 界面
   - 命令行交互
   - API 服务

4. **添加持久化存储**
   - 会话存储
   - 用户偏好
   - 对话历史

5. **利用 TypeScript 功能**
   - 扩展 `types.ts` 中的类型定义
   - 创建自定义接口和枚举
   - 使用泛型提高代码复用性

## 🛠️ 常见问题

### Q: 如何获取 Google API 密钥？
A: 访问 [Google AI Studio](https://aistudio.google.com/)，创建项目并生成 API 密钥。

### Q: 支持哪些 Gemini 模型？
A: 支持 `gemini-pro`、`gemini-pro-vision` 等模型。

### Q: 如何处理错误？
A: 项目包含了基本的错误处理，你可以根据需要扩展。

### Q: 如何添加自定义节点？
A: 创建异步函数，接收状态参数，返回状态更新对象。

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

## 📄 许可证

MIT License

## 🔗 相关链接

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/)
- [LangChain JavaScript](https://js.langchain.com/)

---

**享受使用 LangGraph 和 Gemini 构建 AI 应用的乐趣！** 🎉

---

## 🎯 项目完成总结

### ✅ 已实现功能

1. **基础LangGraph示例**
   - 简单聊天机器人 (`index.ts`)
   - 高级多节点工作流 (`advanced-example.ts`)
   - 意图识别和条件路由

2. **完整的CoC战斗系统**
   - 类型安全的TypeScript实现
   - 完整的骰子系统（1d100、技能检定、对抗检定）
   - SAN检定和理智值管理
   - 先攻系统和回合制战斗
   - 伤害计算和状态管理
   - 敌人AI行为逻辑

3. **模块化架构**
   - `coc-combat-types.ts` - 类型定义
   - `coc-combat-utils.ts` - 工具函数
   - `coc-combat-agent.ts` - 完整状态机（实验性）
   - `coc-basic-demo.ts` - 工作演示

### 🚀 演示命令

```bash
# 基础聊天机器人
npm start

# 高级多节点示例
npm run advanced

# CoC战斗系统演示
npm run coc-basic
```

### 🎲 CoC战斗系统特色

- **真实的CoC规则实现**: 严格按照克苏鲁的呼唤7版规则
- **完整的状态机设计**: 包含战斗开始、先攻、回合处理、状态更新的完整流程
- **智能的AI行为**: 敌人和调查员的行为逻辑
- **统计验证**: 通过大量投掷验证概率分布的正确性
- **可扩展架构**: 易于添加新的敌人、技能、法术等

### 🔮 未来扩展方向

- 完善LangGraph状态机的类型兼容性
- 集成更多CoC规则（法术、装备、环境）
- 添加Web界面用于交互式游戏
- 实现多人游戏支持
- 集成语音识别和语音合成
- 添加图像生成用于场景描述

这个项目展示了如何使用现代TypeScript和LangGraph构建复杂的TRPG系统，为AI驱动的桌游体验奠定了基础。 