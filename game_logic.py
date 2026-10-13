import os
import random

from dotenv import load_dotenv
from google import genai
from spellchecker import SpellChecker

load_dotenv()

WORD_LENGTH = 5
MAX_ATTEMPTS = 6

FALLBACK_WORDS = [
    "apple", "beach", "chair", "dance", "eagle",
    "flame", "grape", "house", "juice", "knife",
    "lemon", "music", "ocean", "plant", "queen",
    "river", "smile", "tiger", "water", "zebra",
]

# Loading the dictionary is slow-ish, so do it once at import time.
spell = SpellChecker()

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    return _client


# ---------- Spell checking ----------

def is_real_word(word: str) -> bool:
    """True if `word` is a 5-letter alphabetic word in the spellchecker dictionary."""
    word = word.strip().lower()
    return len(word) == WORD_LENGTH and word.isalpha() and word in spell


def suggest_words(word: str, limit: int = 3) -> list[str]:
    """Return up to `limit` valid 5-letter suggestions for a misspelled guess."""
    candidates = spell.candidates(word.lower()) or set()
    return sorted(c for c in candidates if len(c) == WORD_LENGTH)[:limit]


def validate_guess(guess: str) -> str | None:
    """Return an error message if the guess is invalid, else None."""
    guess = guess.strip().lower()
    if len(guess) != WORD_LENGTH:
        return f"Guess must be exactly {WORD_LENGTH} letters!"
    if not guess.isalpha():
        return "Guess must contain letters only!"
    if not is_real_word(guess):
        suggestions = suggest_words(guess)
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        return f"'{guess.upper()}' isn't in the dictionary.{hint}"
    return None


# ---------- Word generation ----------

def get_ai_word(used_words: set[str]) -> str:
    avoid_clause = ""
    if used_words:
        avoid_clause = (
            " Do not choose any of these previously used words: "
            f"{', '.join(sorted(used_words))}."
        )

    prompt = (
        "Generate a random, creative English word for a word guessing game "
        f"(ONLY {WORD_LENGTH} letters long)."
        f"{avoid_clause} "
        "Return ONLY the word itself in lowercase, with no extra text, spaces or punctuation."
    )

    for _ in range(3):
        try:
            response = _get_client().models.generate_content(
                model="gemini-3.8-flash",  # double-check this model name
                contents=prompt,
            )
            candidate = response.text.strip().lower()
            # Also require the word to pass the spellchecker so players can always guess it
            if (
                candidate.isalpha()
                and len(candidate) == WORD_LENGTH
                and candidate not in used_words
                and is_real_word(candidate)
            ):
                return candidate
        except Exception as e:
            print(f"Error generating word from AI: {e}")
            break

    available = [w for w in FALLBACK_WORDS if w not in used_words]
    return random.choice(available) if available else random.choice(FALLBACK_WORDS)


# ---------- Scoring ----------

def evaluate_guess(guess: str, secret: str) -> list[tuple[str, str]]:
    """Returns [(letter, 'GREEN' | 'YELLOW' | 'GRAY'), ...]."""
    result = ["GRAY"] * len(secret)
    secret_letters = list(secret)

    for i in range(len(secret)):
        if guess[i] == secret[i]:
            result[i] = "GREEN"
            secret_letters[i] = None

    for i in range(len(secret)):
        if result[i] != "GREEN" and guess[i] in secret_letters:
            result[i] = "YELLOW"
            secret_letters[secret_letters.index(guess[i])] = None

    return list(zip(guess.upper(), result))
