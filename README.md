# Panta Rei

A small 2D narrative game built with Python and Pygame. The current project is a 12-scene narrative game combining authored pixel-art assets, animations, and reusable scene systems. Some presentation details may still be refined.

## Run

Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
python main.py
```

## Language

At startup the game reads the system locale. Italian locales use Italian; every other locale uses English. Dialogue lives in `data/dialogue/it/` and `data/dialogue/en/`, with English as the runtime fallback.

## Contextual help

Interactive scenes automatically display a localized control hint after a period without meaningful progress. Hints disappear after a few seconds or when the player makes progress; non-interactive scenes have no hint.

## Scenes

1. Establishing shot and title.
2. Marco POV gaze interaction.
3. Black-screen dialogue interlude.
4. Follow the river to the estuary.
5. Trace a possible river/sea boundary.
6. Black-screen dialogue interlude.
7. Stella POV: raise her gaze from the phone to Marco.
8. Stella may move closer to Marco; the approach is intentionally one-way.
9. Mirrored silhouettes join briefly, then separate.
10. The river joins the sea irreversibly.
11. Marco looks from Stella to the night sky.
12. Credits scroll inside Stella's phone, then the game fades permanently to black.

## Architecture

The project follows one guiding rule: **JSON says what; Python says how; assets say what it looks/sounds like.**

- `game/core/`: reusable infrastructure: game loop, scene management, dialogue state, localization, assets, transitions, input, validation, and shared world-data loading.
- `game/scenes/`: narrative ownership. Each scene explicitly owns its progression/state machine and decides which presentation/interaction mechanisms it uses.
- `game/systems/`: optional reusable interactions such as gaze interpretation and hand tracing.
- `game/rendering/`: presentation only. Renderers draw shared worlds/characters/UI but do not decide narrative progression. `TextRenderer` owns dialogue/thought/help presentation while `DialogueManager` owns dialogue state and timing.
- `data/scenes/`: scene-specific timings, thresholds, transitions, controls/help, and interaction parameters.
- `data/dialogue/{it,en}/`: localized dialogue plus per-line typewriter speed.
- `data/worlds/`: authored geometry shared by multiple scenes; Scenes 04 and 05 use the same river/estuary definition.
- `assets/`: final artwork, animation, fonts, and audio.

The architecture deliberately avoids a generic scripted-scene framework: unusual narrative mechanics remain explicit in their scene files.

## Input conventions

`InputManager` provides frame-level input state and held-key queries for continuous controls. Scenes may still consume raw Pygame events when event semantics matter (for example, Scene 11 requires a fresh keypress after dialogue and intentionally does not buffer an earlier press).

## Tests

Run the lightweight structural/regression checks with:

```bash
python -m unittest discover -s tests -v
```

They verify localization parity, scene/config references, shared world data, locale normalization, and important irreversible interaction invariants.

## Dialogue controls

Dialogue advances manually. Press **Enter** or **Backspace** while a line is typing to reveal it immediately; press either key again once the line is complete to advance to the next line.
