extends Node3D

signal hotspot_pressed(action: String)

func _ready() -> void:
    _build_room()

func _build_room() -> void:
    var env := WorldEnvironment.new()
    var e := Environment.new()
    e.background_mode = Environment.BG_COLOR
    e.background_color = Color("050a10")
    e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    e.ambient_light_color = Color(0.58, 0.70, 0.82)
    e.ambient_light_energy = 0.72
    e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    env.environment = e
    add_child(env)

    var key := DirectionalLight3D.new()
    key.rotation_degrees = Vector3(-48, -28, 0)
    key.light_energy = 1.55
    key.light_color = Color(0.88, 0.94, 1.0)
    add_child(key)

    var fill := OmniLight3D.new()
    fill.position = Vector3(0, 4.2, 1.5)
    fill.omni_range = 10.0
    fill.light_energy = 1.2
    fill.light_color = Color(0.35, 0.70, 0.90)
    add_child(fill)

    var warm := OmniLight3D.new()
    warm.position = Vector3(-3.8, 2.5, 0.0)
    warm.omni_range = 5.0
    warm.light_energy = 0.75
    warm.light_color = Color(1.0, 0.62, 0.32)
    add_child(warm)

    var camera := Camera3D.new()
    camera.position = Vector3(0, 3.4, 9.4)
    camera.rotation_degrees = Vector3(-11, 0, 0)
    camera.fov = 58.0
    camera.current = true
    add_child(camera)

    _mesh_box("Floor", Vector3(0, -0.1, 0), Vector3(12, 0.2, 7.5), Color("121920"))
    _mesh_box("BackWall", Vector3(0, 3.2, -3.7), Vector3(12, 6.4, 0.2), Color("18232b"))
    _mesh_box("LeftWall", Vector3(-6.0, 3.0, 0), Vector3(0.2, 6.0, 7.5), Color("111b23"))
    _mesh_box("RightWall", Vector3(6.0, 3.0, 0), Vector3(0.2, 6.0, 7.5), Color("111b23"))

    _mesh_box("Desk", Vector3(0, 1.0, 0.9), Vector3(6.2, 0.42, 2.2), Color("4d311f"))
    _mesh_box("DeskFront", Vector3(0, 0.55, 1.05), Vector3(5.5, 0.95, 0.20), Color("302014"))
    _mesh_box("DeskLight", Vector3(0, 1.17, -0.1), Vector3(4.8, 0.05, 0.08), Color("1f9fb8"))

    _mesh_box("TVFrame", Vector3(0, 3.65, -3.48), Vector3(4.7, 2.5, 0.12), Color("0a0e13"))
    _mesh_box("TV", Vector3(0, 3.65, -3.40), Vector3(4.35, 2.16, 0.08), Color("082f46"))
    _mesh_box("NewsStrip", Vector3(0, 2.95, -3.32), Vector3(3.6, 0.18, 0.05), Color("9a251e"))

    _mesh_box("LawFolders", Vector3(0.55, 1.36, 0.52), Vector3(1.35, 0.14, 0.90), Color("174d89"))
    _mesh_box("FolderGold", Vector3(0.55, 1.46, 0.52), Vector3(1.10, 0.03, 0.62), Color("c39a3b"))
    _mesh_box("CrisisPhone", Vector3(-2.0, 1.42, 0.42), Vector3(0.82, 0.24, 0.52), Color("8e1f20"))
    _mesh_sphere("Globe", Vector3(2.25, 1.90, 0.18), 0.62, Color("17779a"))

    _mesh_box("SituationDeskLeft", Vector3(-4.1, 1.0, -1.7), Vector3(2.6, 0.30, 1.25), Color("242d34"))
    _mesh_box("SituationDeskRight", Vector3(4.1, 1.0, -1.7), Vector3(2.6, 0.30, 1.25), Color("242d34"))
    _mesh_box("MonitorLeft", Vector3(-4.1, 1.85, -2.25), Vector3(1.8, 1.0, 0.08), Color("0b4052"))
    _mesh_box("MonitorRight", Vector3(4.1, 1.85, -2.25), Vector3(1.8, 1.0, 0.08), Color("0b4052"))

    _mesh_box("FlagLeft", Vector3(-5.0, 3.0, -3.45), Vector3(0.85, 2.5, 0.08), Color("12643e"))
    _mesh_box("FlagRight", Vector3(5.0, 3.0, -3.45), Vector3(0.85, 2.5, 0.08), Color("214e87"))

func _mesh_box(name_: String, pos: Vector3, size_: Vector3, color: Color) -> void:
    var body := StaticBody3D.new()
    body.name = name_
    body.position = pos
    var mesh_instance := MeshInstance3D.new()
    var box := BoxMesh.new()
    box.size = size_
    mesh_instance.mesh = box
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.12
    mat.roughness = 0.48
    if name_ in ["TV", "DeskLight", "NewsStrip", "MonitorLeft", "MonitorRight"]:
        mat.emission_enabled = true
        mat.emission = color * 0.85
        mat.emission_energy_multiplier = 1.1
    mesh_instance.material_override = mat
    body.add_child(mesh_instance)
    if name_ in ["CrisisPhone", "LawFolders", "Globe", "TV"]:
        var shape := CollisionShape3D.new()
        var box_shape := BoxShape3D.new()
        box_shape.size = size_
        shape.shape = box_shape
        body.add_child(shape)
        body.input_ray_pickable = true
        body.input_event.connect(_on_hotspot_input.bind(name_))
    add_child(body)

func _mesh_sphere(name_: String, pos: Vector3, radius: float, color: Color) -> void:
    var body := StaticBody3D.new()
    body.name = name_
    body.position = pos
    var mi := MeshInstance3D.new()
    var sphere := SphereMesh.new()
    sphere.radius = radius
    sphere.height = radius * 2.0
    sphere.radial_segments = 40
    sphere.rings = 20
    mi.mesh = sphere
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.18
    mat.roughness = 0.30
    mi.material_override = mat
    body.add_child(mi)
    var shape := CollisionShape3D.new()
    var sphere_shape := SphereShape3D.new()
    sphere_shape.radius = radius
    shape.shape = sphere_shape
    body.add_child(shape)
    body.input_ray_pickable = true
    body.input_event.connect(_on_hotspot_input.bind(name_))
    add_child(body)

func _on_hotspot_input(_camera, event: InputEvent, _position, _normal, _shape_idx, action: String) -> void:
    if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        hotspot_pressed.emit(action)
    elif event is InputEventScreenTouch and event.pressed:
        hotspot_pressed.emit(action)
