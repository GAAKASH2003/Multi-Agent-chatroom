export type Role = "user" | "assistant" | "system";

export interface Character {
  id: string;
  name: string;
  avatar: string;
  persona: string;
  traits: string[];
  type?: "seed" | "custom";
  color: 'cyan' | 'green' | 'pink' | 'purple' | 'blue' | 'yellow';
}

export interface Group {
  id: string;
  name: string;
  description: string;
  characterIds: string[];
  createdAt: number;
  createdBy?: string;
  grpType?: "seed" | "custom";
}

export interface ChatSession {
  id: string;
  groupId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  memorySummary?: string;
  convIds?: string[];
}

export interface Message {
  id: string;
  sessionId: string;
  characterId: string | null;
  role: Role;
  content: string;
  createdAt: number;
  streaming?: boolean;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar: string;
}

// lib/types.ts
export interface ConvTurn {
  conv_id: string;
  seq_num: number;
  query: Message;
  responses: Message[];
}

export interface SessionHistory {
  turns: ConvTurn[];
}