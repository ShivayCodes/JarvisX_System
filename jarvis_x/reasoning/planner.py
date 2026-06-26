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

    def plan_and_execute_agent(self, goal: str, local_ai, engine, on_thought_cb: Optional[Callable[[str], None]] = None) -> dict:
        """
        Executes a fully local reasoning loop.
        Decomposes the goal, executes matching local tools, and integrates results.
        """
        thoughts = []
        
        init_thought = f"Decomposing local agent goal: '{goal}'"
        thoughts.append(init_thought)
        if on_thought_cb:
            on_thought_cb(init_thought)

        steps = self.decompose(goal)
        
        # If the goal matches a known system action
        if steps and steps[0]["action"] != "unknown":
            step = steps[0]
            action = step["action"]
            desc = step["description"]
            
            thoughts.append(f"Matching local tool found: '{action}'. Description: {desc}")
            if on_thought_cb:
                on_thought_cb(f"Selected Local Tool: {action}")

            # Run the tool
            res = self.execute_plan(steps, engine)
            final_res = res[0] if res else "Execution failed."
            return {"result": final_res, "thoughts": thoughts}

        # Otherwise, fall back to semantic search & synthesis
        thoughts.append("No direct system action matched. Querying offline knowledge base.")
        if on_thought_cb:
            on_thought_cb("Searching offline knowledge database...")
            
        res_dict = local_ai.query(goal)
        for t in res_dict.get("thoughts", []):
            thoughts.append(t)
            
        return {
            "result": res_dict.get("result", "I am still learning."),
            "thoughts": thoughts
        }
