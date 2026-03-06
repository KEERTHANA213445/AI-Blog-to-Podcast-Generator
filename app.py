import streamlit as st
from firecrawl import FirecrawlApp
from groq import Groq
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="AI Blog to Podcast Generator",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ AI Blog to Podcast Generator")
st.write("Convert any blog article into a multi-speaker podcast episode using AI.")
st.divider()

# Load environment variables
load_dotenv()

# Initialize APIs
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

url = st.text_input("Enter Blog URL")

if st.button("Generate Podcast"):

    if url:

        # Step 1: Scrape blog
        with st.spinner("Scraping blog..."):
            response = firecrawl.scrape(
                url=url,
                formats=["markdown"]
            )
            blog_content = response.markdown

        # Step 2: Generate podcast content (Host + Guest dialogue)
        with st.spinner("Generating podcast episode..."):

            prompt = f"""
            Turn the following blog into a **multi-speaker podcast**.

            Create a dialogue between:
            - Host
            - Guest

            Rules:
            - Make it engaging and conversational
            - Host asks questions
            - Guest explains concepts
            - Keep the conversation around 3–5 minutes

            Blog:
            {blog_content[:4000]}
            """

            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )

            podcast_script = completion.choices[0].message.content

        st.subheader("🎧 Podcast Script")
        st.write(podcast_script)
        st.divider()

        # Step 3: Convert multi-speaker script to audio
        with st.spinner("Generating podcast audio..."):

            # Define voices for Host and Guest
            host_voice = "21m00Tcm4TlvDq8ikWAM"
            guest_voice = "AZnzlk1XvdvUeBnXmlld"

            lines = podcast_script.split("\n")
            audio_segments = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("Host:"):
                    voice_id = host_voice
                    text = line.replace("Host:", "").strip()
                elif line.startswith("Guest:"):
                    voice_id = guest_voice
                    text = line.replace("Guest:", "").strip()
                else:
                    # Skip lines without speaker
                    continue

                audio_piece = elevenlabs.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text
                )
                audio_segments.append(b"".join(audio_piece))

            audio_bytes = b"".join(audio_segments)

        # Step 4: Play audio
        st.subheader("🔊 Podcast Audio")
        st.audio(audio_bytes, format="audio/mp3")

        # Step 5: Download button
        st.download_button(
            label="⬇ Download Podcast",
            data=audio_bytes,
            file_name="podcast.mp3",
            mime="audio/mp3"
        )
    