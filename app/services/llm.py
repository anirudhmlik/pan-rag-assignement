#/app/services/llm.py

import os
from typing import List
from langchain_core.documents import Document as LangchainDocument
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI # Assuming using Gemini
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Configure LLM provider
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
print(f"[LLM] Using provider: {LLM_PROVIDER}")

# Initialize LLM based on provider
def get_llm():
    """
    Initializes and returns the appropriate LLM client based on the LLM_PROVIDER
    environment variable. Supports OpenAI and Gemini.
    """
    if LLM_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        # Using gpt-3.5-turbo as a default model for OpenAI
        return ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key, temperature=0.0)
    elif LLM_PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        # Using gemini-1.5-flash as a default model for Gemini
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0.0)
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}. Please set LLM_PROVIDER to 'openai' or 'gemini'.")

# Initialize LLM instance globally when the module is imported.
# This ensures the LLM is ready for use across the application.
try:
    llm = get_llm()
except Exception as e:
    # If LLM initialization fails (e.g., missing API key, network issues),
    # set llm to None and print an error. The application should handle this gracefully.
    print(f"LLM initialization error: {e}")
    llm = None # Handle this gracefully

async def generate_response(query_text: str, retrieved_chunks: List[LangchainDocument]) -> str:
    if not llm:
        print("LLM service is not available during generate_response. Returning fallback message.")
        return "LLM service is not available. Please check configuration and API keys."

    # Group chunks by document_id (or source)
    grouped_context: dict[str, List[str]] = {}
    for doc in retrieved_chunks:
        doc_id = doc.metadata.get("document_id", doc.metadata.get("source", "unknown"))
        doc_title = doc.metadata.get("source", f"Document {doc_id}")
        if doc_title not in grouped_context:
            grouped_context[doc_title] = []
        grouped_context[doc_title].append(doc.page_content.strip())

    # Format context with document labels
    formatted_context = ""
    for title, chunks in grouped_context.items():
        formatted_context += f"\n\n--- {title} ---\n"
        for chunk in chunks:
            formatted_context += f"- {chunk}\n"

    # Use a more comparative prompt
    prompt_template = PromptTemplate.from_template(
        """You are an AI assistant tasked with evaluating and comparing multiple documents based on a user's question.
Use the provided document sections below. Refer to documents by name when answering.

{context}

Question: {question}
Answer:"""
    )

    rag_chain = (
        {"context": lambda x: formatted_context, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    try:
        response = rag_chain.invoke(query_text)
        return response
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return "An error occurred while generating the response."