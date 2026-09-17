extends Node

signal country_selected(country_id: String)
signal simulation_changed
signal event_created(event: Dictionary)

var day := 15
var month := 9
var year := 2026
var selected_country_id := "BRA"
var player_country_id := "BRA"
var countries: Dictionary = {}
var treasury := 420.0
var tax_rate := 28.0
var interest_rate := 10.5
var social_spending := 18.0
var defense_spending := 1.4
var press_relation := 52.0
var global_tension := 24.0
var last_event: Dictionary = {}

func _ready() -> void:
    _ensure_default_world()

func _ensure_default_world() -> void:
    if not countries.is_empty():
        return
    _add_country("BRA", "Brasil", 215000000, 2.10, 4.8, 7.2, 78.4, 72)
    _add_country("USA", "Estados Unidos", 347000000, 29.18, 2.9, 4.3, 121.0, 96)
    _add_country("CHN", "China", 1410000000, 18.70, 1.1, 5.1, 88.0, 94)
    _add_country("RUS", "Rússia", 144000000, 2.20, 6.8, 2.4, 20.0, 91)
    _add_country("IND", "Índia", 1460000000, 4.30, 4.1, 7.0, 82.0, 86)
    _add_country("ARG", "Argentina", 46000000, 0.64, 18.0, 7.5, 84.0, 55)

func _add_country(id: String, name: String, population: int, gdp_t: float, inflation: float, unemployment: float, debt: float, power: int) -> void:
    countries[id] = {
        "id": id,
        "name": name,
        "population": population,
        "gdp_trillion": gdp_t,
        "inflation": inflation,
        "unemployment": unemployment,
        "debt_gdp": debt,
        "military_power": power,
        "stability": 68.0,
        "approval": 57.0,
        "relations": {},
        "trade_balance": 0.0,
        "sanctioned": false,
        "war": false
    }

func merge_geo_country(id: String, name: String) -> void:
    if id.is_empty() or id == "-99":
        id = name.to_upper().replace(" ", "_")
    if countries.has(id):
        countries[id]["name"] = name
        return
    var seed := abs(name.hash())
    countries[id] = {
        "id": id,
        "name": name,
        "population": 500000 + seed % 180000000,
        "gdp_trillion": 0.05 + float(seed % 800) / 100.0,
        "inflation": 1.0 + float(seed % 110) / 10.0,
        "unemployment": 2.0 + float(seed % 130) / 10.0,
        "debt_gdp": 20.0 + float(seed % 1200) / 10.0,
        "military_power": 15 + seed % 81,
        "stability": 45.0 + float(seed % 500) / 10.0,
        "approval": 40.0 + float(seed % 350) / 10.0,
        "relations": {},
        "trade_balance": float((seed % 400) - 200) / 10.0,
        "sanctioned": false,
        "war": false
    }

func select_country(id: String) -> void:
    if not countries.has(id):
        return
    selected_country_id = id
    country_selected.emit(id)

func selected_country() -> Dictionary:
    return countries.get(selected_country_id, {})

func player_country() -> Dictionary:
    return countries.get(player_country_id, {})

func advance_days(amount: int) -> void:
    day += amount
    while day > 30:
        day -= 30
        month += 1
    while month > 12:
        month -= 12
        year += 1
    _tick_economy(float(amount))
    _maybe_event(amount)
    simulation_changed.emit()

func _tick_economy(days_elapsed: float) -> void:
    for id in countries.keys():
        var c: Dictionary = countries[id]
        var pressure := (float(c["inflation"]) - 4.0) * 0.002 * days_elapsed
        c["approval"] = clamp(float(c["approval"]) - pressure, 0.0, 100.0)
        c["stability"] = clamp(float(c["stability"]) - max(0.0, pressure * 0.45), 0.0, 100.0)
        countries[id] = c
    var player := player_country()
    var fiscal_flow := (tax_rate - social_spending - defense_spending * 2.0) * 0.02 * days_elapsed
    treasury += fiscal_flow
    player["inflation"] = clamp(float(player["inflation"]) + (social_spending - tax_rate * 0.35) * 0.0007 * days_elapsed - interest_rate * 0.00025 * days_elapsed, 0.1, 80.0)
    player["unemployment"] = clamp(float(player["unemployment"]) + (interest_rate - 8.0) * 0.0005 * days_elapsed, 1.0, 40.0)
    countries[player_country_id] = player

func set_relation(a: String, b: String, value: int) -> void:
    if not countries.has(a) or not countries.has(b):
        return
    countries[a]["relations"][b] = clamp(value, -100, 100)
    countries[b]["relations"][a] = clamp(value, -100, 100)
    simulation_changed.emit()

func relation_between(a: String, b: String) -> int:
    if not countries.has(a):
        return 0
    return int(countries[a]["relations"].get(b, 0))

func negotiate_with(target: String) -> void:
    if target == player_country_id or not countries.has(target):
        return
    var current := relation_between(player_country_id, target)
    set_relation(player_country_id, target, current + 5)
    press_relation = clamp(press_relation + 0.4, 0.0, 100.0)
    _make_event("Diplomacia", "Negociação avança com %s" % countries[target]["name"])

func impose_sanctions(target: String) -> void:
    if target == player_country_id or not countries.has(target):
        return
    countries[target]["sanctioned"] = true
    set_relation(player_country_id, target, relation_between(player_country_id, target) - 20)
    global_tension = clamp(global_tension + 4.0, 0.0, 100.0)
    _make_event("Diplomacia", "Brasil impõe sanções a %s" % countries[target]["name"])

func adjust_economy(kind: String, delta: float) -> void:
    match kind:
        "tax": tax_rate = clamp(tax_rate + delta, 5.0, 60.0)
        "interest": interest_rate = clamp(interest_rate + delta, 0.0, 40.0)
        "social": social_spending = clamp(social_spending + delta, 1.0, 40.0)
        "defense": defense_spending = clamp(defense_spending + delta, 0.2, 10.0)
    simulation_changed.emit()

func political_action(kind: String) -> void:
    var c := player_country()
    match kind:
        "speech":
            c["approval"] = clamp(float(c["approval"]) + 0.8, 0.0, 100.0)
            press_relation = clamp(press_relation + 0.6, 0.0, 100.0)
        "reform":
            c["stability"] = clamp(float(c["stability"]) + 1.0, 0.0, 100.0)
            c["approval"] = clamp(float(c["approval"]) - 0.3, 0.0, 100.0)
    countries[player_country_id] = c
    simulation_changed.emit()

func military_action(kind: String) -> void:
    var c := player_country()
    match kind:
        "exercise":
            c["military_power"] = min(100, int(c["military_power"]) + 1)
            treasury -= 1.2
        "mobilize":
            c["military_power"] = min(100, int(c["military_power"]) + 2)
            global_tension = clamp(global_tension + 2.5, 0.0, 100.0)
            treasury -= 2.5
    countries[player_country_id] = c
    simulation_changed.emit()

func _maybe_event(days_elapsed: int) -> void:
    if days_elapsed < 7:
        return
    var c := player_country()
    if float(c["inflation"]) > 8.0:
        _make_event("Economia", "Inflação pressiona consumo e popularidade")
    elif global_tension > 55.0:
        _make_event("Mundo", "Tensão internacional cresce e mercados reagem")

func _make_event(category: String, headline: String) -> void:
    last_event = {
        "category": category,
        "headline": headline,
        "date": "%02d/%02d/%04d" % [day, month, year]
    }
    event_created.emit(last_event)
