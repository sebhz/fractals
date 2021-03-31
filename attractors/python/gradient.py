#!/usr/bin/python3
""" Simple program to test color gradients.
    Uses the palettes module of the attractors
"""
import colorsys
import numpy as np
from matplotlib import pyplot as plt
from attractor import palettes


def map_gradient(hsv_g, num_c, offset, invert):
    """
    Maps a gradient to a number of colors (by stretching the
    value component, applying an offset and possibly inverting)
    """
    for index, components in enumerate(hsv_g):
        cmp_l = list(components)
        cmp_l[2] = offset + (1.0 - offset) * index / num_c
        if invert:
            cmp_l[2] = 1.0 - cmp_l[2]
        hsv_g[index] = tuple(cmp_l)


NUM_COLORS = 768
for i, template in enumerate(palettes.pal_templates):
    hsv_gradient = palettes.getGradient(
        template["gradient_map"], NUM_COLORS, template["colorspace"], "hsv"
    )
    map_gradient(
        hsv_gradient, NUM_COLORS, template["value_offset"], template["invert_value"]
    )
    rgb_gradient = [
        tuple([round(255 * component) for component in colorsys.hsv_to_rgb(*color)])
        for color in hsv_gradient
    ]

    img_array = [rgb_gradient] * 128
    print("Palette %d (%s)" % (i, template["name"]))

    fig = plt.figure()
    fig.patch.set_facecolor("#%06x" % (template["background"]))
    plt.imshow(np.asarray(img_array).astype(np.uint8))
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.show()
