"""
Loads and caches the hotel's JSON knowledge base, and provides simple
keyword-overlap retrieval over it.

Retrieval is intentionally NOT embeddings/vector search -- at this
data scale (a handful of FAQ/amenity/room/policy entries) a vector DB
would be over-engineering. Word-overlap scoring is transparent,
debuggable, and easy to defend in an interview.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "hotel_data.json"

_WORD_PATTERN = re.compile(r"[a-z0-9']+")

# Common words excluded from overlap scoring so that generic phrasing
# ("do you have a...", "is there...") doesn't create false-positive
# matches against unrelated knowledge base entries. Keeping this list
# small and explicit (vs. a stopword library) is easy to defend and
# tune in an interview.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "do", "does", "did",
    "have", "has", "had", "i", "you", "your", "we", "our", "it", "its",
    "this", "that", "these", "those", "of", "for", "to", "in", "on",
    "at", "and", "or", "with", "what", "when", "where", "which", "who",
    "how", "can", "could", "would", "will", "any", "there", "be",
}


@lru_cache
def get_hotel_data() -> dict:
    """
    Load hotel_data.json once and cache it in memory. Using lru_cache
    keeps this simple (no DB, no async I/O) while still avoiding
    re-reading the file on every request.
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize(word: str) -> str:
    """
    Very small, explicit singular/plural normalizer (not a full
    stemmer) so "policies" matches "policy", "rooms" matches "room",
    etc. Deliberately conservative -- only strips common plural
    endings, and only on words long enough that stripping won't
    mangle a short word.
    """
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def _words(text: str) -> set[str]:
    tokens = _WORD_PATTERN.findall(text.lower())
    return {_normalize(t) for t in tokens if t not in _STOPWORDS}


def _score(query_words: set[str], text: str, tags: list[str]) -> int:
    """
    Simple relevance score: count of overlapping (normalized) words
    between the query and the candidate text, plus a bonus for any
    tag whose normalized words overlap the query. Good enough for a
    knowledge base this size, and fully explainable (no black-box
    embedding similarity to defend).
    """
    overlap = len(query_words & _words(text))
    tag_bonus = sum(2 for tag in tags if _words(tag) & query_words)
    return overlap + tag_bonus


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """
    Returns up to top_k relevant knowledge base snippets as
    [{"text": ..., "source": ..., "score": ...}, ...], sorted by
    relevance, highest first. Returns an empty list if nothing in the
    knowledge base is relevant -- callers must treat an empty result
    as "we don't know this" and skip the LLM entirely rather than
    letting it improvise.
    """
    hotel_data = get_hotel_data()
    query_words = _words(query)
    candidates: list[dict] = []

    for entry in hotel_data["faq"]:
        text = f"{entry['question']} {entry['answer']}"
        score = _score(query_words, text, entry.get("tags", []))
        if score > 0:
            candidates.append({"text": entry["answer"], "source": entry["question"], "score": score})

    for amenity in hotel_data["amenities"]:
        text = f"{amenity['name']} {amenity['description']}"
        score = _score(query_words, text, [amenity["name"].lower()])
        if score > 0:
            candidates.append({"text": amenity["description"], "source": amenity["name"], "score": score})

    for room in hotel_data["rooms"]:
        text = (
            f"{room['name']} {room['bedConfig']} max {room['maxAdults']} adults "
            f"{' '.join(room['amenities'])}"
        )
        score = _score(query_words, text, [room["name"].lower()])
        if score > 0:
            candidates.append(
                {
                    "text": (
                        f"{room['name']}: {room['bedConfig']}, accommodates up to "
                        f"{room['maxAdults']} adults, {room['currency']} {room['pricePerNight']} "
                        f"per night. Amenities: {', '.join(room['amenities'])}."
                    ),
                    "source": room["name"],
                    "score": score,
                }
            )

    for key, value in hotel_data["policies"].items():
        # Every policy entry also carries a generic "policy" tag, so a
        # broad question ("what are the policies?") surfaces an
        # overview across all of them, not just whichever policy
        # happens to share a word with the query.
        score = _score(query_words, f"{key} {value}", [key, "policy"])
        if score > 0:
            candidates.append({"text": value, "source": key, "score": score})

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:top_k]
