import { ClassifiedIntent, GraphState, Participant } from "./types";
import { Annotation } from "@langchain/langgraph";

export const StateAnnotation = Annotation.Root({
    previousContext: Annotation<string[]>({ value: (x: string[], y: string[]) => y, default: () => [] }),
    roundEnded: Annotation<boolean>({ value: (x: boolean, y: boolean) => y !== undefined ? y : x, default: () => false }),
    fightEnded: Annotation<boolean>({ value: (x: boolean, y: boolean) => y !== undefined ? y : x, default: () => false }),
    sender: Annotation<string | null>({ value: (x: string | null, y: string | null) => y !== undefined ? y : x, default: () => null }),
    participants: Annotation<Participant[]>({ value: (x: Participant[], y: Participant[]) => y, default: () => [] }),
    initiativeOrder: Annotation<string[]>({ value: (x: string[], y: string[]) => y, default: () => [] }),
    roundNumber: Annotation<number>({ value: (x: number, y: number) => y !== undefined ? y : x, default: () => 0 }),
    currentActorIndex: Annotation<number>({ value: (x: number, y: number) => y !== undefined ? y : x, default: () => 0 }),
    // 使用 reducer 来追加日志
    combatLog: Annotation<string[]>({ reducer: (x: string[], y: string[]) => x.concat(y), default: () => [] }),
    playerInput: Annotation<string | null>({ value: (x: string | null, y: string | null) => y !== undefined ? y : x, default: () => null }),
    requiresPlayerInput: Annotation<boolean>({ value: (x: boolean, y: boolean) => y !== undefined ? y : x, default: () => false }),
    isValidAction: Annotation<boolean>({ value: (x: boolean, y: boolean) => y !== undefined ? y : x, default: () => false }),
    classifiedIntent: Annotation<ClassifiedIntent | null>({ value: (x: ClassifiedIntent | null, y: ClassifiedIntent | null) => y !== undefined ? y : x, default: () => null }),
    map: Annotation<{
        name: string;
        zones: {
            [key: string]: {
                description: string;
                adjacent_zones: string[];
                properties: string[];
            }
        }
    }>({ value: (x, y) => y !== undefined ? y : x, default: () => ({
        name: "禁忌图书馆",
        zones: {
            entrance: {
                description: "图书馆的入口，一扇巨大的橡木门敞开着。",
                adjacent_zones: ["main_hall"],
                properties: ["has_light"]
            }
        }
    })}),
    llmOutput: Annotation<string>({ value: (x: string, y: string) => y !== undefined ? y : x, default: () => "" }),
    normalCircleEnded: Annotation<boolean>({ value: (x: boolean, y: boolean) => y !== undefined ? y : x, default: () => false }),
})

export const defaultState: GraphState = {
    previousContext: [],
    roundEnded: false,
    fightEnded: false,
    sender: null,
    participants: [],
    initiativeOrder: [],
    roundNumber: 0,
    currentActorIndex: 0,
    combatLog: [],
    playerInput: null,
    requiresPlayerInput: false,
    isValidAction: false,
    classifiedIntent: null,
    map: {
        name: "禁忌图书馆",
        zones: {
            entrance: {
                description: "图书馆的入口，一扇巨大的橡木门敞开着。",
                adjacent_zones: ["main_hall"],
                properties: ["has_light"]
            }
        }
    },
    llmOutput: "",
    normalCircleEnded: false,
}