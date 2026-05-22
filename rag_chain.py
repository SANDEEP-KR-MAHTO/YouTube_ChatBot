from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS


def retrieve_context(vectorstore: FAISS, query: str, k: int = 5) -> list[str]:
    docs = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]


def build_prompt(context_chunks: list[str], query: str) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    return f"""You are a helpful assistant that answers questions based strictly on the provided YouTube video transcript excerpts.

If the answer is not found in the transcript, say "I couldn't find that information in the video transcript."

Transcript excerpts:
{context}

Question: {query}

Answer:"""


def generate_answer(
    vectorstore: FAISS,
    query: str,
    chat_history: list[dict],
    k: int = 5,
) -> str:
    context_chunks = retrieve_context(vectorstore, query, k=k)
    prompt = build_prompt(context_chunks, query)

    messages = []
    for turn in chat_history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": prompt})

    llm = ChatGroq(model="llama-3.1-8b-instant")
    response = llm.invoke(messages)
    return response.content
