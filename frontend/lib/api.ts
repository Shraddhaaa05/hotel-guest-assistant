import type {
  AvailabilityRequestPayload,
  AvailabilityResult,
  ChatApiResponse,
  ConversationTurn,
} from "@/types";

// The browser only ever talks to our own backend. No LLM API key or
// LLM endpoint exists anywhere in frontend code -- see README security
// section.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {}

async function extractErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    // Our global validation handler returns {message, type}; FastAPI's
    // default HTTPException shape returns {detail}. Handle both.
    return data?.message || data?.detail || fallback;
  } catch {
    return fallback;
  }
}

export async function sendChatMessage(
  message: string,
  conversation: ConversationTurn[]
): Promise<ChatApiResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation }),
    });
  } catch {
    throw new ApiError(
      "I couldn't reach the assistant service. Please check your connection and try again."
    );
  }

  if (!res.ok) {
    throw new ApiError(
      await extractErrorMessage(res, "I'm having trouble processing that right now. Please try again.")
    );
  }

  return res.json();
}

export async function fetchAvailability(
  payload: AvailabilityRequestPayload
): Promise<AvailabilityResult> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/availability`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(
      "I couldn't reach the availability service. Please check your connection and try again."
    );
  }

  if (!res.ok) {
    throw new ApiError(
      await extractErrorMessage(res, "I couldn't check room availability right now. Please try again in a moment.")
    );
  }

  return res.json();
}
