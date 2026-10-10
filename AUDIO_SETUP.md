# Panta Rei — Audio setup

The audio engine is integrated but intentionally silent until you select sound files.

## Files and paths

Edit `data/audio/audio_config.json`. Audio paths are relative to `assets/`.
Suggested folders: `assets/audio/music/`, `assets/audio/ambience/`, and
`assets/audio/effects/`. Use `.ogg` for music and ambience, `.wav` or `.ogg`
for short effects.

Example (illustrative filenames; these files are not supplied):

```json
{
  "volumes": {"music": 0.65, "ambience": 0.7, "effects": 0.8},
  "music": {"river_theme": "audio/music/river_theme.ogg"},
  "ambience": {"river": "audio/ambience/river.ogg"},
  "effects": {"river_touch": "audio/effects/river_touch.wav"},
  "scenes": {
    "scene_04": {"music": "river_theme", "ambience": "river", "fade_ms": 1500},
    "scene_05": {"music": "river_theme", "ambience": "river"},
    "scene_06": {"music": null, "ambience": null, "fade_ms": 1200}
  }
}
```

The included configuration is silent and has entries for all twelve scenes.
Omitted `music`/`ambience` fields **inherit** the previous scene's sound;
explicit `null` **stops** it. Consecutive scenes using the same name keep
playback position rather than restarting. `fade_ms` fades in a new sound or
fades out a stopped sound; it is **not** a simultaneous two-track crossfade.

From a scene, trigger interaction effects with:

```python
self.game.audio.play_sfx('river_touch')
```

Other supported calls:

```python
self.game.audio.play_music('river_theme', fade_ms=1200, volume=0.6)
self.game.audio.play_ambience('river', fade_ms=1200)
self.game.audio.stop_music(fade_ms=1000)
self.game.audio.stop_ambience(fade_ms=1000)
self.game.audio.set_volume('master', 0.8)
self.game.audio.set_volume('effects', 0.5)
```

Music and ambience loop indefinitely; effects play once on one of eight
reserved channels. Missing files and unavailable audio devices do not crash
the game. They emit warnings instead. All scene configuration and playback
are managed by `AudioManager` (`game/core/audio_manager.py`).
