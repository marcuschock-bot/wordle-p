import os
import streamlit as st

# Make the key from Streamlit secrets available before game_logic builds its client
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass  # no secrets file; fall back to .env / environment

from game_logic import (  # noqa: E402
    MAX_ATTEMPTS,
    WORD_LENGTH,
    evaluate_guess,
    get_ai_word,
    validate_guess,
)

st.set_page_config(page_title="AI Word Guessing Game", page_icon="🟩")

COLORS = {"GREEN": "#538d4e", "YELLOW": "#b59f3b", "GRAY": "#3a3a3c"}


def new_round():
    word = get_ai_word(st.session_state.used_words)
    st.session_state.used_words.add(word)
    st.session_state.secret = word
    st.session_state.board = []
    st.session_state.status = "playing"  # playing | won | lost
    st.session_state.message = ""


def render_tile(letter: str, color: str) -> str:
    return (
        f"<div style='width:52px;height:52px;display:flex;align-items:center;"
        f"justify-content:center;background:{color};color:white;font-weight:700;"
        f"font-size:26px;border-radius:4px;'>{letter}</div>"
    )


def render_row(cells) -> str:
    tiles = "".join(render_tile(ch, COLORS[c]) for ch, c in cells)
    return f"<div style='display:flex;gap:6px;margin-bottom:6px;'>{tiles}</div>"


def render_empty_row() -> str:
    tile = (
        "<div style='width:52px;height:52px;border:2px solid #565758;"
        "border-radius:4px;'></div>"
    )
    return f"<div style='display:flex;gap:6px;margin-bottom:6px;'>{tile * WORD_LENGTH}</div>"


# ---------- State ----------
if "used_words" not in st.session_state:
    st.session_state.used_words = set()
if "secret" not in st.session_state:
    with st.spinner("AI is selecting a word..."):
        new_round()

st.title("🟩 AI-Powered Word Guessing Game")
st.caption(f"Guess the {WORD_LENGTH}-letter word in {MAX_ATTEMPTS} tries.")

# ---------- Board ----------
rows_html = "".join(render_row(r) for r in st.session_state.board)
rows_html += "".join(
    render_empty_row() for _ in range(MAX_ATTEMPTS - len(st.session_state.board))
)
st.markdown(rows_html, unsafe_allow_html=True)

# ---------- Input ----------
if st.session_state.status == "playing":
    with st.form("guess_form", clear_on_submit=True):
        guess = st.text_input("Your guess", max_chars=WORD_LENGTH)
        submitted = st.form_submit_button("Submit")

    if submitted:
        guess = guess.strip().lower()
        error = validate_guess(guess)
        if error:
            st.session_state.message = error
        else:
            st.session_state.message = ""
            st.session_state.board.append(evaluate_guess(guess, st.session_state.secret))
            if guess == st.session_state.secret:
                st.session_state.status = "won"
            elif len(st.session_state.board) >= MAX_ATTEMPTS:
                st.session_state.status = "lost"
        st.rerun()

    if st.session_state.message:
        st.warning(st.session_state.message)
    st.caption(f"Attempt {len(st.session_state.board) + 1} of {MAX_ATTEMPTS}")

elif st.session_state.status == "won":
    st.success("🎉 You solved it!")
else:
    st.error(f"Game over! The word was: {st.session_state.secret.upper()}")

# ---------- Play again ----------
if st.session_state.status != "playing":
    if st.button("Play again"):
        with st.spinner("AI is selecting a new word..."):
            new_round()
        st.rerun()
