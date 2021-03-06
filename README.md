# chess_image_dataset
Scripts to produce chess board image datasets for classification experiments

## Version Information

The script and blender files were tested using Blender 2.78c and
Python 3.6.2. Earlier versions should work as well.

## Variations


## Usage

It seems that blender has some problems if new objects are constantly
created and removed and new images are rendered. (i.e it becomes much
slower over time). Since I was not able to solve this I hacked up a
temporary fix by writing an additional python script that repeatetly
calls blender to render a smaller batch of images. A batch size of 50
to 100 usually works well.

The base image path is hard coded in the script `run_chess_single.py`
so you should change it.

Example usage
~~~~
./run_chess_single.py --start 0 --stop 30000 --batchsize 100 --diff 1 5 10
~~~~

This will produce 30000 images per class in batches of 100 (blender
will be restarted after every batch) for the given problem and for 1,
5, and 10 out of place pawns. So 180000 images will be produces all in
all.

## Changing Resolution
If images of a different resolution are needed, the `.blend` file can
be opened and appropriate changes to the render settings can be made.

It is also easy to change the color and shape of the pawn, different
lighting etc. if you are familiar with Blender.
