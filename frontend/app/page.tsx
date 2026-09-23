import ChatWindow from "@/components/ChatWindow";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-teal px-4 py-8 sm:py-12">
      <div className="w-full max-w-2xl">
        <header className="mb-4 px-2 text-center sm:mb-6">
          <h1 className="font-serif text-3xl text-ivory sm:text-4xl">Grand Horizon Hotel</h1>
          <p className="mt-1 text-sm text-ivory/60">Guest Assistant &middot; here whenever you need us</p>
        </header>

        <div className="flex h-[75vh] min-h-[520px] flex-col overflow-hidden rounded-2xl bg-ivory shadow-[0_20px_60px_rgba(0,0,0,0.25)] sm:h-[70vh]">
          <ChatWindow />
        </div>

        <p className="mt-4 px-2 text-center text-xs text-ivory/40">
          Answers are grounded in our hotel information. For anything else, our front desk is always happy to help.
        </p>
      </div>
    </main>
  );
}
