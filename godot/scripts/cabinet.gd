extends Node3D

signal hotspot_pressed(action: String)

func _ready() -> void:
    _build_room()

func _build_room() -> void:
    var env := WorldEnvironment.new()
    var e := Environment.new()
    e.background_mode = Environment.BG_COLOR
    e.background_color = Color("071019")
    e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    e.ambient_light_color = Color(0.72, 0.78, 0.88)
    e.ambient_light_energy = 0.75
    env.environment = e
    add_child(env)

    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-48, -28, 0)
    light.light_energy = 1.4
    add_child(light)

    var camera := Camera3D.new()
    camera.position = Vector3(0, 3.2, 8.8)
    camera.rotation_degrees = Vector3(-12, 0, 0)
    camera.current = true
    add_child(camera)

    _mesh_box("Floor", Vector3(0, -0.1, 0), Vector3(11, 0.2, 7), Color("1a2228"))
    _mesh_box("BackWall", Vector3(0, 3.0, -3.5), Vector3(11, 6, 0.2), Color("202a32"))
    _mesh_box("Desk", Vector3(0, 1.0, 0.6), Vector3(5.4, 0.45, 2.1), Color("4a2f1d"))
    _mesh_box("DeskFront", Vector3(0, 0.55, 0.95), Vector3(4.7, 0.9, 0.18), Color("382316"))
    _mesh_box("TV", Vector3(0, 3.65, -3.32), Vector3(3.8, 2.0, 0.12), Color("071b2a"))
    _mesh_box("LawFolders", Vector3(0.4, 1.38, 0.3), Vector3(1.2, 0.16, 0.85), Color("123c76"))
    _mesh_box("CrisisPhone", Vector3(-1.75, 1.42, 0.25), Vector3(0.72, 0.22, 0.48), Color("8a1717"))
    _mesh_sphere("Globe", Vector3(2.0, 1.85, 0.05), 0.58, Color("166f8f"))

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
    mat.metallic = 0.1
    mat.roughness = 0.6
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
    mi.mesh = sphere
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.2
    mat.roughness = 0.35
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
