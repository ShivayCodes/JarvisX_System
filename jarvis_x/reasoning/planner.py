import re
from typing import Callable, Dict, List, Optional


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
        elif "recall" in goal_lower or "what do you know" in goal_lower:
            steps = self._plan_recall(goal)
        else:
            steps = [{"action": "unknown", "description": f"Process: {goal}"}]

        self.plans[goal] = steps
        return steps

    def _plan_find_files(self, goal: str) -> List[Dict]:
        match = re.search(r"for\s+(.+)", goal)
        query = match.group(1).strip() if match else "*"
        return [{"action": "find_files", "params": {"query": query}, "description": f"Search files matching '{query}'"}]

    def _plan_open_url(self, goal: str) -> List[Dict]:
        match = re.search(r"(https?://[^\s]+)", goal)
        url = match.group(1) if match else ""
        return [{"action": "web_open", "params": {"url": url}, "description": f"Open {url}"}]

    def _plan_system_info(self) -> List[Dict]:
        return [{"action": "sys_info", "params": {}, "description": "Gather system information"}]

    def _plan_learn(self, goal: str) -> List[Dict]:
        match = re.search(r"(?:remember|learn)\s+(.+)", goal)
        fact = match.group(1).strip() if match else goal
        return [{"action": "learn", "params": {"fact": fact}, "description": f"Remember: {fact}"}]

    def _plan_recall(self, goal: str) -> List[Dict]:
        topic = goal.split("about", 1)[-1].strip() if "about" in goal.lower() else goal
        return [{"action": "recall", "params": {"topic": topic}, "description": f"Recall: {topic}"}]

    def execute_plan(self, plan: List[Dict], engine) -> List[str]:
        results = []
        for step in plan:
            action = step.get("action")
            if action == "unknown":
                results.append(engine.process(step["description"]))
            else:
                results.append(engine.process(step["description"]))
        return results

    def plan_and_execute_agent(self, goal: str, local_ai, engine, on_thought_cb: Optional[Callable[[str], None]] = None) -> dict:
        thoughts = [f"Decomposing local agent goal: '{goal}'"]
        if on_thought_cb:
            on_thought_cb(thoughts[0])

        steps = self.decompose(goal)
        if steps and steps[0]["action"] != "unknown":
            action = steps[0]["action"]
            desc = steps[0]["description"]
            thoughts.append(f"Matching local tool found: '{action}'. Description: {desc}")
            if on_thought_cb:
                on_thought_cb(f"Selected Local Tool: {action}")
            res = self.execute_plan(steps, engine)
            final_res = res[0] if res else "Execution failed."
            return {"result": final_res, "thoughts": thoughts}

        thoughts.append("No direct system action matched. Querying offline knowledge base.")
        if on_thought_cb:
            on_thought_cb("Searching offline knowledge database...")
        res_dict = local_ai.query(goal)
        for thought in res_dict.get("thoughts", []):
            thoughts.append(thought)
        return {"result": res_dict.get("result", "I am still learning."), "thoughts": thoughts}
