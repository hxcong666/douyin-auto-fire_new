"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { LogResponse, StatusResponse, TargetStatus } from "@/lib/types";
import { formatLogDate, formatTime } from "@/lib/messages";

const STATUS_STYLE: Record<TargetStatus, { label: string; className: string }> = {
  success: { label: "成功", className: "text-emerald-600" },
  failed: { label: "失败", className: "text-red-600" },
  skipped: { label: "跳过", className: "text-zinc-500" },
  duplicate: { label: "今日已发", className: "text-zinc-500" },
  unknown: { label: "结果未知", className: "text-amber-600" },
};

export function StatusPanel() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [log, setLog] = useState<LogResponse | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(() => {
    api.status().then(setStatus, (err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 30_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function openLog(date: string) {
    if (!date) return setLog(null);
    try {
      setLog(await api.log(date));
    } catch (err) {
      setError(err instanceof Error ? err.message : "读取日志失败");
    }
  }

  if (!status) return <section className="card text-sm text-zinc-500">{error || "加载运行状态…"}</section>;
  const { last_run: run, history } = status;

  return (
    <section className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">任务状态</h2>
        <span className={`text-sm ${status.running ? "text-amber-600" : "text-zinc-500"}`}>
          {status.running ? "● 正在执行" : "空闲"}
        </span>
      </div>

      <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Stat label="最近执行" value={formatTime(run?.finished_at)} />
        <Stat label="累计运行" value={history ? `${history.total_runs} 次` : "—"} />
        <Stat label="全部成功" value={history ? `${history.total_successful_runs} 次` : "—"} />
        <Stat label="累计发送" value={history ? `${history.total_messages_sent} 条` : "—"} />
      </dl>

      {run && (
        <div className="space-y-1">
          <h3 className="text-sm font-medium">最近一次结果{run.dry_run && "（Dry Run）"}</h3>
          <p className="text-xs text-zinc-500">日志中好友按启用顺序显示为「好友01、好友02…」，不显示真实昵称；对应关系见下方好友卡片上的日志编号。</p>
          <ul className="divide-y divide-zinc-100 text-sm dark:divide-zinc-800">
            {run.results.map((r, i) => (
              <li key={i} className="flex flex-wrap gap-x-3 py-1.5">
                <span className="w-16">{r.target}</span>
                <span className={STATUS_STYLE[r.status].className}>{STATUS_STYLE[r.status].label}</span>
                <span className="text-zinc-500">发送 {r.sent} 条</span>
                {r.error && <span className="w-full text-red-600 sm:w-auto">原因：{r.error}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="space-y-2">
        <select aria-label="选择日志日期" className="input" defaultValue="" onChange={(e) => openLog(e.target.value)}>
          <option value="">查看每日运行日志…</option>
          {status.log_dates.map((d) => (
            <option key={d} value={d}>
              {formatLogDate(d)}
            </option>
          ))}
        </select>
        {log && (
          <pre className="max-h-96 overflow-auto rounded-lg bg-zinc-950 p-3 text-xs leading-relaxed text-zinc-100">
            {log.truncated && "……（仅显示最后 256KB）\n"}
            {log.content}
          </pre>
        )}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-zinc-50 p-2 dark:bg-zinc-800/50">
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="mt-0.5 font-medium">{value}</dd>
    </div>
  );
}
