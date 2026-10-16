"use client";

import type { SaveState } from "@/lib/useConfigEditor";

type Props = {
  dirty: boolean;
  state: SaveState;
  onSave: () => void;
  onReload: () => void;
};

export function SaveBar({ dirty, state, onSave, onReload }: Props) {
  const conflict = state.kind === "error" && state.message.includes("刷新");
  if (!dirty && state.kind !== "saved" && state.kind !== "error") return null;

  return (
    <div role="status" className="fixed inset-x-0 bottom-0 border-t border-zinc-200 bg-white/95 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/95">
      <div className="mx-auto flex max-w-4xl flex-wrap items-center gap-3 px-4 py-3 text-sm">
        <Message state={state} dirty={dirty} />
        <div className="ml-auto flex gap-2">
          {(dirty || conflict) && (
            <button
              type="button"
              className="btn-ghost"
              onClick={() => (!dirty || window.confirm("放弃未保存的修改并重新读取服务器配置？")) && onReload()}
            >
              {conflict ? "刷新" : "放弃修改"}
            </button>
          )}
          {dirty && (
            <button type="button" className="btn-primary" onClick={onSave} disabled={state.kind === "saving"}>
              {state.kind === "saving" ? "保存中…" : "保存到服务器"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Message({ state, dirty }: { state: SaveState; dirty: boolean }) {
  switch (state.kind) {
    case "error":
      return <span className="text-red-600">保存失败：{state.message}</span>;
    case "saved":
      return (
        <span className="text-emerald-600">
          ✓ 已保存{state.nextRun ? "。定时任务正在执行，本次仍用旧配置，下次执行生效" : "，下次定时任务自动生效"}
        </span>
      );
    default:
      return dirty ? <span className="text-amber-600">有未保存的修改</span> : null;
  }
}
