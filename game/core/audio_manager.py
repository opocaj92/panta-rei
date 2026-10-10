"""Centralized optional audio playback for music, ambience and effects.

Audio definitions are authored in data/audio/audio_config.json. Scenes request
logical sound names, never mixer channels or filesystem paths. A missing file
is silent (and warned about once); an unavailable audio device is also safe.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pygame

from .config import ASSETS_DIR, DATA_DIR

LOG = logging.getLogger(__name__)


class AudioManager:
    """Own the mixer, cached sounds, category volumes and scene soundscapes."""

    def __init__(self, config_path=None, *, mixer=None):
        self._mixer = mixer if mixer is not None else pygame.mixer
        path = Path(config_path) if config_path is not None else DATA_DIR / 'audio' / 'audio_config.json'
        with path.open(encoding='utf-8') as stream:
            self.config = json.load(stream)
        self._validate_config()
        self.master_volume = 1.0
        self.volumes = {name: float(self.config.get('volumes', {}).get(name, 1.0))
                        for name in ('music', 'ambience', 'effects')}
        self._sounds = {}
        self._missing = set()
        self._ready = False
        self._ambience_channel = None
        self._effect_channels = []
        self._active_effects = {}
        self._effect_gains = {}
        self._layers = {}
        self._ambience_name = None
        self._music_name = None
        self._music_gain = 1.0
        self._ambience_gain = 1.0
        self._current_scene = None
        self._initialize()

    def _validate_config(self):
        for category in ('music', 'ambience', 'effects'):
            definitions = self.config.get(category, {})
            if not isinstance(definitions, dict):
                raise ValueError(f'Audio {category} definitions must be an object')
            for name, relative in definitions.items():
                if not isinstance(relative, str) or not relative:
                    raise ValueError(f'Audio asset {category}.{name} needs a path')
                path = Path(relative)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError(f'Audio asset path must be relative: {relative!r}')
        if not isinstance(self.config.get('scenes', {}), dict):
            raise ValueError('Audio scenes must be an object')

    def _initialize(self):
        try:
            if not self._mixer.get_init():
                self._mixer.init()
            self._ready = True
            # Reserve dedicated channels so effects cannot interrupt ambience.
            self._mixer.set_num_channels(max(13, self._mixer.get_num_channels()))
            self._ambience_channel = self._mixer.Channel(0)
            self._effect_channels = [self._mixer.Channel(i) for i in range(1, 9)]
        except (pygame.error, OSError) as exc:
            LOG.warning('Audio unavailable; continuing silently: %s', exc)
            self._ready = False

    @property
    def available(self):
        return self._ready

    def _path(self, category, name):
        relative = self.config.get(category, {}).get(name)
        if relative is None:
            self._warn_once((category, name), f'Undefined audio {category}: {name}')
            return None
        path = ASSETS_DIR / relative
        if not path.is_file():
            self._warn_once((category, name), f'Missing audio file: {path}')
            return None
        return path

    def _warn_once(self, key, message):
        if key not in self._missing:
            self._missing.add(key)
            LOG.warning(message)

    def _sound(self, category, name):
        key = (category, name)
        if key not in self._sounds:
            path = self._path(category, name)
            if path is None or not self._ready:
                return None
            try:
                self._sounds[key] = self._mixer.Sound(str(path))
            except (pygame.error, OSError) as exc:
                self._warn_once(key, f'Could not load audio {path}: {exc}')
                return None
        return self._sounds[key]

    @staticmethod
    def _clamp(volume):
        return max(0.0, min(1.0, float(volume)))

    def set_volume(self, category, value):
        """Set master, music, ambience or effects volume in [0, 1]."""
        value = self._clamp(value)
        if category == 'master':
            self.master_volume = value
        elif category in self.volumes:
            self.volumes[category] = value
        else:
            raise ValueError(f'Unknown audio category: {category}')
        self._apply_volumes()

    def _apply_volumes(self):
        if not self._ready:
            return
        self._mixer.music.set_volume(self._clamp(self.master_volume * self.volumes['music'] * self._music_gain))
        self._ambience_channel.set_volume(self._clamp(self.master_volume * self.volumes['ambience'] * self._ambience_gain))
        for channel in self._effect_channels:
            channel.set_volume(self._clamp(self.master_volume * self.volumes['effects'] * self._effect_gains.get(channel, 1.0)))
        for layer in self._layers.values():
            self._apply_layer_volume(layer)

    def play_music(self, name, *, fade_ms=0, volume=1.0, restart=False):
        if name is None:
            self.stop_music(fade_ms=fade_ms)
            return
        if name == self._music_name and not restart:
            self._music_gain = self._clamp(volume)
            self._apply_volumes()
            return
        path = self._path('music', name)
        if not self._ready or path is None:
            return
        try:
            self._mixer.music.load(str(path))
            self._music_name = name
            self._music_gain = self._clamp(volume)
            self._apply_volumes()
            self._mixer.music.play(loops=-1, fade_ms=max(0, int(fade_ms)))
        except (pygame.error, OSError) as exc:
            self._warn_once(('music', name, 'load'), f'Cannot play music {name}: {exc}')

    def pause_music(self):
        """Suspend music without losing its playback position."""
        if self._ready:
            self._mixer.music.pause()

    def resume_music(self):
        if self._ready and self._music_name is not None:
            self._mixer.music.unpause()

    def is_sfx_playing(self, name):
        channel = self._active_effects.get(name)
        return bool(channel and channel.get_busy())

    def stop_music(self, *, fade_ms=0):
        if self._ready:
            if fade_ms > 0:
                self._mixer.music.fadeout(int(fade_ms))
            else:
                self._mixer.music.stop()
        self._music_name = None

    def play_ambience(self, name, *, fade_ms=0, volume=1.0, restart=False):
        if name is None:
            self.stop_ambience(fade_ms=fade_ms)
            return
        if name == self._ambience_name and not restart:
            self._ambience_gain = self._clamp(volume)
            self._apply_volumes()
            return
        sound = self._sound('ambience', name)
        if sound is None:
            return
        self._ambience_name = name
        self._ambience_gain = self._clamp(volume)
        self._apply_volumes()
        self._ambience_channel.play(sound, loops=-1, fade_ms=max(0, int(fade_ms)))

    def stop_ambience(self, *, fade_ms=0):
        if self._ready:
            if fade_ms > 0:
                self._ambience_channel.fadeout(int(fade_ms))
            else:
                self._ambience_channel.stop()
        self._ambience_name = None

    def _apply_layer_volume(self, layer):
        if self._ready:
            layer['channel'].set_volume(self._clamp(
                self.master_volume * self.volumes['ambience'] * layer['gain']))

    def start_ambience_layers(self, definitions):
        """Start named, continuously looping ambience on reserved channels 9-12.

        definitions maps a layer name to an ambience asset name. A layer stays
        playing when its gain is zero, so returning to a view never restarts it.
        """
        self.stop_ambience_layers()
        if not self._ready:
            return
        if len(definitions) > 4:
            raise ValueError('At most four concurrent ambience layers supported')
        for index, (layer_name, sound_name) in enumerate(definitions.items()):
            sound = self._sound('ambience', sound_name)
            if sound is None:
                continue
            channel = self._mixer.Channel(9 + index)
            layer = {'channel': channel, 'gain': 0.0, 'from': 0.0,
                     'target': 0.0, 'elapsed': 0.0, 'duration': 0.0}
            self._layers[layer_name] = layer
            channel.set_volume(0.0)
            channel.play(sound, loops=-1)

    def replace_ambience_layer_sound(self, name, sound_name):
        """Change one looping layer's recording without restarting other layers."""
        layer = self._layers.get(name)
        if layer is None:
            return False
        sound = self._sound('ambience', sound_name)
        if sound is None:
            return False
        layer['channel'].play(sound, loops=-1)
        self._apply_layer_volume(layer)
        return True

    def set_ambience_layer_volume(self, name, volume, *, fade_ms=0):
        layer = self._layers.get(name)
        if layer is None:
            return
        layer['from'] = layer['gain']
        layer['target'] = self._clamp(volume)
        layer['elapsed'] = 0.0
        layer['duration'] = max(0.0, float(fade_ms) / 1000.0)
        if not layer['duration']:
            layer['gain'] = layer['target']
            self._apply_layer_volume(layer)

    def update_ambience_layers(self, dt):
        """Advance smooth gain changes using game time, independent of FPS."""
        for layer in self._layers.values():
            if layer['gain'] == layer['target']:
                continue
            layer['elapsed'] += max(0.0, dt)
            fraction = min(1.0, layer['elapsed'] / max(layer['duration'], 1e-6))
            layer['gain'] = layer['from'] + (layer['target'] - layer['from']) * fraction
            self._apply_layer_volume(layer)

    def stop_ambience_layers(self):
        for layer in self._layers.values():
            layer['channel'].stop()
        self._layers.clear()

    def play_sfx(self, name, *, volume=1.0):
        """Play a one-shot effect; drop it if all effect channels are occupied."""
        sound = self._sound('effects', name)
        if sound is None:
            return False
        for channel in self._effect_channels:
            if not channel.get_busy():
                self._effect_gains[channel] = self._clamp(volume)
                channel.set_volume(self._clamp(self.master_volume * self.volumes['effects'] * self._effect_gains[channel]))
                channel.play(sound)
                self._active_effects[name] = channel
                return True
        return False

    def play_loop_sfx(self, name, *, volume=1.0):
        """Loop an effect on a free effects channel, without touching ambience."""
        channel = self._active_effects.get(name)
        if channel is not None and channel.get_busy():
            self.set_sfx_volume(name, volume)
            return True
        sound = self._sound('effects', name)
        if sound is None:
            return False
        for channel in self._effect_channels:
            if not channel.get_busy():
                self._effect_gains[channel] = self._clamp(volume)
                channel.set_volume(self._clamp(self.master_volume * self.volumes['effects'] * self._effect_gains[channel]))
                channel.play(sound, loops=-1)
                self._active_effects[name] = channel
                return True
        return False

    def set_sfx_volume(self, name, volume):
        """Adjust the volume of a named playing effect."""
        channel = self._active_effects.get(name)
        if channel is not None and channel.get_busy():
            self._effect_gains[channel] = self._clamp(volume)
            channel.set_volume(self._clamp(self.master_volume * self.volumes['effects'] * self._effect_gains[channel]))

    def fade_sfx(self, name, *, fade_ms=0):
        """Fade a currently playing named effect without affecting other sounds."""
        channel = self._active_effects.pop(name, None)
        if channel is None or not self._ready:
            return
        if channel.get_busy():
            if fade_ms > 0:
                channel.fadeout(max(0, int(fade_ms)))
            else:
                channel.stop()

    def enter_scene(self, name):
        """Apply scene soundscape; absent keys inherit the previous soundscape.

        Set music/ambience explicitly to null to stop them. Identical track
        names continue uninterrupted across adjacent scenes.
        """
        self._current_scene = name
        settings = self.config.get('scenes', {}).get(name, {})
        if not isinstance(settings, dict):
            raise ValueError(f'Audio scene {name} must be an object')
        fade_ms = max(0, int(settings.get('fade_ms', 0)))
        if 'music' in settings:
            self.play_music(settings['music'], fade_ms=fade_ms,
                            volume=settings.get('music_volume', 1.0))
        if 'ambience' in settings:
            self.play_ambience(settings['ambience'], fade_ms=fade_ms,
                               volume=settings.get('ambience_volume', 1.0))

    def silence(self):
        """Stop every audio category immediately for deliberately silent scenes."""
        self.stop_music()
        self.stop_ambience()
        self.stop_ambience_layers()
        if self._ready:
            for channel in self._effect_channels:
                channel.stop()
        self._active_effects.clear()
        self._effect_gains.clear()

    def shutdown(self):
        if self._ready:
            self.stop_music()
            self.stop_ambience()
            self.stop_ambience_layers()
            for channel in self._effect_channels:
                channel.stop()
