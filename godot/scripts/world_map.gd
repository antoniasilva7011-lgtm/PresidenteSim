extends Control

signal country_clicked(country_id: String)

const GEOJSON_PATH: String = "res://data/world.geojson"
const TEXTURE_PATH: String = "res://data/world_texture.jpg"
const MIN_ZOOM: float = 1.0
const MAX_ZOOM: float = 8.0

var features: Array = []
var labels: Array = []
var physical_texture: Texture2D = null
var zoom: float = 1.0
var pan: Vector2 = Vector2.ZERO
var _touches: Dictionary = {}
var _touch_start: Dictionary = {}
var _moved: Dictionary = {}
var _last_mouse: Vector2 = Vector2.ZERO
var _mouse_dragging: bool = false
var _mouse_moved: bool = false
var _mouse_start: Vector2 = Vector2.ZERO
var _pinch_start_distance: float = 0.0
var _pinch_start_zoom: float = 1.0
var selected_id: String = "BRA"

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    _load_geojson()
    _load_physical_texture()
    WorldState.country_selected.connect(_on_country_selected)
    resized.connect(_on_resized)
    queue_redraw()

func _on_resized() -> void:
    _clamp_pan()
    queue_redraw()

func _load_physical_texture() -> void:
    if ResourceLoader.exists(TEXTURE_PATH):
        physical_texture = load(TEXTURE_PATH) as Texture2D
    else:
        push_warning("world_texture.jpg ausente; usando fundo procedural.")

func _load_geojson() -> void:
    if not FileAccess.file_exists(GEOJSON_PATH):
        push_warning("world.geojson ausente. Execute godot/tools/prepare_data.py antes de exportar.")
        return
    var raw: String = FileAccess.get_file_as_string(GEOJSON_PATH)
    var parsed: Variant = JSON.parse_string(raw)
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("GeoJSON inválido")
        return
    var parsed_dict: Dictionary = parsed as Dictionary
    features = parsed_dict.get("features", []) as Array
    labels.clear()
    for f_variant: Variant in features:
        var f: Dictionary = f_variant as Dictionary
        var props: Dictionary = f.get("properties", {}) as Dictionary
        var name: String = str(props.get("ADMIN", props.get("name", "País")))
        var iso: String = str(props.get("ADM0_A3", props.get("ISO_A3", "")))
        if iso == "-99" or iso.is_empty():
            iso = name.to_upper().replace(" ", "_")
        f["_presim_id"] = iso
        WorldState.merge_geo_country(iso, name)
        var geom: Dictionary = f.get("geometry", {}) as Dictionary
        var coords: Variant = geom.get("coordinates", [])
        var gtype: String = str(geom.get("type", ""))
        var center_geo: Vector2 = _feature_geo_center(coords, gtype)
        labels.append({
            "id": iso,
            "name": name,
            "geo": center_geo,
            "area_hint": _feature_area_hint(coords, gtype)
        })

func reset_view() -> void:
    zoom = MIN_ZOOM
    pan = Vector2.ZERO
    queue_redraw()

func zoom_by(factor: float, focus: Vector2 = Vector2.ZERO) -> void:
    var old_zoom: float = zoom
    zoom = clampf(zoom * factor, MIN_ZOOM, MAX_ZOOM)
    if focus == Vector2.ZERO:
        focus = size * 0.5
    if not is_equal_approx(old_zoom, zoom):
        pan = focus - (focus - pan) * (zoom / maxf(old_zoom, 0.001))
        _clamp_pan()
        queue_redraw()

func _clamp_pan() -> void:
    if size.x <= 0.0 or size.y <= 0.0:
        return
    if zoom <= MIN_ZOOM + 0.001:
        pan = Vector2.ZERO
        return
    var world_size: Vector2 = size * zoom
    var min_pan: Vector2 = size - world_size
    pan.x = clampf(pan.x, min_pan.x, 0.0)
    pan.y = clampf(pan.y, min_pan.y, 0.0)

func _gui_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        _handle_touch(event as InputEventScreenTouch)
        accept_event()
    elif event is InputEventScreenDrag:
        _handle_drag(event as InputEventScreenDrag)
        accept_event()
    elif event is InputEventMouseButton:
        var mouse_button: InputEventMouseButton = event as InputEventMouseButton
        if mouse_button.button_index == MOUSE_BUTTON_WHEEL_UP and mouse_button.pressed:
            zoom_by(1.18, mouse_button.position)
        elif mouse_button.button_index == MOUSE_BUTTON_WHEEL_DOWN and mouse_button.pressed:
            zoom_by(1.0 / 1.18, mouse_button.position)
        elif mouse_button.button_index == MOUSE_BUTTON_LEFT:
            if mouse_button.pressed:
                _mouse_dragging = true
                _mouse_moved = false
                _mouse_start = mouse_button.position
                _last_mouse = mouse_button.position
            else:
                _mouse_dragging = false
                if not _mouse_moved:
                    _select_at(mouse_button.position)
        accept_event()
    elif event is InputEventMouseMotion and _mouse_dragging:
        var mouse_motion: InputEventMouseMotion = event as InputEventMouseMotion
        if mouse_motion.position.distance_to(_mouse_start) > 8.0:
            _mouse_moved = true
        pan += mouse_motion.position - _last_mouse
        _last_mouse = mouse_motion.position
        _clamp_pan()
        queue_redraw()
        accept_event()

func _handle_touch(event: InputEventScreenTouch) -> void:
    if event.pressed:
        _touches[event.index] = event.position
        _touch_start[event.index] = event.position
        _moved[event.index] = false
        if _touches.size() == 2:
            var pts: Array = _touches.values()
            var p0: Vector2 = pts[0] as Vector2
            var p1: Vector2 = pts[1] as Vector2
            _pinch_start_distance = p0.distance_to(p1)
            _pinch_start_zoom = zoom
            for key: Variant in _moved.keys():
                _moved[key] = true
    else:
        var should_select: bool = not bool(_moved.get(event.index, false)) and _touches.size() == 1
        _touches.erase(event.index)
        _touch_start.erase(event.index)
        _moved.erase(event.index)
        if should_select:
            _select_at(event.position)
        if _touches.size() < 2:
            _pinch_start_distance = 0.0
        _clamp_pan()

func _handle_drag(event: InputEventScreenDrag) -> void:
    _touches[event.index] = event.position
    var start: Vector2 = _touch_start.get(event.index, event.position) as Vector2
    if event.position.distance_to(start) > 8.0:
        _moved[event.index] = true
    if _touches.size() == 1:
        pan += event.relative
        _clamp_pan()
        queue_redraw()
    elif _touches.size() >= 2:
        var pts: Array = _touches.values()
        var p0: Vector2 = pts[0] as Vector2
        var p1: Vector2 = pts[1] as Vector2
        var distance: float = p0.distance_to(p1)
        if _pinch_start_distance <= 0.0:
            _pinch_start_distance = distance
            _pinch_start_zoom = zoom
        var center: Vector2 = (p0 + p1) * 0.5
        var old_zoom: float = zoom
        zoom = clampf(_pinch_start_zoom * distance / maxf(1.0, _pinch_start_distance), MIN_ZOOM, MAX_ZOOM)
        if not is_equal_approx(old_zoom, zoom):
            pan = center - (center - pan) * (zoom / maxf(0.001, old_zoom))
        _clamp_pan()
        queue_redraw()

func _project(coord: Array) -> Vector2:
    var lon: float = float(coord[0])
    var lat: float = float(coord[1])
    var base: Vector2 = Vector2(
        (lon + 180.0) / 360.0 * size.x,
        (90.0 - lat) / 180.0 * size.y
    )
    return base * zoom + pan

func _draw() -> void:
    _draw_world_base()
    _draw_geo_grid()
    if features.is_empty():
        _draw_missing_data()
        return
    for f_variant: Variant in features:
        var f: Dictionary = f_variant as Dictionary
        var id: String = str(f.get("_presim_id", ""))
        var geom: Dictionary = f.get("geometry", {}) as Dictionary
        var gtype: String = str(geom.get("type", ""))
        var coords: Variant = geom.get("coordinates", [])
        var fill: Color = _country_color(id)
        if gtype == "Polygon":
            _draw_polygon_group(coords as Array, fill, id == selected_id)
        elif gtype == "MultiPolygon":
            for poly_variant: Variant in coords as Array:
                _draw_polygon_group(poly_variant as Array, fill, id == selected_id)
    _draw_labels()

func _draw_world_base() -> void:
    if physical_texture != null:
        draw_texture_rect(
            physical_texture,
            Rect2(pan, size * zoom),
            false,
            Color(0.72, 0.80, 0.82, 1.0)
        )
        draw_rect(Rect2(Vector2.ZERO, size), Color(0.015, 0.07, 0.10, 0.20), true)
        return
    _draw_ocean_background()

func _draw_ocean_background() -> void:
    var bands: int = 18
    for i: int in range(bands):
        var t: float = float(i) / float(maxi(1, bands - 1))
        var y: float = size.y * float(i) / float(bands)
        var h: float = size.y / float(bands) + 1.0
        var top: Color = Color(0.018, 0.085, 0.125, 1.0)
        var bottom: Color = Color(0.012, 0.045, 0.075, 1.0)
        var c: Color = top.lerp(bottom, t)
        draw_rect(Rect2(0.0, y, size.x, h), c)
    draw_rect(Rect2(Vector2.ZERO, size), Color(0.02, 0.16, 0.22, 0.16))

func _draw_geo_grid() -> void:
    var grid_color: Color = Color(0.55, 0.78, 0.84, 0.055)
    for lon: int in range(-150, 180, 30):
        var a: Vector2 = _project([float(lon), -90.0])
        var b: Vector2 = _project([float(lon), 90.0])
        draw_line(a, b, grid_color, 1.0)
    for lat: int in range(-60, 90, 30):
        var a: Vector2 = _project([-180.0, float(lat)])
        var b: Vector2 = _project([180.0, float(lat)])
        draw_line(a, b, grid_color, 1.0)

func _draw_polygon_group(rings: Array, fill: Color, selected: bool) -> void:
    if rings.is_empty():
        return
    var outer: PackedVector2Array = PackedVector2Array()
    for c_variant: Variant in rings[0] as Array:
        outer.append(_project(c_variant as Array))
    if outer.size() < 3:
        return
    draw_colored_polygon(outer, fill)
    if selected:
        draw_polyline(outer, Color(0.10, 0.85, 1.0, 0.26), 6.0, true)
        draw_polyline(outer, Color(0.58, 0.97, 1.0, 1.0), 2.2, true)
    else:
        draw_polyline(outer, Color(0.74, 0.83, 0.82, 0.62), 1.0, true)

func _draw_labels() -> void:
    var font: Font = get_theme_default_font()
    var occupied: Array[Rect2] = []
    var ordered: Array = labels.duplicate()
    ordered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return float(a.get("area_hint", 0.0)) > float(b.get("area_hint", 0.0))
    )
    for item_variant: Variant in ordered:
        var item: Dictionary = item_variant as Dictionary
        var geo: Vector2 = item["geo"] as Vector2
        if geo == Vector2.INF:
            continue
        var area_hint: float = float(item["area_hint"])
        var min_zoom: float = _label_min_zoom(area_hint)
        if zoom < min_zoom:
            continue
        var p: Vector2 = _project([geo.x, geo.y])
        if p.x < -100.0 or p.y < -40.0 or p.x > size.x + 100.0 or p.y > size.y + 40.0:
            continue
        var id: String = str(item["id"])
        var name: String = str(item["name"]).to_upper()
        var font_size: int = int(clampf(10.0 + sqrt(zoom) * 2.3, 11.0, 18.0))
        var selected: bool = id == selected_id
        if selected:
            font_size += 2
        var text_size: Vector2 = font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
        var rect: Rect2 = Rect2(p - Vector2(text_size.x * 0.5 + 4.0, text_size.y * 0.5 + 3.0), text_size + Vector2(8.0, 6.0))
        if not selected and _intersects_any(rect, occupied):
            continue
        var color: Color = Color(0.96, 0.98, 0.97, 0.92)
        if selected:
            color = Color(0.64, 0.98, 1.0, 1.0)
            draw_rect(rect, Color(0.02, 0.11, 0.14, 0.76), true)
        draw_string(font, p - Vector2(text_size.x * 0.5, -font_size * 0.35), name, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
        occupied.append(rect)

func _label_min_zoom(area_hint: float) -> float:
    if area_hint >= 130.0:
        return 1.0
    if area_hint >= 50.0:
        return 1.25
    if area_hint >= 22.0:
        return 1.7
    if area_hint >= 10.0:
        return 2.4
    if area_hint >= 4.0:
        return 3.3
    return 4.6

func _intersects_any(rect: Rect2, occupied: Array[Rect2]) -> bool:
    for other: Rect2 in occupied:
        if rect.intersects(other):
            return true
    return false

func _country_color(id: String) -> Color:
    if id == selected_id:
        return Color(0.02, 0.52, 0.64, 0.48)
    var c: Dictionary = WorldState.countries.get(id, {}) as Dictionary
    if bool(c.get("war", false)):
        return Color(0.64, 0.08, 0.08, 0.62)
    if bool(c.get("sanctioned", false)):
        return Color(0.70, 0.39, 0.06, 0.50)
    var stability: float = float(c.get("stability", 55.0))
    var stability_t: float = clampf(stability / 100.0, 0.0, 1.0)
    var hash_value: int = abs(id.hash()) % 100
    var shift: float = float(hash_value) / 100.0
    var cool: Color = Color(0.04, 0.15, 0.16, 0.20)
    var warm: Color = Color(0.15, 0.19, 0.10, 0.22)
    return cool.lerp(warm, 0.25 + shift * 0.45 + stability_t * 0.12)

func _select_at(pos: Vector2) -> void:
    var best_id: String = ""
    var best_distance: float = 99999.0
    for item_variant: Variant in labels:
        var item: Dictionary = item_variant as Dictionary
        var geo: Vector2 = item["geo"] as Vector2
        if geo == Vector2.INF:
            continue
        var center: Vector2 = _project([geo.x, geo.y])
        var distance_to_country: float = center.distance_to(pos)
        if distance_to_country < best_distance:
            best_distance = distance_to_country
            best_id = str(item["id"])
    var threshold: float = clampf(72.0 + 12.0 * minf(zoom, 4.0), 72.0, 120.0)
    if not best_id.is_empty() and best_distance < threshold:
        WorldState.select_country(best_id)
        country_clicked.emit(best_id)

func _feature_geo_center(coords: Variant, gtype: String) -> Vector2:
    var points: Array = []
    var coord_array: Array = coords as Array
    if gtype == "Polygon" and coord_array.size() > 0:
        points = coord_array[0] as Array
    elif gtype == "MultiPolygon" and coord_array.size() > 0:
        var largest: Array = []
        for poly_variant: Variant in coord_array:
            var poly: Array = poly_variant as Array
            if poly.size() > 0:
                var ring: Array = poly[0] as Array
                if ring.size() > largest.size():
                    largest = ring
        points = largest
    if points.is_empty():
        return Vector2.INF
    var sum_lon: float = 0.0
    var sum_lat: float = 0.0
    for c_variant: Variant in points:
        var c: Array = c_variant as Array
        sum_lon += float(c[0])
        sum_lat += float(c[1])
    return Vector2(sum_lon / float(points.size()), sum_lat / float(points.size()))

func _feature_area_hint(coords: Variant, gtype: String) -> float:
    var points: Array = []
    var coord_array: Array = coords as Array
    if gtype == "Polygon" and coord_array.size() > 0:
        points = coord_array[0] as Array
    elif gtype == "MultiPolygon" and coord_array.size() > 0:
        var best_ring: Array = []
        for poly_variant: Variant in coord_array:
            var poly: Array = poly_variant as Array
            if poly.size() > 0:
                var ring: Array = poly[0] as Array
                if ring.size() > best_ring.size():
                    best_ring = ring
        points = best_ring
    if points.is_empty():
        return 0.0
    var min_lon: float = 999.0
    var max_lon: float = -999.0
    var min_lat: float = 999.0
    var max_lat: float = -999.0
    for c_variant: Variant in points:
        var c: Array = c_variant as Array
        min_lon = minf(min_lon, float(c[0]))
        max_lon = maxf(max_lon, float(c[0]))
        min_lat = minf(min_lat, float(c[1]))
        max_lat = maxf(max_lat, float(c[1]))
    return absf(max_lon - min_lon) * absf(max_lat - min_lat)

func _on_country_selected(id: String) -> void:
    selected_id = id
    queue_redraw()

func _draw_missing_data() -> void:
    draw_string(get_theme_default_font(), Vector2(50, 90), "MAPA GEOJSON NÃO PREPARADO", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, Color.WHITE)
    draw_string(get_theme_default_font(), Vector2(50, 130), "Execute: python godot/tools/prepare_data.py", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.6, 0.75, 0.85))
