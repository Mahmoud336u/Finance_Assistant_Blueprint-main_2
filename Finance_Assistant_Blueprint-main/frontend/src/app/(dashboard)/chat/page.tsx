"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Sparkles,
  Copy,
  RotateCcw,
  Check,
  StopCircle,
  ChevronRight,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";
import { useChatStore } from "@/lib/store/chat-store";
import type { ChatMessage } from "@/lib/types";

const SUGGESTIONS = [
  "Where did my money go last month?",
  "Help me optimize my budget",
  "Analyze my subscription spending",
  "What are my biggest expenses?",
  "Create a savings plan for me",
  "Compare my spending to last month",
];

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const {
    messages,
    isStreaming,
    activeConversationId,
    addMessage,
    updateMessage,
    setStreaming,
    startNewConversation,
  } = useChatStore();

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async (text?: string) => {
    const message = text || input.trim();
    if (!message || isStreaming) return;

    setInput("");
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }

    // Add user message
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };
    addMessage(userMsg);

    // Add placeholder assistant message
    const assistantId = `msg-${Date.now() + 1}`;
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      is_streaming: true,
    };
    addMessage(assistantMsg);
    setStreaming(true);

    try {
      let fullContent = "";

      for await (const event of api.streamChat({
        message,
        conversation_id: activeConversationId || undefined,
        stream: true,
      })) {
        if (event.type === "delta") {
          fullContent += event.text;
          updateMessage(assistantId, {
            content: fullContent,
            is_streaming: true,
          });
        } else if (event.type === "metadata") {
          updateMessage(assistantId, {
            content: fullContent,
            is_streaming: false,
            model: "claude-3.5-sonnet",
            provider: "bedrock",
            prompt_tokens: event.data.prompt_tokens,
            completion_tokens: event.data.completion_tokens,
            rag_chunks_used: event.data.rag_chunks_used,
          });
          if (!activeConversationId && event.data.conversation_id) {
            useChatStore
              .getState()
              .setActiveConversation(event.data.conversation_id);
          }
        } else if (event.type === "done") {
          updateMessage(assistantId, { is_streaming: false });
        } else if (event.type === "error") {
          updateMessage(assistantId, {
            content: "Sorry, an error occurred. Please try again.",
            is_streaming: false,
            error: event.message,
          });
        }
      }
    } catch (err) {
      updateMessage(assistantId, {
        content:
          "Unable to connect to the AI service. Please check that the backend is running.",
        is_streaming: false,
        error: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setStreaming(false);
    }
  };

  const handleCopy = async (content: string, id: string) => {
    await navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      {/* Empty state */}
      {isEmpty ? (
        <div className="flex flex-1 flex-col items-center justify-center px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col items-center"
          >
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 glow-primary">
              <Sparkles className="h-8 w-8 text-primary" />
            </div>
            <h1 className="mb-2 text-2xl font-semibold">
              How can I help you today?
            </h1>
            <p className="mb-8 max-w-md text-center text-sm text-foreground-muted">
              Ask me about your spending, budgets, financial goals, or anything
              else related to your finances.
            </p>

            {/* Suggestions grid */}
            <div className="grid max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((suggestion, i) => (
                <motion.button
                  key={suggestion}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.3,
                    delay: 0.1 + i * 0.05,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  onClick={() => handleSend(suggestion)}
                  className={cn(
                    "flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3",
                    "text-left text-sm text-foreground-muted transition-all",
                    "hover:border-primary/30 hover:bg-surface-hover hover:text-foreground",
                  )}
                >
                  <ChevronRight className="h-3.5 w-3.5 shrink-0 text-primary" />
                  {suggestion}
                </motion.button>
              ))}
            </div>
          </motion.div>
        </div>
      ) : (
        /* Messages */
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <div className="mx-auto max-w-3xl space-y-6">
            <AnimatePresence initial={false}>
              {messages.map((msg, i) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.3,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  className={cn(
                    "flex",
                    msg.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  {msg.role === "user" ? (
                    /* User message */
                    <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-primary px-4 py-3 text-sm text-primary-foreground">
                      {msg.content}
                    </div>
                  ) : (
                    /* Assistant message */
                    <div className="max-w-[85%] space-y-2">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/10">
                          <Sparkles className="h-3 w-3 text-primary" />
                        </div>
                        <span className="text-xs font-medium text-foreground-muted">
                          Meridian
                        </span>
                        {msg.is_streaming && (
                          <span className="flex items-center gap-1">
                            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-primary" />
                            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-primary" />
                            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-primary" />
                          </span>
                        )}
                      </div>
                      <div
                        className={cn(
                          "prose prose-sm prose-invert max-w-none",
                          "prose-p:text-foreground-muted prose-p:leading-relaxed",
                          "prose-strong:text-foreground prose-strong:font-semibold",
                          "prose-code:rounded prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:text-xs prose-code:font-[var(--font-mono)]",
                          "prose-pre:rounded-xl prose-pre:border prose-pre:border-border prose-pre:bg-background",
                          "prose-headings:text-foreground prose-headings:font-semibold",
                          "prose-li:text-foreground-muted",
                          "prose-a:text-primary prose-a:no-underline hover:prose-a:underline",
                          msg.error && "text-destructive",
                        )}
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content || " "}
                        </ReactMarkdown>
                      </div>
                      {/* Actions */}
                      {!msg.is_streaming && msg.content && (
                        <div className="flex items-center gap-1 pt-1">
                          <button
                            onClick={() => handleCopy(msg.content, msg.id)}
                            className="flex h-7 items-center gap-1 rounded-md px-2 text-xs text-foreground-subtle hover:bg-surface-hover hover:text-foreground transition-colors"
                          >
                            {copiedId === msg.id ? (
                              <Check className="h-3 w-3 text-success" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                            {copiedId === msg.id ? "Copied" : "Copy"}
                          </button>
                          {msg.prompt_tokens && (
                            <span className="ml-2 text-[10px] text-foreground-subtle tabular-nums">
                              {msg.prompt_tokens + (msg.completion_tokens || 0)}{" "}
                              tokens
                              {msg.latency_ms
                                ? ` · ${(msg.latency_ms / 1000).toFixed(1)}s`
                                : ""}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border bg-background/80 px-4 py-4 backdrop-blur-xl">
        <div className="mx-auto max-w-3xl">
          <div
            className={cn(
              "flex items-end gap-2 rounded-2xl border border-border bg-card p-2",
              "focus-within:border-primary/40 focus-within:ring-1 focus-within:ring-primary/20",
              "transition-all duration-200",
            )}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your finances..."
              rows={1}
              className={cn(
                "flex-1 resize-none bg-transparent px-3 py-2.5 text-sm",
                "placeholder:text-foreground-subtle",
                "focus:outline-none",
                "max-h-[200px]",
              )}
            />
            <button
              onClick={() => (isStreaming ? null : handleSend())}
              disabled={(!input.trim() && !isStreaming)}
              className={cn(
                "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
                "transition-all duration-150",
                isStreaming
                  ? "bg-destructive text-white hover:bg-destructive/80"
                  : input.trim()
                    ? "bg-primary text-primary-foreground hover:bg-primary-hover"
                    : "bg-muted text-foreground-subtle cursor-not-allowed",
              )}
            >
              {isStreaming ? (
                <StopCircle className="h-4 w-4" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>
          <p className="mt-2 text-center text-[10px] text-foreground-subtle">
            Meridian can make mistakes. Always verify financial information.
          </p>
        </div>
      </div>
    </div>
  );
}
