#!/usr/bin/python3

import numpy as np
import colorsys
from matplotlib import pyplot as plt
from attractor import palettes

def mapValueGradient(hsv_gradient, nc, offset, invert):
    for i, v in enumerate(hsv_gradient):
        l = list(v)
        l[2] = offset + (1.0-offset)*i/nc
        if invert: l[2] = 1.0-l[2]
        hsv_gradient[i] = tuple(l)

nc = 768
for i, template in enumerate(palettes.pal_templates):
    hsv_gradient = palettes.getGradient(template['gradient_map'], nc, template['colorspace'], 'hsv')
    mapValueGradient(hsv_gradient, nc, template['value_offset'], template['invert_value'])
    rgb_gradient = [ tuple([ round(255*component) for component in colorsys.hsv_to_rgb(*color)]) for color in hsv_gradient ]

    img_array = [rgb_gradient]*128
    print("Palette %d (%s)" % (i, template['name']))

    fig = plt.figure()
    fig.patch.set_facecolor("#%06x" % (template['background']))
    plt.imshow(np.asarray(img_array).astype(np.uint8))
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.show()
