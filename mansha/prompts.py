"""Loads agent prompts from the prompts/ folder and prepends the shared rules."""
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

LANGUAGE_NAMES = {"ar": "Arabic", "en": "English"}


def load_prompt(name: str) -> str:
    """Read prompts/<name>.md."""
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


def build_system_prompt(agent: str, language: str | None = None) -> str:
    """Shared rules + the agent's own prompt.

    `language` ("ar"/"en") is only known after Intake; earlier agents get a neutral phrase.
    """
    language_text = LANGUAGE_NAMES.get(language or "", "the user's language")
    shared = load_prompt("shared_rules").replace("{language}", language_text)
    return f"{shared}\n\n{load_prompt(agent)}"