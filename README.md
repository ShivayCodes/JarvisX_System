# JARVIS-X

A modular, local-first personal AI assistant written in Python.

JARVIS-X is designed to run locally, remember simple context, support a lightweight command loop, and expand into a more advanced assistant with memory, learning, and AI features.

## Overview

This project is a local-first assistant framework with:
- a CLI chat interface
- a Tkinter GUI interface
- persistent SQLite memory
- intent parsing for greetings, questions, and commands
- dataset validation and starter ingestion flow
- extensible skill registry for future behavior

It is intended as a practical foundation for a personal AI assistant rather than a fully production-ready AI agent.

## Features

- Local-first assistant workflow
- Simple memory persistence using SQLite
- CLI mode for quick interaction
- Tkinter GUI mode for desktop usage
- Dataset validation utilities
- Skills architecture for extensibility
- Easy startup and environment setup

## Project Structure

```text
JarvisX_System/
├── .env.example
├── .gitignore
├── README.md
├── main.py
├── requirements.txt
├── requirements-core.txt
├── requirements-ai.txt
├── requirements-desktop.txt
├── install_autostart.py
├── dataset_pool/
├── data/
├── jarvis_x/
│   ├── __init__.py
│   ├── core/
│   ├── io/
│   ├── memory/
│   ├── nlp/
│   ├── learning/
│   ├── skills/
│   ├── conversation/
│   ├── emotion/
│   └── reasoning/
├── scripts/
├── tests/
└── .github/
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ShivayCodes/JarvisX_System.git
cd JarvisX_System
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

For the core working app:

```bash
pip install -r requirements-core.txt
```

For the optional AI stack:

```bash
pip install -r requirements-ai.txt
```

For optional desktop features like voice and vision:

```bash
pip install -r requirements-desktop.txt
```

If you want the standard project dependency set:

```bash
pip install -r requirements.txt
```

## Configuration

A sample environment file is already included at `.env.example`.

To create a local `.env` file:

```bash
cp .env.example .env
```

Then edit `.env` if you want to change model names or settings.

Example values:

```dotenv
JARVISX_HF_MODEL=HuggingFaceTB/SmolLM2-360M-Instruct
JARVISX_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
JARVISX_MAX_NEW_TOKENS=256
JARVISX_TEMPERATURE=0.3
JARVISX_TOP_P=0.9
```

## Usage

### Run the assistant in CLI mode

```bash
python main.py --cli
```

Example conversation:

```text
You: hello
JARVIS: Hello! I'm JARVIS-X. How can I help you today?

You: what is python?
JARVIS: Based on my knowledge: I found some information but cannot retrieve it right now.

You: quit
Goodbye! Thanks for using JARVIS-X.
```

### Run the GUI

```bash
python main.py
```

This opens a simple Tkinter-based desktop chat interface.

### Initialize the environment

```bash
python main.py --init
```

This creates required folders such as:
- `data/`
- `dataset_pool/`
- `data/memory/`
- `data/embeddings/`
- `data/jarvis.db`

### Show stats

```bash
python main.py --stats
```

### Validate dataset files

```bash
python main.py --validate
```

### Run a benchmark

```bash
python main.py --benchmark
```

### Ingest a sample dataset flow

```bash
python main.py --ingest-squad 100
```

This is a starter ingestion pattern for local knowledge data.

### Install startup behavior

```bash
python main.py --install
```

To remove it:

```bash
python main.py --remove
```

## Quick Check: Is It Working?

Run this first:

```bash
python main.py --init
python main.py --stats
python main.py --cli
```

If the app starts, creates the data folders, and accepts prompts like `hello`, the project is working at the basic level.

## Notes on Current State

This project is a strong local foundation, but it is not yet a full production AI companion. At the moment, it focuses on:
- usable project structure
- basic chat loop
- local memory persistence
- extensible assistant modules
- local dataset preparation

Advanced features such as full LLM reasoning, semantic search, voice understanding, vision processing, and live command execution can be added on top of this foundation.

## Troubleshooting

### Module not found

Make sure you are running from the project root:

```bash
cd JarvisX_System
python main.py --cli
```

### Tkinter not available

If GUI mode fails, use CLI instead:

```bash
python main.py --cli
```

### Dependency issues

Install the core requirements first:

```bash
pip install -r requirements-core.txt
```

Then install optional extras as needed.

### Database errors

Reset local project data:

```bash
rm -rf data
python main.py --init
```

## Development

To run tests:

```bash
python -m unittest discover -s tests
```

## License

This project does not currently declare a specific license in the repository.

## Author

Shubham Varma

GitHub: https://github.com/ShivayCodes
