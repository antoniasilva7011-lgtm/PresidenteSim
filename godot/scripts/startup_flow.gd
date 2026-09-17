extends Control

signal finished

var country_picker: OptionButton
var party_picker: OptionButton
var leader_input: LineEdit
var difficulty_picker: OptionButton
var card: PanelContainer
var stage_root: VBoxContainer
var _country_ids: Array[String] = []
var _pulse: float = 0.0
var _presenter: ColorRect

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_STOP
    z_index = 100
    _build_setup()
    set_process(true)

func _process(delta: float) -> void:
    if _presenter == null or not is_instance_valid(_presenter):
        return
    _pulse += delta
    var k: float = 0.88 + sin(_pulse * 2.4) * 0.06
    _presenter.modulate = Color(k, k, k, 1.0)

func _clear() -> void:
    for child in get_children():
        child.queue_free()
    card = null
    stage_root = null
    _presenter = null

func _backdrop() -> ColorRect:
    var bg := ColorRect.new()
    bg.color = Color(0.008, 0.025, 0.04, 0.985)
    bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(bg)
    return bg

func _make_card(width: float = 1050.0) -> PanelContainer:
    var panel := PanelContainer.new()
    panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
    panel.custom_minimum_size = Vector2(width, 610)
    panel.offset_left = -width * 0.5
    panel.offset_right = width * 0.5
    panel.offset_top = -305
    panel.offset_bottom = 305
    add_child(panel)
    return panel

func _title(text: String, size: int = 32) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_size_override("font_size", size)
    l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return l

func _caption(text: String) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_size_override("font_size", 15)
    l.modulate = Color(0.72, 0.82, 0.87)
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return l

func _build_setup() -> void:
    _clear()
    _backdrop()
    card = _make_card()
    stage_root = VBoxContainer.new()
    stage_root.add_theme_constant_override("separation", 14)
    card.add_child(stage_root)

    stage_root.add_child(_title("PRESIDENTE SIMULATOR", 38))
    stage_root.add_child(_title("CRIAR NOVO GOVERNO", 22))
    stage_root.add_child(_caption("Escolha o país, defina seu personagem e a linha partidária da partida. Depois da confirmação, o jogo abre com um boletim de posse antes de liberar o mapa."))

    var grid := GridContainer.new()
    grid.columns = 2
    grid.add_theme_constant_override("h_separation", 20)
    grid.add_theme_constant_override("v_separation", 12)
    stage_root.add_child(grid)

    grid.add_child(_field_label("PAÍS"))
    country_picker = OptionButton.new()
    country_picker.custom_minimum_size = Vector2(0, 48)
    grid.add_child(country_picker)
    _populate_countries()

    grid.add_child(_field_label("NOME DO LÍDER"))
    leader_input = LineEdit.new()
    leader_input.placeholder_text = "Digite o nome do presidente"
    leader_input.text = "Presidente"
    leader_input.custom_minimum_size = Vector2(0, 48)
    grid.add_child(leader_input)

    grid.add_child(_field_label("PARTIDO / COALIZÃO"))
    party_picker = OptionButton.new()
    for name in ["Independente", "Coalizão Reformista", "Aliança Social", "Movimento Liberal", "Frente Verde", "Partido Nacional"]:
        party_picker.add_item(name)
    party_picker.custom_minimum_size = Vector2(0, 48)
    grid.add_child(party_picker)

    grid.add_child(_field_label("DIFICULDADE"))
    difficulty_picker = OptionButton.new()
    for name in ["Normal", "Realista", "Difícil"]:
        difficulty_picker.add_item(name)
    difficulty_picker.custom_minimum_size = Vector2(0, 48)
    grid.add_child(difficulty_picker)

    var hint := _caption("Nesta versão, partidos são arquétipos de jogo. A estrutura já fica pronta para receber partidos reais por país posteriormente, com dados separados por cenário.")
    stage_root.add_child(hint)

    var spacer := Control.new()
    spacer.custom_minimum_size = Vector2(0, 10)
    stage_root.add_child(spacer)

    var start := Button.new()
    start.text = "INICIAR MANDATO"
    start.custom_minimum_size = Vector2(0, 56)
    start.pressed.connect(_confirm_setup)
    stage_root.add_child(start)

func _field_label(text: String) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_size_override("font_size", 16)
    l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    return l

func _populate_countries() -> void:
    _country_ids.clear()
    country_picker.clear()
    var rows: Array = []
    for id_variant: Variant in WorldState.countries.keys():
        var id: String = str(id_variant)
        var c: Dictionary = WorldState.countries[id] as Dictionary
        rows.append({"id": id, "name": str(c.get("name", id))})
    rows.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return str(a["name"]).nocasecmp_to(str(b["name"])) < 0
    )
    var selected_index: int = 0
    for row_variant: Variant in rows:
        var row: Dictionary = row_variant as Dictionary
        var id: String = str(row["id"])
        country_picker.add_item(str(row["name"]))
        _country_ids.append(id)
        if id == WorldState.player_country_id:
            selected_index = _country_ids.size() - 1
    if country_picker.item_count > 0:
        country_picker.select(selected_index)

func _confirm_setup() -> void:
    if _country_ids.is_empty():
        return
    var index: int = clampi(country_picker.selected, 0, _country_ids.size() - 1)
    var country_id: String = _country_ids[index]
    var leader_name: String = leader_input.text.strip_edges()
    if leader_name.is_empty():
        leader_name = "Presidente"
    var party_name: String = party_picker.get_item_text(party_picker.selected)
    var difficulty: String = difficulty_picker.get_item_text(difficulty_picker.selected)
    WorldState.start_new_game(country_id, leader_name, party_name, difficulty)
    _build_inauguration_news()

func _build_inauguration_news() -> void:
    _clear()
    _backdrop()

    var shell := PanelContainer.new()
    shell.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
    shell.custom_minimum_size = Vector2(1220, 650)
    shell.offset_left = -610
    shell.offset_right = 610
    shell.offset_top = -325
    shell.offset_bottom = 325
    add_child(shell)

    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 10)
    shell.add_child(root)

    var network := Label.new()
    network.text = "PRESIDENTE NEWS • AO VIVO"
    network.add_theme_font_size_override("font_size", 18)
    network.modulate = Color(0.35, 0.92, 1.0)
    root.add_child(network)

    var body := HBoxContainer.new()
    body.size_flags_vertical = Control.SIZE_EXPAND_FILL
    body.add_theme_constant_override("separation", 24)
    root.add_child(body)

    var studio := PanelContainer.new()
    studio.custom_minimum_size = Vector2(420, 0)
    body.add_child(studio)
    var studio_box := VBoxContainer.new()
    studio_box.alignment = BoxContainer.ALIGNMENT_CENTER
    studio_box.add_theme_constant_override("separation", 12)
    studio.add_child(studio_box)

    _presenter = ColorRect.new()
    _presenter.color = Color(0.16, 0.48, 0.60)
    _presenter.custom_minimum_size = Vector2(190, 260)
    studio_box.add_child(_presenter)
    var presenter_name := _title("ÂNCORA • NEWSROOM", 17)
    studio_box.add_child(presenter_name)
    studio_box.add_child(_caption("Boletim especial de início de mandato"))

    var story := VBoxContainer.new()
    story.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    story.add_theme_constant_override("separation", 12)
    body.add_child(story)

    var country: Dictionary = WorldState.player_country()
    story.add_child(_title("NOVO GOVERNO TOMA POSSE", 34))
    var lead := Label.new()
    lead.text = "%s assume o governo de %s representando %s." % [WorldState.player_leader_name, country.get("name", "o país"), WorldState.player_party]
    lead.add_theme_font_size_override("font_size", 21)
    lead.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    story.add_child(lead)

    var stats := Label.new()
    stats.text = "APROVAÇÃO INICIAL  %.0f%%\nPIB  %.2f tri\nINFLAÇÃO  %.1f%%\nESTABILIDADE  %.0f%%\nDIFICULDADE  %s" % [
        float(country.get("approval", 0.0)),
        float(country.get("gdp_trillion", 0.0)),
        float(country.get("inflation", 0.0)),
        float(country.get("stability", 0.0)),
        WorldState.game_difficulty
    ]
    stats.add_theme_font_size_override("font_size", 19)
    story.add_child(stats)

    var challenge := Label.new()
    challenge.text = _opening_challenge(country)
    challenge.add_theme_font_size_override("font_size", 17)
    challenge.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    challenge.modulate = Color(0.82, 0.88, 0.91)
    story.add_child(challenge)

    var ticker := Label.new()
    ticker.text = "BREAKING • MERCADOS ACOMPANHAM NOVO GOVERNO • DIPLOMACIA AGUARDA PRIMEIRAS MEDIDAS • IMPRENSA ANALISA GABINETE"
    ticker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    ticker.add_theme_font_size_override("font_size", 15)
    ticker.modulate = Color(1.0, 0.82, 0.32)
    root.add_child(ticker)

    var enter := Button.new()
    enter.text = "ENTRAR NO MAPA MUNDIAL"
    enter.custom_minimum_size = Vector2(0, 54)
    enter.pressed.connect(_finish_intro)
    root.add_child(enter)

func _opening_challenge(country: Dictionary) -> String:
    var inflation: float = float(country.get("inflation", 0.0))
    var stability: float = float(country.get("stability", 0.0))
    if inflation >= 8.0:
        return "PRIMEIRO DESAFIO: conter a pressão inflacionária sem comprometer emprego e aprovação."
    if stability < 55.0:
        return "PRIMEIRO DESAFIO: estabilizar o ambiente interno e construir apoio político para o novo governo."
    return "PRIMEIRO DESAFIO: definir prioridades econômicas, formar alianças e estabelecer a agenda internacional do mandato."

func _finish_intro() -> void:
    finished.emit()
    queue_free()
