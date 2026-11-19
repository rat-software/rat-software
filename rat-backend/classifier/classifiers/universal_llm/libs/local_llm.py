"""
Local in-process LLM backend for the Universal LLM Classifier.

Runs models directly inside the classifier process (no Ollama / HTTP server)
using Apple's MLX framework on macOS with Apple Silicon (Metal GPU).

Activated by setting the task's base_url to a local scheme, e.g.:
    mlx://local
and the model to a Hugging Face repo id or a local directory, e.g.:
    mlx-community/Qwen2.5-7B-Instruct-4bit
    /Users/me/models/my-mlx-model
"""

import gc
import platform
import re
import sys

LOCAL_SCHEMES = ("mlx://", "local://")


def is_local_base_url(base_url: str) -> bool:
    """True if the task should run in-process instead of via an HTTP API."""
    return (base_url or "").strip().lower().startswith(LOCAL_SCHEMES)


def local_backend_available() -> tuple:
    """Returns (available: bool, reason: str)."""
    if sys.platform != "darwin" or platform.machine() != "arm64":
        return False, "Local MLX inference requires macOS on Apple Silicon (arm64)."
    try:
        import mlx_lm  # noqa: F401
    except ImportError:
        return False, "mlx-lm is not installed. Run: pip install mlx-lm"
    return True, ""


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class LocalLlmBackend:
    """Loads an MLX model once and serves chat completions in-process."""

    def __init__(self, model_name: str):
        ok, reason = local_backend_available()
        if not ok:
            raise RuntimeError(reason)

        from mlx_lm import load

        self.model_name = model_name
        self.model, self.tokenizer = load(model_name)

    def _build_prompt(self, messages):
        kwargs = {"add_generation_prompt": True, "tokenize": True}
        try:
            # Disable "thinking" mode for reasoning models (e.g. Qwen3) - we need pure JSON.
            return self.tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs)
        except TypeError:
            return self.tokenizer.apply_chat_template(messages, **kwargs)
        except Exception:
            # Some templates reject a system role -> merge it into the first user message.
            if messages and messages[0]["role"] == "system":
                merged = [{"role": "user", "content": f"{messages[0]['content']}\n\n{messages[1]['content']}"}] + messages[2:]
                return self.tokenizer.apply_chat_template(merged, **kwargs)
            raise

    def chat(self, messages, max_tokens: int = 250, temperature: float = 0.1):
        """
        Generates a completion for OpenAI-style chat messages.
        Returns (text, finish_reason) with finish_reason in {'stop', 'length', None}.
        """
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler

        prompt = self._build_prompt(messages)
        sampler = make_sampler(temp=temperature)

        parts = []
        finish_reason = None
        for response in stream_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens, sampler=sampler):
            parts.append(response.text)
            finish_reason = response.finish_reason or finish_reason

        text = _THINK_RE.sub("", "".join(parts)).strip()
        return text, finish_reason

    def unload(self):
        """Releases the model and frees unified memory for the next task."""
        self.model = None
        self.tokenizer = None
        gc.collect()
        try:
            import mlx.core as mx
            if hasattr(mx, "clear_cache"):
                mx.clear_cache()
            elif hasattr(mx, "metal") and hasattr(mx.metal, "clear_cache"):
                mx.metal.clear_cache()
        except Exception:
            pass
