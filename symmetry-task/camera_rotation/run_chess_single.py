#! /usr/bin/env python3

import argparse
import sys
import subprocess
import os


def get_args():
    parser = argparse.ArgumentParser()
    # add parser rules
    parser.add_argument('-d', '--diff', type=int, nargs="+",
                        help="number differences")
    parser.add_argument('-a', '--start', type=int, help="starting image")
    parser.add_argument('-b', '--stop', type=int, help="stopping image")
    parser.add_argument('-s', '--batchsize', type=int,
                        help="batch size sent to blender")
    parsed_script_args, _ = parser.parse_known_args()
    return parsed_script_args

args = get_args()

# Run Blender in a loop working on a patch of images. This was needed
# since Blender slows down after generating a few hundred images and I
# have no idea why it is doing this.

batches = list(range(args.start, args.stop, args.batchsize))
if batches[-1] != args.stop:
    batches.append(args.stop)
# pairs of start and stop indices for each iteration
borders = list(zip(batches[:-1], batches[1:]))


blender = "blender "
basecommand = "-b /data/Dropbox/17_18_ws/iccv_workshop/ChessGen/chessboard_single.blend -P /data/Dropbox/17_18_ws/iccv_workshop/ChessGen/chess_single.py -- "
baseimgdir = "/data/chessboard_data/symmetry/"

for diff in args.diff:
    # Check if dir exists, otherwise create
    checkdir = "{}/rot_images_diff{}".format(baseimgdir, diff)
    if not os.path.isdir(checkdir):
        print("Generating directory {}".format(checkdir))
        os.makedirs(checkdir)
    # Generate images
    for start, stop in borders:
        parameters = "--diff {} --start {} --stop {} --rotate".format(diff, start, stop)
        subprocess.call(blender + basecommand + parameters, shell=True)
