import streamlit as st
import os
import openai

# Load environment variables from a .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Expose API_KEY variable from .env or env
API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="Life's Answer Machine", layout="centered")

def _get_api_key():
    # Prefer environment variable first (won't raise). If not set, try Streamlit secrets
    env_key = os.environ.get("API_KEY")
    if env_key:
        return env_key
    try:
        # Accessing st.secrets may raise if no secrets file exists; handle gracefully
        return st.secrets.get("API_KEY")
    except Exception:
        return None


def _get_api_base():
    # Allow overriding the API base (useful for Poe or proxies)
    return os.environ.get("API_BASE") or os.environ.get("POE_BASE_URL") or "https://api.poe.com/v1"


def _get_model():
    return os.environ.get("MODEL") or "gpt-3.5-turbo"


def _get_client():
    # Prefer explicit API_KEY variable loaded from .env
    key = API_KEY or os.environ.get("API_KEY")
    if not key:
        try:
            key = st.secrets.get("API_KEY")
        except Exception:
            key = None
    if not key:
        return None, "API key not found. Set `API_KEY` in .env, environment, or Streamlit secrets."

    base = _get_api_base()
    try:
        client = openai.OpenAI(api_key=key, base_url=base)
        return client, None
    except Exception as e:
        return None, f"Failed to initialize OpenAI client: {e}"

def get_ai_answer(question: str, temperature: float = 0.4, max_tokens: int = 300) -> str:

    client, err = _get_client()
    if err:
        return err
    model = _get_model()

    system_prompt = (
        "You are the 'Book of Answers' — provide concise, logical, and thoughtful answers to hard life "
        "questions. Start with a short direct answer, then give 1-2 sentences of reasoning, and end with "
        "one practical suggestion if applicable. Keep the tone wise, calm, and non-judgmental."
    )

    try:
        # Use the client instance to create a chat completion
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Response shape should be similar; guard access
        try:
            return resp.choices[0].message.content.strip()
        except Exception:
            return str(resp)
    except Exception as e:
        return f"Error calling completion API: {e}"


st.title("✨ Life's Answer Machine — Book of Answers Mode ✨")

with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.4, 0.05)
    max_tokens = st.number_input("Max tokens", min_value=50, max_value=2000, value=300, step=50)
    background = st.selectbox("Background", ("White", "Black"))
    if st.button("Clear history"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]

if background == "Black":
    st.markdown("<style>body { background-color: #0b0c0d; color: #e6e6e6; }</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>body { background-color: white; color: black; }</style>", unsafe_allow_html=True)

if "question" not in st.session_state:
    st.session_state.question = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "reroll" not in st.session_state:
    st.session_state.reroll = 0

question = st.text_input("Ask a hard question about life:", value=st.session_state.question)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Get Answer"):
        if question.strip():
            st.session_state.question = question
            with st.spinner("Consulting the Book of Answers..."):
                st.session_state.answer = get_ai_answer(question, temperature=temperature, max_tokens=int(max_tokens))
                st.session_state.reroll = 0
        else:
            st.warning("Please enter a question.")
with col2:
    if st.button("Reroll Answer"):
        if st.session_state.question:
            st.session_state.reroll += 1
            with st.spinner("Rerolling..."):
                st.session_state.answer = get_ai_answer(st.session_state.question, temperature=temperature, max_tokens=int(max_tokens))
        else:
            st.warning("No previous question to reroll. Ask first.")

if st.session_state.answer:
    safe_html = st.session_state.answer.replace("\n", "<br>")
    st.markdown(
        f"<div style='background:#f6f6f6;padding:16px;border-radius:8px'><h3 style='color:#2b8a3e'>Answer</h3><div>{safe_html}</div></div>",
        unsafe_allow_html=True,
    )

    st.write("---")
    st.write(f"Rerolls: {st.session_state.reroll}")