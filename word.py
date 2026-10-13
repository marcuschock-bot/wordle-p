import os
import random
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

FALLBACK_WORDS = [
    "apple", "beach", "chair", "dance", "eagle",
    "flame", "grape", "house", "juice", "knife",
    "lemon", "music", "ocean", "plant", "queen",
    "river", "smile", "tiger", "water", "zebra"
]

def get_ai_word(used_words):
    avoid_clause = ""
    if used_words:
        avoid_clause = f" Do not choose any of these previously used words: {', '.join(sorted(used_words))}."

    prompt = (
        "Generate a random, creative English word for a word guessing game "
        "(ONLY 5 letters long)."
        f"{avoid_clause} "
        "Return ONLY the word itself in lowercase, with no extra text, spaces or punctuation."
    )

    for _ in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            candidate = response.text.strip().lower()
            if candidate.isalpha() and len(candidate) == 5 and candidate not in used_words:
                return candidate
        except Exception as e:
            print(f"Error generating word from AI: {e}")
            break

    # Fallback to an unused pre-defined word if AI repeats or fails
    available_fallbacks = [w for w in FALLBACK_WORDS if w not in used_words]
    if available_fallbacks:
        return random.choice(available_fallbacks)
    return "python"


def play_round(secret_word):
    board_history = []
    max_attempts = 6

    while len(board_history) < max_attempts:
        print("\n--- BOARD ---")
        for row in board_history:
            print(format_row(row))

        guess = input(f"\nAttempt {len(board_history) + 1}/{max_attempts}: ").strip().lower()

        if len(guess) != 5:
            print("Guess must be exactly 5 letters!")
            continue

        feedback = evaluate_guess(guess, secret_word)
        board_history.append(feedback)

        if guess == secret_word:
            print("\n🎉 You solved the Wordle!")
            return True

    print(f"\nGame over! The word was: {secret_word}")
    return False


def evaluate_guess(guess: str, secret: str) -> list[tuple[str, str]]:
    """
    Returns a list of tuples: (letter, color)
    where color is 'GREEN', 'YELLOW', or 'GRAY'.
    """
    result = ["GRAY"] * len(secret)
    secret_letters = list(secret)

    # Pass 1: Mark all GREENs (exact position matches)
    for i in range(len(secret)):
        if guess[i] == secret[i]:
            result[i] = "GREEN"
            secret_letters[i] = None  # Consume the letter so it isn't used for YELLOW

    # Pass 2: Mark YELLOWs (present in word, wrong position)
    for i in range(len(secret)):
        if result[i] != "GREEN" and guess[i] in secret_letters:
            result[i] = "YELLOW"
            secret_letters[secret_letters.index(guess[i])] = None

    return list(zip(guess.upper(), result))

TILE_EMOJIS = {
    "GREEN": "🟩",
    "YELLOW": "🟨",
    "GRAY": "⬛"
}

def format_row(feedback):
    letters = " ".join(letter for letter, _ in feedback)
    tiles = "".join(TILE_EMOJIS[color] for _, color in feedback)
    return f"{letters}\n{tiles}"

def main():
    used_words = set()
    print("\nWelcome to the AI-Powered Word Guessing Game!")

    while True:
        print("\nAI is selecting a new word...")
        word = get_ai_word(used_words)
        used_words.add(word)

        play_round(word)

        # Play again or exit prompt
        while True:
            choice = input("\nDo you want to play again? (play/exit): ").strip().lower()
            if choice in ["play", "p", "yes", "y"]:
                break
            elif choice in ["exit", "e", "no", "n", "quit", "q"]:
                print("Thanks for playing! Goodbye!\n")
                return
            else:
                print("Invalid option. Please enter 'play' to play again or 'exit' to quit.")

            


if __name__ == "__main__":
    main()