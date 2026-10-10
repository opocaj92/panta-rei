"""Audio configuration contracts that do not require a sound device."""
import json
from pathlib import Path

import pytest

pygame = pytest.importorskip("pygame")
from game.core.audio_manager import AudioManager


class SilentMixer:
    def get_init(self):
        return False

    def init(self):
        raise OSError('No audio device')


def config(tmp_path, **updates):
    data = {'music': {}, 'ambience': {}, 'effects': {}, 'scenes': {}, 'volumes': {}}
    data.update(updates)
    path = tmp_path / 'audio.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return path


def test_no_audio_device_is_safe(tmp_path):
    manager = AudioManager(config(tmp_path), mixer=SilentMixer())
    assert not manager.available
    manager.enter_scene('scene_01')
    assert not manager.play_sfx('missing')
    manager.stop_music()
    manager.stop_ambience()
    manager.shutdown()


def test_volume_clamped_and_unknown_category_rejected(tmp_path):
    manager = AudioManager(config(tmp_path), mixer=SilentMixer())
    manager.set_volume('music', 5)
    manager.set_volume('master', -1)
    assert manager.volumes['music'] == 1
    assert manager.master_volume == 0
    with pytest.raises(ValueError):
        manager.set_volume('unknown', 0.5)


def test_invalid_asset_path_rejected(tmp_path):
    with pytest.raises(ValueError):
        AudioManager(config(tmp_path, music={'bad': '../secret.ogg'}), mixer=SilentMixer())


def test_scene_soundscape_can_be_left_unspecified(tmp_path):
    manager = AudioManager(config(tmp_path, scenes={'scene_02': {}}), mixer=SilentMixer())
    manager.enter_scene('scene_02')
    assert manager._current_scene == 'scene_02'

class FakeChannel:
    def __init__(self):
        self.volume = 1.0
        self.busy = False
        self.fade_duration = None

    def set_volume(self, value):
        self.volume = value

    def get_busy(self):
        return self.busy

    def play(self, sound, loops=0):
        self.busy = True

    def fadeout(self, duration):
        self.fade_duration = duration

    def stop(self):
        self.busy = False


class FakeMusic:
    def set_volume(self, volume):
        self.volume = volume


class FakeMixer:
    def __init__(self):
        self.channels = [FakeChannel() for _ in range(13)]
        self.music = FakeMusic()

    def get_init(self):
        return True

    def get_num_channels(self):
        return 13

    def set_num_channels(self, count):
        pass

    def Channel(self, index):
        return self.channels[index]


def test_effect_gain_survives_master_and_category_volume_changes(tmp_path):
    mixer = FakeMixer()
    manager = AudioManager(config(tmp_path), mixer=mixer)
    manager._sound = lambda category, name: object()
    assert manager.play_sfx('kiss', volume=0.25)
    assert mixer.channels[1].volume == pytest.approx(0.25)
    manager.set_volume('master', 0.6)
    assert mixer.channels[1].volume == pytest.approx(0.15)
    manager.set_volume('effects', 0.5)
    assert mixer.channels[1].volume == pytest.approx(0.075)


def test_loop_gain_updates_survive_volume_changes(tmp_path):
    mixer = FakeMixer()
    manager = AudioManager(config(tmp_path), mixer=mixer)
    manager._sound = lambda category, name: object()
    assert manager.play_loop_sfx('crescendo', volume=0.1)
    manager.set_sfx_volume('crescendo', 0.4)
    manager.set_volume('master', 0.5)
    assert mixer.channels[1].volume == pytest.approx(0.2)
    assert manager.play_loop_sfx('crescendo', volume=0.3)
    assert mixer.channels[1].volume == pytest.approx(0.15)


def test_effect_fade_is_independent_of_other_channels(tmp_path):
    mixer = FakeMixer()
    manager = AudioManager(config(tmp_path), mixer=mixer)
    manager._sound = lambda category, name: object()
    manager.play_sfx('shimmer')
    manager.play_sfx('piano')
    manager.fade_sfx('shimmer', fade_ms=400)
    assert mixer.channels[1].fade_duration == 400
    assert mixer.channels[2].fade_duration is None
    assert manager.is_sfx_playing('piano')
