extends Control

signal country_clicked(country_id: String)

const GEOJSON_PATH := "res://data/world.geojson"
var features: Array = []
var zoom := 1.0
var pan := Vector2.ZERO
var _touches: Dictionary = {}
var _last_mouse := Vector2.ZERO
var _mouse_dragging := false
var _pinch_start_distance := 0.0
var _pinch_start_zoom := 1.0
var selected_id := "BRA"

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    _load_geojson()
    WorldState.country_selected.connect(_on_country_selected)
    queue_redraw()

func _load_geojson() -> void:
    if not FileAccess.file_exists(GEOJSON_PATH):
        push_warning("world.geojson ausente. Execute godot/tools/prepare_data.py antes de exportar.")
        return
    var raw := FileAccess.get_file_as_string(GEOJSON_PATH)
    var parsed = JSON.parse_string(raw)
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("GeoJSON inválido")
        return
    features = parsed.get("features", [])
    for f in features:
        var props: Dictionary = f.get("properties", {})
        var name := str(props.get("ADMIN", props.get("name", "País")))
        var iso := str(props.get("ADM0_A3", props.get("ISO_A3", props.get("ISO3166-1-Alpha-3", ""))))
        if iso == "-99" or iso.is_empty():
            iso = name.to_upper().replace(" ", "_")
        f["_presim_id"] = iso
        WorldState.merge_geo_country(iso, name)

func reset_view() -> void:
    zoom = 1.0
    pan = Vector2.ZERO
    queue_redraw()

func zoom_by(factor: float, focus := Vector2.ZERO) -> void:
    var old := zoom
    zoom = clamp(zoom * factor, 1.0, 8.0)
    if focus != Vector2.ZERO:
        pan = focus - (focus - pan) * (zoom / old)
    queue_redraw()

func _gui_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        _handle_touch(event)
        accept_event()
    elif event is InputEventScreenDrag:
        _handle_drag(event)
        accept_event()
    elif event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
            zoom_by(1.18, event.position)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
            zoom_by(1.0 / 1.18, event.position)
        elif event.button_index == MOUSE_BUTTON_LEFT:
            _mouse_dragging = event.pressed
            _last_mouse = event.position
            if not event.pressed:
                _select_at(event.position)
        accept_event()
    elif event is InputEventMouseMotion and _mouse_dragging:
        pan += event.position - _last_mouse
        _last_mouse = event.position
        queue_redraw()
        accept_event()

func _handle_touch(event: InputEventScreenTouch) -> void:
    if event.pressed:
        _touches[event.index] = event.position
        if _touches.size() == 2:
            var pts := _touches.values()
            _pinch_start_distance = pts[0].distance_to(pts[1])
            _pinch_start_zoom = zoom
    else:
        var release_pos := event.position
        var was_single := _touches.size() == 1
        _touches.erase(event.index)
        if was_single:
            _select_at(release_pos)
        if _touches.size() < 2:
            _pinch_start_distance = 0.0

func _handle_drag(event: InputEventScreenDrag) -> void:
    _touches[event.index] = event.position
    if _touches.size() == 1:
        pan += event.relative
        queue_redraw()
    elif _touches.size() >= 2:
        var pts := _touches.values()
        var distance := pts[0].distance_to(pts[1])
        if _pinch_start_distance <= 0.0:
            _pinch_start_distance = distance
            _pinch_start_zoom = zoom
        var center: Vector2 = (pts[0] + pts[1]) * 0.5
        var old := zoom
        zoom = clamp(_pinch_start_zoom * distance / max(1.0, _pinch_start_distance), 1.0, 8.0)
        pan = center - (center - pan) * (zoom / max(0.001, old))
        queue_redraw()

func _project(coord: Array) -> Vector2:
    var lon := float(coord[0])
    var lat := float(coord[1])
    var base := Vector2((lon + 180.0) / 360.0 * size.x, (90.0 - lat) / 180.0 * size.y)
    return base * zoom + pan

func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO, size), Color("07131d"))
    if features.is_empty():
        _draw_missing_data()
        return
    for f in features:
        var id := str(f.get("_presim_id", ""))
        var geom: Dictionary = f.get("geometry", {})
        var gtype := str(geom.get("type", ""))
        var coords = geom.get("coordinates", [])
        var fill := _country_color(id)
        if gtype == "Polygon":
            _draw_polygon_group(coords, fill)
        elif gtype == "MultiPolygon":
            for poly in coords:
                _draw_polygon_group(poly, fill)

func _draw_polygon_group(rings: Array, fill: Color) -> void:
    if rings.is_empty():
        return
    var outer: PackedVector2Array = []
    for c in rings[0]:
        outer.append(_project(c))
    if outer.size() >= 3:
        draw_colored_polygon(outer, fill)
        draw_polyline(outer, Color(0.15, 0.72, 0.95, 0.38), 1.0, true)

func _country_color(id: String) -> Color:
    if id == selected_id:
        return Color(0.08, 0.58, 0.78, 0.95)
    var c: Dictionary = WorldState.countries.get(id, {})
    var stability := float(c.get("stability", 55.0))
    var t := clamp(stability / 100.0, 0.0, 1.0)
    return Color(0.05 + 0.08 * t, 0.16 + 0.22 * t, 0.20 + 0.16 * t, 0.96)

func _select_at(pos: Vector2) -> void:
    var best_id := ""
    var best_distance := 99999.0
    for f in features:
        var id := str(f.get("_presim_id", ""))
        var geom: Dictionary = f.get("geometry", {})
        var coords = geom.get("coordinates", [])
        var center := _feature_center(coords, str(geom.get("type", "")))
        if center == Vector2.INF:
            continue
        var d := center.distance_to(pos)
        if d < best_distance:
            best_distance = d
            best_id = id
    if not best_id.is_empty() and best_distance < 120.0 * max(1.0, zoom):
        WorldState.select_country(best_id)
        country_clicked.emit(best_id)

func _feature_center(coords, gtype: String) -> Vector2:
    var points: Array = []
    if gtype == "Polygon" and coords.size() > 0:
        points = coords[0]
    elif gtype == "MultiPolygon" and coords.size() > 0 and coords[0].size() > 0:
        points = coords[0][0]
    if points.is_empty():
        return Vector2.INF
    var sum := Vector2.ZERO
    var count := 0
    for c in points:
        sum += _project(c)
        count += 1
    return sum / max(1, count)

func _on_country_selected(id: String) -> void:
    selected_id = id
    queue_redraw()

func _draw_missing_data() -> void:
    draw_string(get_theme_default_font(), Vector2(50, 90), "MAPA GEOJSON NÃO PREPARADO", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, Color.WHITE)
    draw_string(get_theme_default_font(), Vector2(50, 130), "Execute: python godot/tools/prepare_data.py", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.6,0.75,0.85))
