from __future__ import annotations

from typing import Iterable

from jarvis_x.core.config import Config


class HuggingFaceBackend:
    """Local instruction-model backend with lazy loading and safe fallbacks."""

    def __init__(self, model_id: str | None = None):
        self.model_id = model_id or Config.HF_MODEL_ID
        self._tokenizer = None
        self._model = None

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    def _load(self) -> None:
        if self._model is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        self._model.eval()

    def chat(
        self,
        messages: Iterable[dict],
        max_new_tokens: int | None = None,
    ) -> str:
        self._load()
        import torch

        messages = list(messages)
        try:
            prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except (AttributeError, ValueError):
            prompt = "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                for m in messages
            ) + "\nASSISTANT:"

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=min(
                getattr(self._tokenizer, "model_max_length", 4096), 4096
            ),
        )

        with torch.inference_mode():
            output = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens or Config.HF_MAX_NEW_TOKENS,
                do_sample=Config.HF_TEMPERATURE > 0,
                temperature=max(Config.HF_TEMPERATURE, 1e-5),
                top_p=Config.HF_TOP_P,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        generated = output[0][inputs["input_ids"].shape[-1]:]
        return self._tokenizer.decode(
            generated, skip_special_tokens=True
        ).strip()

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
