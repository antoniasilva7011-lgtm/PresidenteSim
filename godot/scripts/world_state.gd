extends Node

signal country_selected(country_id: String)
signal simulation_changed

var day := 15
var month := 9
var year := 2026
var selected_country_id := "BRA"
var countries: Dictionary = {}

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
        "relations": {}
    }

func merge_geo_country(id: String, name: String) -> void:
    if id.is_empty():
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
        "relations": {}
    }

func select_country(id: String) -> void:
    if not countries.has(id):
        return
    selected_country_id = id
    country_selected.emit(id)

func selected_country() -> Dictionary:
    return countries.get(selected_country_id, {})

func advance_days(amount: int) -> void:
    day += amount
    while day > 30:
        day -= 30
        month += 1
    while month > 12:
        month -= 12
        year += 1
    _tick_economy(float(amount))
    simulation_changed.emit()

func _tick_economy(days_elapsed: float) -> void:
    for id in countries.keys():
        var c: Dictionary = countries[id]
        var pressure := (c["inflation"] - 4.0) * 0.002 * days_elapsed
        c["approval"] = clamp(c["approval"] - pressure, 0.0, 100.0)
        c["stability"] = clamp(c["stability"] - max(0.0, pressure * 0.45), 0.0, 100.0)
        countries[id] = c

func set_relation(a: String, b: String, value: int) -> void:
    if not countries.has(a) or not countries.has(b):
        return
    countries[a]["relations"][b] = clamp(value, -100, 100)
    countries[b]["relations"][a] = clamp(value, -100, 100)
    simulation_changed.emit()

func negotiate_with(target: String) -> void:
    var current := int(countries[selected_country_id]["relations"].get(target, 0))
    set_relation(selected_country_id, target, current + 5)
