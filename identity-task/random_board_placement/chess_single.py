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
    parser.add_argument('-r', '--rotate', action='store_true',
                        default=False, help="randomly rotate camera")
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


def relativemove(obj, x, y, z=0):
    ox, oy, oz = obj.location
    obj.location = (ox + x, oy + y, oz + z)


def move(object, x, y, z=0):
    object.location = (x, y, z)


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


def apply_config(config, xoffset=0, yoffset=0):
    for x in range(len(config[0])):
        for y in range(len(config)):
            if config[y][x] == 1:
                put_pawn(x + xoffset, y + yoffset)
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


board_right = bpy.data.objects['board_right']
board_left = bpy.data.objects['board_left']


def reset_board_right():
    board_right.location = (4, 0, -0.25)


# return !(right(a) < left(b) ||
    # right(b) < left(a) ||
    # bottom(a)< top(b) ||
    # bottom(b)< top(a))


def isoverlapping(x1, y1, width1, height1, x2, y2, width2, height2):
    "True if the two rects are overlapping"
    right1 = x1 + width1
    right2 = x2 + width2
    bottom1 = y1 + height1
    bottom2 = y2 + height2
    return not((right1 < x2) or (right2 < x2) or (bottom1 < y2) or (bottom2 < y1))


def getnonoverlappingpos(x, y, width, height, rectwidth, rectheight):
    x1 = random.uniform(x, x + width - rectwidth)
    y1 = random.uniform(y, y + height - rectheight)
    x2 = x1 - 1
    y2 = y1 - 1
    while isoverlapping(x1, y1, rectwidth, rectheight, x2, y2, rectwidth, rectheight):
        x1 = random.uniform(x, x + width - rectwidth)
        y1 = random.uniform(y, y + height - rectheight)
    return x1, y1, x2, y2


args = get_args()
initial_remove_pawn_copies()

viewx = viewy = -12
viewwidth = viewheight = 2 * 12
boardwidth = boardheight = 8


with open("/data/chessboard_data/similarity/labels.txt", "w") as f:
    for i in range(args.start, args.stop):
        d = args.diff

        # Make mirrored image
        x1, y1, x2, y2 = getnonoverlappingpos(
            viewx, viewy, viewwidth, viewheight, boardwidth, boardheight)
        move(board_left, x1 + boardwidth / 2 - 0.5, y1 + boardwidth / 2 - 0.5)
        move(board_right, x2 + boardwidth / 2 - 0.5, y2 + boardwidth / 2 - 0.5)
        remove_pawn_copies()
        conf = create_random_config()
        apply_config(conf, xoffset=x1, yoffset=y1)
        apply_config(conf, xoffset=x2, yoffset=y2)
        filename = "single_chess_mirror_" + str(i).zfill(5) + ".jpg"
        render_to_file(
            "/data/chessboard_data/similarity/random_board_images_big_diff" + str(d) + "/" + filename)
        f.write(filename + " 0\n")

        # Make non-mirrored config
        x1, y1, x2, y2 = getnonoverlappingpos(
            viewx, viewy, viewwidth, viewheight, boardwidth, boardheight)
        move(board_left, x1 + boardwidth / 2 - 0.5, y1 + boardwidth / 2 - 0.5)
        move(board_right, x2 + boardwidth / 2 - 0.5, y2 + boardwidth / 2 - 0.5)
        remove_pawn_copies()
        conf = create_random_config()
        apply_config(conf, xoffset=x1, yoffset=y1)
        apply_config(flip_pawns(conf, d), xoffset=x2, yoffset=y2)
        filename = "single_chess_nomirror_" + str(i).zfill(5) + ".jpg"
        f.write(filename + " 1\n")
        render_to_file(
            "/data/chessboard_data/similarity/random_board_images_big_diff" + str(d) + "/" + filename)
        f.flush()
