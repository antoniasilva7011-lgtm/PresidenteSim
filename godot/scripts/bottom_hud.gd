extends Control

signal section_requested(section: String)

var map_view: Control
var active_section: String = "map"
var country_code: Label
var country_name: Label
var country_stats: Label
var relation_label: Label
var nav_buttons: Dictionary = {}
var action_box: HBoxContainer
var context_title: Label

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
    offset_left = 78
    offset_right = -78
    offset_top = -116
    offset_bottom = -10
    _build_hud()
    WorldState.country_selected.connect(_on_country_selected)
    WorldState.simulation_changed.connect(_refresh)
    _refresh()

func set_map_view(value: Control) -> void:
    map_view = value

func set_active_section(section: String) -> void:
    active_section = section
    _update_nav_state()
    _rebuild_actions()

func _build_hud() -> void:
    var shell := PanelContainer.new()
    shell.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    shell.add_theme_stylebox_override("panel", _panel_style(Color(0.018, 0.035, 0.052, 0.94), Color(0.18, 0.35, 0.43, 0.55), 10))
    add_child(shell)

    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 8)
    shell.add_child(row)

    row.add_child(_build_country_card())
    row.add_child(_build_navigation())
    row.add_child(_build_context_actions())

func _build_country_card() -> Control:
    var panel := PanelContainer.new()
    panel.custom_minimum_size = Vector2(380, 0)
    panel.add_theme_stylebox_override("panel", _panel_style(Color(0.028, 0.064, 0.083, 0.96), Color(0.24, 0.66, 0.76, 0.5), 8))

    var root := HBoxContainer.new()
    root.add_theme_constant_override("separation", 12)
    panel.add_child(root)

    var badge := PanelContainer.new()
    badge.custom_minimum_size = Vector2(72, 72)
    badge.add_theme_stylebox_override("panel", _panel_style(Color(0.035, 0.30, 0.38, 1.0), Color(0.45, 0.95, 1.0, 0.8), 7))
    country_code = Label.new()
    country_code.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    country_code.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    country_code.add_theme_font_size_override("font_size", 17)
    country_code.add_theme_color_override("font_color", Color(0.86, 0.99, 1.0))
    badge.add_child(country_code)
    root.add_child(badge)

    var text := VBoxContainer.new()
    text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    text.add_theme_constant_override("separation", 2)
    country_name = Label.new()
    country_name.add_theme_font_size_override("font_size", 18)
    country_name.add_theme_color_override("font_color", Color(0.95, 0.98, 1.0))
    country_stats = Label.new()
    country_stats.add_theme_font_size_override("font_size", 12)
    country_stats.add_theme_color_override("font_color", Color(0.67, 0.78, 0.83))
    relation_label = Label.new()
    relation_label.add_theme_font_size_override("font_size", 12)
    relation_label.add_theme_color_override("font_color", Color(0.39, 0.88, 0.94))
    text.add_child(country_name)
    text.add_child(country_stats)
    text.add_child(relation_label)
    root.add_child(text)
    return panel

func _build_navigation() -> Control:
    var panel := PanelContainer.new()
    panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    panel.add_theme_stylebox_override("panel", _panel_style(Color(0.015, 0.027, 0.041, 0.93), Color(0.15, 0.25, 0.31, 0.6), 8))

    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 4)
    panel.add_child(root)

    var title := Label.new()
    title.text = "CENTRAL DE COMANDO"
    title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    title.add_theme_font_size_override("font_size", 11)
    title.add_theme_color_override("font_color", Color(0.43, 0.63, 0.70))
    root.add_child(title)

    var nav := HBoxContainer.new()
    nav.size_flags_vertical = Control.SIZE_EXPAND_FILL
    nav.add_theme_constant_override("separation", 4)
    root.add_child(nav)

    var items := [
        ["GAB", "cabinet"], ["ECO", "economy"], ["POL", "government"],
        ["MIL", "military"], ["DIP", "diplomacy"], ["MÍDIA", "media"], ["MAPA", "map"]
    ]
    for item in items:
        var button := Button.new()
        button.text = item[0]
        button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        button.custom_minimum_size = Vector2(74, 54)
        button.focus_mode = Control.FOCUS_NONE
        button.pressed.connect(_on_nav_pressed.bind(item[1]))
        nav.add_child(button)
        nav_buttons[item[1]] = button
    _update_nav_state()
    return panel

func _build_context_actions() -> Control:
    var panel := PanelContainer.new()
    panel.custom_minimum_size = Vector2(420, 0)
    panel.add_theme_stylebox_override("panel", _panel_style(Color(0.028, 0.046, 0.061, 0.96), Color(0.27, 0.39, 0.46, 0.55), 8))

    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 4)
    panel.add_child(root)

    context_title = Label.new()
    context_title.text = "AÇÕES RÁPIDAS"
    context_title.add_theme_font_size_override("font_size", 11)
    context_title.add_theme_color_override("font_color", Color(0.56, 0.72, 0.78))
    root.add_child(context_title)

    action_box = HBoxContainer.new()
    action_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
    action_box.add_theme_constant_override("separation", 5)
    root.add_child(action_box)
    _rebuild_actions()
    return panel

func _on_nav_pressed(section: String) -> void:
    set_active_section(section)
    section_requested.emit(section)

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
    country_stats.text = "PODER %d/100   •   ESTABILIDADE %.0f%%" % [power, stability]
    if id == WorldState.player_country_id:
        relation_label.text = "SEU GOVERNO   •   %s" % WorldState.player_party.to_upper()
    else:
        relation_label.text = "RELAÇÃO %+d   •   TOQUE EM AÇÕES PARA INTERAGIR" % relation
    _rebuild_actions()

func _on_country_selected(_id: String) -> void:
    _refresh()

func _update_nav_state() -> void:
    for key in nav_buttons.keys():
        var button: Button = nav_buttons[key] as Button
        var active: bool = str(key) == active_section
        button.add_theme_stylebox_override("normal", _button_style(active))
        button.add_theme_stylebox_override("hover", _button_style(true))
        button.add_theme_stylebox_override("pressed", _button_style(true))
        button.add_theme_color_override("font_color", Color(0.72, 0.96, 1.0) if active else Color(0.72, 0.78, 0.82))

func _rebuild_actions() -> void:
    if action_box == null:
        return
    for child in action_box.get_children():
        child.queue_free()
    context_title.text = _context_name(active_section)
    var actions: Array = []
    match active_section:
        "map":
            actions = [["CENTRALIZAR", "center"], ["ABRIR PAÍS", "open_country"], ["DIPLOMACIA", "diplomacy"]]
        "diplomacy":
            actions = [["NEGOCIAR", "negotiate"], ["SANÇÕES", "sanctions"], ["ABRIR PAÍS", "open_country"]]
        "military":
            actions = [["EXERCÍCIO", "exercise"], ["MOBILIZAR", "mobilize"], ["DEFESA +", "defense_up"]]
        "economy":
            actions = [["IMPOSTO -", "tax_down"], ["JUROS -", "interest_down"], ["SOCIAL +", "social_up"]]
        "government":
            actions = [["DISCURSO", "speech"], ["REFORMA", "reform"], ["+7 DIAS", "days7"]]
        "media":
            actions = [["COLETIVA", "speech"], ["+30 DIAS", "days30"], ["PAÍS", "open_country"]]
        "cabinet":
            actions = [["MAPA", "map"], ["POLÍTICA", "government"], ["DIPLOMACIA", "diplomacy"]]
    for item in actions:
        var b := Button.new()
        b.text = item[0]
        b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        b.custom_minimum_size = Vector2(110, 54)
        b.focus_mode = Control.FOCUS_NONE
        b.add_theme_stylebox_override("normal", _button_style(false))
        b.add_theme_stylebox_override("hover", _button_style(true))
        b.add_theme_stylebox_override("pressed", _button_style(true))
        b.pressed.connect(_execute_action.bind(item[1]))
        action_box.add_child(b)

func _execute_action(action: String) -> void:
    var target: String = WorldState.selected_country_id
    match action:
        "center":
            if map_view != null and map_view.has_method("reset_view"):
                map_view.call("reset_view")
        "open_country":
            set_active_section("diplomacy")
            section_requested.emit("diplomacy")
        "diplomacy", "government", "map":
            set_active_section(action)
            section_requested.emit(action)
        "negotiate":
            if target != WorldState.player_country_id:
                WorldState.negotiate_with(target)
        "sanctions":
            if target != WorldState.player_country_id:
                WorldState.impose_sanctions(target)
        "exercise": WorldState.military_action("exercise")
        "mobilize": WorldState.military_action("mobilize")
        "defense_up": WorldState.adjust_economy("defense", 0.2)
        "tax_down": WorldState.adjust_economy("tax", -1.0)
        "interest_down": WorldState.adjust_economy("interest", -0.5)
        "social_up": WorldState.adjust_economy("social", 1.0)
        "speech": WorldState.political_action("speech")
        "reform": WorldState.political_action("reform")
        "days7": WorldState.advance_days(7)
        "days30": WorldState.advance_days(30)

func _context_name(section: String) -> String:
    match section:
        "economy": return "ECONOMIA • AÇÕES RÁPIDAS"
        "government": return "POLÍTICA • AÇÕES RÁPIDAS"
        "military": return "MILITAR • AÇÕES RÁPIDAS"
        "diplomacy": return "DIPLOMACIA • AÇÕES RÁPIDAS"
        "media": return "MÍDIA • AÇÕES RÁPIDAS"
        "cabinet": return "GABINETE • ACESSOS"
        _: return "MAPA • CONTEXTO"

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
    style.content_margin_left = 12
    style.content_margin_right = 12
    style.content_margin_top = 8
    style.content_margin_bottom = 8
    return style

func _button_style(active: bool) -> StyleBoxFlat:
    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.035, 0.22, 0.28, 0.96) if active else Color(0.025, 0.045, 0.06, 0.94)
    style.border_color = Color(0.31, 0.82, 0.91, 0.82) if active else Color(0.14, 0.23, 0.28, 0.72)
    style.set_border_width_all(1)
    style.corner_radius_top_left = 6
    style.corner_radius_top_right = 6
    style.corner_radius_bottom_left = 6
    style.corner_radius_bottom_right = 6
    return style
