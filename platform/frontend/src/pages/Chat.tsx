import { RotateCcw, Send, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import { AgentBadge } from "../components/AgentBadge";
import { TypingIndicator } from "../components/TypingIndicator";
import type { ChatMessage, ChatResponse } from "../types";

const SUGGESTIONS = [
  "Why was TXN-000123 flagged?",
  "What time patterns exist in flagged transactions?",
  "Find cases similar to TXN-000123",
  "Give me a summary of high-risk activity",
];

const HISTORY_KEY = "dazai-chat-history";

function loadHistory(): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(HISTORY_KEY);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    sessionStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (question: string) => {
    if (!question.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const response = await api.post<ChatResponse>("/chat", { question });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: response.answer,
          sources: response.sources,
          intent: response.intent,
          agent: response.agent,
          ok: response.ok,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Couldn't reach the server. Check your connection and try again.", failed: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const retry = () => {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser) send(lastUser.text);
  };

  const clearHistory = () => {
    setMessages([]);
    sessionStorage.removeItem(HISTORY_KEY);
  };

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              disabled={loading}
              className="rounded-full bg-white/[0.03] px-3 py-1 text-xs text-slate-400 ring-1 ring-inset ring-white/[0.06] hover:text-slate-200 disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            className="flex shrink-0 items-center gap-1 text-xs text-slate-500 hover:text-slate-300"
          >
            <Trash2 size={13} /> Clear
          </button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-white/[0.06] bg-ink-900 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Ask about a specific alert, a pattern, similar cases, or a summary.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex flex-col items-start gap-1"}>
            <div
              className={`inline-block max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-accent-600 text-white"
                  : m.failed
                    ? "bg-red-500/10 text-red-300 ring-1 ring-inset ring-red-500/20"
                    : m.ok === false
                      ? "bg-amber-500/10 text-amber-200 ring-1 ring-inset ring-amber-500/20"
                      : "bg-ink-800 text-slate-200"
              }`}
            >
              <p className="whitespace-pre-line">{m.text}</p>
              {m.failed && (
                <button
                  onClick={retry}
                  className="mt-2 flex items-center gap-1 text-xs font-medium text-red-300 hover:text-red-200"
                >
                  <RotateCcw size={12} /> Retry
                </button>
              )}
            </div>
            {m.role === "assistant" && m.agent && (
              <div className="flex flex-wrap items-center gap-1.5 px-1">
                <AgentBadge agent={m.agent} />
                {m.sources?.map((s) => (
                  <span key={s} className="pill bg-white/[0.03] text-slate-500 ring-white/[0.06]">
                    based on: {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          placeholder="Ask a question..."
          className="flex-1 rounded-xl border border-white/[0.08] bg-ink-900 px-3 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-accent-600/50 focus:outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex items-center gap-1.5 rounded-xl bg-accent-600 px-4 py-2.5 text-sm font-medium text-white shadow-glow hover:bg-accent-500 disabled:opacity-40"
        >
          <Send size={14} /> Send
        </button>
      </form>
    </div>
  );
}
