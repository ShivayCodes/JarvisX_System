import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("JarvisLLM")

class LLMClient:
    def __init__(self, engine=None):
        self.engine = engine
        self.anthropic_client = None
        self.openai_client = None
        self.provider = None

        # Try Anthropic first
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                self.provider = "anthropic"
            except ImportError:
                logger.warning("Anthropic package not installed despite key present.")

        # Fallback to OpenAI
        if not self.provider:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    import openai
                    self.openai_client = openai.OpenAI(api_key=openai_key)
                    self.provider = "openai"
                except ImportError:
                    logger.warning("OpenAI package not installed despite key present.")

    def is_available(self) -> bool:
        return self.provider is not None

    def get_tool_definitions(self, format_type="anthropic"):
        if format_type == "anthropic":
            return [
                {
                    "name": "web_open",
                    "description": "Open a website or URL in the user's default web browser.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The absolute URL to open starting with http:// or https://"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "sys_info",
                    "description": "Retrieve information about the user's operating system, python version, and architecture.",
                    "input_schema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "find_files",
                    "description": "Search the local directories for files matching a specific query or name pattern.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search term or filename pattern to look for"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "learn",
                    "description": "Remember or store a new fact, preference, detail, or pattern to the knowledge base.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string", "description": "The fact or detail to remember"}
                        },
                        "required": ["fact"]
                    }
                },
                {
                    "name": "recall",
                    "description": "Recall or search the knowledge base for previously remembered information or facts.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "The topic or detail to retrieve"}
                        },
                        "required": ["topic"]
                    }
                }
            ]
        elif format_type == "openai":
            return [
                {
                    "type": "function",
                    "function": {
                        "name": "web_open",
                        "description": "Open a website or URL in the user's default web browser.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "description": "The absolute URL to open starting with http:// or https://"}
                            },
                            "required": ["url"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "sys_info",
                        "description": "Retrieve information about the user's operating system, python version, and architecture.",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "find_files",
                        "description": "Search the local directories for files matching a specific query or name pattern.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search term or filename pattern to look for"}
                            },
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "learn",
                        "description": "Remember or store a new fact, preference, detail, or pattern to the knowledge base.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "fact": {"type": "string", "description": "The fact or detail to remember"}
                            },
                            "required": ["fact"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "recall",
                        "description": "Recall or search the knowledge base for previously remembered information or facts.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string", "description": "The topic or detail to retrieve"}
                            },
                            "required": ["topic"]
                        }
                    }
                }
            ]
        return []

    def execute_tool(self, name: str, args: dict) -> str:
        if not self.engine:
            return "Engine not connected."
        try:
            if name == "web_open":
                url = args.get("url", "")
                class MockIntent:
                    entities = {"url": url}
                return self.engine._web_open(MockIntent())
            elif name == "sys_info":
                return self.engine._sys_info()
            elif name == "find_files":
                query = args.get("query", "*")
                class MockIntent:
                    entities = {"query": query}
                return self.engine._find_files(MockIntent())
            elif name == "learn":
                fact = args.get("fact", "")
                class MockIntent:
                    entities = {"fact": fact}
                return self.engine._learn(MockIntent())
            elif name == "recall":
                topic = args.get("topic", "")
                class MockIntent:
                    entities = {"topic": topic}
                return self.engine._recall(MockIntent(), topic)
            else:
                return f"Tool {name} is not recognized."
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"

    def chat(self, messages: list, system_prompt: str = "", use_tools: bool = True) -> dict:
        """
        Send a chat message sequence to the configured model.
        Returns a dict: {"content": str, "thinking": list_of_thought_steps, "tool_calls": list_of_calls}
        """
        if not self.is_available():
            return {"content": "LLM API Key not set. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY.", "thinking": [], "tool_calls": []}

        if self.provider == "anthropic":
            return self._chat_anthropic(messages, system_prompt, use_tools)
        elif self.provider == "openai":
            return self._chat_openai(messages, system_prompt, use_tools)
        return {"content": "No LLM provider available.", "thinking": [], "tool_calls": []}

    def _chat_anthropic(self, messages: list, system_prompt: str, use_tools: bool) -> dict:
        anth_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                if not system_prompt:
                    system_prompt = msg["content"]
                continue
            anth_messages.append({"role": role, "content": msg["content"]})

        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": anth_messages,
            "max_tokens": 4000,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if use_tools:
            kwargs["tools"] = self.get_tool_definitions("anthropic")

        try:
            response = self.anthropic_client.messages.create(**kwargs)
            content_text = ""
            tool_calls = []
            thinking = []

            for content_block in response.content:
                if content_block.type == "text":
                    content_text += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append({
                        "id": content_block.id,
                        "name": content_block.name,
                        "arguments": content_block.input
                    })
                elif hasattr(content_block, 'type') and content_block.type == "thinking":
                    thinking.append(content_block.thinking)

            return {
                "content": content_text,
                "thinking": thinking,
                "tool_calls": tool_calls
            }
        except Exception as e:
            return {"content": f"Anthropic error: {str(e)}", "thinking": [], "tool_calls": []}

    def _chat_openai(self, messages: list, system_prompt: str, use_tools: bool) -> dict:
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            if msg["role"] == "system" and system_prompt:
                continue
            openai_messages.append(msg)

        kwargs = {
            "model": "gpt-4o",
            "messages": openai_messages,
        }
        if use_tools:
            kwargs["tools"] = self.get_tool_definitions("openai")

        try:
            response = self.openai_client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            content_text = message.content or ""
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    })
            return {
                "content": content_text,
                "thinking": [],
                "tool_calls": tool_calls
            }
        except Exception as e:
            return {"content": f"OpenAI error: {str(e)}", "thinking": [], "tool_calls": []}
