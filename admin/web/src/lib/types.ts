// 与后端 admin/server/configs/schema.py 一一对应的类型定义

export type TextMessage = { type: "text"; content: string };
export type StickerMessage = { type: "douyin_sticker"; sticker: string };
export type ImageMessage = { type: "image"; path: string };
export type SimpleMessage = TextMessage | StickerMessage | ImageMessage;
export type RandomMessage = { type: "random"; choices: SimpleMessage[] };
export type Message = SimpleMessage | RandomMessage;
export type MessageType = Message["type"];

export type Friend = { name: string; enabled: boolean; messages: Message[] };

export type Sticker = {
  label?: string | null;
  accessible_name?: string | null;
  category?: string | null;
  fallback_index?: number | null;
};

export type FriendsConfig = {
  friends: Friend[];
  stickers: Record<string, Sticker>;
  version: string;
};

export type SaveResponse = { config: FriendsConfig; applies_next_run: boolean };

export type TargetStatus = "success" | "failed" | "skipped" | "duplicate" | "unknown";
export type TargetResult = { target: string; status: TargetStatus; sent: number; error: string | null };
export type RunResult = { task_id: string; dry_run: boolean; finished_at: string; results: TargetResult[] };

export type History = {
  total_runs: number;
  total_successful_runs: number;
  total_messages_sent: number;
  average_success_rate: number;
  last_run_at: string;
  first_run_at: string;
};

export type StatusResponse = {
  running: boolean;
  last_run: RunResult | null;
  history: History | null;
  log_dates: string[];
};

export type LogResponse = { date: string; content: string; truncated: boolean };
export type Me = { username: string; csrf_token: string };
