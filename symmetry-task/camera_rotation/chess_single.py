import random
import argparse

import bpy
from math import cos, pi, sin


width = height = 8
left_board_center = (-5, 0, -0.25)

# Contains object that should be unlinked from the scene. Not really
# sure if this is helping but I experienced quite a few slowdowns when
# rendering a lot of images and I tried to get rid of as much data as
# possible per iterations
unlinkcache = []


def get_args():
    parser = argparse.ArgumentParser()

    # get all script args
    _, all_arguments = parser.parse_known_args()
    double_dash_index = all_arguments.index('--')
    script_args = all_arguments[double_dash_index + 1:]

    # add parser rules
    parser.add_argument('-d', '--diff', type=int, help="number differences")
    parser.add_argument('-a', '--start', type=int, help="starting image")
    parser.add_argument('-b', '--stop', type=int, help="stopping image")
    parser.add_argument('-r', '--rotate', action='store_true', default=False, help="randomly rotate camera")
    parsed_script_args, _ = parser.parse_known_args(script_args)
    return parsed_script_args


def blender_garbage_collect():
    """Tries to remove as much not used data as possible in an attempt to
reduce the slowdown over time"""
    for datablock in bpy.data.objects:
        if datablock.users == 0:
            bpy.data.objects.remove(datablock)
    for datablock in bpy.data.meshes:
        if datablock.users == 0:
            bpy.data.meshes.remove(datablock)


def copy_pawn(pawn=bpy.data.objects['pawn']):
    """Copies the pawn object and returns the object"""
    global unlinkcache
    pwn_copy = bpy.data.objects.new("Pawncopy", pawn.data)
    pwn_copy.rotation_euler = pawn.rotation_euler
    # pwn_copy.location = pawn.location
    pwn_copy.scale = pawn.scale
    bpy.context.scene.objects.link(pwn_copy)
    unlinkcache.append(pwn_copy)
    return pwn_copy


def initial_remove_pawn_copies():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern="pawncopy*")
    bpy.ops.object.delete()


def remove_pawn_copies():
    global unlinkcache
    for obj in unlinkcache:
        obj.select = True
    bpy.ops.object.delete()
    unlinkcache = []
    # Do some manual garbage collection
    blender_garbage_collect()


def move(object, x, y):
    global_x = -8.5 + x
    global_y = 3.5 - y
    object.location = (global_x, global_y, 0)


def put_pawn(x, y):
    """Put copy of pawn at certain position on board"""
    pwncpy = copy_pawn()
    move(pwncpy, x, y)


def create_random_config():
    return [[random.randint(0, 1) for x in range(width)] for y in range(height)]


def mirror_config(cfg):
    "Mirrors the config around the x axis"
    res = [[None] * width for x in range(height)]
    # copy left side
    for x in range(width // 2):
        for y in range(height):
            res[y][x] = cfg[y][x]
    # copy right side mirrored
    for x in range(width // 2):
        for y in range(height):
            res[y][-(x + 1)] = cfg[y][x]
    return res


def flip_pawns(config, number):
    from copy import copy
    res = copy(config)
    flipped = [(-1, -1)]

    for i in range(number):
        x = y = -1
        while (x, y) in flipped:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

        res[y][x] = 0 if res[y][x] == 1 else 1

        if (x, y) not in flipped:
            flipped += [(x, y), (width - x - 1, y)]
    return res


def apply_config(config):
    for x in range(len(config[0])):
        for y in range(len(config)):
            if config[y][x] == 1:
                put_pawn(x, y)
    bpy.context.scene.update()


def render_to_file(filepath):
    """Renders current scene to a file"""
    bpy.data.scenes['Scene'].render.filepath = filepath
    bpy.ops.render.render(write_still=True, use_viewport=False)


def position_camera(x, y, z):
    "Positions the camera to x,y,z"
    cam = bpy.data.objects["Camera"]
    cam.location = (x, y, z)


def position_camera_on_sphere(x, y, z, r, thetaxy, thetayz):
    """Positions camera on a sphere with radius r around center x,y,z with
positions thetaxy and thetayz. Theta is in radians"""
    px = x + r * cos(thetaxy) * sin(thetayz)
    py = y + r * sin(thetaxy) * sin(thetayz)
    pz = z + r * cos(thetayz)
    position_camera(px, py, pz)

args = get_args()
initial_remove_pawn_copies()

with open("/data/chessboard_data/symmetry/labels.txt", "w") as f:
    for i in range(args.start, args.stop):
        d = args.diff
        # Make mirrored image
        remove_pawn_copies()
        conf = mirror_config(create_random_config())
        apply_config(conf)
        filename = "single_chess_mirror_" + str(i).zfill(5) + ".jpg"
        if args.rotate:
            position_camera_on_sphere(*left_board_center, r=random.uniform(12,20),
                                      thetaxy=random.uniform(0, 2 * pi),
                                      thetayz=random.uniform(pi / 6, pi / 3))
        render_to_file(
            "/data/chessboard_data/symmetry/rot_images_diff" + str(d) + "/" + filename)
        f.write(filename + " 0\n")
        # Make non-mirrored config
        remove_pawn_copies()
        conf = mirror_config(create_random_config())
        apply_config(flip_pawns(conf, d))
        filename = "single_chess_nomirror_" + str(i).zfill(5) + ".jpg"
        f.write(filename + " 1\n")
        if args.rotate:
            position_camera_on_sphere(*left_board_center, r=random.uniform(12,20),
                                      thetaxy=random.uniform(0, 2 * pi),
                                      thetayz=random.uniform(pi / 6, pi / 3))
        render_to_file(
            "/data/chessboard_data/symmetry/rot_images_diff" + str(d) + "/" + filename)
        f.flush()
