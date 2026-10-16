"use client";

import { useState } from "react";
import type { Sticker } from "@/lib/types";

type Props = {
  stickers: Record<string, Sticker>;
  usedBy: (name: string) => number;
  onChange: (stickers: Record<string, Sticker>) => void;
};

export function StickerPanel({ stickers, usedBy, onChange }: Props) {
  const [name, setName] = useState("");
  const names = Object.keys(stickers);

  function add() {
    const trimmed = name.trim();
    if (!trimmed || trimmed in stickers) return;
    onChange({ ...stickers, [trimmed]: { label: trimmed } });
    setName("");
  }

  function remove(key: string) {
    const count = usedBy(key);
    if (count > 0) {
      window.alert(`表情「${key}」正在被 ${count} 条消息使用，请先修改这些消息。`);
      return;
    }
    const next = { ...stickers };
    delete next[key];
    onChange(next);
  }

  return (
    <section className="card space-y-3">
      <div>
        <h2 className="font-semibold">表情库</h2>
        <p className="text-xs text-zinc-500">名称需与抖音表情面板中的名字一致，如「比心」「嗨」。</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {names.length === 0 && <span className="text-sm text-zinc-500">暂无表情</span>}
        {names.map((key) => (
          <span key={key} className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-3 py-1 text-sm dark:bg-zinc-800">
            {key}
            <button type="button" aria-label={`删除表情 ${key}`} className="text-zinc-400 hover:text-red-600" onClick={() => remove(key)}>
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          aria-label="新表情名称"
          className="input"
          placeholder="新表情名称"
          value={name}
          maxLength={100}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
        />
        <button type="button" className="btn-ghost shrink-0" onClick={add} disabled={!name.trim() || name.trim() in stickers}>
          添加
        </button>
      </div>
    </section>
  );
}
