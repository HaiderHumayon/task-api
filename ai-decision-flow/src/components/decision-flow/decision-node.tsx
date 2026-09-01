"use client";

import {
  Handle,
  Position,
  type NodeProps,
} from "@xyflow/react";
import { Bot, GripVertical } from "lucide-react";

import type { DecisionFlowNode } from "./types";

export function DecisionNode({
  id,
  data,
  selected,
}: NodeProps<DecisionFlowNode>) {
  return (
    <article
      className={[
        "w-[310px] overflow-hidden rounded-2xl border bg-slate-950/95 shadow-2xl transition",
        selected
          ? "border-sky-400 ring-2 ring-sky-400/20"
          : "border-slate-700",
      ].join(" ")}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-3 !w-3 !border-2 !border-slate-950 !bg-sky-400"
      />

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

      <div className="p-4">
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
          placeholder="Ask a question the AI can eventually answer YES or NO..."
        />

        <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
          <span>{data.prompt.length} characters</span>
          <span>Editable</span>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-3 !w-3 !border-2 !border-slate-950 !bg-violet-400"
      />
    </article>
  );
}