KNOWN_TRANSITIONS = {"none", "fade_to_black", "fade_from_black", "eye_blink"}


def _require(mapping, keys, context):
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise ValueError(f"{context} missing required keys: {', '.join(missing)}")


def _positive(value, context, *, allow_zero=False):
    number = float(value)
    valid = number >= 0 if allow_zero else number > 0
    if not valid:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{context} must be {qualifier}, got {value!r}")
    return number


def _fraction(value, context):
    number = float(value)
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

    if name == "scene_02":
        _require(config, ("views", "initial_view", "attention_sequence"), name)
        views = config["views"]
        if not isinstance(views, list) or not views:
            raise ValueError("scene_02.views must be a non-empty list")
        if config["initial_view"] not in views:
            raise ValueError("scene_02.initial_view must be present in scene_02.views")
        for index, step in enumerate(config["attention_sequence"]):
            _require(step, ("view", "duration"), f"scene_02.attention_sequence[{index}]")
            if step["view"] not in views:
                raise ValueError(
                    f"scene_02.attention_sequence[{index}].view must be present in scene_02.views"
                )
            _positive(step["duration"], f"scene_02.attention_sequence[{index}].duration")
        _positive(config.get("dialogue_start_delay", 0.0), "scene_02.dialogue_start_delay", allow_zero=True)

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
        _require(config, ("approach", "next_scene"), name)
        approach = config["approach"]
        _require(approach, ("drag_sensitivity", "max_safe_zoom"), f"{name}.approach")
        _positive(approach["drag_sensitivity"], "scene_08.approach.drag_sensitivity")
        if float(approach["max_safe_zoom"]) < 1.0:
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
        _require(interaction, ("min_x", "max_x", "min_y", "max_y"), "scene_10.interaction")
        if float(interaction["min_x"]) > float(interaction["max_x"]):
            raise ValueError("scene_10.interaction.min_x must be <= max_x")
        if float(interaction["min_y"]) > float(interaction["max_y"]):
            raise ValueError("scene_10.interaction.min_y must be <= max_y")
        if "sea_edge_fraction" in interaction:
            _fraction(interaction["sea_edge_fraction"], "scene_10.interaction.sea_edge_fraction")
        if "snap_distance" in interaction:
            _positive(interaction["snap_distance"], "scene_10.interaction.snap_distance", allow_zero=True)
