extends Control

var map_view: Control
var cabinet_container: SubViewportContainer
var cabinet_viewport: SubViewport
var section_panel: PanelContainer
var bottom_hud: Control
var title_label: Label
var content_box: VBoxContainer
var date_label: Label
var top_approval: Label
var top_gdp: Label
var top_inflation: Label
var event_label: Label

func _ready() -> void:
    _build_background()
    _build_map()
    _build_cabinet()
    _build_topbar()
    _build_left_nav()
    _build_section_panel()
    _build_event_strip()
    _build_dynamic_hud()
    _build_version_badge()
    WorldState.country_selected.connect(_refresh_country)
    WorldState.simulation_changed.connect(_refresh_all)
    WorldState.event_created.connect(_show_event)
    _refresh_all()
    _build_startup_flow()

func _build_background() -> void:
    var bg := ColorRect.new()
    bg.color = Color("050b12")
    bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(bg)

func _build_map() -> void:
    map_view = Control.new()
    map_view.name = "WorldMap"
    map_view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    map_view.offset_top = 72
    map_view.offset_bottom = -120
    map_view.offset_left = 74
    map_view.offset_right = -74
    map_view.set_script(load("res://scripts/world_map.gd"))
    add_child(map_view)

func _build_cabinet() -> void:
    cabinet_container = SubViewportContainer.new()
    cabinet_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    cabinet_container.offset_top = 72
    cabinet_container.offset_bottom = -120
    cabinet_container.offset_left = 74
    cabinet_container.offset_right = -74
    cabinet_container.stretch = true
    cabinet_container.visible = false
    cabinet_viewport = SubViewport.new()
    cabinet_viewport.size = Vector2i(1280, 720)
    cabinet_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    cabinet_viewport.handle_input_locally = true
    var scene := Node3D.new()
    scene.set_script(load("res://scripts/cabinet.gd"))
    scene.hotspot_pressed.connect(_on_cabinet_hotspot)
    cabinet_viewport.add_child(scene)
    cabinet_container.add_child(cabinet_viewport)
    add_child(cabinet_container)

func _build_topbar() -> void:
    var top := HBoxContainer.new()
    top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
    top.offset_left = 102
    top.offset_right = -102
    top.offset_top = 8
    top.offset_bottom = 60
    top.add_theme_constant_override("separation", 18)
    top_approval = _top_stat()
    top_gdp = _top_stat()
    top_inflation = _top_stat()
    date_label = _top_stat()
    top.add_child(top_approval)
    top.add_child(top_gdp)
    top.add_child(top_inflation)
    top.add_child(date_label)
    var spacer := Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    top.add_child(spacer)
    for pair in [["1D",1],["7D",7],["30D",30]]:
        var b := Button.new()
        b.text = pair[0]
        b.custom_minimum_size = Vector2(62, 42)
        b.pressed.connect(func(days=pair[1]): WorldState.advance_days(days))
        top.add_child(b)
    add_child(top)

func _top_stat() -> Label:
    var l := Label.new()
    l.add_theme_font_size_override("font_size", 16)
    return l

func _build_left_nav() -> void:
    var nav := VBoxContainer.new()
    nav.set_anchors_and_offsets_preset(Control.PRESET_LEFT_WIDE)
    nav.offset_left = 12
    nav.offset_right = 64
    nav.offset_top = 118
    nav.offset_bottom = -128
    nav.add_theme_constant_override("separation", 6)
    var items = [
        ["GOV", "government"], ["ECO", "economy"], ["MIL", "military"],
        ["DIP", "diplomacy"], ["MID", "media"], ["MAP", "map"], ["CAB", "cabinet"]
    ]
    for item in items:
        var b := Button.new()
        b.text = item[0]
        b.custom_minimum_size = Vector2(50, 48)
        b.pressed.connect(_open_section.bind(item[1]))
        nav.add_child(b)
    add_child(nav)

func _build_dynamic_hud() -> void:
    bottom_hud = Control.new()
    bottom_hud.name = "DynamicBottomHUD"
    bottom_hud.set_script(load("res://scripts/bottom_hud.gd"))
    bottom_hud.section_requested.connect(_open_section)
    add_child(bottom_hud)
    bottom_hud.call("set_map_view", map_view)
    bottom_hud.call("set_active_section", "map")

func _build_section_panel() -> void:
    section_panel = PanelContainer.new()
    section_panel.set_anchors_and_offsets_preset(Control.PRESET_RIGHT_WIDE)
    section_panel.offset_left = -470
    section_panel.offset_right = -18
    section_panel.offset_top = 82
    section_panel.offset_bottom = -122
    section_panel.visible = false
    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.018, 0.035, 0.048, 0.965)
    style.border_color = Color(0.18, 0.39, 0.46, 0.72)
    style.set_border_width_all(1)
    style.corner_radius_top_left = 10
    style.corner_radius_bottom_left = 10
    style.content_margin_left = 16
    style.content_margin_right = 16
    style.content_margin_top = 14
    style.content_margin_bottom = 14
    section_panel.add_theme_stylebox_override("panel", style)

    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 9)
    var header := HBoxContainer.new()
    title_label = Label.new()
    title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    title_label.add_theme_font_size_override("font_size", 22)
    var close := Button.new()
    close.text = "×"
    close.custom_minimum_size = Vector2(44, 40)
    close.pressed.connect(func(): section_panel.visible = false)
    header.add_child(title_label)
    header.add_child(close)
    root.add_child(header)
    var scroll := ScrollContainer.new()
    scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    content_box = VBoxContainer.new()
    content_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    content_box.add_theme_constant_override("separation", 8)
    scroll.add_child(content_box)
    root.add_child(scroll)
    section_panel.add_child(root)
    add_child(section_panel)

func _build_event_strip() -> void:
    var panel := PanelContainer.new()
    panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
    panel.offset_left = 560
    panel.offset_right = -560
    panel.offset_top = 62
    panel.offset_bottom = 96
    event_label = Label.new()
    event_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    event_label.add_theme_font_size_override("font_size", 14)
    panel.add_child(event_label)
    add_child(panel)

func _build_version_badge() -> void:
    var badge := Label.new()
    badge.text = "v0.5 • COMMAND EXPERIENCE"
    badge.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
    badge.offset_left = -260
    badge.offset_right = -86
    badge.offset_top = -136
    badge.offset_bottom = -120
    badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
    badge.add_theme_font_size_override("font_size", 10)
    badge.modulate = Color(0.45, 0.75, 0.82)
    add_child(badge)

func _build_startup_flow() -> void:
    var flow := Control.new()
    flow.name = "StartupFlow"
    flow.set_script(load("res://scripts/startup_flow.gd"))
    add_child(flow)

func _open_section(section: String) -> void:
    if bottom_hud != null and bottom_hud.has_method("set_active_section"):
        bottom_hud.call("set_active_section", section)
    map_view.visible = section != "cabinet"
    cabinet_container.visible = section == "cabinet"
    if section in ["map", "cabinet"]:
        section_panel.visible = false
        return
    section_panel.visible = true
    section_panel.set_meta("section", section)
    _refresh_section(section)

func _clear_content() -> void:
    for child in content_box.get_children():
        child.queue_free()

func _label(text: String, size := 17) -> Label:
    var l := Label.new()
    l.text = text
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    l.add_theme_font_size_override("font_size", size)
    l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    return l

func _section_heading(text: String) -> Label:
    var l := _label(text, 13)
    l.modulate = Color(0.40, 0.87, 0.94)
    return l

func _button(text: String, callback: Callable) -> Button:
    var b := Button.new()
    b.text = text
    b.custom_minimum_size = Vector2(0, 46)
    b.pressed.connect(callback)
    return b

func _refresh_section(section: String) -> void:
    _clear_content()
    var c := WorldState.selected_country()
    match section:
        "economy": _build_economy(c)
        "government": _build_government(c)
        "military": _build_military(c)
        "diplomacy": _build_diplomacy(c)
        "media": _build_media(c)

func _build_economy(c: Dictionary) -> void:
    title_label.text = "ECONOMIA"
    content_box.add_child(_section_heading("PAINEL MACROECONÔMICO"))
    content_box.add_child(_label("PIB: R$ %.2f tri\nInflação: %.1f%%\nDesemprego: %.1f%%\nDívida/PIB: %.1f%%\nTesouro: R$ %.1f bi" % [c.get("gdp_trillion",0.0), c.get("inflation",0.0), c.get("unemployment",0.0), c.get("debt_gdp",0.0), WorldState.treasury], 17))
    content_box.add_child(_section_heading("POLÍTICA FISCAL"))
    content_box.add_child(_label("IMPOSTOS %.1f%%   |   JUROS %.1f%%   |   SOCIAL %.1f%%" % [WorldState.tax_rate, WorldState.interest_rate, WorldState.social_spending], 14))
    content_box.add_child(_button("REDUZIR IMPOSTOS -1%", func(): WorldState.adjust_economy("tax", -1.0)))
    content_box.add_child(_button("AUMENTAR IMPOSTOS +1%", func(): WorldState.adjust_economy("tax", 1.0)))
    content_box.add_child(_button("REDUZIR JUROS -0,5%", func(): WorldState.adjust_economy("interest", -0.5)))
    content_box.add_child(_button("AUMENTAR GASTO SOCIAL +1%", func(): WorldState.adjust_economy("social", 1.0)))

func _build_government(c: Dictionary) -> void:
    title_label.text = "GOVERNO / POLÍTICA"
    content_box.add_child(_section_heading("MANDATO"))
    content_box.add_child(_label("Líder: %s\nPartido: %s\nPromessa: %s\nAprovação: %.1f%%\nEstabilidade: %.1f%%\nRelação com imprensa: %.1f%%" % [WorldState.player_leader_name, WorldState.player_party, WorldState.campaign_promise, c.get("approval",0.0), c.get("stability",0.0), WorldState.press_relation], 17))
    content_box.add_child(_section_heading("GABINETE-CHAVE"))
    for member in WorldState.cabinet:
        content_box.add_child(_label("%s • %s\nCompetência %d  |  Lealdade %d  |  Risco %d" % [member.get("office","Ministério"), member.get("name","Ministro"), int(member.get("competence",0)), int(member.get("loyalty",0)), int(member.get("risk",0))], 13))
    content_box.add_child(_button("PRONUNCIAMENTO NACIONAL", func(): WorldState.political_action("speech")))
    content_box.add_child(_button("ENVIAR REFORMA AO CONGRESSO", func(): WorldState.political_action("reform")))
    content_box.add_child(_button("AVANÇAR 7 DIAS", func(): WorldState.advance_days(7)))

func _build_military(c: Dictionary) -> void:
    title_label.text = "FORÇAS ARMADAS"
    content_box.add_child(_section_heading("SITUAÇÃO ESTRATÉGICA"))
    content_box.add_child(_label("Poder militar: %d/100\nGasto de defesa: %.1f%% do PIB\nTensão global: %.1f%%" % [int(c.get("military_power",0)), WorldState.defense_spending, WorldState.global_tension], 17))
    content_box.add_child(_button("REALIZAR EXERCÍCIO MILITAR", func(): WorldState.military_action("exercise")))
    content_box.add_child(_button("MOBILIZAR FORÇAS", func(): WorldState.military_action("mobilize")))
    content_box.add_child(_button("AUMENTAR ORÇAMENTO +0,2%", func(): WorldState.adjust_economy("defense", 0.2)))

func _build_diplomacy(c: Dictionary) -> void:
    title_label.text = "DIPLOMACIA"
    var id := WorldState.selected_country_id
    var relation := WorldState.relation_between(WorldState.player_country_id, id)
    var player_name: String = str(WorldState.player_country().get("name", "Seu país"))
    content_box.add_child(_section_heading("DOSSIÊ DO PAÍS"))
    content_box.add_child(_label("%s\nPopulação: %s\nPIB: %.2f tri\nPoder militar: %d/100\nRelação com %s: %+d" % [c.get("name","-"), _fmt_population(int(c.get("population",0))), c.get("gdp_trillion",0.0), int(c.get("military_power",0)), player_name, relation], 17))
    if id != WorldState.player_country_id:
        content_box.add_child(_button("NEGOCIAR (+5 RELAÇÃO)", func(): WorldState.negotiate_with(id)))
        content_box.add_child(_button("IMPOSTAR SANÇÕES", func(): WorldState.impose_sanctions(id)))
    content_box.add_child(_label("ENTIDADES DE GOVERNO CARREGADAS: %d" % WorldState.countries.size(), 13))

func _build_media(_c: Dictionary) -> void:
    title_label.text = "MÍDIA / IMPRENSA"
    var headline := "Nenhum grande evento no momento."
    if not WorldState.last_event.is_empty():
        headline = "%s | %s" % [WorldState.last_event.get("category","Geral"), WorldState.last_event.get("headline","")]
    content_box.add_child(_section_heading("CENTRAL DE NOTÍCIAS"))
    content_box.add_child(_label("Relação com imprensa: %.1f%%\n\nMANCHETE\n%s" % [WorldState.press_relation, headline], 17))
    content_box.add_child(_section_heading("TERMÔMETRO PÚBLICO"))
    content_box.add_child(_label("Promessa em foco: %s\nAprovação do governo: %.0f%%\nTensão global: %.0f%%" % [WorldState.campaign_promise, float(WorldState.player_country().get("approval",0.0)), WorldState.global_tension], 14))
    content_box.add_child(_button("CONVOCAR COLETIVA", func(): WorldState.political_action("speech")))
    content_box.add_child(_button("AVANÇAR 30 DIAS", func(): WorldState.advance_days(30)))

func _fmt_population(value: int) -> String:
    if value >= 1000000000:
        return "%.2f bi" % (float(value) / 1000000000.0)
    if value >= 1000000:
        return "%.1f mi" % (float(value) / 1000000.0)
    return str(value)

func _refresh_country(_id: String) -> void:
    _refresh_all()

func _refresh_all() -> void:
    var player := WorldState.player_country()
    date_label.text = "%02d/%02d/%04d" % [WorldState.day, WorldState.month, WorldState.year]
    top_approval.text = "APROVAÇÃO %.0f%%" % float(player.get("approval",0.0))
    top_gdp.text = "PIB R$ %.2f tri" % float(player.get("gdp_trillion",0.0))
    top_inflation.text = "INFLAÇÃO %.1f%%" % float(player.get("inflation",0.0))
    if section_panel.visible:
        _refresh_section(str(section_panel.get_meta("section", "government")))

func _show_event(event: Dictionary) -> void:
    event_label.text = "%s: %s" % [event.get("category","Geral"), event.get("headline","")]

func _on_cabinet_hotspot(action: String) -> void:
    match action:
        "CrisisPhone": _open_section("diplomacy")
        "LawFolders": _open_section("government")
        "Globe": _open_section("map")
        "TV": _open_section("media")
