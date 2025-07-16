# CoC战斗系统 - 基于LangGraph和Gemini的克苏鲁的呼唤战斗模拟器

这是一个使用 LangGraph 和 Google Gemini 构建的《克苏鲁的呼唤》(Call of Cthulhu) 战斗系统。系统实现了完整的战斗轮机制，包括先攻判定、行动解析、骰子系统、伤害计算等功能。

## 🎲 核心特性

- **完整的战斗轮系统**：基于LangGraph状态机的回合制战斗
- **智能AI守秘人**：使用Gemini模型进行战斗判定和描述
- **骰子系统**：支持1d20、1d100、伤害骰等多种骰子类型
- **多智能体架构**：专门的输入分类、行动解析、怪物AI等智能体
- **实时战斗日志**：详细的战斗过程记录
- **TypeScript支持**：完整的类型安全和开发体验

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制环境变量模板并配置你的 Google API 密钥：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```env
GOOGLE_API_KEY=your_actual_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash
IS_DEBUG=false
```

### 3. 获取 Google API 密钥

1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 创建一个新的 API 密钥
3. 将密钥复制到 `.env` 文件中

### 4. 运行项目

```bash
# 运行CoC战斗演示
npm run coc-demo

# 测试API连接
npm run test-api

# 构建TypeScript项目
npm run build
```

## 📁 项目结构

```
cocFight/
├── src/
│   ├── coc-keeper.ts          # 主战斗系统状态机
│   ├── coc-keeper-demo.ts     # 战斗演示程序
│   ├── agents.ts              # 智能体定义
│   ├── types.ts               # TypeScript类型定义
│   ├── state.ts               # 状态管理
│   └── tools/
│       └── dice-tools.ts      # 骰子系统工具
├── dist/                      # 编译输出目录
├── test-api.js               # API测试文件
├── package.json              # 项目配置
├── tsconfig.json             # TypeScript配置
├── env.example               # 环境变量模板
└── README.md                 # 项目说明
```

## 🎯 系统架构

### 核心组件

#### 1. 状态机 (coc-keeper.ts)
- **StateGraph**: 基于LangGraph的战斗流程状态机
- **节点**: 输入路由、战斗初始化、回合处理、行动解析等
- **条件边**: 根据战斗状态和玩家输入进行流程控制

#### 2. 智能体系统 (agents.ts)
- **PlayerInputTriageAgent**: 玩家输入意图分类
- **PlayerActionAgent**: 玩家行动解析和合法性验证
- **MonsterAiAgent**: 怪物AI行为决策
- **RulesKeeperAgent**: 规则查询处理
- **OocAgent**: 游戏外对话处理
- **KeeperNarratorAgent**: 守秘人叙述生成

#### 3. 骰子系统 (tools/dice-tools.ts)
- **RollDTool**: 支持多种骰子表示法 (1d20, 2d6+3, 1d100-5)
- **DiceResult**: 完整的骰子结果数据结构
- **集成LLM**: 通过工具调用实现智能骰子判定

#### 4. 类型系统 (types.ts)
- **GraphState**: 完整的战斗状态定义
- **Participant**: 参与者（调查员/敌人）数据结构
- **ClassifiedIntent**: 玩家输入意图分类
- **CombatStatus**: 战斗状态枚举

### 战斗流程

```
开始战斗 → 投掷先攻 → 处理回合 → 解析行动 → 更新状态 → 检查结束条件
    ↓           ↑                                    ↓
  结束战斗 ← 开始新轮次 ← ← ← ← ← ← ← ← ← ← ← ← ← ← 继续战斗
```

## 🎮 使用示例

### 基础战斗演示

```bash
npm run coc-demo
```

演示包含：
- 调查员 vs 食尸鬼的完整战斗
- 先攻判定和回合顺序
- 武器攻击和伤害计算
- 闪避和对抗判定
- 战斗日志和状态更新

### API测试

```bash
npm run test-api
```

测试内容：
- Gemini API连接验证
- 工具调用功能测试
- 骰子系统集成测试

## 🔧 智能体详解

### PlayerInputTriageAgent
负责将玩家输入分类为：
- `direct_action`: 直接行动（攻击、闪避等）
- `query`: 规则查询
- `ooc`: 游戏外对话
- `fuzzy_intent`: 模糊意图

### PlayerActionAgent
处理玩家行动：
- 验证行动合法性
- 调用骰子系统进行判定
- 计算伤害和状态变化
- 生成战斗描述

### MonsterAiAgent
控制怪物行为：
- 基于当前状态做出决策
- 执行攻击或其他行动
- 调用骰子系统
- 更新战斗状态

## 🎲 骰子系统

### 支持的骰子类型
- **1d20**: 技能检定、命中判定
- **1d100**: 百分骰、技能检定
- **伤害骰**: 1d10（手枪）、2d6+4（步枪）等
- **修正值**: 支持+/-修正值

## 🛠️ 开发指南

### 添加新的行动类型
1. 在 `types.ts` 中定义新的行动类型
2. 在相应的智能体中添加处理逻辑
3. 更新状态机流程

### 扩展骰子系统
1. 在 `dice-tools.ts` 中添加新的骰子函数
2. 更新工具描述和参数
3. 在智能体中集成新功能

### 自定义怪物AI
1. 修改 `MonsterAiAgent` 的决策逻辑
2. 添加新的行为模式
3. 调整AI的响应策略

## 🔍 调试模式

设置环境变量启用调试模式：
```env
IS_DEBUG=true
```

调试模式会输出：
- 智能体调用日志
- 状态变化详情
- 骰子结果
- 流程控制信息

## 📝 技术栈

- **LangGraph**: 状态机和工作流管理
- **Google Gemini**: 大语言模型
- **TypeScript**: 类型安全和开发体验
- **Node.js**: 运行时环境
- **Zod**: 数据验证和模式定义

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## �� 许可证

MIT License 