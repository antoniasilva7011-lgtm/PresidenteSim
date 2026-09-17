extends Control

var t: float = 0.0

func _ready() -> void:
    custom_minimum_size = Vector2(300, 300)
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    set_process(true)
    queue_redraw()

func _process(delta: float) -> void:
    t += delta
    queue_redraw()

func _draw() -> void:
    var w := size.x
    var h := size.y
    if w <= 0.0 or h <= 0.0:
        return

    # Newsroom background
    draw_rect(Rect2(Vector2.ZERO, size), Color(0.018, 0.075, 0.10, 1.0), true)
    draw_rect(Rect2(Vector2(0, h * 0.68), Vector2(w, h * 0.32)), Color(0.012, 0.035, 0.055, 1.0), true)
    for i in range(5):
        var x := 18.0 + float(i) * (w - 36.0) / 4.0
        draw_line(Vector2(x, 18), Vector2(x, h * 0.64), Color(0.12, 0.62, 0.72, 0.16), 1.0)
    draw_line(Vector2(0, h * 0.64), Vector2(w, h * 0.64), Color(0.30, 0.92, 1.0, 0.42), 2.0)

    # Desk
    var desk_y := h * 0.73
    draw_colored_polygon(PackedVector2Array([
        Vector2(w * 0.12, desk_y), Vector2(w * 0.88, desk_y),
        Vector2(w * 0.78, h * 0.92), Vector2(w * 0.22, h * 0.92)
    ]), Color(0.045, 0.105, 0.13, 1.0))
    draw_line(Vector2(w * 0.16, desk_y), Vector2(w * 0.84, desk_y), Color(0.34, 0.90, 1.0, 0.8), 2.0)

    # Presenter body
    var cx := w * 0.5
    var head_y := h * 0.34
    var head_r := minf(w, h) * 0.105
    var shoulder_y := h * 0.55
    draw_colored_polygon(PackedVector2Array([
        Vector2(cx - w * 0.18, h * 0.70),
        Vector2(cx - w * 0.13, shoulder_y),
        Vector2(cx, h * 0.48),
        Vector2(cx + w * 0.13, shoulder_y),
        Vector2(cx + w * 0.18, h * 0.70)
    ]), Color(0.08, 0.18, 0.28, 1.0))
    draw_colored_polygon(PackedVector2Array([
        Vector2(cx - w * 0.055, h * 0.49),
        Vector2(cx, h * 0.60),
        Vector2(cx + w * 0.055, h * 0.49)
    ]), Color(0.88, 0.92, 0.95, 1.0))

    # Hair + face
    draw_circle(Vector2(cx, head_y - head_r * 0.12), head_r * 1.05, Color(0.08, 0.055, 0.045, 1.0))
    draw_circle(Vector2(cx, head_y), head_r, Color(0.82, 0.61, 0.48, 1.0))
    draw_colored_polygon(PackedVector2Array([
        Vector2(cx - head_r * 0.95, head_y - head_r * 0.35),
        Vector2(cx - head_r * 0.55, head_y - head_r * 1.02),
        Vector2(cx + head_r * 0.80, head_y - head_r * 0.92),
        Vector2(cx + head_r * 1.02, head_y - head_r * 0.18),
        Vector2(cx + head_r * 0.42, head_y - head_r * 0.48),
        Vector2(cx - head_r * 0.25, head_y - head_r * 0.36)
    ]), Color(0.07, 0.045, 0.04, 1.0))

    # Eyes blink every ~3.6 seconds
    var blink_phase := fmod(t, 3.6)
    var blink := blink_phase > 3.42
    var eye_y := head_y - head_r * 0.05
    var eye_dx := head_r * 0.36
    if blink:
        draw_line(Vector2(cx - eye_dx - 7, eye_y), Vector2(cx - eye_dx + 7, eye_y), Color(0.10, 0.07, 0.06), 2.0)
        draw_line(Vector2(cx + eye_dx - 7, eye_y), Vector2(cx + eye_dx + 7, eye_y), Color(0.10, 0.07, 0.06), 2.0)
    else:
        draw_circle(Vector2(cx - eye_dx, eye_y), 3.4, Color(0.08, 0.06, 0.05, 1.0))
        draw_circle(Vector2(cx + eye_dx, eye_y), 3.4, Color(0.08, 0.06, 0.05, 1.0))

    # Nose and animated mouth = speaking effect
    draw_line(Vector2(cx, head_y + head_r * 0.02), Vector2(cx - 2, head_y + head_r * 0.24), Color(0.46, 0.28, 0.22, 0.75), 1.5)
    var mouth_open := 2.5 + absf(sin(t * 7.0)) * 6.0
    draw_rect(Rect2(Vector2(cx - head_r * 0.28, head_y + head_r * 0.46), Vector2(head_r * 0.56, mouth_open)), Color(0.36, 0.08, 0.09, 1.0), true)

    # Earpiece / mic
    draw_circle(Vector2(cx + head_r * 0.98, head_y + head_r * 0.12), 3.0, Color(0.25, 0.90, 1.0, 0.9))
    draw_line(Vector2(cx + head_r * 0.98, head_y + head_r * 0.12), Vector2(cx + head_r * 0.76, head_y + head_r * 0.48), Color(0.25, 0.90, 1.0, 0.7), 1.5)

    # Studio bug
    var font := get_theme_default_font()
    draw_string(font, Vector2(16, 28), "PRESIDENTE NEWS", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.65, 0.96, 1.0))
    draw_circle(Vector2(w - 64, 23), 4.0, Color(1.0, 0.22, 0.18))
    draw_string(font, Vector2(w - 54, 28), "AO VIVO", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1.0, 0.72, 0.70))
