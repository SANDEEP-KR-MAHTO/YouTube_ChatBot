import os
import streamlit as st
from dotenv import load_dotenv
from transcript import get_transcript
from vectorstore import get_or_build_vectorstore
from rag_chain import generate_answer

load_dotenv()

st.set_page_config(
    page_title="YouTube RAG Chatbot",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 YouTube Video Chatbot")
st.caption("Paste a YouTube URL, then ask anything about the video.")


def _resolve_api_key() -> str | None:
    """Try Streamlit secrets (Cloud), then .env / environment variable."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    return os.getenv("GROQ_API_KEY")


@st.cache_resource(show_spinner=False)
def _build_vectorstore(transcript: str, video_id: str):
    """Cache vectorstore in memory across reruns and sessions."""
    return get_or_build_vectorstore(transcript, video_id)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**Model info**")
    st.markdown("- Embeddings: `all-MiniLM-L6-v2` (free, local)")
    st.markdown("- LLM: `llama-3.1-8b-instant` (free, Groq)")
    st.markdown("- Vector Store: FAISS (local)")

    st.divider()
    api_key = _resolve_api_key()
    if not api_key:
        api_key_input = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get a free key at console.groq.com",
        )
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input
            api_key = api_key_input
    else:
        st.success("API key loaded ✓")

# ── Session state init ───────────────────────────────────────────────────────
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "video_loaded" not in st.session_state:
    st.session_state.video_loaded = False

# ── Video URL input ──────────────────────────────────────────────────────────
with st.form("video_form"):
    url = st.text_input(
        "YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )
    load_btn = st.form_submit_button("Load Video", type="primary")

if load_btn and url:
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        with st.spinner("Fetching transcript and building vector index..."):
            try:
                transcript, video_id = get_transcript(url)

                if video_id != st.session_state.video_id:
                    st.session_state.chat_history = []

                _build_vectorstore(transcript, video_id)
                st.session_state.video_id = video_id
                st.session_state.transcript = transcript
                st.session_state.video_loaded = True
                st.success(f"Video loaded! ({len(transcript.split())} words in transcript)")
            except Exception as e:
                st.error(f"Error: {e}")

# ── Chat interface ───────────────────────────────────────────────────────────
if st.session_state.video_loaded and st.session_state.video_id:

    vectorstore = _build_vectorstore(
        st.session_state.transcript, st.session_state.video_id
    )

    st.divider()

    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    user_query = st.chat_input("Ask anything about the video...")

    if user_query:
        if not api_key:
            st.error("Please enter your Groq API key in the sidebar.")
        else:
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        answer = generate_answer(
                            vectorstore,
                            user_query,
                            st.session_state.chat_history,
                        )
                        st.markdown(answer)

                        st.session_state.chat_history.append(
                            {"role": "user", "content": user_query}
                        )
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": answer}
                        )
                    except Exception as e:
                        st.error(f"Error generating answer: {e}")

    if st.session_state.chat_history:
        if st.button("Clear Chat", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()

elif not st.session_state.video_loaded:
    st.info("Load a YouTube video above to start chatting.")
