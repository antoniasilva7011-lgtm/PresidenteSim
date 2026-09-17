extends Control

signal finished

const STEPS := ["PAÍS", "LÍDER", "PARTIDO", "DIFICULDADE", "PROMESSA"]
const PARTIES := ["Independente", "Coalizão Reformista", "Aliança Social", "Movimento Liberal", "Frente Verde", "Partido Nacional"]
const DIFFICULTIES := ["Normal", "Realista", "Difícil", "Hardcore"]
const PROMISES := ["Estabilidade econômica", "Reduzir impostos", "Fortalecer defesa", "Expandir saúde e educação", "Combater corrupção", "Aumentar influência internacional"]

var card: PanelContainer
var stage_root: VBoxContainer
var country_preview: Label
var step_label: Label
var next_button: Button
var back_button: Button
var country_picker: OptionButton
var leader_input: LineEdit
var party_picker: OptionButton
var difficulty_picker: OptionButton
var promise_picker: OptionButton
var step_index: int = 0
var _country_ids: Array[String] = []
var _presenter_panel: PanelContainer
var _pulse: float = 0.0

var selected_country_id: String = "BRA"
var selected_leader_name: String = "Presidente"
var selected_party: String = "Independente"
var selected_difficulty: String = "Normal"
var selected_promise: String = "Estabilidade econômica"

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_STOP
    z_index = 100
    selected_country_id = WorldState.player_country_id
    selected_leader_name = WorldState.player_leader_name
    selected_party = WorldState.player_party
    selected_difficulty = WorldState.game_difficulty
    selected_promise = WorldState.campaign_promise
    _build_wizard()
    set_process(true)

func _process(delta: float) -> void:
    if _presenter_panel == null or not is_instance_valid(_presenter_panel):
        return
    _pulse += delta
    var k := 0.97 + sin(_pulse * 1.8) * 0.015
    _presenter_panel.modulate = Color(k, k, k, 1.0)

func _clear() -> void:
    for child in get_children():
        child.queue_free()
    card = null
    stage_root = null
    _presenter_panel = null

func _backdrop() -> void:
    var bg := ColorRect.new()
    bg.color = Color(0.006, 0.018, 0.030, 0.995)
    bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(bg)
    var glow := ColorRect.new()
    glow.color = Color(0.02, 0.13, 0.18, 0.16)
    glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    glow.offset_left = 70
    glow.offset_right = -70
    glow.offset_top = 55
    glow.offset_bottom = -55
    add_child(glow)

func _style(bg: Color, border: Color, radius: int = 10) -> StyleBoxFlat:
    var s := StyleBoxFlat.new()
    s.bg_color = bg
    s.border_color = border
    s.set_border_width_all(1)
    s.corner_radius_top_left = radius
    s.corner_radius_top_right = radius
    s.corner_radius_bottom_left = radius
    s.corner_radius_bottom_right = radius
    s.content_margin_left = 18
    s.content_margin_right = 18
    s.content_margin_top = 16
    s.content_margin_bottom = 16
    return s

func _make_card(width: float = 1180.0, height: float = 650.0) -> PanelContainer:
    var panel := PanelContainer.new()
    panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
    panel.custom_minimum_size = Vector2(width, height)
    panel.offset_left = -width * 0.5
    panel.offset_right = width * 0.5
    panel.offset_top = -height * 0.5
    panel.offset_bottom = height * 0.5
    panel.add_theme_stylebox_override("panel", _style(Color(0.022, 0.034, 0.047, 0.99), Color(0.18, 0.40, 0.48, 0.82), 12))
    add_child(panel)
    return panel

func _title(text: String, size: int = 30) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_size_override("font_size", size)
    l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return l

func _caption(text: String, size: int = 14) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_size_override("font_size", size)
    l.modulate = Color(0.70, 0.82, 0.87)
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return l

func _build_wizard() -> void:
    _clear()
    _backdrop()
    card = _make_card()
    var outer := VBoxContainer.new()
    outer.add_theme_constant_override("separation", 10)
    card.add_child(outer)
    outer.add_child(_title("PRESIDENTE SIMULATOR", 36))
    var subtitle := _title("NOVA PARTIDA • FORMAÇÃO DO GOVERNO", 18)
    subtitle.modulate = Color(0.43, 0.91, 0.98)
    outer.add_child(subtitle)
    step_label = _caption("")
    step_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    outer.add_child(step_label)
    var progress := HBoxContainer.new()
    progress.name = "Progress"
    progress.alignment = BoxContainer.ALIGNMENT_CENTER
    progress.add_theme_constant_override("separation", 5)
    for i in range(STEPS.size()):
        var chip := Label.new()
        chip.text = "%d  %s" % [i + 1, STEPS[i]]
        chip.custom_minimum_size = Vector2(142, 32)
        chip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        chip.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
        chip.add_theme_font_size_override("font_size", 12)
        progress.add_child(chip)
    outer.add_child(progress)
    var body := HBoxContainer.new()
    body.size_flags_vertical = Control.SIZE_EXPAND_FILL
    body.add_theme_constant_override("separation", 16)
    outer.add_child(body)
    var preview_panel := PanelContainer.new()
    preview_panel.custom_minimum_size = Vector2(365, 0)
    preview_panel.add_theme_stylebox_override("panel", _style(Color(0.014, 0.064, 0.083, 0.97), Color(0.23, 0.70, 0.80, 0.58), 10))
    body.add_child(preview_panel)
    var preview_box := VBoxContainer.new()
    preview_box.add_theme_constant_override("separation", 10)
    preview_panel.add_child(preview_box)
    var pt := _caption("DOSSIÊ INICIAL", 13)
    pt.modulate = Color(0.42, 0.91, 0.98)
    preview_box.add_child(pt)
    country_preview = Label.new()
    country_preview.add_theme_font_size_override("font_size", 16)
    country_preview.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    preview_box.add_child(country_preview)
    stage_root = VBoxContainer.new()
    stage_root.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    stage_root.add_theme_constant_override("separation", 14)
    body.add_child(stage_root)
    var controls := HBoxContainer.new()
    controls.add_theme_constant_override("separation", 8)
    outer.add_child(controls)
    back_button = Button.new()
    back_button.text = "VOLTAR"
    back_button.custom_minimum_size = Vector2(170, 48)
    back_button.pressed.connect(_previous_step)
    controls.add_child(back_button)
    var spacer := Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    controls.add_child(spacer)
    next_button = Button.new()
    next_button.text = "PRÓXIMO"
    next_button.custom_minimum_size = Vector2(270, 48)
    next_button.pressed.connect(_next_step)
    controls.add_child(next_button)
    _show_step(0, false)

func _capture_step_state() -> void:
    match step_index:
        0:
            if country_picker != null and is_instance_valid(country_picker) and country_picker.item_count > 0:
                selected_country_id = _country_ids[clampi(country_picker.selected, 0, _country_ids.size() - 1)]
        1:
            if leader_input != null and is_instance_valid(leader_input):
                var value := leader_input.text.strip_edges()
                selected_leader_name = value if not value.is_empty() else "Presidente"
        2:
            if party_picker != null and is_instance_valid(party_picker) and party_picker.item_count > 0:
                selected_party = party_picker.get_item_text(party_picker.selected)
        3:
            if difficulty_picker != null and is_instance_valid(difficulty_picker) and difficulty_picker.item_count > 0:
                selected_difficulty = difficulty_picker.get_item_text(difficulty_picker.selected)
        4:
            if promise_picker != null and is_instance_valid(promise_picker) and promise_picker.item_count > 0:
                selected_promise = promise_picker.get_item_text(promise_picker.selected)

func _show_step(index: int, capture: bool = true) -> void:
    if capture:
        _capture_step_state()
    step_index = clampi(index, 0, STEPS.size() - 1)
    for child in stage_root.get_children():
        child.queue_free()
    step_label.text = "ETAPA %d DE %d • %s" % [step_index + 1, STEPS.size(), STEPS[step_index]]
    back_button.disabled = step_index == 0
    next_button.text = "INICIAR MANDATO" if step_index == STEPS.size() - 1 else "PRÓXIMO"
    var progress := card.get_child(0).get_node("Progress") as HBoxContainer
    for i in range(progress.get_child_count()):
        var chip := progress.get_child(i) as Label
        chip.modulate = Color(0.50, 0.96, 1.0) if i == step_index else Color(0.48, 0.57, 0.62)
    match step_index:
        0: _build_country_step()
        1: _build_leader_step()
        2: _build_party_step()
        3: _build_difficulty_step()
        4: _build_promise_step()
    _update_preview()

func _build_country_step() -> void:
    stage_root.add_child(_title("ESCOLHA O PAÍS", 25))
    stage_root.add_child(_caption("O país define o ponto de partida econômico, político e militar da campanha."))
    country_picker = OptionButton.new()
    country_picker.custom_minimum_size = Vector2(0, 58)
    country_picker.item_selected.connect(func(_idx: int):
        if not _country_ids.is_empty():
            selected_country_id = _country_ids[clampi(country_picker.selected, 0, _country_ids.size() - 1)]
        _update_preview()
    )
    stage_root.add_child(country_picker)
    _populate_countries()

func _build_leader_step() -> void:
    stage_root.add_child(_title("CRIE SEU LÍDER", 25))
    stage_root.add_child(_caption("O nome aparece em pronunciamentos, boletins, crises e eventos de mídia."))
    leader_input = LineEdit.new()
    leader_input.placeholder_text = "Nome do líder"
    leader_input.text = selected_leader_name
    leader_input.custom_minimum_size = Vector2(0, 60)
    leader_input.virtual_keyboard_type = LineEdit.KEYBOARD_TYPE_DEFAULT
    leader_input.text_changed.connect(func(value: String):
        selected_leader_name = value.strip_edges() if not value.strip_edges().is_empty() else "Presidente"
        _update_preview()
    )
    stage_root.add_child(leader_input)
    stage_root.add_child(_caption("Etapa isolada no mobile para o teclado não cobrir as demais opções."))

func _build_party_step() -> void:
    stage_root.add_child(_title("PARTIDO / COALIZÃO", 25))
    stage_root.add_child(_caption("Arquétipos de gameplay para a campanha. A estrutura permite dados próprios por país e cenário no futuro."))
    party_picker = OptionButton.new()
    for name in PARTIES:
        party_picker.add_item(name)
    _select_text(party_picker, selected_party)
    party_picker.custom_minimum_size = Vector2(0, 58)
    party_picker.item_selected.connect(func(_idx: int):
        selected_party = party_picker.get_item_text(party_picker.selected)
        _update_preview()
    )
    stage_root.add_child(party_picker)

func _build_difficulty_step() -> void:
    stage_root.add_child(_title("DIFICULDADE", 25))
    stage_root.add_child(_caption("Define a pressão econômica, política e internacional durante a campanha."))
    difficulty_picker = OptionButton.new()
    for name in DIFFICULTIES:
        difficulty_picker.add_item(name)
    _select_text(difficulty_picker, selected_difficulty)
    difficulty_picker.custom_minimum_size = Vector2(0, 58)
    difficulty_picker.item_selected.connect(func(_idx: int):
        selected_difficulty = difficulty_picker.get_item_text(difficulty_picker.selected)
        _update_preview()
    )
    stage_root.add_child(difficulty_picker)

func _build_promise_step() -> void:
    stage_root.add_child(_title("PROMESSA DE CAMPANHA", 25))
    stage_root.add_child(_caption("A promessa define a prioridade pública do mandato e será usada por mídia e eventos."))
    promise_picker = OptionButton.new()
    for name in PROMISES:
        promise_picker.add_item(name)
    _select_text(promise_picker, selected_promise)
    promise_picker.custom_minimum_size = Vector2(0, 58)
    promise_picker.item_selected.connect(func(_idx: int):
        selected_promise = promise_picker.get_item_text(promise_picker.selected)
        _update_preview()
    )
    stage_root.add_child(promise_picker)

func _select_text(button: OptionButton, wanted: String) -> void:
    for i in range(button.item_count):
        if button.get_item_text(i) == wanted:
            button.select(i)
            return

func _populate_countries() -> void:
    _country_ids.clear()
    country_picker.clear()
    var rows: Array = []
    for id_variant in WorldState.countries.keys():
        var id := str(id_variant)
        var c: Dictionary = WorldState.countries[id] as Dictionary
        rows.append({"id": id, "name": str(c.get("name", id))})
    rows.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return str(a["name"]).nocasecmp_to(str(b["name"])) < 0
    )
    var selected_index := 0
    for row_variant in rows:
        var row: Dictionary = row_variant as Dictionary
        var id := str(row["id"])
        country_picker.add_item(str(row["name"]))
        _country_ids.append(id)
        if id == selected_country_id:
            selected_index = _country_ids.size() - 1
    if country_picker.item_count > 0:
        country_picker.select(selected_index)

func _update_preview() -> void:
    if country_preview == null:
        return
    var c: Dictionary = WorldState.countries.get(selected_country_id, WorldState.player_country()) as Dictionary
    country_preview.text = "%s\n\nLíder: %s\nLinha política: %s\nDificuldade: %s\n\nPIB: %.2f tri\nInflação: %.1f%%\nDesemprego: %.1f%%\nEstabilidade: %.0f%%\nPoder militar: %d/100\n\nPromessa: %s" % [
        str(c.get("name", "País")).to_upper(), selected_leader_name, selected_party, selected_difficulty,
        float(c.get("gdp_trillion", 0.0)), float(c.get("inflation", 0.0)), float(c.get("unemployment", 0.0)),
        float(c.get("stability", 0.0)), int(c.get("military_power", 0)), selected_promise
    ]

func _previous_step() -> void:
    if step_index > 0:
        _show_step(step_index - 1)

func _next_step() -> void:
    if step_index < STEPS.size() - 1:
        _show_step(step_index + 1)
    else:
        _capture_step_state()
        WorldState.start_new_game(selected_country_id, selected_leader_name, selected_party, selected_difficulty, selected_promise)
        _build_inauguration_news()

func _build_inauguration_news() -> void:
    _clear()
    _backdrop()
    var shell := _make_card(1260, 680)
    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 10)
    shell.add_child(root)

    var top := HBoxContainer.new()
    root.add_child(top)
    var network := Label.new()
    network.text = "PRESIDENTE NEWS • AO VIVO"
    network.add_theme_font_size_override("font_size", 18)
    network.modulate = Color(0.32, 0.93, 1.0)
    top.add_child(network)
    var spacer := Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    top.add_child(spacer)
    var date := Label.new()
    date.text = "%02d/%02d/%04d" % [WorldState.day, WorldState.month, WorldState.year]
    date.modulate = Color(0.70, 0.80, 0.84)
    top.add_child(date)

    var body := HBoxContainer.new()
    body.size_flags_vertical = Control.SIZE_EXPAND_FILL
    body.add_theme_constant_override("separation", 18)
    root.add_child(body)

    _presenter_panel = PanelContainer.new()
    _presenter_panel.custom_minimum_size = Vector2(430, 0)
    _presenter_panel.add_theme_stylebox_override("panel", _style(Color(0.016, 0.075, 0.10, 1.0), Color(0.28, 0.75, 0.83, 0.68), 10))
    body.add_child(_presenter_panel)
    var studio := VBoxContainer.new()
    studio.alignment = BoxContainer.ALIGNMENT_CENTER
    studio.add_theme_constant_override("separation", 7)
    _presenter_panel.add_child(studio)

    var anchor := Control.new()
    anchor.custom_minimum_size = Vector2(350, 330)
    anchor.set_script(load("res://scripts/news_anchor.gd"))
    studio.add_child(anchor)
    var presenter_name := _title("HELENA MORAES • PRESIDENTE NEWS", 15)
    presenter_name.modulate = Color(0.82, 0.96, 1.0)
    studio.add_child(presenter_name)
    var live := Label.new()
    live.text = "● AO VIVO   •   NEWSROOM CENTRAL"
    live.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    live.modulate = Color(1.0, 0.42, 0.35)
    studio.add_child(live)

    var story := VBoxContainer.new()
    story.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    story.add_theme_constant_override("separation", 10)
    body.add_child(story)
    var country: Dictionary = WorldState.player_country()

    var breaking := Label.new()
    breaking.text = "PLANTÃO • TRANSIÇÃO DE PODER"
    breaking.add_theme_font_size_override("font_size", 13)
    breaking.modulate = Color(1.0, 0.78, 0.28)
    story.add_child(breaking)
    story.add_child(_title("NOVO GOVERNO TOMA POSSE", 31))

    var lead := Label.new()
    lead.text = "%s assume o governo de %s representando %s. O país acompanha as primeiras horas do novo mandato." % [WorldState.player_leader_name, country.get("name", "o país"), WorldState.player_party]
    lead.add_theme_font_size_override("font_size", 19)
    lead.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    story.add_child(lead)

    var stats_panel := PanelContainer.new()
    stats_panel.add_theme_stylebox_override("panel", _style(Color(0.012, 0.045, 0.060, 0.94), Color(0.14, 0.37, 0.43, 0.7), 8))
    var stats := Label.new()
    stats.text = "APROVAÇÃO  %.0f%%    •    PIB  %.2f tri\nINFLAÇÃO  %.1f%%    •    ESTABILIDADE  %.0f%%\nDIFICULDADE  %s\nPROMESSA  %s" % [
        float(country.get("approval", 0.0)), float(country.get("gdp_trillion", 0.0)), float(country.get("inflation", 0.0)),
        float(country.get("stability", 0.0)), WorldState.game_difficulty, WorldState.campaign_promise
    ]
    stats.add_theme_font_size_override("font_size", 16)
    stats_panel.add_child(stats)
    story.add_child(stats_panel)

    var challenge := Label.new()
    challenge.text = _opening_challenge(country)
    challenge.add_theme_font_size_override("font_size", 16)
    challenge.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    challenge.modulate = Color(0.82, 0.88, 0.91)
    story.add_child(challenge)

    var ticker_panel := PanelContainer.new()
    ticker_panel.add_theme_stylebox_override("panel", _style(Color(0.16, 0.045, 0.025, 0.95), Color(0.62, 0.27, 0.10, 0.85), 3))
    var ticker := Label.new()
    ticker.text = "BREAKING  •  MERCADOS REAGEM À POSSE  •  GABINETE PREPARA PRIMEIRAS MEDIDAS  •  DIPLOMACIA OBSERVA NOVO GOVERNO  •  IMPRENSA COBRA PRIORIDADES"
    ticker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    ticker.add_theme_font_size_override("font_size", 13)
    ticker.modulate = Color(1.0, 0.86, 0.62)
    ticker_panel.add_child(ticker)
    root.add_child(ticker_panel)

    var actions := HBoxContainer.new()
    actions.add_theme_constant_override("separation", 8)
    root.add_child(actions)
    var skip := Button.new()
    skip.text = "PULAR INTRODUÇÃO"
    skip.custom_minimum_size = Vector2(260, 52)
    skip.pressed.connect(_finish_intro)
    actions.add_child(skip)
    var gap := Control.new()
    gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    actions.add_child(gap)
    var briefing := Button.new()
    briefing.text = "VER BRIEFING DO PAÍS"
    briefing.custom_minimum_size = Vector2(320, 52)
    briefing.pressed.connect(_build_briefing)
    actions.add_child(briefing)

func _opening_challenge(country: Dictionary) -> String:
    var inflation := float(country.get("inflation", 0.0))
    var stability := float(country.get("stability", 0.0))
    if inflation >= 8.0:
        return "PRIMEIRO DESAFIO: conter a pressão inflacionária sem provocar uma crise de emprego e popularidade."
    if stability < 55.0:
        return "PRIMEIRO DESAFIO: reconstruir estabilidade interna e formar apoio político suficiente para sustentar o governo."
    if int(country.get("military_power", 0)) < 35:
        return "PRIMEIRO DESAFIO: equilibrar prioridades internas com a necessidade de ampliar capacidade estratégica e diplomática."
    return "PRIMEIRO DESAFIO: definir prioridades econômicas, montar alianças e estabelecer a agenda internacional do mandato."

func _build_briefing() -> void:
    _clear()
    _backdrop()
    var shell := _make_card(1180, 650)
    var root := VBoxContainer.new()
    root.add_theme_constant_override("separation", 12)
    shell.add_child(root)
    root.add_child(_title("BRIEFING PRESIDENCIAL", 32))
    var country := WorldState.player_country()
    var sub := _caption("%s • relatório inicial de governo" % str(country.get("name", "País")).to_upper(), 16)
    sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    root.add_child(sub)
    var columns := HBoxContainer.new()
    columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
    columns.add_theme_constant_override("separation", 14)
    root.add_child(columns)
    columns.add_child(_brief_card("SITUAÇÃO INTERNA", "Aprovação: %.0f%%\nEstabilidade: %.0f%%\nInflação: %.1f%%\nDesemprego: %.1f%%\nDívida/PIB: %.1f%%" % [float(country.get("approval",0)), float(country.get("stability",0)), float(country.get("inflation",0)), float(country.get("unemployment",0)), float(country.get("debt_gdp",0))]))
    columns.add_child(_brief_card("SEGURANÇA E PODER", "Poder militar: %d/100\nDefesa: %.1f%% do PIB\nTensão global: %.0f%%\nTesouro: %.1f bi\nRelação com imprensa: %.0f%%" % [int(country.get("military_power",0)), WorldState.defense_spending, WorldState.global_tension, WorldState.treasury, WorldState.press_relation]))
    columns.add_child(_brief_card("AGENDA DO MANDATO", "Promessa principal:\n%s\n\nPrioridade imediata:\n%s\n\nGabinete inicial: %d ministros-chave" % [WorldState.campaign_promise, _opening_challenge(country).replace("PRIMEIRO DESAFIO: ", ""), WorldState.cabinet.size()]))
    var enter := Button.new()
    enter.text = "ENTRAR NA CENTRAL DE COMANDO"
    enter.custom_minimum_size = Vector2(0, 56)
    enter.pressed.connect(_finish_intro)
    root.add_child(enter)

func _brief_card(title_text: String, body_text: String) -> PanelContainer:
    var panel := PanelContainer.new()
    panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    panel.add_theme_stylebox_override("panel", _style(Color(0.018, 0.050, 0.066, 0.96), Color(0.18, 0.48, 0.56, 0.55), 9))
    var box := VBoxContainer.new()
    box.add_theme_constant_override("separation", 10)
    panel.add_child(box)
    var t := Label.new()
    t.text = title_text
    t.add_theme_font_size_override("font_size", 16)
    t.modulate = Color(0.42, 0.90, 0.96)
    box.add_child(t)
    var body := Label.new()
    body.text = body_text
    body.add_theme_font_size_override("font_size", 16)
    body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    box.add_child(body)
    return panel

func _finish_intro() -> void:
    finished.emit()
    queue_free()
