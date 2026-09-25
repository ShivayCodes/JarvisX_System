#!/usr/bin/env python3
"""Download a real public QA dataset and build the local JARVIS-X RAG index."""

import argparse

from datasets import load_dataset

from jarvis_x.ai.rag import SemanticRAG


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest SQuAD into the local JARVIS-X semantic index")
    parser.add_argument("--limit", type=int, default=5000, help="Maximum training examples to ingest")
    args = parser.parse_args()

    ds = load_dataset("rajpurkar/squad", split=f"train[:{args.limit}]")
    docs = []
    for row in ds:
        answers = row.get("answers", {}).get("text", [])
        answer = answers[0] if answers else ""
        docs.append({
            "text": row["context"],
            "question": row["question"],
            "answer": answer,
            "source": "rajpurkar/squad",
            "title": row.get("title", ""),
        })

    rag = SemanticRAG()
    added = rag.add(docs)
    rag.save()
    print(f"Ingested {added} SQuAD examples into the local RAG index.")


if __name__ == "__main__":
    main()
