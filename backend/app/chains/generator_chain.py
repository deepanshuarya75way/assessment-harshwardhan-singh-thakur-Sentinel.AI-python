"""
Generator Chain (Tier 2) — LangChain LCEL equivalent of backend/agents/generatorAgent.js
"""

import logging
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.config import settings
from app.services.llm import get_llm

logger = logging.getLogger("sentinel.generator_chain")

SYSTEM_PROMPT = """You are Sentinel.AI — an intelligent and helpful AI assistant.

Your rules:
1. If relevant documents are provided, prioritize them and cite inline using [Doc N] notation.
2. If documents are insufficient or not provided, use your own knowledge to give a complete answer.
3. Always provide thorough, accurate, and helpful answers — never refuse unnecessarily.
4. Clearly label answers not backed by documents with: "[General Knowledge]" at the start.
5. Be professional, clear, and detailed. Never truncate your answer.
6. Never fabricate citations — only use [Doc N] if that document was actually provided.
7. Conversation Memory & User Facts: Use the full conversation history to maintain context, recall facts explicitly shared by the user (such as their name, preferences, or constraints), and resolve references (like "the second point" or "that part", which refer to items in your previous answer rather than [Doc N]).
   - Do not add a [Doc N] citation when answering from conversation history.
   - If a user-stated fact contradicts an uploaded document, prioritize the document for factual/policy questions, explicitly note the discrepancy to the user, and ask which one they want to treat as authoritative.
"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), MessagesPlaceholder("history"), ("user", "{user_prompt}")]
)


async def run_generator_chain(user_query: str, filtered_documents: List[dict], history: List[dict] | None = None) -> str:
    logger.info(f"[GeneratorChain] Starting. Using {len(filtered_documents)} documents.")

    has_documents = len(filtered_documents) > 0
    if has_documents:
        context_block = "\n\n---\n\n".join(
            f"[Doc {i + 1}] — {d['title']}\n{d['content']}" for i, d in enumerate(filtered_documents)
        )
        user_prompt = (
            f'Context Documents:\n{context_block}\n\n---\n\nUser Query: "{user_query}"\n\n'
            "Using the above documents as your primary source, provide a comprehensive and "
            "accurate answer. Cite documents inline where relevant."
        )
    else:
        user_prompt = (
            f'User Query: "{user_query}"\n\nNo documents were found in the knowledge base for '
            "this query. Answer using your general knowledge. Be thorough and helpful."
        )

    if history:
        user_prompt += (
            "\n\n Note: This is a follow-up question. Phrases like \"the second point\" or "
            "\" the first one\" refers to the items in YOUR PREVIOUS ANSWER in this conversation, "
            "NOT to document numbers like [Doc 2]. Expand on that item of your previous answer."
        )
    
    llm = get_llm(settings.GENERATOR_AGENT_MODEL, temperature=0.4, max_tokens=4096, json_mode=False)
    chain = _prompt | llm | StrOutputParser()

    chat_history = [
        ("human" if m["role"] == "user" else "ai", m["content"]) for m in (history or [])
    ]

    logger.info(f"[GeneratorChain] history sent: {[(r, c[:30]) for r, c in chat_history]}")

    answer = await chain.ainvoke({"user_prompt": user_prompt, "history": chat_history})
    logger.info(f"[GeneratorChain] Done. Answer length: {len(answer)} chars.")
    return answer
