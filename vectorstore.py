from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


STORE_DIR = Path("vectorstores")


def _store_path(video_id: str) -> Path:
    return STORE_DIR / video_id


def _get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def build_vectorstore(transcript: str, video_id: str) -> FAISS:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(transcript)
    docs = [Document(page_content=chunk, metadata={"video_id": video_id, "chunk_index": i})
            for i, chunk in enumerate(chunks)]

    vectorstore = FAISS.from_documents(docs, _get_embeddings())

    store_path = _store_path(video_id)
    store_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(store_path))

    return vectorstore


def load_vectorstore(video_id: str) -> FAISS | None:
    store_path = _store_path(video_id)
    if not store_path.exists():
        return None
    return FAISS.load_local(str(store_path), _get_embeddings(), allow_dangerous_deserialization=True)


def get_or_build_vectorstore(transcript: str, video_id: str) -> FAISS:
    existing = load_vectorstore(video_id)
    if existing is not None:
        return existing
    return build_vectorstore(transcript, video_id)
