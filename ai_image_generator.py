# -----------------------------------------------------------------
# AI Image Generator with DALL-E 3 & Streamlit
#
# This is a single-file Streamlit application that generates images
# based on user descriptions using OpenAI's DALL-E 3 model.
#
# To Run:
# 1. Make sure you have a .streamlit/secrets.toml file with your
#    OPENAI_API_KEY.
# 2. Run `streamlit run app.py` in your terminal.
# -----------------------------------------------------------------

import streamlit as st
import openai
from dotenv import load_dotenv
import os

API_KEY = os.getenv("API_KEY")

# --- 1. PAGE CONFIGURATION ---
# Configure the page with a title, icon, and layout.
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="centered",
)

# --- 2. APPLICATION HEADER ---
st.title("🎨 AI Image Generator")
st.markdown("Powered by Streamlit and OpenAI's DALL-E 3. Describe the image you want to create below.")

# --- 3. API KEY & CLIENT INITIALIZATION ---
# Securely fetch the API key from Streamlit Secrets.
# The app will show an error and stop if the key is not found.
try:
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url="https://api.poe.com/v1",
    )
    api_key_present = True
except Exception:
    api_key_present = False
    st.error("Your OpenAI API key is not configured. Please add it to your Streamlit secrets.", icon="🔒")

# --- 4. USER INPUT FORM ---
# Use a form to group inputs and a single submit button.
with st.form("image_form"):
    # Text area for the main prompt
    prompt_text = st.text_area(
        "Enter a detailed description for your image:",
        height=150,
        placeholder="e.g., A photorealistic image of a majestic lion wearing a crown, sitting on a throne in a futuristic jungle."
    )

    # Columns for side-by-side options
    col1, col2 = st.columns(2)
    with col1:
        image_size = st.selectbox("Image Size:", ("1024x1024", "1792x1024", "1024x1792"), help="Select the desired dimensions for your image.")
    with col2:
        image_quality = st.selectbox("Image Quality:", ("standard", "hd"), help="HD quality costs more and may have longer generation times.")

    # The submit button for the form
    submit_button = st.form_submit_button("Generate Image")

# --- 5. IMAGE GENERATION LOGIC ---
# This block runs only when the form is submitted and the API key is present.
if submit_button and api_key_present:
    if not prompt_text:
        st.warning("Please enter a description to generate an image.", icon="⚠️")
    else:
        ##------------------------------------------------------------------------------
        try:
                        # Use chat completions with Qwen-Image model (as shown in basic_openai.py)
                        qwen_response = client.chat.completions.create(
                            model="Qwen-Image",
                            messages=[
                                {"role": "user", "content": image_prompt}
                            ],
                            extra_body={
                                "aspect": "3:2",    # Options: "1:1", "3:2", "2:3", "auto"
                                "quality": "high"   # Options: "low", "medium", "high"
                            },
                            stream=False
                        )
                        # Get image URL from response content (as shown in basic_openai.py)
                        image_url = qwen_response.choices[0].message.content
                        
                        # Extract URL if it's embedded in text
                        url_match = re.search(r'https?://[^\s\)]+', image_url)
                        if url_match:
                            image_url = url_match.group(0)
                            
                    except Exception as qwen_error:
                        # Fallback: try with simple prompt
                        try:
                            color_name = {"紅色": "red", "橙色": "orange", "黃色": "yellow", "綠色": "green", "藍色": "blue", "紫色": "purple", "粉紅色": "pink", "白色": "white", "黑色": "black", "金色": "gold"}.get(question2, "")
                            simple_prompt = f"A beautiful, professional food photograph of {recipe_title}"
                            if color_name:
                                simple_prompt += f" with {color_name} color accents"
                            simple_prompt += ", appetizing, well-lit, high quality"
                            
                            qwen_response = client.chat.completions.create(
                                model="Qwen-Image",
                                messages=[
                                    {"role": "user", "content": simple_prompt}
                                ],
                                extra_body={
                                    "aspect": "3:2",
                                    "quality": "high"
                                },
                                stream=False
                            )
                            image_url = qwen_response.choices[0].message.content
                            url_match = re.search(r'https?://[^\s\)]+', image_url)
                            if url_match:
                                image_url = url_match.group(0)
                        except Exception as e:
                            raise Exception(f"Qwen-Image generation failed: {str(e)}")

elif submit_button and not api_key_present:
    # Remind the user if they try to generate without a key
    st.error("Cannot generate image because the API key is missing.", icon="🔒")

# --- 6. FOOTER ---
st.markdown("---")
st.markdown("Made with ❤️ by a Streamlit Tech Master")
