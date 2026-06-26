import re
import json
from typing import List, Dict, Callable, Optional


class TaskPlanner:
    def __init__(self):
        self.plans = {}

    def decompose(self, goal: str, available_actions: List[str] = None) -> List[Dict]:
        goal_lower = goal.lower()
        steps = []

        if "find" in goal_lower and "file" in goal_lower:
            steps = self._plan_find_files(goal)
        elif "open" in goal_lower and ("site" in goal_lower or "url" in goal_lower):
            steps = self._plan_open_url(goal)
        elif "system" in goal_lower and "info" in goal_lower:
            steps = self._plan_system_info()
        elif "remember" in goal_lower or "learn" in goal_lower:
            steps = self._plan_learn(goal)
        else:
            steps = [{"action": "unknown", "description": f"Process: {goal}"}]

        self.plans[goal] = steps
        return steps

    def _plan_find_files(self, goal: str) -> List[Dict]:
        match = re.search(r'for\s+(.+)', goal)
        query = match.group(1).strip() if match else "*"
        return [
            {"action": "find_files", "params": {"query": query},
             "description": f"Search files matching '{query}'"}
        ]

    def _plan_open_url(self, goal: str) -> List[Dict]:
        match = re.search(r'(https?://[^\s]+)', goal)
        url = match.group(1) if match else ""
        return [
            {"action": "web_open", "params": {"url": url},
             "description": f"Open {url}"}
        ]

    def _plan_system_info(self) -> List[Dict]:
        return [
            {"action": "sys_info", "params": {},
             "description": "Gather system information"}
        ]

    def _plan_learn(self, goal: str) -> List[Dict]:
        match = re.search(r'(?:remember|learn)\s+(.+)', goal)
        fact = match.group(1).strip() if match else goal
        return [
            {"action": "learn", "params": {"fact": fact},
             "description": f"Remember: {fact}"}
        ]

    def execute_plan(self, plan: List[Dict], engine) -> List[str]:
        results = []
        for step in plan:
            action = step.get("action")
            if action == "unknown":
                results.append(engine.process(step["description"]))
            else:
                text = step["description"]
                results.append(engine.process(text))
        return results

    def plan_and_execute_agent(self, goal: str, llm, engine, on_thought_cb: Optional[Callable[[str], None]] = None) -> dict:
        """
        Executes an agentic reasoning loop using Claude/OpenAI tool calling.
        """
        thoughts = []
        messages = [
            {"role": "user", "content": goal}
        ]

        system_prompt = (
            "You are JARVIS-X, an advanced self-learning AI assistant.\n"
            "Critical thinking mode is active. When answering:\n"
            "1. Explain your reasoning and thinking process step-by-step.\n"
            "2. Use tools to search files, open websites, learn new facts, or recall them if necessary.\n"
            "3. Analyze outputs critically and correct course if something fails."
        )

        max_turns = 6
        final_answer = ""

        # Log initial thought
        init_thought = f"Analyzing goal: '{goal}'. Initializing critical thinking loop."
        thoughts.append(init_thought)
        if on_thought_cb:
            on_thought_cb(init_thought)

        for turn in range(max_turns):
            response = llm.chat(messages, system_prompt=system_prompt, use_tools=True)
            
            # Extract any thinking/reasoning blocks
            if response.get("thinking"):
                for thought in response["thinking"]:
                    thoughts.append(thought)
                    if on_thought_cb:
                        on_thought_cb(thought)

            # If there's text content, log it or append to final answer
            text_content = response.get("content", "").strip()
            if text_content:
                # We can treat non-tool intermediate text as thoughts/reasoning
                if response.get("tool_calls"):
                    thoughts.append(text_content)
                    if on_thought_cb:
                        on_thought_cb(text_content)
                else:
                    final_answer = text_content

            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                break

            # Handle tool calls
            # For Anthropic/OpenAI compatibility we need to construct assistant and tool message blocks
            assistant_content = []
            if text_content:
                assistant_content.append({"type": "text", "text": text_content})
            
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]
                tool_id = tool_call["id"]

                thought_msg = f"Executing function: '{tool_name}' with args: {json.dumps(tool_args)}"
                thoughts.append(thought_msg)
                if on_thought_cb:
                    on_thought_cb(thought_msg)

                # Execute tool
                tool_result = llm.execute_tool(tool_name, tool_args)
                result_msg = f"Function result: {tool_result}"
                thoughts.append(result_msg)
                if on_thought_cb:
                    on_thought_cb(result_msg)

                # Construct assistant content block for Anthropic
                if llm.provider == "anthropic":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_args
                    })

            if llm.provider == "anthropic":
                messages.append({"role": "assistant", "content": assistant_content})
                # Add tool responses
                for tool_call in tool_calls:
                    tool_id = tool_call["id"]
                    tool_name = tool_call["name"]
                    tool_result = llm.execute_tool(tool_name, tool_call["arguments"])
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": tool_result
                            }
                        ]
                    })
            else: # OpenAI fallback
                messages.append({
                    "role": "assistant",
                    "content": text_content,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])}
                        } for tc in tool_calls
                    ]
                })
                for tool_call in tool_calls:
                    tool_result = llm.execute_tool(tool_call["name"], tool_call["arguments"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["name"],
                        "content": tool_result
                    })

        if not final_answer:
            final_answer = "Thinking process completed but no final answer was generated."

        return {"result": final_answer, "thoughts": thoughts}
