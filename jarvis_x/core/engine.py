import os
import sys
import webbrowser
import threading
import platform
from pathlib import Path
from collections import deque

from jarvis_x.core.config import Config
from jarvis_x.learning.self_learning import SelfLearning
from jarvis_x.nlp.intent import IntentParser
from jarvis_x.memory.store import KnowledgeBase
from jarvis_x.core.llm import LLMClient
from jarvis_x.reasoning.planner import TaskPlanner


class JarvisEngine:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.running = True
        self.history = deque(maxlen=Config.CONTEXT_WINDOW)
        self._lock = threading.Lock()
        self.last_query = None
        self.last_response = None
        self.self_learning = SelfLearning(self.kb)
        self.llm = LLMClient(self)
        self.planner = TaskPlanner()

    def process(self, text: str, on_thought_cb=None) -> str:
        if not text.strip():
            return "Say something."

        text_lower = text.lower().strip()

        # Handle Critical Thinking Toggles
        if text_lower in ("enable critical thinking", "critical thinking on", "turn on critical thinking"):
            Config.CRITICAL_THINKING = True
            return "Critical thinking mode enabled. I will now analyze complex queries step-by-step."
        if text_lower in ("disable critical thinking", "critical thinking off", "turn off critical thinking"):
            Config.CRITICAL_THINKING = False
            return "Critical thinking mode disabled. Switched to direct processing."

        intent = IntentParser.parse(text)

        correction = self.self_learning.handle_correction(text)
        if correction:
            return f"Ah, you meant: {correction}. I'll remember that."

        if intent.action == 'shutdown':
            self.running = False
            return "Shutting down. Goodbye."

        if intent.action == 'greet':
            return self._greet()

        if intent.action == 'help':
            return self._help()

        if intent.action == 'self_learn':
            return self._self_learn()

        if intent.action == 'load_dataset':
            return self._load_dataset(intent)

        if intent.action == 'learn':
            return self._learn(intent)

        if intent.action == 'recall':
            return self._recall(intent, text)

        if intent.action == 'sys_info':
            return self._sys_info()

        if intent.action == 'web_open':
            return self._web_open(intent)

        if intent.action == 'web_scrape':
            return self._web_scrape(intent)

        if intent.action == 'find_files':
            return self._find_files(intent)

        if intent.action == 'feedback_positive':
            return self._feedback(text, True)

        if intent.action == 'feedback_negative':
            return self._feedback(text, False)

        if intent.action == 'unknown':
            # Check if LLM client is available
            if self.llm.is_available():
                if Config.CRITICAL_THINKING:
                    # Run critical level thinking loop
                    agent_res = self.planner.plan_and_execute_agent(text, self.llm, self, on_thought_cb)
                    return agent_res.get("result", "Thinking failed.")
                else:
                    # Direct chat response without agent loop
                    messages = [{"role": "user", "content": text}]
                    res = self.llm.chat(messages, use_tools=False)
                    return res.get("content", "Failed to communicate with LLM.")
            
            # Fallback to local KB
            result = self.kb.recall(text)
            if result:
                return result
            return f"I didn't understand. Try 'help' to see what I can do."

        return f"Command '{intent.action}' not implemented yet."

    def _greet(self):
        return f"Hello {Config.OWNER}. Systems online."

    def _help(self):
        llm_status = "Available" if self.llm.is_available() else "Unavailable (set ANTHROPIC_API_KEY)"
        ct_status = "ON" if Config.CRITICAL_THINKING else "OFF"
        return (f"Commands: open site [url] | system info | find files for [name] | "
                f"remember [fact] | recall [topic] | load dataset [path] | self learn | hello | help | quit | "
                f"+1 / -1 to teach me\n\n"
                f"AI Config: LLM API ({llm_status}) | Critical Thinking ({ct_status})\n"
                f"Toggle Critical Thinking: 'enable critical thinking' / 'disable critical thinking'")

    def _self_learn(self):
        count = self.self_learning.auto_improve(dry_run=False)
        summary = self.self_learning.summarize()
        if count:
            return f"Self-learning cycle complete: learned {count} new patterns.\n{summary}"
        return "Self-learning is active and watching.\n" + summary

    def _learn(self, intent):
        fact = intent.entities.get('fact', '')
        if fact:
            self.kb.learn(fact, f"Stored: {fact}")
            self.kb.log_learning("learn", fact)
            return f"I'll remember: {fact}"
        return "What should I remember?"

    def _load_dataset(self, intent):
        dataset_path = intent.entities.get('path', '').strip()
        if not dataset_path:
            return "Please specify a dataset path to load."
        return self.self_learning.learn_from_dataset(dataset_path)

    def _recall(self, intent, text):
        topic = intent.entities.get('topic', text)
        result = self.kb.recall(topic)
        if result:
            return f"I recall: {result}"
        return "I don't know about that yet."

    def _sys_info(self):
        return (f"OS: {platform.system()} {platform.release()}\n"
                f"Python: {sys.version.split()[0]}\n"
                f"Arch: {platform.machine()}\n"
                f"Host: {platform.node()}")

    def _web_open(self, intent):
        url = intent.entities.get('url', '')
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url} in your browser."

    def _web_scrape(self, intent):
        url = intent.entities.get('url', '')
        return f"Web scraping will be available in the skills module. Got URL: {url}"

    def _find_files(self, intent):
        query = intent.entities.get('query', '*')
        found = []
        for base in Config.ALLOWED_DIRS:
            try:
                found.extend(str(p) for p in Path(base).rglob(f"*{query}*") if p.is_file())
            except (PermissionError, OSError):
                continue
        found = found[:10]
        if found:
            return f"Found {len(found)} files:\n" + "\n".join(found[:5])
        return "No files found."

    def _feedback(self, text: str, positive: bool):
        source_text = self.last_query or text
        source_response = self.last_response or text
        self.self_learning.reinforce(source_text, source_response, positive)
        tag = "+1" if positive else "-1"
        self.kb.log_learning("feedback", f"{tag} {source_text}")
        if positive:
            return "Glad I could help!"
        return "Thanks for the feedback. I'll improve."

    def process_with_history(self, text: str, on_thought_cb=None) -> str:
        self.last_query = text
        response = self.process(text, on_thought_cb)
        self.last_response = response
        self.history.append({"in": text, "out": response})
        self.kb.save_interaction(text, response)

        try:
            intent = IntentParser.parse(text)
            extracted = self.self_learning.extract_and_learn(
                text, intent.action, intent.confidence
            )
            if extracted and intent.action == "unknown":
                response += f"\n(I noticed: {extracted[0]})"
                self.last_response = response
            self.self_learning.set_context(self.last_query, self.last_response)
            self.self_learning.auto_improve()
        except Exception:
            pass

        return response

    def shutdown(self):
        self.running = False
        self.kb.close()
