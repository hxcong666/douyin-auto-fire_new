"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api } from "./api";
import type { Friend, FriendsConfig, Message, Sticker } from "./types";

export type SaveState = { kind: "idle" } | { kind: "saving" } | { kind: "saved"; nextRun: boolean } | { kind: "error"; message: string };

function countSticker(messages: Message[], name: string): number {
  return messages.reduce(
    (n, m) => n + (m.type === "douyin_sticker" && m.sticker === name ? 1 : m.type === "random" ? countSticker(m.choices, name) : 0),
    0,
  );
}

/** 管理配置的编辑状态：加载、本地修改、保存、并发冲突处理。 */
export function useConfigEditor(onUnauthorized: () => void) {
  const [saved, setSaved] = useState<FriendsConfig | null>(null);
  const [draft, setDraft] = useState<FriendsConfig | null>(null);
  const [save, setSave] = useState<SaveState>({ kind: "idle" });
  const [loadError, setLoadError] = useState("");

  const load = useCallback(async () => {
    try {
      const config = await api.getConfig();
      setSaved(config);
      setDraft(config);
      setSave({ kind: "idle" });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) return onUnauthorized();
      setLoadError(err instanceof Error ? err.message : "读取配置失败");
    }
  }, [onUnauthorized]);

  useEffect(() => {
    void load();
  }, [load]);

  const dirty = useMemo(() => JSON.stringify(saved) !== JSON.stringify(draft), [saved, draft]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const edit = (patch: Partial<FriendsConfig>) => {
    setDraft((d) => (d ? { ...d, ...patch } : d));
    setSave({ kind: "idle" });
  };

  return {
    draft,
    dirty,
    save,
    loadError,
    reload: load,
    setFriends: (friends: Friend[]) => edit({ friends }),
    setStickers: (stickers: Record<string, Sticker>) => edit({ stickers }),
    stickerUsage: (name: string) => (draft ? countSticker(draft.friends.flatMap((f) => f.messages), name) : 0),
    async submit() {
      if (!draft) return;
      setSave({ kind: "saving" });
      try {
        const result = await api.saveConfig(draft);
        setSaved(result.config);
        setDraft(result.config);
        setSave({ kind: "saved", nextRun: result.applies_next_run });
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return onUnauthorized();
        setSave({ kind: "error", message: err instanceof Error ? err.message : "保存失败" });
      }
    },
  };
}
