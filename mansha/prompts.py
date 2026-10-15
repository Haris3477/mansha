"""Load agent prompts from prompts/ and build each agent's system prompt."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

LANGUAGE_NAMES = {"ar": "Arabic", "en": "English"}


def load_prompt(name: str) -> str:
    """Return the text of prompts/<name>.md."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_system_prompt(agent: str, language: str | None = None) -> str:
    """Shared rules + the agent's own prompt, with {language} filled in both.

    language: "ar", "en", or None (before Intake has run).
    """
    language_name = LANGUAGE_NAMES.get(language or "", "the user's language")
    text = f"{load_prompt('shared_rules')}\n\n{load_prompt(agent)}"
    return text.replace("{language}", language_name)