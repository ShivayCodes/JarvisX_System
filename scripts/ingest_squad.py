"""SQuAD dataset ingestion script."""
import json
from pathlib import Path
from jarvis_x.core.config import Config
from jarvis_x.memory.store import MemoryStore


def main():
    """
    Ingest SQuAD dataset examples.
    
    This is a placeholder that demonstrates the ingestion pattern.
    In production, this would download from HuggingFace datasets.
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest SQuAD dataset")
    parser.add_argument("--limit", type=int, default=100, help="Number of examples to ingest")
    args = parser.parse_args()
    
    print(f"SQuAD Ingestion: Preparing to load {args.limit} examples...")
    print(f"Dataset pool: {Config.DATASET_POOL_DIR}")
    
    memory = MemoryStore()
    
    # Create sample dataset
    sample_data = [
        {
            "question": "What is JARVIS-X?",
            "context": "JARVIS-X is a local-first personal AI assistant written in Python.",
            "answer": "A modular AI assistant for local processing"
        },
        {
            "question": "How to install JARVIS-X?",
            "context": "Clone the repo and install dependencies with pip install -r requirements.txt",
            "answer": "Run git clone and pip install requirements"
        }
    ]
    
    for i, item in enumerate(sample_data[:min(args.limit, len(sample_data))]):
        memory.store({
            "query": item["question"],
            "response": item["answer"],
            "intent": {"type": "qa"},
            "timestamp": "dataset-init"
        })
        if (i + 1) % 10 == 0:
            print(f"  Loaded {i + 1}/{min(args.limit, len(sample_data))} examples")
    
    print(f"✓ Ingestion complete. Total stored: {memory.count()}")


if __name__ == "__main__":
    main()
