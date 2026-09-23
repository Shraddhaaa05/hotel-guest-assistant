// Mirrors backend/app/models/schemas.py — keep these two in sync.

export type MessageRole = "user" | "assistant";

export interface ConversationTurn {
  role: MessageRole;
  content: string;
}

export type ChatResponseType = "knowledge" | "availability" | "fallback" | "error";

export interface RoomAvailability {
  id: string;
  name: string;
  bedConfig: string;
  capacity: number;
  pricePerNight: number;
  currency: string;
  amenities: string[];
}

export interface AvailabilityResult {
  available: boolean;
  checkIn: string;
  checkOut: string;
  guests: number;
  nights: number;
  rooms: RoomAvailability[];
  message: string;
}

export interface ChatApiResponse {
  message: string;
  type: ChatResponseType;
  sources: string[];
  availability: AvailabilityResult | null;
}

export interface AvailabilityRequestPayload {
  checkIn: string;
  checkOut: string;
  adults: number;
}

// Frontend-only chat message model, layered on top of the API response
// so the UI can render loading/error states that the backend never sees.
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  type?: ChatResponseType;
  availability?: AvailabilityResult | null;
  isError?: boolean;
}
