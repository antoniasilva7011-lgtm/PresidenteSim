extends Control

signal section_requested(section: String)

var map_view: Control
var active_section: String = "map"
var country_code: Label
var country_name: Label
var country_stats: Label
var relation_label: Label
var action_box: HBoxContainer
var context_title: Label
var mode_label: Label
var mode_buttons: Dictionary = {}
var active_map_mode: String = "political"

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
    offset_left = 76
    offset_right = -76
    offset_top = -106
    offset_bottom = -10
    _build_hud()
    WorldState.country_selected.connect(_on_country_selected)
    WorldState.simulation_changed.connect(_refresh)
    _refresh()

func set_map_view(value: Control) -> void:
    map_view = value
    _apply_map_mode()

func set_active_section(section: String) -> void:
    active_section = section
    _rebuild_actions()

func _build_hud() -> void:
    var row := HBoxContainer.new()
    row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    row.add_theme_constant_override("separation", 8)
    add_child(row)
    row.add_child(_build_country_card())
    row.add_child(_build_map_controls())
    row.add_child(_build_context_actions())

func _build_country_card() -> Control:
    var panel := PanelContainer.new()
    panel.custom_minimum_size = Vector2(390, 0)
    panel.add_theme_stylebox_override("panel", _panel_style(Color(0.018, 0.050, 0.068, 0.97), Color(0.21, 0.63, 0.72, 0.58), 9))
    var root := HBoxContainer.new()
    root.add_theme_constant_override("separation", 10)
    panel.add_child(root)

    var badge := PanelContainer.new()
    badge.custom_minimum_size = Vector2(66, 66)
    badge.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.25, 0.33, 1.0), Color(0.44, 0.94, 1.0, 0.78), 8))
    country_code = Label.new()
    country_code.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    country_code.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    country_code.add_theme_font_size_override("font_size", 16)
    badge.add_child(country_code)
    root.add_child(badge)

    var text := VBoxContainer.new()
    text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    text.add_theme_constant_override("separation", 1)
    country_name = Label.new()
    country_name.add_theme_font_size_override("font_size", 17)
    country_stats = Label.new()
    country_stats.add_theme_font_size_override("font_size", 11)
    country_stats.modulate = Color(0.68, 0.79, 0.84)
    relation_label = Label.new()
    relation_label.add_theme_font_size_override("font_size", 11)
    relation_label.modulate = Color(0.39, 0.88, 0.94)
    text.add_child(country_name)
    text.add_child(country_stats)
    text.add_child(relation_label)
    root.add_child(text)
    return panel

func _build_map_controls() -> Control:
    var panel := PanelContainer.new()
    panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    panel.add_theme_stylebox_override("panel", _panel_style(Color(0.010, 0.024, 0.038, 0.965), Color(0.13, 0.25, 0.31, 0.64), 9))
    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 3)
    panel.add_child(root)

    var head := HBoxContainer.new()
    root.add_child(head)
    var title := Label.new()
    title.text = "CAMADAS DO MAPA"
    title.add_theme_font_size_override("font_size", 10)
    title.modulate = Color(0.46, 0.67, 0.73)
    head.add_child(title)
    var spacer := Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    head.add_child(spacer)
    mode_label = Label.new()
    mode_label.text = "POLÍTICO"
    mode_label.add_theme_font_size_override("font_size", 10)
    mode_label.modulate = Color(0.35, 0.84, 0.90)
    head.add_child(mode_label)

    var nav := HBoxContainer.new()
    nav.size_flags_vertical = Control.SIZE_EXPAND_FILL
    nav.add_theme_constant_override("separation", 4)
    root.add_child(nav)
    var items := [
        ["POLÍTICO", "political"], ["ECONÔMICO", "economic"],
        ["MILITAR", "military"], ["DIPLOMÁTICO", "diplomatic"],
        ["CONFLITOS", "conflict"]
    ]
    for item in items:
        var button := Button.new()
        button.text = item[0]
        button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        button.custom_minimum_size = Vector2(100, 48)
        button.focus_mode = Control.FOCUS_NONE
        button.pressed.connect(_set_map_mode.bind(item[1]))
        nav.add_child(button)
        mode_buttons[item[1]] = button
    _update_mode_state()
    return panel

func _build_context_actions() -> Control:
    var panel := PanelContainer.new()
    panel.custom_minimum_size = Vector2(410, 0)
    panel.add_theme_stylebox_override("panel", _panel_style(Color(0.020, 0.040, 0.056, 0.97), Color(0.25, 0.39, 0.46, 0.55), 9))
    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 3)
    panel.add_child(root)
    context_title = Label.new()
    context_title.add_theme_font_size_override("font_size", 10)
    context_title.modulate = Color(0.56, 0.72, 0.78)
    root.add_child(context_title)
    action_box = HBoxContainer.new()
    action_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
    action_box.add_theme_constant_override("separation", 5)
    root.add_child(action_box)
    _rebuild_actions()
    return panel

func _set_map_mode(mode: String) -> void:
    active_map_mode = mode
    _update_mode_state()
    _apply_map_mode()

func _apply_map_mode() -> void:
    if map_view != null and map_view.has_method("set_map_mode"):
        map_view.call("set_map_mode", active_map_mode)

func _update_mode_state() -> void:
    if mode_label != null:
        mode_label.text = active_map_mode.to_upper()
    for key in mode_buttons.keys():
        var button: Button = mode_buttons[key] as Button
        var active := str(key) == active_map_mode
        button.add_theme_stylebox_override("normal", _button_style(active))
        button.add_theme_stylebox_override("hover", _button_style(true))
        button.add_theme_stylebox_override("pressed", _button_style(true))
        button.add_theme_color_override("font_color", Color(0.76, 0.97, 1.0) if active else Color(0.70, 0.77, 0.81))

func _refresh() -> void:
    if country_name == null:
        return
    var selected := WorldState.selected_country()
    var id: String = WorldState.selected_country_id
    var name: String = str(selected.get("name", "VISÃO GLOBAL"))
    var power: int = int(selected.get("military_power", 0))
    var stability: float = float(selected.get("stability", 0.0))
    var relation: int = WorldState.relation_between(WorldState.player_country_id, id)
    country_code.text = _short_code(id)
    country_name.text = name.to_upper()
    country_stats.text = "PODER %d/100  •  ESTAB. %.0f%%" % [power, stability]
    if id == WorldState.player_country_id:
        relation_label.text = "SEU GOVERNO  •  %s" % WorldState.player_party.to_upper()
    else:
        relation_label.text = "RELAÇÃO %+d  •  PAÍS SELECIONADO" % relation
    _rebuild_actions()

func _on_country_selected(_id: String) -> void:
    _refresh()

func _rebuild_actions() -> void:
    if action_box == null:
        return
    for child in action_box.get_children():
        child.queue_free()
    var target := WorldState.selected_country_id
    var own_country := target == WorldState.player_country_id
    context_title.text = "AÇÕES DO PAÍS" if not own_country else "CONTROLES DO MAPA"
    var actions: Array
    if own_country:
        actions = [["CENTRALIZAR", "center"], ["ZOOM +", "zoom_in"], ["ZOOM -", "zoom_out"]]
    else:
        actions = [["DOSSIÊ", "open_country"], ["NEGOCIAR", "negotiate"], ["SANÇÕES", "sanctions"]]
    for item in actions:
        var b := Button.new()
        b.text = item[0]
        b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        b.custom_minimum_size = Vector2(108, 48)
        b.focus_mode = Control.FOCUS_NONE
        b.add_theme_stylebox_override("normal", _button_style(false))
        b.add_theme_stylebox_override("hover", _button_style(true))
        b.add_theme_stylebox_override("pressed", _button_style(true))
        b.pressed.connect(_execute_action.bind(item[1]))
        action_box.add_child(b)

func _execute_action(action: String) -> void:
    var target := WorldState.selected_country_id
    match action:
        "center":
            if map_view != null and map_view.has_method("reset_view"):
                map_view.call("reset_view")
        "zoom_in":
            if map_view != null and map_view.has_method("zoom_by"):
                map_view.call("zoom_by", 1.35)
        "zoom_out":
            if map_view != null and map_view.has_method("zoom_by"):
                map_view.call("zoom_by", 1.0 / 1.35)
        "open_country":
            section_requested.emit("diplomacy")
        "negotiate":
            if target != WorldState.player_country_id:
                WorldState.negotiate_with(target)
        "sanctions":
            if target != WorldState.player_country_id:
                WorldState.impose_sanctions(target)

func _short_code(id: String) -> String:
    if id.length() <= 3:
        return id.to_upper()
    var pieces := id.split("_")
    if pieces.size() > 1:
        var built := ""
        for piece in pieces:
            if not piece.is_empty():
                built += piece.substr(0, 1)
        return built.substr(0, mini(3, built.length())).to_upper()
    return id.substr(0, mini(3, id.length())).to_upper()

func _panel_style(bg: Color, border: Color, radius: int) -> StyleBoxFlat:
    var style := StyleBoxFlat.new()
    style.bg_color = bg
    style.border_color = border
    style.set_border_width_all(1)
    style.corner_radius_top_left = radius
    style.corner_radius_top_right = radius
    style.corner_radius_bottom_left = radius
    style.corner_radius_bottom_right = radius
    style.content_margin_left = 10
    style.content_margin_right = 10
    style.content_margin_top = 7
    style.content_margin_bottom = 7
    return style

func _button_style(active: bool) -> StyleBoxFlat:
    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.030, 0.21, 0.27, 0.97) if active else Color(0.018, 0.040, 0.055, 0.96)
    style.border_color = Color(0.32, 0.82, 0.91, 0.84) if active else Color(0.12, 0.22, 0.27, 0.74)
    style.set_border_width_all(1)
    style.corner_radius_top_left = 6
    style.corner_radius_top_right = 6
    style.corner_radius_bottom_left = 6
    style.corner_radius_bottom_right = 6
    return style
