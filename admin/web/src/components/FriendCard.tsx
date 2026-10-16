"use client";

import { useState } from "react";
import type { Friend } from "@/lib/types";
import { emptyMessage, summarize } from "@/lib/messages";
import { MessageEditor } from "./MessageEditor";

type Props = {
  friend: Friend;
  /** 运行日志中的编号，如「好友03」；停用的好友没有编号 */
  alias: string | null;
  stickers: string[];
  onChange: (friend: Friend) => void;
  onRemove: () => void;
};

export function FriendCard({ friend, alias, stickers, onChange, onRemove }: Props) {
  const [open, setOpen] = useState(friend.name === "");

  function remove() {
    if (window.confirm(`确定删除好友「${friend.name || "未命名"}」吗？只想暂停可以直接关闭开关。`)) onRemove();
  }

  return (
    <article className={`card space-y-3 ${friend.enabled ? "" : "opacity-60"}`}>
      <header className="flex flex-wrap items-center gap-3">
        <label className="flex cursor-pointer items-center gap-2" title={friend.enabled ? "已启用" : "已停用"}>
          <input
            type="checkbox"
            role="switch"
            className="peer sr-only"
            checked={friend.enabled}
            onChange={(e) => onChange({ ...friend, enabled: e.target.checked })}
          />
          <span className="relative h-6 w-11 rounded-full bg-zinc-300 transition peer-checked:bg-brand peer-focus-visible:ring-2 peer-focus-visible:ring-brand/40 after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:transition peer-checked:after:translate-x-5 dark:bg-zinc-700" />
          <span className="sr-only">启用续火花</span>
        </label>
        <input
          aria-label="好友昵称"
          className="input min-w-40 flex-1 font-medium"
          placeholder="好友昵称（与抖音私信列表中的名字一致）"
          value={friend.name}
          onChange={(e) => onChange({ ...friend, name: e.target.value })}
        />
        <span className={`text-xs ${friend.enabled ? "text-emerald-600" : "text-zinc-500"}`}>
          {friend.enabled ? `启用中 · 日志编号 ${alias}` : "已停用"}
        </span>
        <button type="button" className="btn-ghost" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "收起" : "编辑消息"}
        </button>
        <button type="button" className="btn-danger" onClick={remove}>
          删除
        </button>
      </header>

      {!open && (
        <ul className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
          {friend.messages.map((m, i) => (
            <li key={i} className="truncate">
              {i + 1}. {summarize(m)}
            </li>
          ))}
        </ul>
      )}

      {open && (
        <div className="space-y-2">
          {friend.messages.map((message, index) => (
            <MessageEditor
              key={index}
              message={message}
              stickers={stickers}
              allowRandom
              onChange={(next) => onChange({ ...friend, messages: friend.messages.map((m, i) => (i === index ? next : m)) })}
              onRemove={() => onChange({ ...friend, messages: friend.messages.filter((_, i) => i !== index) })}
            />
          ))}
          {friend.messages.length === 0 && <p className="text-sm text-amber-600">至少需要一条消息</p>}
          <button
            type="button"
            className="btn-ghost"
            onClick={() => onChange({ ...friend, messages: [...friend.messages, emptyMessage("text", stickers[0] ?? "")] })}
          >
            + 添加消息
          </button>
        </div>
      )}
    </article>
  );
}
