"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, fetchAvailability, sendChatMessage } from "@/lib/api";
import type {
  AvailabilityRequestPayload,
  ChatMessage,
  ConversationTurn,
} from "@/types";
import MessageBubble from "./MessageBubble";
import SuggestedQuestions from "./SuggestedQuestions";
import AvailabilityForm from "./AvailabilityForm";

const SUGGESTED_QUESTIONS = [
  "What time is check-in?",
  "Does the hotel have a pool?",
  "Which room fits 4 guests?",
  "Is breakfast included?",
  "What is the cancellation policy?",
];

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAvailabilityForm, setShowAvailabilityForm] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const requestInFlightRef = useRef(false);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  function buildConversationHistory(): ConversationTurn[] {
    return messages
      .filter((m) => !m.isError)
      .map((m) => ({ role: m.role, content: m.content }));
  }

  async function handleSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || requestInFlightRef.current) return;

    requestInFlightRef.current = true;
    const history = buildConversationHistory();
    const userMessage: ChatMessage = { id: newId(), role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChatMessage(trimmed, history);
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          content: response.message,
          type: response.type,
          availability: response.availability,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", content: message, isError: true },
      ]);
    } finally {
      requestInFlightRef.current = false;
      setLoading(false);
    }
  }

  async function handleAvailabilitySubmit(payload: AvailabilityRequestPayload) {
    if (requestInFlightRef.current) return;
    requestInFlightRef.current = true;
    setLoading(true);
    setShowAvailabilityForm(false);

    const summary = `Check availability: ${payload.checkIn} to ${payload.checkOut}, ${payload.adults} guest(s)`;
    setMessages((prev) => [...prev, { id: newId(), role: "user", content: summary }]);

    try {
      const result = await fetchAvailability(payload);
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          content: result.message,
          type: "availability",
          availability: result,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "I couldn't check room availability right now. Please try again in a moment.";
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", content: message, isError: true },
      ]);
    } finally {
      requestInFlightRef.current = false;
      setLoading(false);
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="chat-scroll flex-1 space-y-4 overflow-y-auto px-4 py-6 sm:px-6">
        {!hasMessages && (
          <div className="mx-auto max-w-md space-y-5 py-6 text-center">
            <p className="font-serif text-xl italic text-teal-dark">
              Welcome to Grand Horizon. How can I help with your stay?
            </p>
            <p className="text-sm text-ink/60">
              Ask about rooms, amenities, or policies — or check room availability for your
              dates.
            </p>
            <SuggestedQuestions questions={SUGGESTED_QUESTIONS} onSelect={handleSend} />
            <button
              type="button"
              onClick={() => setShowAvailabilityForm(true)}
              className="mx-auto block text-sm font-medium text-brass-dark underline decoration-brass/40 underline-offset-4 hover:decoration-brass"
            >
              Check room availability
            </button>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm border border-teal/10 bg-white px-4 py-3">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal/40 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal/40 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal/40" />
            </div>
          </div>
        )}

        {showAvailabilityForm && (
          <AvailabilityForm
            onSubmit={handleAvailabilitySubmit}
            onCancel={() => setShowAvailabilityForm(false)}
            loading={loading}
          />
        )}
      </div>

      {hasMessages && !showAvailabilityForm && (
        <div className="border-t border-teal/8 px-4 py-3 sm:px-6">
          <button
            type="button"
            onClick={() => setShowAvailabilityForm(true)}
            className="mb-2 text-xs font-medium text-brass-dark underline decoration-brass/40 underline-offset-4 hover:decoration-brass"
          >
            Check room availability
          </button>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(input);
        }}
        className="flex items-center gap-2 border-t border-teal/10 bg-white/60 px-4 py-3 sm:px-6"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about rooms, amenities, policies…"
          disabled={loading}
          className="flex-1 rounded-full border border-teal/15 bg-white px-4 py-2.5 text-sm text-ink
                     placeholder:text-ink/40 focus-visible:outline focus-visible:outline-2
                     focus-visible:outline-offset-2 focus-visible:outline-brass disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="shrink-0 rounded-full bg-brass px-5 py-2.5 text-sm font-medium text-ivory
                     transition-colors hover:bg-brass-dark disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
