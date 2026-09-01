"use client";

import {
  Handle,
  Position,
  type NodeProps,
} from "@xyflow/react";
import {
  Bot,
  Check,
  GripVertical,
  X,
} from "lucide-react";

import type { DecisionFlowNode } from "./types";

export function DecisionNode({
  id,
  data,
  selected,
}: NodeProps<DecisionFlowNode>) {
  return (
    <article
      className={[
        "relative w-[310px] overflow-visible rounded-2xl border bg-slate-950/95 shadow-2xl transition",
        selected
          ? "border-sky-400 ring-2 ring-sky-400/20"
          : "border-slate-700",
      ].join(" ")}
    >
      <Handle
        id="input"
        type="target"
        position={Position.Top}
        className="!h-3 !w-3 !border-2 !border-slate-950 !bg-sky-400"
      />

      <div className="overflow-hidden rounded-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-sky-400/10 text-sky-300">
              <Bot size={18} />
            </span>

            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">
                Decision
              </p>
              <h3 className="truncate text-sm font-semibold text-white">
                {data.title}
              </h3>
            </div>
          </div>

          <GripVertical
            size={18}
            className="shrink-0 text-slate-600"
            aria-hidden="true"
          />
        </div>

        <div className="p-4 pb-7">
          <label
            htmlFor={`prompt-${id}`}
            className="mb-2 block text-xs font-medium text-slate-400"
          >
            Prompt
          </label>

          <textarea
            id={`prompt-${id}`}
            value={data.prompt}
            onChange={(event) => {
              data.onPromptChange?.(id, event.target.value);
            }}
            onPointerDown={(event) => {
              event.stopPropagation();
            }}
            rows={5}
            spellCheck={false}
            className="nodrag nowheel w-full resize-none rounded-xl border border-slate-800 bg-slate-900 px-3 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-sky-500"
            placeholder="Ask a question the AI must answer YES or NO..."
          />

          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
            <span>{data.prompt.length} characters</span>
            <span>Strict YES / NO</span>
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 -bottom-5 flex justify-around px-8">
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-slate-950 px-2 py-1 text-[10px] font-bold tracking-[0.12em] text-emerald-300">
          <Check size={11} />
          YES
        </span>

        <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/30 bg-slate-950 px-2 py-1 text-[10px] font-bold tracking-[0.12em] text-rose-300">
          <X size={11} />
          NO
        </span>
      </div>

      <Handle
        id="yes"
        type="source"
        position={Position.Bottom}
        style={{
          left: "34%",
        }}
        className="!h-4 !w-4 !border-2 !border-slate-950 !bg-emerald-400"
      />

      <Handle
        id="no"
        type="source"
        position={Position.Bottom}
        style={{
          left: "66%",
        }}
        className="!h-4 !w-4 !border-2 !border-slate-950 !bg-rose-400"
      />
    </article>
  );
}