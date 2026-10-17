"""
Play Prompt Output Node for ComfyUI
- Loads all prompts*.json in the package directory and merges plays
- Select / random play; select / random male type
- {male} replaced in visual fields
- Seed re-randomized every execution
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from comfy_api.latest import io


_PACKAGE_DIR = Path(__file__).parent
_CACHED_DATA: dict[str, Any] | None = None


def _load_prompts() -> dict[str, Any]:
    """Load and merge all prompts*.json files in the package directory."""
    global _CACHED_DATA
    if _CACHED_DATA is not None:
        return _CACHED_DATA

    files = sorted(_PACKAGE_DIR.glob("prompts*.json"))
    if not files:
        raise FileNotFoundError(
            f"No prompts*.json found in {_PACKAGE_DIR}. "
            "Place at least one prompts.json next to the node package."
        )

    merged_plays: list[dict[str, Any]] = []
    merged_males: list[dict[str, Any]] = []
    seen_play_ids: set[str] = set()
    seen_male_ids: set[str] = set()
    sources: list[str] = []

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sources.append(path.name)

        for male in data.get("male_types", []):
            mid = male.get("id") or male.get("name")
            if mid and mid not in seen_male_ids:
                seen_male_ids.add(mid)
                merged_males.append(male)

        for play in data.get("plays", []):
            pid = play.get("id") or play.get("name")
            if not pid:
                continue
            if pid in seen_play_ids:
                # later file overrides earlier with same id
                merged_plays = [p for p in merged_plays if (p.get("id") or p.get("name")) != pid]
            seen_play_ids.add(pid)
            merged_plays.append(play)

    _CACHED_DATA = {
        "version": "merged",
        "sources": sources,
        "male_types": merged_males,
        "plays": merged_plays,
    }
    return _CACHED_DATA


def _get_play_names() -> list[str]:
    try:
        data = _load_prompts()
        plays = data.get("plays", [])
        names = [p.get("name", p.get("id", f"play_{i}")) for i, p in enumerate(plays)]
        return names if names else ["(no plays loaded)"]
    except Exception:
        return ["(failed to load prompts)"]


def _get_male_type_names() -> list[str]:
    try:
        data = _load_prompts()
        types = data.get("male_types", [])
        names = [t.get("name", t.get("id", f"type_{i}")) for i, t in enumerate(types)]
        return names if names else ["(no male types)"]
    except Exception:
        return ["(failed to load prompts)"]


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
    patterns = play.get("patterns", [])
    if not patterns:
        return {
            "shot1": f"[ERROR] Play '{play.get('name', '?')}' has no patterns.",
            "shot2": f"[ERROR] Play '{play.get('name', '?')}' has no patterns.",
            "dialogue_shot1": "",
            "dialogue_shot2": "",
            "overall_soundscape": "",
            "summary_action": "",
            "camera_lock": "",
            "negative": "",
        }
    return rng.choice(patterns)


def _apply_male(text: str, male_prompt: str) -> str:
    if not text:
        return text or ""
    if "{male}" in text:
        return text.replace("{male}", male_prompt)
    return text


class PlayPromptOutput(io.ComfyNode):
    """Play prompt output with multi-JSON support."""

    @classmethod
    def define_schema(cls):
        play_names = _get_play_names()
        male_names = _get_male_type_names()

        return io.Schema(
            node_id="PlayPromptOutput",
            display_name="Play Prompt Output (Shot1/Shot2)",
            category="prompt/play",
            description=(
                "Loads all prompts*.json in the package, merges plays, "
                "outputs Shot1/Shot2, Japanese dialogue, soundscape, "
                "summary_action, camera_lock, negative. Seed changes every run."
            ),
            inputs=[
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
                    tooltip="Used only when mode=select.",
                ),
                io.Combo.Input(
                    "male_mode",
                    options=["select", "random"],
                    default="select",
                    tooltip="select or random male type",
                ),
                io.Combo.Input(
                    "male_type",
                    options=male_names,
                    default=male_names[0] if male_names else "Average man",
                    tooltip="Used only when male_mode=select.",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFFFFFFFFFF,
                    tooltip="Base seed; node forces a new random seed every execution.",
                ),
            ],
            outputs=[
                io.String.Output("Shot1"),
                io.String.Output("Shot2"),
                io.String.Output("Dialogue_Shot1"),
                io.String.Output("Dialogue_Shot2"),
                io.String.Output("overall_soundscape"),
                io.String.Output("summary_action"),
                io.String.Output("camera_lock"),
                io.String.Output("negative"),
                io.String.Output("play_name"),
                io.String.Output("pattern_id"),
                io.String.Output("male_type_name"),
                io.Int.Output("used_seed"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, mode, play, male_mode, male_type, seed):
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
            empty = "[ERROR] No plays defined in prompts*.json"
            return io.NodeOutput(
                empty, empty, "", "", "", empty, "", "", "", "", "", effective_seed
            )

        if mode == "select":
            selected_play = _find_play_by_name(play) or plays[0]
        else:
            selected_play = rng.choice(plays)

        pattern = _pick_pattern(selected_play, rng)

        if not male_types:
            male_prompt, male_name = "a man", "(none)"
        elif male_mode == "select":
            selected_male = _find_male_type_by_name(male_type) or male_types[0]
            male_prompt = selected_male.get("prompt", "a man")
            male_name = selected_male.get("name", selected_male.get("id", ""))
        else:
            selected_male = rng.choice(male_types)
            male_prompt = selected_male.get("prompt", "a man")
            male_name = selected_male.get("name", selected_male.get("id", ""))

        shot1 = _apply_male(pattern.get("shot1", ""), male_prompt)
        shot2 = _apply_male(pattern.get("shot2", ""), male_prompt)
        dialogue_shot1 = pattern.get("dialogue_shot1", "") or ""
        dialogue_shot2 = pattern.get("dialogue_shot2", "") or ""
        overall_soundscape = pattern.get("overall_soundscape", "") or ""
        summary_action = _apply_male(
            pattern.get("summary_action")
            or selected_play.get("description")
            or selected_play.get("name", ""),
            male_prompt,
        )
        camera_lock = pattern.get("camera_lock", "") or ""
        negative = pattern.get("negative", "") or ""
        play_name = selected_play.get("name", selected_play.get("id", ""))
        pattern_id = pattern.get("id", "")

        return io.NodeOutput(
            shot1,
            shot2,
            dialogue_shot1,
            dialogue_shot2,
            overall_soundscape,
            summary_action,
            camera_lock,
            negative,
            play_name,
            pattern_id,
            male_name,
            effective_seed,
        )


class ReloadPlayPrompts(io.ComfyNode):
    """Clear cache and reload all prompts*.json."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ReloadPlayPrompts",
            display_name="Reload Play Prompts JSON",
            category="prompt/play",
            description="Clears cache and reloads all prompts*.json in the package.",
            inputs=[
                io.Boolean.Input("reload", default=True, tooltip="Trigger reload."),
            ],
            outputs=[io.String.Output("status")],
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
            return io.NodeOutput(
                f"Reloaded. sources={data.get('sources')} "
                f"plays={len(data.get('plays', []))} "
                f"male_types={len(data.get('male_types', []))}"
            )
        except Exception as e:
            return io.NodeOutput(f"Reload failed: {e}")
