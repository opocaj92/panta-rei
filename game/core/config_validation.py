import math

KNOWN_TRANSITIONS = {"none", "fade_to_black", "fade_from_black", "eye_blink"}


def _require(mapping, keys, context):
    if not isinstance(mapping, dict):
        raise ValueError(f"{context} must be an object")
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise ValueError(f"{context} missing required keys: {', '.join(missing)}")


def _finite_number(value, context):
    if isinstance(value, bool):
        raise ValueError(f"{context} must be a finite number, got {value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} must be a finite number, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{context} must be a finite number, got {value!r}")
    return number


def _positive(value, context, *, allow_zero=False):
    number = _finite_number(value, context)
    valid = number >= 0 if allow_zero else number > 0
    if not valid:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{context} must be {qualifier}, got {value!r}")
    return number


def _fraction(value, context):
    number = _finite_number(value, context)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{context} must be between 0 and 1, got {value!r}")
    return number


def validate_scene_config(name, config):
    """Fail early on malformed authored scene data without owning scene behavior."""
    _require(config, ("id", "type"), name)
    if config["id"] != name:
        raise ValueError(
            f"Scene config id mismatch: expected {name!r}, got {config['id']!r}"
        )

    for key in ("transition_in", "transition_out"):
        transition = config.get(key)
        if transition is None:
            continue
        _require(transition, ("type", "duration"), f"{name}.{key}")
        if transition["type"] not in KNOWN_TRANSITIONS:
            raise ValueError(
                f"Unknown transition type in {name}.{key}: {transition['type']!r}"
            )
        _positive(transition["duration"], f"{name}.{key}.duration", allow_zero=True)

    help_cfg = config.get("help")
    if isinstance(help_cfg, dict):
        _require(help_cfg, ("it", "en"), f"{name}.help")

    for key in ("help_delay", "help_duration", "post_dialogue_delay", "post_complete_delay", "auto_delay"):
        if key in config:
            _positive(config[key], f"{name}.{key}", allow_zero=True)
    if "next_scene" in config:
        from game.core.config import DATA_DIR
        destination = config["next_scene"]
        if not isinstance(destination, str) or not (DATA_DIR / "scenes" / f"{destination}.json").is_file():
            raise ValueError(f"{name}.next_scene refers to an unknown scene: {destination!r}")
    presentation = config.get("presentation", {})
    if not isinstance(presentation, dict):
        raise ValueError(f"{name}.presentation must be an object")
    if "stella_placement" in presentation:
        placement = presentation["stella_placement"]
        _require(placement, ("scale", "offset"), f"{name}.presentation.stella_placement")
        _positive(placement["scale"], f"{name}.presentation.stella_placement.scale")
        if not isinstance(placement["offset"], (list, tuple)) or len(placement["offset"]) != 2:
            raise ValueError(f"{name}.presentation.stella_placement.offset must be [x, y]")
        for axis, value in zip(("x", "y"), placement["offset"]):
            _finite_number(value, f"{name}.presentation.stella_placement.offset.{axis}")
    if "marco" in presentation:
        marco = presentation["marco"]
        _require(marco, ("height", "left", "bottom"), f"{name}.presentation.marco")
        _positive(marco["height"], f"{name}.presentation.marco.height")
        for axis in ("left", "bottom"):
            _finite_number(marco[axis], f"{name}.presentation.marco.{axis}")
    if "phone_glass_rect" in presentation:
        rect = presentation["phone_glass_rect"]
        if not isinstance(rect, list) or len(rect) != 4:
            raise ValueError(f"{name}.presentation.phone_glass_rect must be [x, y, width, height]")
        for index, value in enumerate(rect):
            _finite_number(value, f"{name}.presentation.phone_glass_rect[{index}]")
        _positive(rect[2], f"{name}.presentation.phone_glass_rect.width")
        _positive(rect[3], f"{name}.presentation.phone_glass_rect.height")

    if name == "scene_02":
        _require(config, ("horizontal_views", "initial_view", "attention_sequence"), name)
        views = config["horizontal_views"]
        if not isinstance(views, list) or not views:
            raise ValueError("scene_02.horizontal_views must be a non-empty list")
        if config["initial_view"] not in views:
            raise ValueError("scene_02.initial_view must be present in scene_02.horizontal_views")
        for index, step in enumerate(config["attention_sequence"]):
            _require(step, ("view", "duration"), f"scene_02.attention_sequence[{index}]")
            if step["view"] not in views:
                raise ValueError(
                    f"scene_02.attention_sequence[{index}].view must be present in scene_02.horizontal_views"
                )
            _positive(step["duration"], f"scene_02.attention_sequence[{index}].duration")
        _positive(config.get("dialogue_start_delay", 0.0), "scene_02.dialogue_start_delay", allow_zero=True)

        shooting_star = config.get("presentation", {}).get("shooting_star", {})
        if shooting_star:
            _positive(shooting_star.get("fps", 11.0), "scene_02.presentation.shooting_star.fps")
            min_delay = _positive(
                shooting_star.get("min_delay", 8.0),
                "scene_02.presentation.shooting_star.min_delay",
                allow_zero=True,
            )
            max_delay = _positive(
                shooting_star.get("max_delay", 20.0),
                "scene_02.presentation.shooting_star.max_delay",
                allow_zero=True,
            )
            if min_delay > max_delay:
                raise ValueError(
                    "scene_02.presentation.shooting_star.min_delay must be <= max_delay"
                )
            position = shooting_star.get("position", [310, 105])
            if not isinstance(position, list) or len(position) != 2:
                raise ValueError(
                    "scene_02.presentation.shooting_star.position must be [x, y]"
                )

    elif name == "scene_04":
        _require(config, ("world", "next_scene", "estuary"), name)
        _positive(config.get("camera_speed", 360.0), "scene_04.camera_speed")
        _fraction(
            config["estuary"].get("required_visible_fraction", 0.35),
            "scene_04.estuary.required_visible_fraction",
        )

    elif name == "scene_05":
        _require(config, ("world", "next_scene"), name)
        _positive(config.get("post_dialogue_delay", 0.0), "scene_05.post_dialogue_delay", allow_zero=True)

    elif name == "scene_08":
        _require(config, ("approach", "next_scene", "help"), name)
        approach = config["approach"]
        _require(approach, ("drag_sensitivity", "max_safe_zoom"), f"{name}.approach")
        _positive(approach["drag_sensitivity"], "scene_08.approach.drag_sensitivity")
        if _positive(approach["max_safe_zoom"], "scene_08.approach.max_safe_zoom") < 1.0:
            raise ValueError("scene_08.approach.max_safe_zoom must be at least 1")

    elif name == "scene_09":
        _require(config, ("interaction", "next_scene"), name)
        interaction = config["interaction"]
        _require(interaction, ("final_separation", "join_threshold"), "scene_09.interaction")
        final_separation = _positive(
            interaction["final_separation"], "scene_09.interaction.final_separation"
        )
        join_threshold = _positive(
            interaction["join_threshold"], "scene_09.interaction.join_threshold", allow_zero=True
        )
        if final_separation < join_threshold:
            raise ValueError(
                "scene_09.interaction.final_separation must be >= join_threshold"
            )

    elif name == "scene_10":
        _require(config, ("interaction", "next_scene"), name)
        interaction = config["interaction"]
        # Scene 10 now reveals a river horizontally; the old free-drag
        # min/max x/y bounds no longer apply.
        _require(
            interaction,
            ("initial_visible_fraction", "sea_edge_fraction", "river_center_fraction", "grab_radius"),
            "scene_10.interaction",
        )
        initial = _fraction(interaction["initial_visible_fraction"], "scene_10.interaction.initial_visible_fraction")
        sea_edge = _fraction(interaction["sea_edge_fraction"], "scene_10.interaction.sea_edge_fraction")
        _fraction(interaction["river_center_fraction"], "scene_10.interaction.river_center_fraction")
        _positive(interaction["grab_radius"], "scene_10.interaction.grab_radius")
        if 1.0 - initial <= sea_edge:
            raise ValueError("scene_10.interaction initial river tip must begin to the right of the sea edge")
