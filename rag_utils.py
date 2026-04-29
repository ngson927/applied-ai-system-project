import os
import re
from typing import List

_KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base", "strategy_tips.md")


def load_knowledge_base(kb_path: str = _KNOWLEDGE_BASE_PATH) -> List[dict]:
    """Load and chunk the knowledge base by section headings."""
    if not os.path.exists(kb_path):
        return []

    with open(kb_path, "r") as f:
        content = f.read()

    chunks = []
    # Split on level-2 headings, keeping the heading text
    parts = re.split(r'\n(?=## )', content)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        title = lines[0].lstrip('#').strip()
        body = "\n".join(lines[1:]).strip()
        if body:
            chunks.append({"title": title, "text": body})

    return chunks


def retrieve_relevant_chunks(query: str, chunks: List[dict], top_k: int = 3) -> List[str]:
    """Return top-k chunks most relevant to the query using keyword overlap scoring."""
    if not chunks:
        return []

    query_words = set(re.findall(r'\w+', query.lower()))

    scored = []
    for chunk in chunks:
        combined = (chunk["title"] + " " + chunk["text"]).lower()
        chunk_words = set(re.findall(r'\w+', combined))
        score = len(query_words & chunk_words)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    # Always return at least top_k chunks even if score is 0
    return [f"## {c['title']}\n{c['text']}" for _, c in scored[:top_k]]
