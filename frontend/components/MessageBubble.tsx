import type { ChatMessage } from "@/types";
import AvailabilityCard from "./AvailabilityCard";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex animate-rise-in justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-teal px-4 py-2.5 text-sm text-ivory sm:max-w-[70%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex animate-rise-in justify-start">
      <div className="max-w-[85%] sm:max-w-[75%]">
        <div
          className={`rounded-2xl rounded-bl-sm border px-4 py-2.5 text-sm ${
            message.isError
              ? "border-rust/25 bg-rust/5 text-rust"
              : "border-teal/10 bg-white text-ink"
          }`}
        >
          {message.content}
        </div>
        {message.availability && <AvailabilityCard result={message.availability} />}
      </div>
    </div>
  );
}
