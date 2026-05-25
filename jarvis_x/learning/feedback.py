from jarvis_x.memory.store import KnowledgeBase


class FeedbackHandler:
    def __init__(self, kb: KnowledgeBase = None):
        self.kb = kb

    def record(self, user_input: str, positive: bool):
        if self.kb:
            self.kb.record_feedback(user_input, positive)

    def adjust_confidence(self, intent_action: str, positive: bool, kb: KnowledgeBase):
        delta = 0.1 if positive else -0.05
        cur = kb.conn.execute(
            "SELECT id, confidence FROM knowledge WHERE pattern LIKE ?",
            (f"%{intent_action}%",)
        )
        row = cur.fetchone()
        if row:
            new_conf = max(0.1, min(1.0, row["confidence"] + delta))
            with kb.conn:
                kb.conn.execute(
                    "UPDATE knowledge SET confidence = ? WHERE id = ?",
                    (new_conf, row["id"])
                )
            kb.log_learning("confidence_adjust", f"{intent_action}: {row['confidence']}->{new_conf}")
