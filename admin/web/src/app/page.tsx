"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { FriendCard } from "@/components/FriendCard";
import { SaveBar } from "@/components/SaveBar";
import { StatusPanel } from "@/components/StatusPanel";
import { StickerPanel } from "@/components/StickerPanel";
import { api } from "@/lib/api";
import { logAliases } from "@/lib/messages";
import { useConfigEditor } from "@/lib/useConfigEditor";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState("");
  const toLogin = useCallback(() => router.replace("/login"), [router]);
  const editor = useConfigEditor(toLogin);

  useEffect(() => {
    api.me().then((me) => setUser(me.username), toLogin);
  }, [toLogin]);

  async function logout() {
    await api.logout().catch(() => undefined);
    toLogin();
  }

  const { draft } = editor;
  if (!user) return null;

  const stickers = draft ? Object.keys(draft.stickers) : [];
  const enabledCount = draft?.friends.filter((f) => f.enabled).length ?? 0;
  const aliases = logAliases(draft?.friends ?? []);

  return (
    <div className="mx-auto max-w-4xl space-y-4 px-4 py-6 pb-28">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">🔥 续火花管理后台</h1>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-zinc-500">{user}</span>
          <button type="button" className="btn-ghost" onClick={logout}>
            退出
          </button>
        </div>
      </header>

      <StatusPanel />

      {editor.loadError && <p className="card text-sm text-red-600">{editor.loadError}</p>}

      {draft && (
        <>
          <section className="space-y-3">
            <div className="flex items-end justify-between">
              <div>
                <h2 className="font-semibold">续火花好友</h2>
                <p className="text-xs text-zinc-500">
                  共 {draft.friends.length} 位，启用 {enabledCount} 位。保存后下次定时任务自动使用新配置。
                </p>
              </div>
              <button
                type="button"
                className="btn-primary"
                onClick={() =>
                  editor.setFriends([...draft.friends, { name: "", enabled: true, messages: [{ type: "text", content: "" }] }])
                }
              >
                + 添加好友
              </button>
            </div>
            {draft.friends.map((friend, index) => (
              <FriendCard
                key={index}
                friend={friend}
                alias={aliases[index] ?? null}
                stickers={stickers}
                onChange={(next) => editor.setFriends(draft.friends.map((f, i) => (i === index ? next : f)))}
                onRemove={() => editor.setFriends(draft.friends.filter((_, i) => i !== index))}
              />
            ))}
          </section>

          <StickerPanel stickers={draft.stickers} usedBy={editor.stickerUsage} onChange={editor.setStickers} />
        </>
      )}

      <SaveBar dirty={editor.dirty} state={editor.save} onSave={editor.submit} onReload={editor.reload} />
    </div>
  );
}
