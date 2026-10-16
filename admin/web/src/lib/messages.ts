// 消息相关的纯函数：默认值、展示文案

import type { Friend, Message, MessageType, SimpleMessage } from "./types";

export const MESSAGE_TYPE_LABELS: Record<MessageType, string> = {
  text: "文字",
  douyin_sticker: "抖音表情",
  image: "图片",
  random: "随机一条",
};

export function emptyMessage(type: MessageType, firstSticker: string): Message {
  switch (type) {
    case "text":
      return { type, content: "" };
    case "douyin_sticker":
      return { type, sticker: firstSticker };
    case "image":
      return { type, path: "" };
    case "random":
      return { type, choices: [{ type: "text", content: "" }] };
  }
}

export function emptySimpleMessage(type: SimpleMessage["type"], firstSticker: string): SimpleMessage {
  return emptyMessage(type, firstSticker) as SimpleMessage;
}

export function summarize(message: Message): string {
  switch (message.type) {
    case "text":
      return message.content || "（空）";
    case "douyin_sticker":
      return `[${message.sticker}]`;
    case "image":
      return `图片 ${message.path}`;
    case "random":
      return `随机：${message.choices.map(summarize).join(" / ")}`;
  }
}

/** 与续火花程序一致：按启用好友的顺序编号为 好友01、好友02…，停用的为 null */
export function logAliases(friends: Friend[]): (string | null)[] {
  let n = 0;
  return friends.map((f) => (f.enabled ? `好友${String(++n).padStart(2, "0")}` : null));
}

export function formatTime(iso: string | undefined | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("zh-CN", { hour12: false });
}

export function formatLogDate(date: string): string {
  return `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`;
}
