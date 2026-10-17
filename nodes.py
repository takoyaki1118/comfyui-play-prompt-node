"""
Play Prompt Output Node for ComfyUI
- Selects or randomly picks a play from prompts.json
- Even in select mode, if the chosen play has multiple patterns, one is chosen at random
- Male type (Black / fat / old / muscular / ...) can be selected or randomized
- {male} placeholder in prompts is replaced with the chosen male description
- Outputs Shot1 and Shot2 English prompts with slight variations
- Seed is re-randomized on every execution (not_idempotent)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from comfy_api.latest import io
from typing_extensions import override


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROMPTS_PATH = Path(__file__).parent / "prompts.json"
_CACHED_DATA: dict[str, Any] | None = None


def _load_prompts() -> dict[str, Any]:
    """Load and cache the prompts JSON."""
    global _CACHED_DATA
    if _CACHED_DATA is None:
        if not _PROMPTS_PATH.exists():
            raise FileNotFoundError(
                f"prompts.json not found at {_PROMPTS_PATH}. "
                "Place the play list JSON next to the node package."
            )
        with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
            _CACHED_DATA = json.load(f)
    return _CACHED_DATA


def _get_play_names() -> list[str]:
    try:
        data = _load_prompts()
        plays = data.get("plays", [])
        names = [p.get("name", p.get("id", f"play_{i}")) for i, p in enumerate(plays)]
        return names if names else ["(no plays loaded)"]
    except Exception:
        return ["(failed to load prompts.json)"]


def _get_male_type_names() -> list[str]:
    try:
        data = _load_prompts()
        types = data.get("male_types", [])
        names = [t.get("name", t.get("id", f"type_{i}")) for i, t in enumerate(types)]
        return names if names else ["(no male types)"]
    except Exception:
        return ["(failed to load prompts.json)"]


def _find_play_by_name(name: str) -> dict[str, Any] | None:
    data = _load_prompts()
    for play in data.get("plays", []):
        if play.get("name") == name or play.get("id") == name:
            return play
    return None


def _find_male_type_by_name(name: str) -> dict[str, Any] | None:
    data = _load_prompts()
    for t in data.get("male_types", []):
        if t.get("name") == name or t.get("id") == name:
            return t
    return None


def _pick_pattern(play: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """Pick one pattern from the play's patterns list (always random among them)."""
    patterns = play.get("patterns", [])
    if not patterns:
        return {
            "shot1": f"[ERROR] Play '{play.get('name', '?')}' has no patterns.",
            "shot2": f"[ERROR] Play '{play.get('name', '?')}' has no patterns.",
        }
    return rng.choice(patterns)


def _apply_male(text: str, male_prompt: str) -> str:
    """Replace {male} placeholder. If no placeholder, leave text unchanged."""
    if "{male}" in text:
        return text.replace("{male}", male_prompt)
    return text


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class PlayPromptOutput(io.ComfyNode):
    """
    Outputs Shot1 / Shot2 text prompts based on play content stored in prompts.json.

    Play modes
    ----------
    - select : User chooses a play by name. If that play has multiple patterns,
               one pattern is still chosen at random.
    - random : A play is chosen uniformly at random, then a pattern from it.

    Male type modes
    ---------------
    - select : User chooses a specific male type (Black man, fat man, old man, ...).
    - random : A male type is chosen uniformly at random.

    The chosen male description replaces the {male} placeholder in the prompt.
    If a pattern has no {male}, the male_type setting is ignored for that pattern.

    Seed
    ----
    Forced random on every execution (not_idempotent + fingerprint_inputs).
    """

    @classmethod
    def define_schema(cls):
        play_names = _get_play_names()
        male_names = _get_male_type_names()

        return io.Schema(
            node_id="PlayPromptOutput",
            display_name="Play Prompt Output (Shot1/Shot2)",
            category="prompt/play",
            description=(
                "Select or randomly pick a play and a male type from prompts.json, "
                "then output English Shot1 / Shot2 prompts plus a summary_action. "
                "{male} placeholders are replaced with the chosen male description. "
                "Multiple patterns under one play are always randomized even in select mode. "
                "Seed changes every run."
            ),
            inputs=[
                # --- Play ---
                io.Combo.Input(
                    "mode",
                    options=["select", "random"],
                    default="random",
                    tooltip="select = choose a specific play; random = pick any play",
                ),
                io.Combo.Input(
                    "play",
                    options=play_names,
                    default=play_names[0],
                    tooltip="Used only when mode=select. Ignored in random mode.",
                ),
                # --- Male type ---
                io.Combo.Input(
                    "male_mode",
                    options=["select", "random"],
                    default="select",
                    tooltip="select = choose a specific male type; random = pick any type",
                ),
                io.Combo.Input(
                    "male_type",
                    options=male_names,
                    default=male_names[0] if male_names else "Average man",
                    tooltip="Used only when male_mode=select. Replaces {male} in prompts.",
                ),
                # --- Seed ---
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFFFFFFFFFF,
                    tooltip=(
                        "Base seed (for reference). The node forces a new random "
                        "seed on every execution so results differ each run."
                    ),
                ),
            ],
            outputs=[
                io.String.Output("Shot1"),
                io.String.Output("Shot2"),
                io.String.Output("summary_action"),
                io.String.Output("play_name"),
                io.String.Output("pattern_id"),
                io.String.Output("male_type_name"),
                io.Int.Output("used_seed"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, mode, play, male_mode, male_type, seed):
        """Force re-execution on every run."""
        import time
        return time.time_ns()

    @classmethod
    def execute(cls, mode: str, play: str, male_mode: str, male_type: str, seed: int):
        effective_seed = random.randint(0, 0xFFFFFFFFFFFFFFFF)
        rng = random.Random(effective_seed)

        data = _load_prompts()
        plays = data.get("plays", [])
        male_types = data.get("male_types", [])

        if not plays:
            empty = "[ERROR] No plays defined in prompts.json"
            return io.NodeOutput(empty, empty, empty, "", "", "", effective_seed)

        # ----- Select play -----
        if mode == "select":
            selected_play = _find_play_by_name(play)
            if selected_play is None:
                selected_play = plays[0]
        else:
            selected_play = rng.choice(plays)

        pattern = _pick_pattern(selected_play, rng)

        # ----- Select male type -----
        if not male_types:
            male_prompt = "a man"
            male_name = "(none)"
        elif male_mode == "select":
            selected_male = _find_male_type_by_name(male_type)
            if selected_male is None:
                selected_male = male_types[0]
            male_prompt = selected_male.get("prompt", "a man")
            male_name = selected_male.get("name", selected_male.get("id", ""))
        else:
            selected_male = rng.choice(male_types)
            male_prompt = selected_male.get("prompt", "a man")
            male_name = selected_male.get("name", selected_male.get("id", ""))

        # ----- Apply {male} -----
        shot1 = _apply_male(pattern.get("shot1", ""), male_prompt)
        shot2 = _apply_male(pattern.get("shot2", ""), male_prompt)

        # summary_action: prefer pattern-level field, else play description
        summary_action = (
            pattern.get("summary_action")
            or selected_play.get("description")
            or selected_play.get("name", "")
        )

        play_name = selected_play.get("name", selected_play.get("id", ""))
        pattern_id = pattern.get("id", "")

        return io.NodeOutput(
            shot1,
            shot2,
            summary_action,
            play_name,
            pattern_id,
            male_name,
            effective_seed,
        )


# ---------------------------------------------------------------------------
# Reload helper
# ---------------------------------------------------------------------------

class ReloadPlayPrompts(io.ComfyNode):
    """Force-reload prompts.json from disk (clears the in-memory cache)."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ReloadPlayPrompts",
            display_name="Reload Play Prompts JSON",
            category="prompt/play",
            description="Clears the cached prompts.json so the next PlayPromptOutput run reads the latest file.",
            inputs=[
                io.Boolean.Input(
                    "reload",
                    default=True,
                    tooltip="Trigger reload (value is ignored; just connect or toggle).",
                ),
            ],
            outputs=[
                io.String.Output("status"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, reload):
        import time
        return time.time_ns()

    @classmethod
    def execute(cls, reload: bool):
        global _CACHED_DATA
        _CACHED_DATA = None
        try:
            data = _load_prompts()
            play_count = len(data.get("plays", []))
            male_count = len(data.get("male_types", []))
            return io.NodeOutput(
                f"Reloaded successfully. {play_count} play(s), {male_count} male type(s) loaded."
            )
        except Exception as e:
            return io.NodeOutput(f"Reload failed: {e}")
