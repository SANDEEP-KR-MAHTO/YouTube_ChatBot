# YouTube Video Chatbot (RAG)

A conversational AI chatbot that lets you ask questions about any YouTube video using its transcript. Built with **Retrieval-Augmented Generation (RAG)** — completely free to run.

---

## How It Works

```
YouTube URL
    ↓
Fetch transcript (youtube-transcript-api)
    ↓
Split into chunks → Convert to vectors (HuggingFace all-MiniLM-L6-v2)
    ↓
Store vectors locally (FAISS)
    ↓
User asks a question → Find relevant chunks → Generate answer (Groq LLaMA 3.1)
```

---

## Features

- Paste any YouTube URL and start chatting about the video
- Conversation memory — remembers last few messages for context
- Vectorstore caching — same video won't be re-processed on reload
- Fully free — no paid APIs required

---

## Tech Stack

| Component | Tool | Cost |
|---|---|---|
| UI | Streamlit | Free |
| Transcript | youtube-transcript-api | Free |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | Free (local) |
| Vector Store | FAISS | Free (local) |
| LLM | Groq `llama-3.1-8b-instant` | Free |

---

## Prerequisites

- Python 3.9+
- A free [Groq API key](https://console.groq.com)

---

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/SANDEEP-KR-MAHTO/YouTube_ChatBot.git
cd your-repo-name
```

**2. Create a virtual environment (recommended)**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

> Note: First run will download the `all-MiniLM-L6-v2` model (~90MB). This is a one-time download.

**4. Set up environment variables**

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

**5. Run the app**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Usage

1. Paste a YouTube video URL in the input box
2. Click **Load Video** — wait for transcript to be fetched and indexed
3. Ask any question about the video in the chat box
4. Use **Clear Chat** to start a fresh conversation

---

## YouTube_ChatBot Link
👉 [Click_Here](https://youtubechatbot-sm6xzpczwbj7kwjm5pno2e.streamlit.app/)

---

## Project Structure

```
RAG/
├── app.py              # Streamlit UI
├── transcript.py       # Fetches YouTube transcript
├── vectorstore.py      # Builds and loads FAISS vectorstore
├── rag_chain.py        # Retrieves context and generates answers
├── requirements.txt    # Python dependencies
├── .env                # API keys (never commit this)
├── .env.example        # Example env file
└── vectorstores/       # Cached vectorstores (auto-created)
```

---

## Limitations

- Only works for YouTube videos that have **captions or auto-generated subtitles**
- Videos without transcripts will return an error

> Coming soon: Whisper-based audio transcription as fallback for videos without subtitles

---

## License

MIT License — free to use and modify.
