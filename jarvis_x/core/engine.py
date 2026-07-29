import os
import platform
import sys
import threading
import webbrowser
from collections import deque
from pathlib import Path

from jarvis_x.core.algorithm import LocalAIEngine
from jarvis_x.core.config import Config
from jarvis_x.core.memory_manager import MemoryManager
from jarvis_x.core.semantic_matcher import SemanticMatcher
from jarvis_x.learning.query_processor import QueryProcessor
from jarvis_x.learning.self_learning import SelfLearning
from jarvis_x.memory.store import KnowledgeBase
from jarvis_x.reasoning.planner import TaskPlanner
from jarvis_x.nlp.intent import IntentParser
from jarvis_x.conversation.conversation_manager import ConversationManager
from jarvis_x.core.environment_setup import initialize_environment
from jarvis_x.core.plugin_manager import PluginManager
from jarvis_x.core.llm_backend import OllamaClient
import re



class JarvisEngine:
    def __init__(self):
        initialize_environment()
        self.kb = KnowledgeBase()
        self.running = True
        self.history = deque(maxlen=Config.CONTEXT_WINDOW)
        self._lock = threading.Lock()
        self.last_query = None
        self.last_response = None
        self.self_learning = SelfLearning(self.kb)
        self.semantic_matcher = SemanticMatcher()
        self.memory_manager = MemoryManager(Config.MEMORY_DB_PATH)
        self.local_ai = LocalAIEngine(self.kb, semantic_matcher=self.semantic_matcher, memory_manager=self.memory_manager)
        self.planner = TaskPlanner()
        self.query_processor = QueryProcessor()
        self.conversation_manager = ConversationManager()
        self.pm = PluginManager(self)
        self.pm.discover()

        self.llm_client = OllamaClient()
        self.llm_history = []
        try:
            self.self_learning.dataset_learner.auto_scan_pool()
        except Exception:
            pass
        self.local_ai.rebuild_index()

    def process(self, text: str, on_thought_cb=None) -> str:
        if not text.strip():
            return "Say something."

        text_lower = text.lower().strip()
        if text_lower in ("enable critical thinking", "critical thinking on", "turn on critical thinking"):
            Config.CRITICAL_THINKING = True
            return "Critical thinking mode enabled. I will show semantic indexing metrics and reasoning steps."
        if text_lower in ("disable critical thinking", "critical thinking off", "turn off critical thinking"):
            Config.CRITICAL_THINKING = False
            return "Critical thinking mode disabled. Switched to direct processing."

        # Intercept quick commands
        normalized_text = self.query_processor.normalize(text)
        intent = IntentParser.parse(normalized_text)

        if intent.action == "shutdown":
            self.running = False
            return "Shutting down. Goodbye."
        if intent.action == "greet":
            return self._greet()
        if intent.action == "help":
            return self._help()
        if intent.action == "self_learn":
            return self._self_learn()
        if intent.action == "feedback_positive":
            return self._feedback(normalized_text, True)
        if intent.action == "feedback_negative":
            return self._feedback(normalized_text, False)

        # Try local LLM backend
        if Config.LLM_ENABLED:
            if self.llm_client.is_available():
                try:
                    # Retrieve context (RAG)
                    rag_res = self.local_ai.query(normalized_text)
                    retrieved_context = rag_res.get("result", "")
                    
                    # Log retrieval thought
                    if on_thought_cb:
                        on_thought_cb(f"Retrieved Context: {retrieved_context[:200]}...")

                    # Prepare messages payload
                    messages = []
                    for turn in self.llm_history:
                        messages.append(turn)
                    
                    user_content = (
                        f"Context from local knowledge base:\n{retrieved_context}\n\n"
                        f"User query: {text}"
                    )
                    messages.append({"role": "user", "content": user_content})

                    # Call LLM
                    raw_response = self.llm_client.chat(messages, Config.SYSTEM_PROMPT)

                    # Extract thoughts
                    thinking_content = ""
                    thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw_response, re.DOTALL)
                    if thinking_match:
                        thinking_content = thinking_match.group(1).strip()
                        if on_thought_cb and thinking_content:
                            on_thought_cb(thinking_content)
                    
                    # Clean response
                    cleaned_response = re.sub(r"<thinking>.*?</thinking>", "", raw_response, flags=re.DOTALL).strip()

                    # Handle Tool Use
                    tool_pattern = re.compile(r'\[TOOL:\s*(\w+)(.*?)\]')
                    tool_matches = tool_pattern.findall(cleaned_response)
                    
                    if tool_matches:
                        for tool_name, args_str in tool_matches:
                            args = {}
                            for k, v in re.findall(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s\]]+))', args_str):
                                args[k] = v[0] or v[1] or v[2] if isinstance(v, tuple) else v
                            
                            # Clean args dict
                            clean_args = {}
                            for key, val in args.items():
                                if isinstance(val, tuple):
                                    clean_args[key] = next((x for x in val if x), "")
                                else:
                                    clean_args[key] = val

                            if on_thought_cb:
                                on_thought_cb(f"Executing tool: {tool_name} with args {clean_args}")
                            
                            tool_result = self._execute_tool(tool_name, clean_args)
                            
                            # Feed back to LLM
                            messages.append({"role": "assistant", "content": raw_response})
                            messages.append({"role": "user", "content": f"Tool '{tool_name}' output: {tool_result}"})
                            
                            raw_response = self.llm_client.chat(messages, Config.SYSTEM_PROMPT)
                            
                            # Parse thinking again if any
                            thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw_response, re.DOTALL)
                            if thinking_match:
                                thinking_content = thinking_match.group(1).strip()
                                if on_thought_cb and thinking_content:
                                    on_thought_cb(thinking_content)
                            
                            cleaned_response = re.sub(r"<thinking>.*?</thinking>", "", raw_response, flags=re.DOTALL).strip()

                    # Handle Artifacts
                    artifact_pattern = re.compile(r'\[ARTIFACT:\s*([^\s\]]+)\](.*?)\[/ARTIFACT\]', re.DOTALL)
                    artifact_matches = artifact_pattern.findall(cleaned_response)
                    if artifact_matches:
                        project_root = Path(__file__).resolve().parents[2]
                        artifacts_dir = project_root / "artifacts"
                        artifacts_dir.mkdir(parents=True, exist_ok=True)
                        
                        for filename, content in artifact_matches:
                            filepath = artifacts_dir / filename
                            filepath.write_text(content.strip(), encoding="utf-8")
                            
                            note = f"\n\n[Artifact saved to: {filepath.name}]"
                            cleaned_response += note
                            
                            # Automatically open HTML/SVG files
                            if filename.lower().endswith((".html", ".htm", ".svg")):
                                webbrowser.open(filepath.as_uri())

                        # Strip artifact tags from final printed response to keep it clean
                        cleaned_response = re.sub(r'\[ARTIFACT:\s*[^\s\]]+\].*?\[/ARTIFACT\]', '', cleaned_response, flags=re.DOTALL).strip()

                    return cleaned_response
                except Exception as e:
                    if on_thought_cb:
                        on_thought_cb(f"LLM Error: {e}. Falling back to standard algorithms.")

        # Fallback to standard TF-IDF & Markov
        if on_thought_cb:
            on_thought_cb("[Warning] Local LLM (Ollama) is not running/available. Falling back to TF-IDF & Markov engine. To enable local LLMs, start Ollama locally.")
        
        correction = self.self_learning.handle_correction(normalized_text)
        if correction:
            self.local_ai.rebuild_index()
            return f"Ah, you meant: {correction}. I'll remember that."

        if intent.action in self.pm.skills:
            try:
                return self.pm.skills[intent.action](intent)
            except Exception as e:
                return f"Error executing plugin skill '{intent.action}': {e}"

        if intent.action == "load_dataset":
            res = self._load_dataset(intent)
            self.local_ai.rebuild_index()
            return res
        if intent.action == "learn":
            res = self._learn(intent)
            self.local_ai.rebuild_index()
            return res
        if intent.action == "recall":
            return self._recall(intent, normalized_text)
        if intent.action == "sys_info":
            return self._sys_info()
        if intent.action == "web_open":
            return self._web_open(intent)
        if intent.action == "web_scrape":
            return self._web_scrape(intent)
        if intent.action == "find_files":
            return self._find_files(intent)

        if intent.action == "unknown" or True:
            res_dict = self.local_ai.query(normalized_text)
            if Config.CRITICAL_THINKING and on_thought_cb:
                for thought in res_dict.get("thoughts", []):
                    on_thought_cb(thought)
            return res_dict.get("result", "I am still learning.")

    def _execute_tool(self, name: str, args: dict) -> str:
        from jarvis_x.nlp.intent import IntentResult
        intent = IntentResult(action=name, entities=args)
        
        if name in self.pm.skills:
            try:
                return self.pm.skills[name](intent)
            except Exception as e:
                return f"Error: {e}"
        
        if name == "sys_info":
            return self._sys_info()
        if name == "find_files":
            return self._find_files(intent)
        if name == "web_open":
            return self._web_open(intent)
        if name == "web_scrape":
            # scrape skill is in the pm.skills usually under 'web_scrape'
            if "web_scrape" in self.pm.skills:
                return self.pm.skills["web_scrape"](intent)
            return self._web_scrape(intent)
            
        return f"Unknown tool: {name}"

    def _greet(self):
        return f"Hello {Config.OWNER}. Local AI systems online."

    def _help(self):
        ct_status = "ON" if Config.CRITICAL_THINKING else "OFF"
        return (
            f"Commands: open site [url] | system info | find files for [name] | "
            f"remember [fact] | recall [topic] | load dataset [path] | self learn | hello | help | quit | "
            f"+1 / -1 to teach me\n\n"
            f"AI Config: Fully Local LLM (Ollama) with TF-IDF fallback | Critical Thinking ({ct_status})\n"
            f"Toggle Critical Thinking: 'enable critical thinking' / 'disable critical thinking'"
        )

    def _self_learn(self):
        count = self.self_learning.auto_improve(dry_run=False)
        summary = self.self_learning.summarize()
        if count:
            self.local_ai.rebuild_index()
            return f"Self-learning cycle complete: learned {count} new patterns.\n{summary}"
        return "Self-learning is active and watching.\n" + summary

    def _learn(self, intent):
        fact = intent.entities.get("fact", "")
        if fact:
            self.kb.learn(fact, f"Stored: {fact}")
            self.kb.log_learning("learn", fact)
            return f"I'll remember: {fact}"
        return "What should I remember?"

    def _load_dataset(self, intent):
        dataset_path = intent.entities.get("path", "").strip()
        if not dataset_path:
            return "Please specify a dataset path to load."
        return self.self_learning.learn_from_dataset(dataset_path)

    def _recall(self, intent, text):
        topic = intent.entities.get("topic", text)
        result = self.kb.recall(topic)
        if result:
            return f"I recall: {result}"
        return "I don't know about that yet."

    def _sys_info(self):
        return (
            f"OS: {platform.system()} {platform.release()}\n"
            f"Python: {sys.version.split()[0]}\n"
            f"Arch: {platform.machine()}\n"
            f"Host: {platform.node()}"
        )

    def _web_open(self, intent):
        url = intent.entities.get("url", "")
        if not url:
            return "No URL provided."
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url} in your browser."

    def _web_scrape(self, intent):
        url = intent.entities.get("url", "")
        return f"Web scraping will be available in the skills module. Got URL: {url}"

    def _find_files(self, intent):
        query = intent.entities.get("query", "*")
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
        self.local_ai.rebuild_index()
        if positive:
            return "Glad I could help!"
        return "Thanks for the feedback. I'll improve."

    def process_with_history(self, text: str, on_thought_cb=None) -> str:
        self.last_query = text
        response = self.process(text, on_thought_cb)
        self.last_response = response
        self.history.append({"in": text, "out": response})
        self.kb.save_interaction(text, response)

        # Update LLM History
        self.llm_history.append({"role": "user", "content": text})
        self.llm_history.append({"role": "assistant", "content": response})
        self.llm_history = self.llm_history[-20:] # Bound history size

        try:
            intent = IntentParser.parse(text)
            extracted = self.self_learning.extract_and_learn(text, intent.action, intent.confidence)
            if extracted and intent.action == "unknown":
                response += f"\n(I noticed: {extracted[0]})"
                self.last_response = response
                self.local_ai.rebuild_index()
            self.self_learning.set_context(self.last_query, self.last_response)
            self.self_learning.auto_improve()
        except Exception:
            pass

        self.conversation_manager.add_turn(text, response)
        return response

    def shutdown(self):
        self.running = False
        self.kb.close()
        self.memory_manager.close()
