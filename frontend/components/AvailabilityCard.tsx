import type { AvailabilityResult } from "@/types";

function formatDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function AvailabilityCard({ result }: { result: AvailabilityResult }) {
  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-teal/12 bg-white">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-b border-teal/10 bg-teal/[0.03] px-4 py-3">
        <p className="text-sm text-ink/70">
          {formatDate(result.checkIn)} &rarr; {formatDate(result.checkOut)} &middot; {result.nights}{" "}
          {result.nights === 1 ? "night" : "nights"} &middot; {result.guests}{" "}
          {result.guests === 1 ? "guest" : "guests"}
        </p>
      </div>

      {result.rooms.length === 0 ? (
        <p className="px-4 py-4 text-sm text-ink/70">
          No rooms match those dates and party size. Try a different date range or fewer guests.
        </p>
      ) : (
        <ul>
          {result.rooms.map((room, idx) => (
            <li
              key={room.id}
              className={`flex items-center justify-between gap-4 px-4 py-3 ${
                idx !== result.rooms.length - 1 ? "border-b border-teal/8" : ""
              }`}
            >
              <div>
                <p className="font-medium text-ink">{room.name}</p>
                <p className="text-sm text-ink/60">
                  {room.bedConfig} &middot; up to {room.capacity} guests
                </p>
              </div>
              <div className="shrink-0 text-right">
                <p className="font-medium text-brass-dark">
                  {room.currency === "INR" ? "₹" : room.currency}
                  {room.pricePerNight.toLocaleString("en-IN")}
                </p>
                <p className="text-xs text-ink/50">per night</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
