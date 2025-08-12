import gradio as gr
import google.generativeai as genai
import os

# --- PASTE YOUR GOOGLE AI API KEY HERE ---
# This is the key you just created in Google AI Studio.
# It is recommended to set this as an environment variable for better security.
# For example: os.environ['GOOGLE_API_KEY'] = "YOUR_KEY_HERE"
GOOGLE_API_KEY = ""  # Paste your key here

# Configure the Google AI client
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Google AI: {e}")
    # Handle the error, maybe by exiting or showing a message in the UI

def generate_fictional_story(prompt_text):
    """
    This function generates a fictional story using the Google Gemini Pro model.
    """
    if not GOOGLE_API_KEY:
        return ("--- \n"
                "**Error: Google AI API key is missing!**\n\n"
                "1. Get a free API key from https://aistudio.google.com/app/apikey\n"
                "2. Paste it into the `GOOGLE_API_KEY` variable in the code.\n"
                "3. Restart the application."
                "\n---")

    # This is the prompt structure for the Gemini model
    # We give it a clear persona and a task.
    full_prompt = f"""You are a master storyteller. Your task is to write a short, compelling, and creative fictional story based on the user's idea. The story should have a clear beginning, middle, and end.

**User's Idea:** "{prompt_text}"

**Your Story:**
"""

    try:
        # Initialize the Gemini Pro model
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # Generate the content
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                top_p=0.95,
                max_output_tokens=1024,
            )
        )
        
        # Check if the response has text and return it
        if response and hasattr(response, 'text'):
            return response.text.strip()
        else:
            # Handle cases where the response might be empty or blocked
            return ("Error: The model did not return a valid story. This might be due to the safety filter "
                    "or an internal issue. Please try a different prompt.")

    except Exception as e:
        # Catch all other potential errors during API call
        return f"An unexpected error occurred with the Google AI API: {e}"


# --- Gradio User Interface ---
with gr.Blocks(theme=gr.themes.Monochrome(primary_hue="rose")) as app:
    gr.Markdown(
        """
        # ✨ AI Story Generator (Powered by Google Gemini) ✨
        This app uses a reliable, public API to finally get the job done. Enter your idea to get a unique story.
        """
    )

    with gr.Row():
        text_input = gr.Textbox(
            label="Your Story Concept",
            placeholder="e.g., A world where people's memories are stored in glass orbs that can be traded...",
            lines=3,
        )

    generate_button = gr.Button("✅ Generate My Story (This will work!)", variant="primary")

    with gr.Column():
        story_output = gr.Textbox(
            label="Your Generated Story",
            interactive=False,
            lines=25,
            placeholder="Your creative narrative will appear here...",
        )

    generate_button.click(
        fn=generate_fictional_story,
        inputs=text_input,
        outputs=story_output,
        show_progress="full"
    )

    gr.Markdown(
        """
        ---
        <p style='text-align: center;'>Powered by Google Gemini</p>
        """
    )

if __name__ == "__main__":
    app.launch()