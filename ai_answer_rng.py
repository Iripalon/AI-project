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
        "You are a close friend giving advice on life questions."
        "Keep the answer fun and in a relaxing, suggestive way, and often use slang or meme language. "
        "Use gangster like style or language to talk, such as 'bruv', 'dude', 'bro', 'dunno', 'ig', 'prob', etc, but don't overuse them, STRICTLY maximum 1 within 3 sentences."
        "Use informal tone, such as 'Idk bro, maybe a piece of burrito would be nice?' or 'Bruv, just chill and vibe, y'know?'. "
        "Respond in first person, like 'I think you should...' or 'How about...'. "
        "Use less punctuation, such as 'idk bro' or 'that may be fun i guess'."
        "Keep answers short, around 20-40 words, simple, easy-to-understand, and positive."
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


if "background" not in st.session_state:
    st.session_state.background = "White"
if "history" not in st.session_state:
    st.session_state.history = []
if "has_asked" not in st.session_state:
    st.session_state.has_asked = False

def apply_background():
    if st.session_state.background == "Black":
        st.markdown("<style>body { background-color: #0b0c0d; color: #e6e6e6; }</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>body { background-color: white; color: black; }</style>", unsafe_allow_html=True)

def home():
    apply_background()
    st.title(" The Very Cool Machine which can answer all your questions 👍")
    st.image("https://www.mercurynews.com/wp-content/uploads/2016/08/20150607_051142_sjm-lolrobots0607.jpg?w=572")
    with st.sidebar:
        st.header("Settings")
        temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.4, 0.05)
        max_tokens = st.number_input("Max tokens", min_value=50, max_value=2000, value=300, step=50)
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.question = ""
            st.session_state.answer = ""
            st.session_state.reroll = 0

    if "question" not in st.session_state:
        st.session_state.question = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "reroll" not in st.session_state:
        st.session_state.reroll = 0

    question = st.text_input("Ask a random question:", value=st.session_state.question)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Get Answer"):
            if question.strip():
                st.session_state.question = question
                with st.spinner("Consulting the Book of Answers..."):
                    st.session_state.answer = get_ai_answer(question, temperature=temperature, max_tokens=int(max_tokens))
                    st.session_state.reroll = 0
                    st.session_state.history.append({"question": question, "answer": st.session_state.answer, "rerolls": 0})
                    st.session_state.has_asked = True
            else:
                st.warning("Please enter a question.")
    with col2:
        if st.button("Reroll Answer"):
            if st.session_state.question:
                st.session_state.reroll += 1
                with st.spinner("Rerolling..."):
                    st.session_state.answer = get_ai_answer(st.session_state.question, temperature=temperature, max_tokens=int(max_tokens))
                    if st.session_state.history:
                        st.session_state.history[-1]["answer"] = st.session_state.answer
                        st.session_state.history[-1]["rerolls"] = st.session_state.reroll
            else:
                st.warning("No previous question to reroll. Ask first.")

    if st.session_state.answer and not st.session_state.answer.startswith("Error"):
        safe_html = st.session_state.answer.replace("\n", "<br>")
        st.markdown(
            f"<div style='background:#f6f6f6;padding:16px;border-radius:8px'><h3 style='color:#2b8a3e'>Answer</h3><div>{safe_html}</div></div>",
            unsafe_allow_html=True,
        )

        st.write("---")
        st.write(f"Rerolls: {st.session_state.reroll}")

def history_page():
    apply_background()
    st.title("History Archive")

    with st.sidebar:
        st.header("Settings")
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.question = ""
            st.session_state.answer = ""
            st.session_state.reroll = 0

    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            st.write(f"**Question {i+1}:** {item['question']}")
            st.write(f"**Answer:** {item['answer']}")
            st.write(f"**Rerolls:** {item['rerolls']}")
            st.write("---")
    elif not st.session_state.has_asked:
        st.write("Go ask some questions bruv")

def preset_page():
    apply_background()
    st.title("Preset Questions")

    with st.sidebar:
        st.header("Settings")
        temperature = st.slider("Creativity (temperature)", 0.0, 1.0, 0.4, 0.05)
        max_tokens = st.number_input("Max tokens", min_value=50, max_value=2000, value=300, step=50)
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.question = ""
            st.session_state.answer = ""
            st.session_state.reroll = 0

    preset_questions = [
        "How can I be happy?",
        "What should I eat for health?",
        "Why is exercise important?",
        "How to make new friends?",
        "How to study better?",
        "How to save money?",
        "How to be kind to others?"
    ]

    selected_question = st.selectbox("Choose a preset question:", preset_questions)

    if st.button("Get Answer"):
        with st.spinner("The Machine is now overheating..."):
            answer = get_ai_answer(selected_question, temperature=temperature, max_tokens=int(max_tokens))
            st.session_state.history.append({"question": selected_question, "answer": answer, "rerolls": 0})
            st.session_state.has_asked = True
        st.success("Answer generated! Check the History page or go back to ask the Machine.")
        st.markdown(f"**Question:** {selected_question}")
        safe_html = answer.replace("\n", "<br>")
        st.markdown(
            f"<div style='background:#f6f6f6;padding:16px;border-radius:8px'><h3 style='color:#2b8a3e'>Answer</h3><div>{safe_html}</div></div>",
            unsafe_allow_html=True,
        )

def chillspace_page():
    st.title("Chillspace for the Bored")
    st.write("This game is in Beta. Bugs and issues may occue.")
    st.write("Double-clciking may accidentally select the picture and turn it blue. To solve this, simply click anywhere ourside the picture to deselect it.")
    st.write("Spamming the button may crash the game.")
    st.write("Anyway, enjoy the game :D")

    import random

    if "animation" not in st.session_state:
        st.session_state.animation = "fly1"
    if "cat_image" not in st.session_state:
        st.session_state.cat_image = "https://static.wikia.nocookie.net/nyancat/images/4/44/Glitchynyancatgif.gif/revision/latest/scale-to-width-down/250?cb=20210323054747"

    with st.sidebar:
        st.header("Settings")
        if st.button("Switch to OHHH MY GODDD"):
            st.session_state.cat_image = "https://media.tenor.com/vkYnJE2Jdj8AAAAe/oh-my-god.png"
        if st.button("Switch to YAAI"):
            st.session_state.cat_image = "https://static.wikia.nocookie.net/find-the-yaais/images/5/55/YAAI.png/revision/latest?cb=20240731032833"
        if st.button("Switch to Nyan Cat"):
            st.session_state.cat_image = "https://static.wikia.nocookie.net/nyancat/images/4/44/Glitchynyancatgif.gif/revision/latest/scale-to-width-down/250?cb=20210323054747"

    # Check for click from URL
    query_params = st.query_params
    if 'click' in query_params and query_params['click'] in [['1'], '1']:
        st.session_state.animation = random.choice(["fly1", "fly2", "fly3", "fly4"])
        st.query_params.clear()

    # Flying Nyan Cat HTML
    nyan_html = f"""
    <div style="position: relative; height: 400px; width: 100%; overflow: hidden;">
    <img id="nyan" src="{st.session_state.cat_image}" style="position: absolute; width: 100px; height: 60px; animation: fly1 10s infinite linear; cursor: pointer;" onclick="changeDirection()" alt="Flying Cat" />
    </div>
    <style>
    @keyframes fly1 {{
        0% {{ left: 0%; top: 10%; transform: rotate(0deg); }}
        25% {{ left: 75%; top: 20%; transform: rotate(90deg); }}
        50% {{ left: 25%; top: 70%; transform: rotate(180deg); }}
        75% {{ left: 80%; top: 40%; transform: rotate(270deg); }}
        100% {{ left: 0%; top: 10%; transform: rotate(360deg); }}
    }}
    @keyframes fly2 {{
        0% {{ left: 10%; top: 0%; transform: rotate(0deg); }}
        25% {{ left: 80%; top: 75%; transform: rotate(-90deg); }}
        50% {{ left: 20%; top: 25%; transform: rotate(-180deg); }}
        75% {{ left: 90%; top: 80%; transform: rotate(-270deg); }}
        100% {{ left: 10%; top: 0%; transform: rotate(-360deg); }}
    }}
    @keyframes fly3 {{
        0% {{ left: 50%; top: 0%; transform: rotate(45deg); }}
        25% {{ left: 0%; top: 50%; transform: rotate(135deg); }}
        50% {{ left: 50%; top: 100%; transform: rotate(225deg); }}
        75% {{ left: 100%; top: 50%; transform: rotate(315deg); }}
        100% {{ left: 50%; top: 0%; transform: rotate(405deg); }}
    }}
    @keyframes fly4 {{
        0% {{ left: 0%; top: 50%; transform: rotate(180deg); }}
        25% {{ left: 50%; top: 0%; transform: rotate(90deg); }}
        50% {{ left: 100%; top: 50%; transform: rotate(0deg); }}
        75% {{ left: 50%; top: 100%; transform: rotate(-90deg); }}
        100% {{ left: 0%; top: 50%; transform: rotate(180deg); }}
    }}
    </style>
    <script>
    function changeDirection() {{
        const elem = document.getElementById('nyan');
        elem.style.animation = 'none';
        setTimeout(() => {{
            const animations = ['fly1', 'fly2', 'fly3', 'fly4'];
            const randomAnim = animations[Math.floor(Math.random() * animations.length)];
            elem.style.animation = randomAnim + ' 10s infinite linear';
        }}, 10);
    }}
    </script>
    """
    st.components.v1.html(nyan_html, height=450)

def credits_page():
    st.title("Credits")
    st.write("Built with:")
    st.write("- Streamlit")
    st.write("- OpenAI API")
    st.write("- Python")
    st.write("(Most of the work is wrote by AI tho hehe)")
    st.title("MORE UPDATES COMING SOON!!!!! STAY TUNED :D")

# Navigation
pages = [
    st.Page(home, title="Ask AI", icon=":material/question_answer:"),
    st.Page(history_page, title="History", icon=":material/history:"),
    st.Page(preset_page, title="Preset Questions", icon=":material/list:"),
    st.Page(chillspace_page, title="Chillspace for the Bored", icon=":material/pets:"),
    st.Page(credits_page, title="Credits", icon=":material/info:")
]

pg = st.navigation(pages)
pg.run()