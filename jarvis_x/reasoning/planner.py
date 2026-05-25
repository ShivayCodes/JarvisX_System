import re
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
