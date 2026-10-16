"use client";

import type { Message, MessageType, SimpleMessage } from "@/lib/types";
import { MESSAGE_TYPE_LABELS, emptyMessage, emptySimpleMessage } from "@/lib/messages";

type Props<T extends Message> = {
  message: T;
  stickers: string[];
  allowRandom: boolean;
  onChange: (message: T) => void;
  onRemove: () => void;
};

const SIMPLE_TYPES: SimpleMessage["type"][] = ["text", "douyin_sticker", "image"];

export function MessageEditor<T extends Message>({ message, stickers, allowRandom, onChange, onRemove }: Props<T>) {
  const types: MessageType[] = allowRandom ? [...SIMPLE_TYPES, "random"] : SIMPLE_TYPES;
  const firstSticker = stickers[0] ?? "";

  return (
    <div className="space-y-2 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
      <div className="flex items-center gap-2">
        <select
          aria-label="消息类型"
          className="input w-auto"
          value={message.type}
          onChange={(e) => onChange(emptyMessage(e.target.value as MessageType, firstSticker) as T)}
        >
          {types.map((type) => (
            <option key={type} value={type}>
              {MESSAGE_TYPE_LABELS[type]}
            </option>
          ))}
        </select>
        <button type="button" className="btn-danger ml-auto" onClick={onRemove}>
          删除
        </button>
      </div>
      <MessageBody message={message} stickers={stickers} onChange={onChange} />
    </div>
  );
}

function MessageBody<T extends Message>({ message, stickers, onChange }: Pick<Props<T>, "message" | "stickers" | "onChange">) {
  switch (message.type) {
    case "text":
      return (
        <textarea
          aria-label="文字内容"
          className="input min-h-16"
          maxLength={2000}
          placeholder="要发送的文字"
          value={message.content}
          onChange={(e) => onChange({ ...message, content: e.target.value })}
        />
      );
    case "douyin_sticker":
      return stickers.length === 0 ? (
        <p className="text-sm text-amber-600">还没有表情，请先在「表情库」中添加。</p>
      ) : (
        <select
          aria-label="表情"
          className="input"
          value={message.sticker}
          onChange={(e) => onChange({ ...message, sticker: e.target.value })}
        >
          {!stickers.includes(message.sticker) && <option value={message.sticker}>{message.sticker}（未在表情库中）</option>}
          {stickers.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      );
    case "image":
      return (
        <div className="space-y-1">
          <input
            aria-label="图片路径"
            className="input"
            placeholder="服务器上的图片路径，如 data/images/hi.png"
            value={message.path}
            onChange={(e) => onChange({ ...message, path: e.target.value })}
          />
          <p className="text-xs text-zinc-500">相对项目目录的路径，支持 PNG / JPG / GIF / WEBP，文件需已上传到服务器。</p>
        </div>
      );
    case "random":
      return <RandomChoices message={message} stickers={stickers} onChange={(m) => onChange(m as T)} />;
  }
}

function RandomChoices({
  message,
  stickers,
  onChange,
}: {
  message: Extract<Message, { type: "random" }>;
  stickers: string[];
  onChange: (message: Message) => void;
}) {
  const update = (choices: SimpleMessage[]) => onChange({ ...message, choices });
  return (
    <div className="space-y-2 border-l-2 border-brand/40 pl-3">
      <p className="text-xs text-zinc-500">每次运行从下面随机选一条发送</p>
      {message.choices.map((choice, index) => (
        <MessageEditor
          key={index}
          message={choice}
          stickers={stickers}
          allowRandom={false}
          onChange={(next) => update(message.choices.map((c, i) => (i === index ? next : c)))}
          onRemove={() => update(message.choices.filter((_, i) => i !== index))}
        />
      ))}
      <button
        type="button"
        className="btn-ghost"
        onClick={() => update([...message.choices, emptySimpleMessage("text", stickers[0] ?? "")])}
      >
        + 添加候选
      </button>
    </div>
  );
}
