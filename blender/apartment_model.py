"""Build a provisional, editable apartment shell from the supplied plan."""

import bpy
import math


COLLECTION_NAME = "Apartment Model - Provisional"
AREA_TARGET_M2 = 53.0
WALL_HEIGHT_M = 2.40
EXTERIOR_WALL_M = 0.12
INTERIOR_WALL_M = 0.10

# These traced image coordinates preserve the plan's topology only; the drawing
# explicitly says it is not to scale.
LEFT, RIGHT = 142.0, 1641.0
TOP, STEP_Y, STEP_X, BOTTOM = 169.0, 790.0, 807.0, 1030.0
PLAN_OUTLINE = [
    (LEFT, TOP),
    (RIGHT, TOP),
    (RIGHT, STEP_Y),
    (STEP_X, STEP_Y),
    (STEP_X, BOTTOM),
    (LEFT, BOTTOM),
]


def polygon_area(points):
    return abs(
        sum(
            points[i][0] * points[(i + 1) % len(points)][1]
            - points[(i + 1) % len(points)][0] * points[i][1]
            for i in range(len(points))
        )
    ) * 0.5


def get_interior_area(scale):
    inset = EXTERIOR_WALL_M / 2.0
    right = (RIGHT - LEFT) * scale
    step_x = (STEP_X - LEFT) * scale
    step_y = (BOTTOM - STEP_Y) * scale
    top = (BOTTOM - TOP) * scale
    inner = [
        (inset, inset),
        (step_x - inset, inset),
        (step_x - inset, step_y + inset),
        (right - inset, step_y + inset),
        (right - inset, top - inset),
        (inset, top - inset),
    ]
    return polygon_area(inner)


low, high = 0.001, 0.02
for _ in range(80):
    scale = (low + high) * 0.5
    if get_interior_area(scale) < AREA_TARGET_M2:
        low = scale
    else:
        high = scale
PIXEL_TO_M = (low + high) * 0.5


def px_to_x(px):
    return (px - LEFT) * PIXEL_TO_M


def px_to_y(py):
    return (BOTTOM - py) * PIXEL_TO_M


def make_material(name, color, roughness=0.82):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.roughness = roughness
    return material


def link_mesh(name, vertices, faces, material, collection):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def add_box(name, location, dimensions, material, collection):
    dx, dy, dz = dimensions
    x, y, z = location
    vertices = [
        (x - dx / 2, y - dy / 2, z - dz / 2),
        (x + dx / 2, y - dy / 2, z - dz / 2),
        (x + dx / 2, y + dy / 2, z - dz / 2),
        (x - dx / 2, y + dy / 2, z - dz / 2),
        (x - dx / 2, y - dy / 2, z + dz / 2),
        (x + dx / 2, y - dy / 2, z + dz / 2),
        (x + dx / 2, y + dy / 2, z + dz / 2),
        (x - dx / 2, y + dy / 2, z + dz / 2),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return link_mesh(name, vertices, faces, material, collection)


def add_floor(name, x0, x1, y0, y1, material, collection):
    return add_box(
        name,
        ((x0 + x1) / 2, (y0 + y1) / 2, -0.04),
        (x1 - x0, y1 - y0, 0.08),
        material,
        collection,
    )


def add_wall_piece(axis, a, b, fixed, thickness, z0, z1, material, name, collection):
    if b <= a or z1 <= z0:
        return
    if axis == "H":
        x0, x1 = px_to_x(a), px_to_x(b)
        location = ((x0 + x1) / 2, px_to_y(fixed), (z0 + z1) / 2)
        dimensions = (x1 - x0, thickness, z1 - z0)
    else:
        y0, y1 = px_to_y(a), px_to_y(b)
        location = (px_to_x(fixed), (y0 + y1) / 2, (z0 + z1) / 2)
        dimensions = (thickness, y0 - y1, z1 - z0)
    add_box(name, location, dimensions, material, collection)


def add_window(axis, a, b, fixed, thickness, sill, head, frame, glass, name, collection):
    trim = 0.04
    inset_px = trim / (2.0 * PIXEL_TO_M)
    if axis == "H":
        middle_x = (px_to_x(a) + px_to_x(b)) / 2
        location = (middle_x, px_to_y(fixed), (sill + head) / 2)
        dimensions = (px_to_x(b) - px_to_x(a) - trim, 0.018, head - sill - trim)
    else:
        middle_y = (px_to_y(a) + px_to_y(b)) / 2
        location = (px_to_x(fixed), middle_y, (sill + head) / 2)
        dimensions = (0.018, px_to_y(a) - px_to_y(b) - trim, head - sill - trim)
    add_box(name + " Glass", location, dimensions, glass, collection)
    add_wall_piece(axis, a, a + inset_px, fixed, thickness, sill, head, frame, name + " Jamb A", collection)
    add_wall_piece(axis, b - inset_px, b, fixed, thickness, sill, head, frame, name + " Jamb B", collection)
    add_wall_piece(axis, a, b, fixed, thickness, sill - trim / 2, sill + trim / 2, frame, name + " Sill", collection)
    add_wall_piece(axis, a, b, fixed, thickness, head - trim / 2, head + trim / 2, frame, name + " Head", collection)


def add_wall(axis, start, end, fixed, thickness, name, collection, wall_material, frame_material, glass_material, openings=()):
    cursor = start
    for opening_start, opening_end, opening_type in sorted(openings):
        add_wall_piece(
            axis,
            cursor,
            opening_start,
            fixed,
            thickness,
            0.0,
            WALL_HEIGHT_M,
            wall_material,
            name + " Wall",
            collection,
        )
        if opening_type == "window":
            sill, head = 0.78, 2.02
            add_wall_piece(axis, opening_start, opening_end, fixed, thickness, 0.0, sill, wall_material, name + " Window Sill Wall", collection)
            add_wall_piece(axis, opening_start, opening_end, fixed, thickness, head, WALL_HEIGHT_M, wall_material, name + " Window Header Wall", collection)
            add_window(axis, opening_start, opening_end, fixed, thickness, sill, head, frame_material, glass_material, name + " Window", collection)
        else:
            add_wall_piece(axis, opening_start, opening_end, fixed, thickness, 2.02, WALL_HEIGHT_M, wall_material, name + " Door Header", collection)
        cursor = opening_end
    add_wall_piece(
        axis,
        cursor,
        end,
        fixed,
        thickness,
        0.0,
        WALL_HEIGHT_M,
        wall_material,
        name + " Wall",
        collection,
    )


def add_text(name, body, location, size, material, collection):
    curve = bpy.data.curves.new(name + " Text", "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    curve.materials.append(material)
    collection.objects.link(obj)
    return obj


scene = bpy.context.scene
old_collection = bpy.data.collections.get(COLLECTION_NAME)


def remove_collection_tree(collection):
    for child in list(collection.children):
        remove_collection_tree(child)
    for old_obj in list(collection.objects):
        bpy.data.objects.remove(old_obj, do_unlink=True)
    bpy.data.collections.remove(collection)


if old_collection:
    remove_collection_tree(old_collection)

root = bpy.data.collections.new(COLLECTION_NAME)
scene.collection.children.link(root)
collections = {}
for name in ("Floors", "Shell", "Windows", "Built-ins", "Fixtures", "Room Labels"):
    child = bpy.data.collections.new(name)
    root.children.link(child)
    collections[name] = child

floor_mat = make_material("Apartment - warm light floor", (0.54, 0.50, 0.42, 1.0))
wall_mat = make_material("Apartment - warm white walls", (0.84, 0.82, 0.76, 1.0))
frame_mat = make_material("Apartment - window frames", (0.16, 0.20, 0.22, 1.0))
glass_mat = make_material("Apartment - provisional glazing", (0.24, 0.52, 0.66, 1.0), 0.25)
wood_mat = make_material("Apartment - built-in wood", (0.47, 0.32, 0.20, 1.0))
fixture_mat = make_material("Apartment - fixture blockouts", (0.88, 0.89, 0.86, 1.0))
appliance_mat = make_material("Apartment - appliance blockouts", (0.48, 0.53, 0.56, 1.0))
label_mat = make_material("Apartment - room labels", (0.10, 0.10, 0.09, 1.0))
metal_mat = make_material("Apartment - kitchen stainless", (0.62, 0.65, 0.66, 1.0), 0.35)
cooktop_mat = make_material("Apartment - cooktop glass", (0.08, 0.09, 0.10, 1.0), 0.28)

half_wall = EXTERIOR_WALL_M / 2
right_x = px_to_x(RIGHT)
notch_x = px_to_x(STEP_X)
step_y = px_to_y(STEP_Y)
top_y = px_to_y(TOP)
bottom_y = px_to_y(BOTTOM)
left_inside = half_wall
right_inside = right_x - half_wall
notch_inside = notch_x - half_wall
top_inside = top_y - half_wall
step_inside = step_y + half_wall
bottom_inside = half_wall

add_floor("Main apartment floor", left_inside, right_inside, step_inside, top_inside, floor_mat, collections["Floors"])
add_floor("Kitchen and entry floor", left_inside, notch_inside, bottom_inside, step_inside, floor_mat, collections["Floors"])

# Exterior walls: window and entrance dimensions are provisional interpretations
# of the drawn symbols, not verified construction measurements.
add_wall("H", LEFT, RIGHT, TOP, EXTERIOR_WALL_M, "North facade", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", TOP, STEP_Y, RIGHT, EXTERIOR_WALL_M, "East facade", collections["Shell"], wall_mat, frame_mat, glass_mat, [(289, 664, "window")])
add_wall("H", STEP_X, RIGHT, STEP_Y, EXTERIOR_WALL_M, "Living room facade", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", STEP_Y, BOTTOM, STEP_X, EXTERIOR_WALL_M, "Entry return", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", LEFT, STEP_X, BOTTOM, EXTERIOR_WALL_M, "Entrance facade", collections["Shell"], wall_mat, frame_mat, glass_mat, [(662, 778, "door")])
add_wall("V", TOP, BOTTOM, LEFT, EXTERIOR_WALL_M, "West facade", collections["Shell"], wall_mat, frame_mat, glass_mat, [(347, 539, "window"), (768, 956, "window")])

# Internal partitions and open passage locations follow the plan's visible breaks.
add_wall("V", 199, 622, 747, INTERIOR_WALL_M, "Bedroom bathroom partition", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", 199, 622, 937, INTERIOR_WALL_M, "Bathroom living partition", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", 170, 747, 622, INTERIOR_WALL_M, "Bedroom hall partition", collections["Shell"], wall_mat, frame_mat, glass_mat, [(654, 724, "door")])
add_wall("H", 747, 805, 622, INTERIOR_WALL_M, "Bathroom threshold west", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", 907, 937, 622, INTERIOR_WALL_M, "Bathroom threshold east", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", 170, 497, 637, INTERIOR_WALL_M, "Kitchen north return", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", 637, 725, 497, INTERIOR_WALL_M, "Kitchen hall return", collections["Shell"], wall_mat, frame_mat, glass_mat)

# Bedroom built-in storage marked G in the drawing; each unit remains separate.
for index, (a, b) in enumerate(((199, 285), (286, 366), (367, 439), (440, 526)), start=1):
    x0, x1 = px_to_x(674), px_to_x(747)
    y0, y1 = px_to_y(b), px_to_y(a)
    add_box(
        "Bedroom built-in G" + str(index),
        ((x0 + x1) / 2, (y0 + y1) / 2, 1.08),
        (x1 - x0, y1 - y0, 2.16),
        wood_mat,
        collections["Built-ins"],
    )

x0, x1 = px_to_x(550), px_to_x(630)
y0, y1 = px_to_y(721), px_to_y(638)
add_box("Hall built-in G", ((x0 + x1) / 2, (y0 + y1) / 2, 1.05), (x1 - x0, y1 - y0, 2.10), wood_mat, collections["Built-ins"])

# Wall-connected kitchen run follows the plan's north kitchen wall; photos guide fixture layout.
kitchen_wall_face = px_to_y(637) - INTERIOR_WALL_M / 2
kitchen_x0, kitchen_x1 = px_to_x(170), px_to_x(497)
counter_depth = 0.58
counter_front = kitchen_wall_face - counter_depth
kitchen_center_x = (kitchen_x0 + kitchen_x1) / 2
counter_center_y = (kitchen_wall_face + counter_front) / 2
add_box(
    "Kitchen fitted base cabinets",
    (kitchen_center_x, counter_center_y, 0.42),
    (kitchen_x1 - kitchen_x0, counter_depth, 0.84),
    wall_mat,
    collections["Built-ins"],
)
add_box(
    "Kitchen fitted countertop",
    (kitchen_center_x, kitchen_wall_face - (counter_depth + 0.04) / 2, 0.87),
    (kitchen_x1 - kitchen_x0 + 0.04, counter_depth + 0.04, 0.06),
    wood_mat,
    collections["Built-ins"],
)
add_box(
    "Kitchen tiled backsplash",
    (kitchen_center_x, kitchen_wall_face - 0.012, 1.22),
    (kitchen_x1 - kitchen_x0, 0.024, 0.64),
    wall_mat,
    collections["Built-ins"],
)

upper_depth = 0.34
upper_y = kitchen_wall_face - upper_depth / 2
for index, (a, b) in enumerate(((170, 250), (250, 330), (330, 412), (412, 497)), start=1):
    x0, x1 = px_to_x(a), px_to_x(b)
    add_box(
        "Kitchen wall cabinet " + str(index),
        ((x0 + x1) / 2, upper_y, 1.94),
        (x1 - x0 - 0.015, upper_depth, 0.72),
        wall_mat,
        collections["Built-ins"],
    )

# Inset sink and tap, positioned on the counter's west/left half.
sink_center_x = px_to_x(299)
add_box("Kitchen sink rim", (sink_center_x, counter_center_y, 0.914), (0.52, 0.40, 0.025), metal_mat, collections["Fixtures"])
add_box("Kitchen sink basin", (sink_center_x, counter_center_y, 0.918), (0.39, 0.28, 0.018), cooktop_mat, collections["Fixtures"])
add_box("Kitchen sink tap stem", (sink_center_x, kitchen_wall_face - 0.065, 0.99), (0.035, 0.035, 0.15), metal_mat, collections["Fixtures"])
add_box("Kitchen sink tap spout", (sink_center_x, kitchen_wall_face - 0.15, 1.055), (0.035, 0.17, 0.035), metal_mat, collections["Fixtures"])

# Built-in oven and hob share a cabinet bay; no freestanding dining furniture is added.
oven_center_x = px_to_x(367)
oven_width = 0.58
add_box("Kitchen built-in oven", (oven_center_x, counter_center_y, 0.40), (oven_width, counter_depth - 0.04, 0.64), appliance_mat, collections["Built-ins"])
add_box("Kitchen oven front", (oven_center_x, counter_front - 0.012, 0.41), (oven_width - 0.04, 0.024, 0.58), cooktop_mat, collections["Built-ins"])
add_box("Kitchen oven window", (oven_center_x, counter_front - 0.027, 0.36), (oven_width - 0.16, 0.012, 0.26), frame_mat, collections["Built-ins"])
add_box("Kitchen oven handle", (oven_center_x, counter_front - 0.035, 0.66), (oven_width - 0.12, 0.035, 0.035), metal_mat, collections["Built-ins"])
add_box("Kitchen cooktop", (oven_center_x, counter_center_y, 0.914), (0.58, 0.48, 0.022), cooktop_mat, collections["Fixtures"])


def add_burner(name, center, radius, material, collection, segments=24):
    vertices = [
        (center[0] + radius * math.cos(2 * math.pi * i / segments),
         center[1] + radius * math.sin(2 * math.pi * i / segments),
         center[2])
        for i in range(segments)
    ]
    return link_mesh(name, vertices, [tuple(range(segments))], material, collection)


for index, (dx, dy) in enumerate(((-0.15, -0.12), (0.15, -0.12), (-0.15, 0.12), (0.15, 0.12)), start=1):
    add_burner("Kitchen hob burner " + str(index), (oven_center_x + dx, counter_center_y + dy, 0.928), 0.055, metal_mat, collections["Fixtures"])

# K and F in the drawing identify separate tall kyl (fridge) and frys (freezer) units.
fridge_back_y = px_to_y(BOTTOM) + EXTERIOR_WALL_M / 2
fridge_depth = 0.62
for label, a, b, name in (("K", 484, 557, "Kyl - refrigerator"), ("F", 557, 630, "Frys - freezer")):
    x0, x1 = px_to_x(a), px_to_x(b)
    width = x1 - x0 - 0.02
    center_x = (x0 + x1) / 2
    center_y = fridge_back_y + fridge_depth / 2
    material = appliance_mat if label == "K" else metal_mat
    add_box(name, (center_x, center_y, 0.92), (width, fridge_depth, 1.84), material, collections["Fixtures"])
    add_box(name + " door", (center_x, fridge_back_y + fridge_depth - 0.012, 0.92), (width - 0.035, 0.024, 1.78), wall_mat, collections["Fixtures"])
    handle_x = x1 - 0.06 if label == "K" else x0 + 0.06
    add_box(name + " handle", (handle_x, fridge_back_y + fridge_depth + 0.005, 0.98), (0.025, 0.035, 0.62), frame_mat, collections["Fixtures"])
    add_text("Kitchen marker " + label, label, (center_x, center_y, 1.85), 0.20, label_mat, collections["Room Labels"])

def add_ellipsoid(name, location, dimensions, material, collection, segments=24, rings=12):
    x, y, z = location
    rx, ry, rz = (dimension / 2 for dimension in dimensions)
    vertices = []
    for ring in range(rings + 1):
        latitude = -math.pi / 2 + math.pi * ring / rings
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            vertices.append(
                (
                    x + rx * math.cos(latitude) * math.cos(angle),
                    y + ry * math.cos(latitude) * math.sin(angle),
                    z + rz * math.sin(latitude),
                )
            )
    faces = []
    for ring in range(rings):
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    ring * segments + segment,
                    ring * segments + next_segment,
                    (ring + 1) * segments + next_segment,
                    (ring + 1) * segments + segment,
                )
            )
    return link_mesh(name, vertices, faces, material, collection)


def add_oval_surface(name, center, radii, z, material, collection, segments=32):
    vertices = [
        (center[0] + radii[0] * math.cos(2 * math.pi * i / segments),
         center[1] + radii[1] * math.sin(2 * math.pi * i / segments),
         z)
        for i in range(segments)
    ]
    return link_mesh(name, vertices, [tuple(range(segments))], material, collection)


def add_oval_ring(name, center, outer_radii, inner_radii, z, material, collection, segments=32):
    vertices = []
    for radii in (outer_radii, inner_radii):
        vertices.extend(
            (center[0] + radii[0] * math.cos(2 * math.pi * i / segments),
             center[1] + radii[1] * math.sin(2 * math.pi * i / segments),
             z)
            for i in range(segments)
        )
    faces = [
        (i, (i + 1) % segments, segments + (i + 1) % segments, segments + i)
        for i in range(segments)
    ]
    return link_mesh(name, vertices, faces, material, collection)


def add_shower_sector(center_px, center_py, radius_x_px, radius_y_px):
    cx, cy = px_to_x(center_px), px_to_y(center_py)
    radius_x = px_to_x(center_px + radius_x_px) - cx
    radius_y = cy - px_to_y(center_py + radius_y_px)
    segments = 24
    arc = [
        (
            cx + radius_x * math.cos(math.pi * i / (2 * segments)),
            cy - radius_y * math.sin(math.pi * i / (2 * segments)),
        )
        for i in range(segments + 1)
    ]
    vertices = [(cx, cy, 0.015)] + [(x, y, 0.015) for x, y in arc]
    faces = [(0, i + 1, i + 2) for i in range(segments)]
    link_mesh("Bathroom curved shower tray", vertices, faces, fixture_mat, collections["Fixtures"])

    thickness = 0.022
    inset_x, inset_y = thickness, thickness
    angles = [math.pi * i / (2 * segments) for i in range(segments + 1)]
    vertices = []
    for angle in angles:
        for rx, ry, z in (
            (radius_x, radius_y, 0.02),
            (radius_x, radius_y, 1.95),
            (radius_x - inset_x, radius_y - inset_y, 0.02),
            (radius_x - inset_x, radius_y - inset_y, 1.95),
        ):
            vertices.append((cx + rx * math.cos(angle), cy - ry * math.sin(angle), z))
    faces = []
    for i in range(segments):
        a, b = 4 * i, 4 * (i + 1)
        faces.extend(
            (
                (a, b, b + 1, a + 1),
                (a + 2, a + 3, b + 3, b + 2),
                (a + 1, b + 1, b + 3, a + 3),
                (a + 2, b + 2, b, a),
            )
        )
    faces.extend(((0, 1, 3, 2), (4 * segments, 4 * segments + 2, 4 * segments + 3, 4 * segments + 1)))
    link_mesh("Bathroom curved shower screen", vertices, faces, glass_mat, collections["Fixtures"])


# The plan fixes the positions; the photo informs the fixture forms and facing.
# Align each fixture's back edge to the modeled interior wall face.
bath_west_face = px_to_x(747) + INTERIOR_WALL_M / 2
bath_east_face = px_to_x(937) - INTERIOR_WALL_M / 2
bath_north_face = px_to_y(TOP) - EXTERIOR_WALL_M / 2
bath_west_pixel = LEFT + bath_west_face / PIXEL_TO_M
bath_north_pixel = BOTTOM - bath_north_face / PIXEL_TO_M
add_shower_sector(bath_west_pixel, bath_north_pixel, 110, 114)

# Vanity and vessel basin on the left wall, between the shower and toilet.
sink_x0 = bath_west_face
sink_x1 = sink_x0 + px_to_x(826) - px_to_x(779)
sink_y0, sink_y1 = px_to_y(473), px_to_y(402)
sink_center = ((sink_x0 + sink_x1) / 2, (sink_y0 + sink_y1) / 2)
add_box("Bathroom vanity cabinet", (sink_center[0], sink_center[1], 0.37), (sink_x1 - sink_x0, sink_y1 - sink_y0, 0.74), wall_mat, collections["Fixtures"])
add_box("Bathroom vanity countertop", (sink_center[0] + 0.03, sink_center[1], 0.77), (sink_x1 - sink_x0 + 0.06, sink_y1 - sink_y0 + 0.06, 0.06), fixture_mat, collections["Fixtures"])
add_ellipsoid("Bathroom vessel basin", (sink_center[0], sink_center[1], 0.88), (0.30, 0.40, 0.12), fixture_mat, collections["Fixtures"])
add_oval_surface("Bathroom basin interior", sink_center, (0.105, 0.15), 0.934, glass_mat, collections["Fixtures"])
add_box("Bathroom basin tap", (sink_x0 + 0.045, sink_center[1], 0.95), (0.045, 0.045, 0.08), frame_mat, collections["Fixtures"])

# The toilet faces into the room from the west wall, close to the entry.
toilet_x0 = bath_west_face
toilet_x1 = toilet_x0 + px_to_x(856) - px_to_x(773)
toilet_y0, toilet_y1 = px_to_y(581), px_to_y(532)
toilet_center = ((toilet_x0 + toilet_x1) / 2, (toilet_y0 + toilet_y1) / 2)
cistern_x0 = bath_west_face
cistern_x1 = cistern_x0 + px_to_x(798) - px_to_x(773)
cistern_y0, cistern_y1 = px_to_y(566), px_to_y(532)
add_box(
    "Bathroom toilet cistern",
    ((cistern_x0 + cistern_x1) / 2, (cistern_y0 + cistern_y1) / 2, 0.39),
    (cistern_x1 - cistern_x0, cistern_y1 - cistern_y0, 0.78),
    fixture_mat,
    collections["Fixtures"],
)
toilet_bowl_width = px_to_x(856) - px_to_x(795)
toilet_bowl_center = (cistern_x1 + toilet_bowl_width / 2 - 0.02, toilet_center[1])
add_ellipsoid("Bathroom toilet bowl", (toilet_bowl_center[0], toilet_bowl_center[1], 0.24), (toilet_bowl_width, 0.31, 0.40), fixture_mat, collections["Fixtures"])
add_oval_ring("Bathroom toilet seat", toilet_bowl_center, (0.205, 0.145), (0.125, 0.078), 0.445, fixture_mat, collections["Fixtures"])
add_oval_surface("Bathroom toilet opening", toilet_bowl_center, (0.122, 0.075), 0.446, glass_mat, collections["Fixtures"])

# Washer follows the TM symbol on the right wall, with its control/front toward the entry.
washer_x1 = bath_east_face
washer_x0 = washer_x1 - px_to_x(936) + px_to_x(875)
washer_y0, washer_y1 = px_to_y(325), px_to_y(228)
washer_center = ((washer_x0 + washer_x1) / 2, (washer_y0 + washer_y1) / 2)
add_box("Bathroom washing machine TM", (washer_center[0], washer_center[1], 0.43), (washer_x1 - washer_x0, washer_y1 - washer_y0, 0.86), fixture_mat, collections["Fixtures"])
washer_top_width = washer_x1 - washer_x0 - 0.03
add_box("Bathroom washer top", (washer_x1 - washer_top_width / 2, washer_center[1], 0.875), (washer_top_width, washer_y1 - washer_y0 - 0.03, 0.03), wall_mat, collections["Fixtures"])
add_box("Bathroom washer control panel", (washer_center[0], washer_y1 - 0.055, 0.89), (washer_x1 - washer_x0 - 0.06, 0.07, 0.018), appliance_mat, collections["Fixtures"])

# Room-name labels make the top-down layout easy to read; they can be hidden or edited.
for name, label, px, py in (
    ("Bedroom label", "SOVRUM", 420, 420),
    ("Bathroom label", "BADRUM", 867, 495),
    ("Living room label", "VARDAGSRUM", 1280, 480),
    ("Kitchen label", "KÖK", 330, 850),
    ("Hall label", "HALL", 715, 790),
):
    add_text(name, label, (px_to_x(px), px_to_y(py), 0.012), 0.32, label_mat, collections["Room Labels"])

# Remove only the untouched default cube; keep the user's camera and light.
default_cube = bpy.data.objects.get("Cube")
if default_cube and default_cube.type == "MESH":
    bpy.data.objects.remove(default_cube, do_unlink=True)

scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene["apartment_floor_area_target_m2"] = AREA_TARGET_M2
scene["apartment_floor_area_basis"] = "53 m2 clear floor area; scaled from the non-scale drawing outline"
scene["apartment_wall_height_m"] = WALL_HEIGHT_M
scene["apartment_assumptions"] = (
    "Provisional visualization only. The plan is explicitly not to scale. "
    "Only 53 m2 apartment area and 2.40 m height were supplied. "
    "Wall thicknesses, exterior dimensions, opening widths/heights, window levels, "
    "fixture sizes, and room proportions are estimates; verify before construction."
)
scene["apartment_fixture_reference"] = (
    "Bathroom fixture positions follow the floor-plan symbols. A supplementary bathroom photo "
    "informed the curved shower screen, vanity basin, toilet form, and washer orientation; "
    "fixtures are aligned flush to modeled interior wall faces. The photo is not a measured source."
)
scene["apartment_kitchen_reference"] = (
    "Kitchen photos inform the wall-connected counter, sink, oven/hob, and cabinets. K/F in the "
    "floor plan are modeled as separate refrigerator and freezer appliances against the south wall. "
    "No dining table or other freestanding furniture is included; dimensions are provisional."
)
scene["apartment_scale_m_per_plan_pixel"] = PIXEL_TO_M
scene["apartment_outer_outline_area_estimate_m2"] = polygon_area(
    [((x - LEFT) * PIXEL_TO_M, (BOTTOM - y) * PIXEL_TO_M) for x, y in PLAN_OUTLINE]
)

# Configure a useful plan view and camera while retaining existing scene objects.
center_x = right_x / 2
center_y = (top_y + bottom_y) / 2
camera = scene.camera
if camera is None:
    camera_data = bpy.data.cameras.new("Apartment Plan Camera")
    camera = bpy.data.objects.new("Apartment Plan Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
camera.location = (center_x, center_y, 13.0)
camera.rotation_euler = (0.0, 0.0, 0.0)
camera.data.type = "ORTHO"
camera.data.ortho_scale = right_x * 1.15
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100

light = bpy.data.objects.get("Light")
if light and light.type == "LIGHT":
    light.data.type = "AREA"
    light.data.energy = 1800
    light.data.shape = "DISK"
    light.data.size = 9.0
    light.location = (center_x, center_y, 8.0)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            region = area.spaces.active.region_3d
            region.view_perspective = "ORTHO"
            region.view_location = (center_x, center_y, 1.1)
            region.view_distance = right_x * 1.38
            region.view_rotation = (1.0, 0.0, 0.0, 0.0)
            area.spaces.active.shading.color_type = "MATERIAL"
            area.spaces.active.overlay.show_extras = False
            area.spaces.active.overlay.show_cursor = False

print(
    "Apartment model built:",
    round(get_interior_area(PIXEL_TO_M), 2),
    "m2 clear floor target;",
    round(scene["apartment_outer_outline_area_estimate_m2"], 2),
    "m2 outer outline estimate;",
    round(PIXEL_TO_M, 6),
    "m per reference pixel.",
)
