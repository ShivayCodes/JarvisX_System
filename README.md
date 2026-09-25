<div align="center">

# 🧠 JARVIS-X

### A modular, local-first personal AI assistant written in Python

**Learn locally · Remember context · Process knowledge · Experiment with intelligent behavior**

<p>
  <a href="https://github.com/ShivayCodes/JarvisX_System"><img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <img src="https://img.shields.io/badge/AI-Local%20First-111827?style=for-the-badge" alt="Local first AI">
  <img src="https://img.shields.io/badge/Interface-CLI%20%2B%20GUI-2563EB?style=for-the-badge" alt="CLI and GUI">
  <img src="https://img.shields.io/badge/License-Not%20Specified-6B7280?style=for-the-badge" alt="License">
</p>

</div>

---

## ✨ Overview

**JARVIS-X** is an experimental Python-based personal assistant designed as a modular system rather than a single monolithic script.

The current codebase separates concerns across **core execution, learning, memory, NLP, reasoning, conversation, skills, emotion, and input/output**. The main entry point supports both GUI and CLI operation, plus initialization, validation, statistics, benchmarking, and auto-start workflows.

> **Design direction:** build an assistant that can be understood, extended, tested, and progressively improved.

---

## 🧩 Architecture

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   CLI / GUI Layer   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │    Jarvis Engine    │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
       ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
       │     NLP     │       │   Reasoning │       │   Learning   │
       └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
              │                     │                     │
       ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
       │ Conversation│       │   Memory    │       │ Dataset Pool │
       └─────────────┘       └─────────────┘       └──────────────┘
```

### Project modules

| Module | Responsibility |
|---|---|
| `core/` | Configuration, engine, environment and plugins |
| `learning/` | Dataset validation and learning workflows |
| `memory/` | Persistent assistant memory |
| `nlp/` | Natural-language processing components |
| `reasoning/` | Reasoning and task-oriented behavior |
| `conversation/` | Conversation handling |
| `skills/` | Extensible assistant capabilities |
| `emotion/` | Experimental emotional-state components |
| `io/` | CLI and GUI interfaces |
| `tests/` | Project testing |

---

## 🧠 Real-World AI Stack

JARVIS-X now uses a **local-first open-source AI pipeline**:

```
User Query
   │
   ▼
Intent + Conversation
   │
   ├──► Semantic RAG ──► Sentence Transformers embeddings
   │          │
   │          └──────► Real public datasets
   │
   └──► Local LLM ───► Hugging Face Transformers
                 │
                 ▼
          Grounded Response
                 │
                 ▼
        Memory + Feedback
```

### Open-source components

- **Transformers** — local text generation with `HuggingFaceTB/SmolLM2-360M-Instruct`.
- **Sentence Transformers** — semantic embeddings and retrieval with `sentence-transformers/all-MiniLM-L6-v2`.
- **Hugging Face Datasets** — reproducible dataset ingestion.
- **SQuAD** — real public question-answering data for the initial RAG knowledge source.
- **NumPy + SQLite** — lightweight local indexing and persistent memory.

### Real dataset ingestion

The repository does **not** commit a large dataset dump. Instead, it downloads the public dataset when requested:

```bash
python main.py --ingest-squad 5000
```

SQuAD contains question/context/answer examples derived from Wikipedia articles. Its dataset card documents the dataset structure and licensing.

### Quick start

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python main.py --ingest-squad 5000
python main.py --cli
```

The first run downloads model and dataset assets into local caches. The repository itself does not store model weights, dataset dumps, databases, credentials, or personal memory.

For lower-memory systems, begin with 1,000–5,000 dataset examples and the 360M model. Larger models can be configured later through `.env`.

---

## 🚀 Current Capabilities

The current entry point exposes several operational modes:

```bash
python main.py
```

Launch the assistant interface.

```bash
python main.py --cli
```

Run the CLI interface.

```bash
python main.py --init
```

Initialize the local environment and dataset/memory directories.

```bash
python main.py --stats
```

Display local knowledge and AI statistics.

```bash
python main.py --validate
```

Validate the configured dataset pool.

```bash
python main.py --benchmark
```

Run the built-in offline benchmark.

### Auto-start

```bash
python main.py --install
python main.py --remove
```

The project contains platform-specific auto-start handling for Windows, Linux, and macOS.

---

## 📚 Local Knowledge Pipeline

The project includes a dedicated `dataset_pool/` area for local knowledge.

The intended workflow is:

```text
Documents
   ↓
Dataset Pool
   ↓
Validation
   ↓
Learning / Indexing
   ↓
Knowledge + Memory
   ↓
Query Processing
   ↓
JARVIS-X Response
```

This architecture makes the knowledge layer replaceable and keeps the assistant's runtime separate from its data.

---

## 🛠️ Installation

### Requirements

- Python 3.x
- Git
- A working microphone/audio stack if voice features are used
- Tkinter for the GUI on systems where it is not bundled

### Clone

```bash
git clone https://github.com/ShivayCodes/JarvisX_System.git
cd JarvisX_System
```

### Virtual environment

**Windows**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Initialize

```bash
python main.py --init
```

### Run

```bash
python main.py
```

Or:

```bash
python main.py --cli
```

---

## 📦 Dependency Stack

The repository currently declares packages including **Transformers, Hugging Face Datasets, Sentence Transformers, PyTorch, NumPy, scikit-learn, TensorFlow**, plus the existing audio/GUI dependencies.

- PyTorch
- Sentence Transformers
- NumPy
- scikit-learn
- TensorFlow
- OpenCV
- Pillow
- PyAudio
- SpeechRecognition
- pyttsx3
- sounddevice
- playsound
- python-dotenv

The dependency set is intentionally broad because JARVIS-X experiments with **language processing, machine learning, speech, audio, computer vision, and local assistant workflows**.

---

## 🧪 Development Workflow

A useful development loop for this project is:

```text
Idea
 ↓
Small implementation
 ↓
Run locally
 ↓
Test
 ↓
Benchmark
 ↓
Inspect behavior
 ↓
Refactor
 ↓
Repeat
```

Useful built-in checks:

```bash
python main.py --validate
python main.py --stats
python main.py --benchmark
```

---

## 🗺️ Roadmap

### Foundation
- [x] Modular Python package structure
- [x] CLI and GUI entry points
- [x] Dataset initialization
- [x] Validation command
- [x] Statistics command
- [x] Offline benchmark command
- [x] Cross-platform auto-start workflow

### Intelligence
- [ ] Improve semantic retrieval
- [ ] Strengthen contextual memory
- [ ] Improve response ranking
- [ ] Expand local knowledge ingestion
- [ ] Improve feedback-driven learning

### Engineering
- [ ] Expand automated tests
- [ ] Improve dependency isolation
- [ ] Add reproducible development setup
- [ ] Improve documentation and examples
- [ ] Add CI quality gates

---

## ⚠️ Project Status

**Experimental / active development.**

JARVIS-X is a personal engineering project. APIs, internal modules, algorithms, and dependencies may change as the architecture evolves.

Performance claims and future capabilities should be treated as development targets unless verified by the current implementation and benchmarks.

---

## 🔐 Security & Privacy

JARVIS-X is designed around local processing and local data, but **local-first does not automatically mean secure**.

Before using sensitive datasets:

- Review the code and dependencies.
- Keep secrets outside source control.
- Do not commit API keys, passwords, tokens, or private datasets.
- Review audio, camera, filesystem, and auto-start permissions.
- Run untrusted datasets in an isolated environment.

---

## 📁 Repository Layout

```text
JarvisX_System/
├── data/
├── dataset_pool/
├── jarvis_x/
│   ├── conversation/
│   ├── core/
│   ├── emotion/
│   ├── io/
│   ├── learning/
│   ├── memory/
│   ├── nlp/
│   ├── reasoning/
│   ├── skills/
│   └── tests/
├── tests/
├── main.py
├── install_autostart.py
├── requirements.txt
└── jarvis_v6.db
```

---

## 👨‍💻 Author

**Shubham Varma · [@ShivayCodes](https://github.com/ShivayCodes)**

Building systems, learning continuously, and improving one iteration at a time.

---

<div align="center">

### Learn → Build → Test → Understand → Improve

</div>
