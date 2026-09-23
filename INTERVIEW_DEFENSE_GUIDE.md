# Interview Defense Guide

Everything below is written the way I'd actually say it out loud — plain,
short sentences, no jargon for its own sake.

## 1. 30-Second Project Explanation

"I built a chat assistant for a hotel's website. Guests can ask questions
about rooms, amenities, and policies, and check room availability — all in
one conversation. The key design decision is that the AI only answers
questions using facts from the hotel's own data; it never invents prices,
policies, or room availability. Availability is calculated by a separate,
plain Python function that has nothing to do with the AI at all."

## 2. 2-Minute Architecture Explanation

"There are two apps: a Next.js frontend and a FastAPI backend. The browser
only ever talks to my backend — never directly to an LLM, so no API key is
ever exposed to the client.

When a message comes in, the backend first classifies the *intent* —
is this an availability question or a knowledge question? That's done with
simple keyword and date-pattern matching, not AI, because I want that
routing decision to be 100% predictable and testable.

If it's an availability question, I call a deterministic function —
`checkAvailability()` — that filters rooms by capacity and a mock inventory
rule, and returns structured JSON. No AI involved.

If it's a knowledge question, I search a small JSON knowledge base for
relevant facts using keyword overlap. If nothing relevant is found, I return
a fixed 'I don't know' message immediately — I don't even call the AI. If
something relevant *is* found, I pass just those facts to the AI provider
and ask it to answer using only those facts. That's either a lightweight
mock generator that just returns the facts directly, or a real LLM call to
Groq if a key is configured."

## 3. Why FastAPI?

"It gives me request validation, JSON serialization, and API docs for free
through Pydantic, it's async-capable if I need to scale later, and it's
fast to write clean, typed endpoints without much boilerplate — a good fit
for a project this size."

## 4. Why React/Next.js?

"Next.js's App Router gives me a sensible project structure out of the box,
first-class TypeScript support, and I can share types conceptually with the
backend's Pydantic models so the contract between frontend and backend
stays consistent."

## 5. Why Use an LLM at All?

"Because guest questions are open-ended and phrased in natural language —
'is breakfast included' vs 'do you serve food in the morning' should get
the same answer. A rules engine would need to anticipate every phrasing. An
LLM, grounded in the actual facts, can handle that variation without me
hand-writing hundreds of if-statements."

## 6. Why Not Let the LLM Determine Availability?

"Availability is a factual, business-critical answer — guests could act on
it. LLMs can be wrong or inconsistent, and I never want a guest told a room
is available when it isn't. So availability is calculated by plain,
testable, deterministic code, completely outside the AI's control. The
LLM's job is limited to natural-language understanding of open-ended
questions, not making business decisions."

## 7. How Hallucinations Are Prevented

"Three layers: First, retrieval happens before generation — I search the
knowledge base for relevant facts, and if nothing relevant comes back, I
return a fixed fallback message and skip the AI call entirely. Second, when
I do call the AI, the system prompt explicitly restricts it to only the
facts I retrieved and tells it to say 'I don't know' rather than guess.
Third, the mock provider — which is what runs by default with no API key —
literally just returns the retrieved text, so it's structurally incapable
of inventing anything. I also have a specific test for this: asking about
something totally absent from the knowledge base, like a helicopter pad,
and confirming it falls back instead of guessing."

## 8. How Conversation Context Works

"The frontend keeps the full message history in React state and sends it
with every request — the backend itself is stateless, which keeps things
simple. For follow-up questions like 'what are its timings?', I check if
the message uses a pronoun and, if so, fold the guest's previous message
into the search query before retrieval — so 'its' effectively gets resolved
to whatever the previous question was about. That's a deliberate, rule-based
choice, not something I leave to the AI to guess at."

## 9. How Errors Are Handled

"Every failure mode has a specific, honest message — invalid dates, AI
provider down, availability service failing, or a totally unexpected
server error. Nothing ever shows the guest a raw stack trace; I have a
global exception handler in FastAPI that catches anything unhandled and
returns a clean, generic error instead. On the frontend, network failures
and API errors are caught and shown as a distinct error-styled chat
bubble, and the input box is always re-enabled afterward so the guest isn't
stuck."

## 10. How the System Could Scale

"Right now the backend is stateless and the knowledge base is loaded into
memory once at startup, so I could run multiple backend instances behind a
load balancer with no changes. The two things that would need to change for
real scale: move conversation history server-side (e.g. Redis) if I want it
to survive page reloads or work across devices, and swap keyword-overlap
retrieval for an embeddings-based search if the knowledge base grew from a
dozen entries to hundreds."

## 11. How I Would Productionize It

"Add a real reservations database instead of the mock inventory rule, add
authentication if guests need personalized bookings, add response
streaming for a snappier feel on AI-generated answers, add proper
structured logging and metrics, add rate limiting on the public endpoints,
and round out the test suite with frontend component tests."

## 12. Possible Interviewer Questions and Strong Simple Answers

**"What happens if the Groq API is down?"**
"The provider raises a specific error type, `AIProviderError`, which the
chat service catches and turns into a fixed 'I'm having trouble processing
that right now' message. I actually test this — I have a test that
monkeypatches the provider to throw, and confirms the guest still gets a
clean response, not a 500 error."

**"Why JSON instead of a real database for the knowledge base?"**
"At this scale — a handful of FAQ entries, four room types, a few
policies — a database would add setup complexity with no real benefit. If
the knowledge base grew to hundreds of entries or needed concurrent writes,
I'd move it to a proper database."

**"How do you know your intent classifier is reliable?"**
"It's simple by design — keyword and date-pattern matching — so its
behavior is fully predictable, and I have unit tests covering both
directions: explicit availability language routes to the availability
tool, plain FAQ-style questions route to knowledge retrieval."

**"What's the biggest weakness of this design?"**
"The keyword-overlap retrieval. It works well for a small, curated
knowledge base, but it would start missing relevant matches if the data
grew large or the phrasing got more indirect. Embeddings-based retrieval
would fix that, and I called it out explicitly as a production
improvement rather than pretending the current approach scales
indefinitely."

**"Why is availability inventory a hash instead of real bookings?"**
"Because this is a demo without a real reservations system behind it. I
needed availability to look and behave realistically — different rooms
booked on different dates — without building a full booking engine, which
would be out of scope for this assignment. It's documented directly in the
code as a mock, not hidden."
