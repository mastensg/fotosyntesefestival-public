import ctypes
import os
import struct
import sys

import pygame

def log2(n):
    for i in range(32):
        if 2 ** i >= n:
            return i

def make_animation(prefix):
    vma_path = "%s.vma" % prefix

    paths = ["graphics/" + s for s in sorted(filter(lambda x: x.startswith(prefix + "_"), os.listdir("graphics")))]

    if paths == []:
        sys.stderr.write("no images matching %s/%s* found\n" % ("graphics", prefix))
        sys.exit(1)

    vma_mtime = os.path.getmtime(vma_path) if os.path.exists(vma_path) else 0

    update = False
    for path in paths:
        if os.path.getmtime(path) > vma_mtime:
            update = True

    if not update:
        return

    images = []
    for path in paths:
        print(path)
        images.append(pygame.image.load(path))

    frames = len(images)

    w, h = images[0].get_rect()[2:4]

    f = open(vma_path, "wb")

    f.write(struct.pack("B", frames))
    f.write(struct.pack(">H", w))
    f.write(struct.pack(">H", h))

    for i in range(len(images)):
        img = images[i]

        if img.get_rect() != images[0].get_rect():
            sys.stderr.write("different image sizes: %s (%dx%d) differs from %s (%dx%d)\n" %
                    (paths[i], img.get_rect()[2], img.get_rect()[3], paths[0], w, h))
            sys.exit(1)

        f.write(pygame.image.tostring(img, "RGBA"))

    f.close()

[make_animation(f) for f in [
"ballz",
"bg",
"char",
"co2",
"credits",
"fire",
"fireS",
"highscore",
"house",
"houseS",
"intro",
"start",
"subtitle",
"sun",
"titleS",
"wat",
"wood"
]]
