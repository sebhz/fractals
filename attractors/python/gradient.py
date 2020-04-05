#!/usr/bin/python3

import numpy as np
from matplotlib import pyplot as plt
from attractor import palettes
import colorsys
import random

# Colors are specified in the s array in RGB888
def getGradientSlice(s, n, grad_type='hsv_cw', out_space='hsv'):
    grad_space = grad_type[0:3]
    grad_dir   = grad_type[4:6]

    rgb_norm = lambda x: (((x>>16)&0xFF)/0xFF, ((x>>8)&0xFF)/0xFF, ((x>>0)&0xFF)/0xFF,)
    (start_color, end_color) = map(rgb_norm, (s['start_color'], s['end_color']))
    ns  = round(n*s['slice_percent']/100)
    if grad_space == 'hsv':
        (start_color, end_color) = (colorsys.rgb_to_hsv(*start_color), colorsys.rgb_to_hsv(*end_color))
        inc = [(x-y)/ns for (x, y) in zip(end_color, start_color)]
        # HSV gradients hue can go clockwise (red towards green) or counterclockwise (red towards blue)
        delta_hue = end_color[0]-start_color[0]
        if (delta_hue > 0 and grad_dir == 'cc'): inc[0] = (1-delta_hue)/ns
        if (delta_hue < 0 and grad_dir == 'cw'): inc[0] = (1+delta_hue)/ns
    else:
        inc = [(x-y)/ns for (x, y) in zip(end_color, start_color)]

    gs = list()

    for i in range(ns):
        cur_color = [ x+i*y for (x,y) in zip(start_color, inc) ]
        if grad_space == out_space:
            out_color = cur_color
        elif out_space == 'rgb':
            out_color = colorsys.hsv_to_rgb(*cur_color)
        else:
            out_color = colorsys.rgb_to_hsv(*cur_color)
        gs.append(tuple(out_color))
    return gs

def getGradient(m, n, grad_type='hsv_cw', out_space='hsv'):
    g = list()
    for s in m:
        g += getGradientSlice(s, n, grad_type, out_space)
    return g

def mapValueGradient(hsv_gradient, nc, offset, invert):
    for i, v in enumerate(hsv_gradient):
        l = list(v)
        l[2] = offset + (1.0-offset)*i/nc
        print(l[2])
        if invert: l[2] = 1.0-l[2]
        hsv_gradient[i] = tuple(l)

nc = 768
for i, template in enumerate(palettes.pal_templates):
    hsv_gradient = getGradient(template['gradient_map'], nc, template['colorspace'], 'hsv')
    mapValueGradient(hsv_gradient, nc, template['value_offset'], template['invert_value'])
    rgb_gradient = [ tuple([ round(255*component) for component in colorsys.hsv_to_rgb(*color)]) for color in hsv_gradient ]

    img_array = [rgb_gradient]*128
    print("Palette %d (%s)" % (i, template['name']))
    plt.imshow(np.asarray(img_array).astype(np.uint8))
    plt.show()
