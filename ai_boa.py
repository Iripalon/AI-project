import streamlit as st
import os
import openai
import random

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
    env_key = os.environ.get("API_KEY")
    if env_key:
        return env_key
    try:
        return st.secrets.get("API_KEY")
    except Exception:
        return None

def _get_api_base():
    return os.environ.get("API_BASE") or os.environ.get("POE_BASE_URL") or "https://api.poe.com/v1"

def _get_model():
    return os.environ.get("MODEL") or "gpt-3.5-turbo"

def _get_client():
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

def get_ai_image(prompt: str) -> str:
    client, err = _get_client()  # Make sure your client is correctly set up for Poe's API
    if err:
        return err

    try:
        response = client.chat.completions.create(
            model="Imagen-4",
            messages=[{"role": "user", "content": "accord to the user prompt to genertate an image:"+ prompt}],
            extra_body={
                "aspect": "3:2",    # Options: "1:1", "3:2", "2:3", "auto"
                "quality": "high"   # Options: "low", "medium", "high"
            },
            stream=False  # Recommended for image generation
        )

        image_url = response.choices[0].message.content
        
        # Extract URL if it's embedded in text
        import re

        url_match = re.search(r'https?://[^\s\)]+', image_url)
        if url_match:
            image_url = url_match.group(0)
            return image_url
    except Exception as e:
        return f"Error generating image: {e}"

def get_ai_answer(question: str, temperature: float = 0.4, max_tokens: int = 300) -> str:
    client, err = _get_client()
    if err:
        return err
    model = _get_model()

    system_prompt = (
        "You are a close friend giving advice on life questions."
        "Keep the answer fun and in a relaxing, suggestive way, and often meme language. "
        "Use informal tone, such as 'I dont know, maybe a piece of burrito would be nice?'"
        "Sound kind of unsure when answering questions, use words such as 'i dont know' 'i guess'"
        "Respond in first person, like 'I think you should...' or 'How about...'. "
        "Use less punctuation, such as 'i dont know' or 'that may be fun i guess'."
        "Keep answers short, around 20-40 words, simple, easy-to-understand, and positive."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
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
    pass

def home():
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
    st.title("History Archive")

    with st.sidebar:
        st.header("Settings")
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.question = ""
            st.session_state.answer = ""
            st.session_state.reroll = 0

    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            st.write(f"**Question {len(st.session_state.history) - i}:** {item['question']}")
            st.write(f"**Answer:** {item['answer']}")
            st.write(f"**Rerolls:** {item['rerolls']}")
            st.write("---")
    elif not st.session_state.has_asked:
        st.write("Go ask some questions bruv")

def preset_page():
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

    if st.button("Get Answer for Preset"):
        with st.spinner("The Machine is now overheating..."):
            answer = get_ai_answer(selected_question, temperature=temperature, max_tokens=int(max_tokens))
            st.session_state.history.append({"question": selected_question, "answer": answer, "rerolls": 0})
            st.session_state.has_asked = True
        st.success("Answer generated!")
        st.markdown(f"**Question:** {selected_question}")
        safe_html = answer.replace("\n", "<br>")
        st.markdown(
            f"<div style='background:#f6f6f6;padding:16px;border-radius:8px'><h3 style='color:#2b8a3e'>Answer</h3><div>{safe_html}</div></div>",
            unsafe_allow_html=True,
        )

def chillspace_page():
    st.title("Chillspace for the Bored")
    st.write("This game is in Beta. Bugs and issues may occur.")
    st.write("Double-clicking may accidentally select the picture and turn it blue. To solve this, simply click anywhere outside the picture to deselect it.")
    st.write("Spamming the button may crash the game.")
    st.write("Anyway, enjoy the game :D")

    if "animation" not in st.session_state:
        st.session_state.animation = "fly1"
    if "cat_image" not in st.session_state:
        st.session_state.cat_image = "https://i.imgur.com/k6wZt0i.gif"  # Nyan Cat

    with st.sidebar:
        st.header("Settings")
        if st.button("Switch to OHHH MY GODDD"):
            st.session_state.cat_image = "https://media.tenor.com/vkYnJE2Jdj8AAAAe/oh-my-god.png"
        if st.button("Switch to YAAI"):
            st.session_state.cat_image = "https://static.wikia.nocookie.net/find-the-yaais/images/5/55/YAAI.png/revision/latest?cb=20240731032833"
        if st.button("Switch to Nyan Cat"):
            st.session_state.cat_image = "https://static.wikia.nocookie.net/nyancat/images/4/44/Glitchynyancatgif.gif/revision/latest/scale-to-width-down/250?cb=20210323054747"

        # --- NEW SECTION FOR AI IMAGE GENERATION ---
        st.divider()
        st.header("Generate Your Own Flyer")
        image_prompt = st.text_input("Describe your character (e.g., 'a flying burrito'): ")

        if st.button("Generate with AI"):
            if image_prompt:
                with st.spinner("AI is painting your character... this can take a minute!"):
                    new_image_url = get_ai_image(image_prompt)  # Ensure this is now defined
                    st.session_state.cat_image = new_image_url
                    st.write(new_image_url)
                    st.success("Character generated! It's now flying.")
                    st.rerun()
            else:
                st.warning("Please describe the character you want to generate.")
        # --- END OF NEW SECTION ---

    # Check for click from URL
    query_params = st.query_params
    if 'click' in query_params and query_params['click'] in [['1'], '1']:
        st.session_state.animation = random.choice(["fly1", "fly2", "fly3", "fly4"])
        st.query_params.clear()

    # HTML part uses st.session_state.cat_image
    nyan_html = f"""
    <div style="position: relative; height: 400px; width: 100%; overflow: hidden; border: 1px solid #ddd; border-radius: 8px;">
    <img id="nyan" src="{st.session_state.cat_image}" style="position: absolute; width: 100px; height: auto; object-fit: contain; animation: {st.session_state.animation} 10s infinite linear; cursor: pointer;" onclick="changeDirection()" alt="Flying Cat" />
    </div>
    <style>
    @keyframes fly1 {{
        0% {{ left: -10%; top: 10%; }}
        25% {{ left: 75%; top: 20%; }}
        50% {{ left: 25%; top: 70%; }}
        75% {{ left: 80%; top: 40%; }}
        100% {{ left: -10%; top: 10%; }}
    }}
    @keyframes fly2 {{
        0% {{ left: 10%; top: -10%; }}
        25% {{ left: 80%; top: 75%; }}
        50% {{ left: 20%; top: 25%; }}
        75% {{ left: 90%; top: 80%; }}
        100% {{ left: 10%; top: -10%; }}
    }}
    @keyframes fly3 {{
        0% {{ left: 50%; top: -10%; }}
        25% {{ left: -10%; top: 50%; }}
        50% {{ left: 50%; top: 110%; }}
        75% {{ left: 110%; top: 50%; }}
        100% {{ left: 50%; top: -10%; }}
    }}
    @keyframes fly4 {{
        0% {{ left: -10%; top: 50%; }}
        25% {{ left: 50%; top: -10%; }}
        50% {{ left: 110%; top: 50%; }}
        75% {{ left: 50%; top: 110%; }}
        100% {{ left: -10%; top: 50%; }}
    }}
    </style>
    <script>
    function changeDirection() {{
        const elem = document.getElementById('nyan');
        const animations = ['fly1', 'fly2', 'fly3', 'fly4'];
        const currentAnim = elem.style.animationName;
        let nextAnim = currentAnim;
        while (nextAnim === currentAnim) {{
            nextAnim = animations[Math.floor(Math.random() * animations.length)];
        }}
        elem.style.animationName = nextAnim;
    }}
    </script>
    """
    st.components.v1.html(nyan_html, height=420)

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
    st.Page(home, title="Ask AI", icon="❓"),
    st.Page(history_page, title="History", icon="📚"),
    st.Page(preset_page, title="Preset Questions", icon="📋"),
    st.Page(chillspace_page, title="Chillspace", icon="🕹️"),
    st.Page(credits_page, title="Credits", icon="🏆")
]

pg = st.navigation(pages)
pg.run()