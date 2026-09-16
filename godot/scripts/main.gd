extends Control

var map_view: Control
var cabinet_container: SubViewportContainer
var cabinet_viewport: SubViewport
var info_panel: PanelContainer
var section_panel: PanelContainer
var title_label: Label
var content_label: Label
var selected_label: Label
var date_label: Label

func _ready() -> void:
    _build_background()
    _build_map()
    _build_cabinet()
    _build_topbar()
    _build_left_nav()
    _build_bottom_nav()
    _build_info_panel()
    _build_section_panel()
    WorldState.country_selected.connect(_refresh_country)
    WorldState.simulation_changed.connect(_refresh_all)
    _refresh_all()

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
    map_view.offset_bottom = -72
    map_view.offset_left = 74
    map_view.offset_right = -74
    map_view.set_script(load("res://scripts/world_map.gd"))
    add_child(map_view)

func _build_cabinet() -> void:
    cabinet_container = SubViewportContainer.new()
    cabinet_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    cabinet_container.offset_top = 72
    cabinet_container.offset_bottom = -72
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
    top.offset_left = 120
    top.offset_right = -120
    top.offset_top = 10
    top.offset_bottom = 62
    top.add_theme_constant_override("separation", 20)
    for text in ["APROVAÇÃO 57%", "PIB R$ 12,4 tri", "INFLAÇÃO 4,8%"]:
        var l := Label.new()
        l.text = text
        l.add_theme_font_size_override("font_size", 17)
        top.add_child(l)
    date_label = Label.new()
    date_label.add_theme_font_size_override("font_size", 17)
    top.add_child(date_label)
    var spacer := Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    top.add_child(spacer)
    var play := Button.new()
    play.text = "▶"
    play.pressed.connect(func(): WorldState.advance_days(1))
    top.add_child(play)
    for pair in [["1D",1],["7D",7],["30D",30]]:
        var b := Button.new()
        b.text = pair[0]
        b.pressed.connect(func(days=pair[1]): WorldState.advance_days(days))
        top.add_child(b)
    add_child(top)

func _build_left_nav() -> void:
    var nav := VBoxContainer.new()
    nav.set_anchors_and_offsets_preset(Control.PRESET_LEFT_WIDE)
    nav.offset_left = 12
    nav.offset_right = 66
    nav.offset_top = 120
    nav.offset_bottom = -120
    nav.add_theme_constant_override("separation", 6)
    var items = [
        ["GOV", "government"], ["ECO", "economy"], ["MIL", "military"],
        ["DIP", "diplomacy"], ["MID", "media"], ["MAP", "map"]
    ]
    for item in items:
        var b := Button.new()
        b.text = item[0]
        b.custom_minimum_size = Vector2(52, 54)
        b.pressed.connect(_open_section.bind(item[1]))
        nav.add_child(b)
    add_child(nav)

func _build_bottom_nav() -> void:
    var nav := HBoxContainer.new()
    nav.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
    nav.offset_left = 260
    nav.offset_right = -260
    nav.offset_top = -62
    nav.offset_bottom = -12
    nav.add_theme_constant_override("separation", 6)
    var items = [
        ["GABINETE", "cabinet"], ["ECONOMIA", "economy"], ["POLÍTICA", "government"],
        ["MILITAR", "military"], ["DIPLOMACIA", "diplomacy"], ["MÍDIA", "media"], ["MAPA", "map"]
    ]
    for item in items:
        var b := Button.new()
        b.text = item[0]
        b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        b.pressed.connect(_open_section.bind(item[1]))
        nav.add_child(b)
    add_child(nav)

func _build_info_panel() -> void:
    info_panel = PanelContainer.new()
    info_panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
    info_panel.offset_left = 88
    info_panel.offset_right = 460
    info_panel.offset_top = -118
    info_panel.offset_bottom = -72
    var box := HBoxContainer.new()
    selected_label = Label.new()
    selected_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    var dip := Button.new()
    dip.text = "DIPLOMACIA"
    dip.pressed.connect(_open_section.bind("diplomacy"))
    box.add_child(selected_label)
    box.add_child(dip)
    info_panel.add_child(box)
    add_child(info_panel)

func _build_section_panel() -> void:
    section_panel = PanelContainer.new()
    section_panel.set_anchors_and_offsets_preset(Control.PRESET_RIGHT_WIDE)
    section_panel.offset_left = -430
    section_panel.offset_right = -18
    section_panel.offset_top = 84
    section_panel.offset_bottom = -84
    section_panel.visible = false
    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 10)
    var header := HBoxContainer.new()
    title_label = Label.new()
    title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    title_label.add_theme_font_size_override("font_size", 24)
    var close := Button.new()
    close.text = "X"
    close.pressed.connect(func(): section_panel.visible = false)
    header.add_child(title_label)
    header.add_child(close)
    root.add_child(header)
    content_label = Label.new()
    content_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    content_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
    content_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
    content_label.add_theme_font_size_override("font_size", 18)
    root.add_child(content_label)
    var action := Button.new()
    action.name = "ActionButton"
    action.text = "EXECUTAR AÇÃO"
    action.pressed.connect(_section_action)
    root.add_child(action)
    section_panel.add_child(root)
    add_child(section_panel)

func _open_section(section: String) -> void:
    map_view.visible = section != "cabinet"
    cabinet_container.visible = section == "cabinet"
    if section in ["map", "cabinet"]:
        section_panel.visible = false
        return
    section_panel.visible = true
    section_panel.set_meta("section", section)
    _refresh_section(section)

func _refresh_section(section: String) -> void:
    var c := WorldState.selected_country()
    match section:
        "economy":
            title_label.text = "ECONOMIA"
            content_label.text = "PIB: R$ %.2f tri\nInflação: %.1f%%\nDesemprego: %.1f%%\nDívida/PIB: %.1f%%\n\nDecisões econômicas alteram crescimento, aprovação e estabilidade." % [c.get("gdp_trillion",0.0), c.get("inflation",0.0), c.get("unemployment",0.0), c.get("debt_gdp",0.0)]
        "government":
            title_label.text = "GOVERNO / POLÍTICA"
            content_label.text = "Aprovação: %.1f%%\nEstabilidade: %.1f%%\n\nGabinete, Congresso, leis, crises e resposta pública serão conectados neste módulo." % [c.get("approval",0.0), c.get("stability",0.0)]
        "military":
            title_label.text = "FORÇAS ARMADAS"
            content_label.text = "Poder militar: %d/100\n\nPróximo estágio: tropas, bases, marinha, aviação, alcance e linhas de frente no mapa." % int(c.get("military_power",0))
        "diplomacy":
            title_label.text = "DIPLOMACIA"
            content_label.text = "País selecionado: %s\nRelações bilaterais, comércio, sanções, alianças e negociação ficam aqui." % c.get("name","-")
        "media":
            title_label.text = "MÍDIA / IMPRENSA"
            content_label.text = "Telejornal, jornais, redes sociais e coletivas serão alimentados pelo mesmo estado da simulação."

func _section_action() -> void:
    var section := str(section_panel.get_meta("section", ""))
    var c := WorldState.selected_country()
    match section:
        "economy":
            c["approval"] = clamp(float(c.get("approval",57.0)) + 0.5, 0.0, 100.0)
            c["debt_gdp"] = float(c.get("debt_gdp",70.0)) + 0.2
            WorldState.countries[WorldState.selected_country_id] = c
        "government":
            c["stability"] = clamp(float(c.get("stability",60.0)) + 0.6, 0.0, 100.0)
            WorldState.countries[WorldState.selected_country_id] = c
        "military":
            c["military_power"] = min(100, int(c.get("military_power",50)) + 1)
            WorldState.countries[WorldState.selected_country_id] = c
        "diplomacy":
            if WorldState.selected_country_id != "BRA":
                WorldState.set_relation("BRA", WorldState.selected_country_id, int(WorldState.countries["BRA"]["relations"].get(WorldState.selected_country_id,0)) + 5)
        "media":
            WorldState.advance_days(1)
    _refresh_all()

func _refresh_country(_id: String) -> void:
    _refresh_all()

func _refresh_all() -> void:
    var c := WorldState.selected_country()
    selected_label.text = "%s  |  PODER %d/100" % [c.get("name","País"), int(c.get("military_power",0))]
    date_label.text = "%02d/%02d/%04d" % [WorldState.day, WorldState.month, WorldState.year]
    if section_panel.visible:
        _refresh_section(str(section_panel.get_meta("section", "government")))

func _on_cabinet_hotspot(action: String) -> void:
    match action:
        "CrisisPhone": _open_section("diplomacy")
        "LawFolders": _open_section("government")
        "Globe": _open_section("map")
        "TV": _open_section("media")
