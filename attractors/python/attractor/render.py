#!/usr/bin/python3

import logging
import random
import math
import colorsys
import random
import numpy
import cv2
from . import palettes

defaultParameters = {
    'downsampleRatio': 1,
    'bpc' : 8,
    'dimension' : 2,
    'geometry' : (800, 600),
    'paletteIndex': None
}

class Renderer(object):
    def __init__(self, **kwargs):
        getParam = lambda k: kwargs[k] if kwargs and k in kwargs else defaultParameters[k]

        self.INTERNAL_BPC    = 16
        self.fullRange       = (1<<self.INTERNAL_BPC)-1
        self.logger          = logging.getLogger(__name__)
        self.downsampleRatio = getParam('downsampleRatio')
        self.bpc             = getParam('bpc')
        self.dimension       = getParam('dimension')
        self.geometry        = getParam('geometry')
        self.paletteIndex    = getParam('paletteIndex')
        self.geometry        = [x*self.downsampleRatio for x in self.geometry]
        if self.dimension < 2 or self.dimension > 3:
            self.logger.warning("Trying to create renderer with invalid dimension (" + self.dimension + "). Defaulting to 2.")
            self.dimension = 2
        if self.paletteIndex == None:
            self.paletteIndex = random.choice(range(len(palettes.pal_templates)))

    def getGradientSlice(self, s, n, in_space='hsv', out_space='hsv'):
        ns  = round(n*s['slice_percent']/100)
        inc = [(x-y)/ns for (x, y) in zip(s['end_color'], s['start_color'])]
        gs = list()

        for i in range(ns):
            cur_color = [ x+i*y for (x,y) in zip(s['start_color'], inc) ]
            if in_space == out_space:
                out_color = cur_color
            elif out_space == 'rgb':
                out_color = colorsys.hsv_to_rgb(*cur_color)
            else:
                out_color = colorsys.rgb_to_hsv(*cur_color)
            gs.append(tuple(out_color))
        return gs

    def getGradient(self, m, n, in_space='hsv', out_space='hsv'):
        g = list()
        for s in m:
            g += self.getGradientSlice(s, n, in_space, out_space)
        return g

    def getPalette(self, frequencies):
        self.logger.debug("Choosing palette %d (%s)" % (self.paletteIndex, palettes.pal_templates[self.paletteIndex]['name']))
        template = palettes.pal_templates[self.paletteIndex]
        gradient = self.getGradient(template['gradient_map'], len(frequencies), template['colorspace'])
        while len(gradient) < len(frequencies):
            gradient.append(gradient[-1])

        colormap = dict()
        for i, freq in enumerate(sorted(frequencies)):
            v = freq/self.fullRange
            if template['invert_value']: v = 1.0-v
            v = template['value_offset'] + v*(1-template['value_offset'])
            (r, g, b) = colorsys.hsv_to_rgb(gradient[i][0], gradient[i][1], v)
            colormap[freq] = tuple([round(x*((1<<self.bpc)-1)) for x in (b, g, r)])

        self.palette = dict()
        self.palette['background'] = tuple([round(component * ((1 << self.bpc)-1)) for component in template['background']])
        self.palette['colormap']   = colormap

    def colorizeAttractor(self, p):
        self.getPalette(list(set(p.values())))

        for c, v in p.items():
            p[c] = self.palette['colormap'][v]

        self.logger.debug("Number of unique colors in the attractor after colorization: %d." % (len(set(p.values()))))

    # Creates the final image array
    def createImageArray(self, p):
        (w, h) = self.geometry[0:2]

        img = [ [ list(self.palette['background']) for col in range(0, w) ] for row in range(0,h) ]
        for c, v in p.items():
            (col, row) = c
            try:
                img[row][col] = list(v)
            except IndexError as e:
                # This can occur if the bounds were not correctly assessed
                # and a point of the attractor happens to fall out of them.
                self.logger.debug("Looks like a point fell out of our bounds. Ignoring it.")
        return img

    # Performs histogram equalization on the attractor pixels
    def equalizeAttractor(self, p):
        pools = [0]*(1<<self.INTERNAL_BPC)

        # Create cumulative distribution
        for v in p.values():
            pools[v] += 1
        for i in range(len(pools) - 1):
            pools[i+1] += pools[i]

        # Stretch the values to the [1, (1<<INTERNAL_BPC)-1] range
        for i, v in enumerate(pools):
            pools[i] = 1 + (self.fullRange - 1)*(pools[i]-pools[0])/(pools[-1]-pools[0])

        # Now reapply the stretched values
        for k in p:
            p[k] = round(pools[p[k]])

    # Render the attractor
    # attractor: attractor points: dict (X,Y) and containing :
    # - frequency for 2D
    # - Z for 3D
    #
    # 1- Perform histogram equalization on the attractor frequency
    # 2- Colorize the attractor (map frequency to color gradient)
    # 3- if needed downsize the attractor
    def renderAttractor(self, a):
        if not a: return None
        M = max(a.values())

        self.logger.debug("Number of frequencies in attractor: %d" % (len(set(a.values()))))
        # Now send the map in the [0, (1<<self.INTERNAL_BPC)-1] range
        for i, pt in a.items():
            a[i] = int (pt*self.fullRange/M)

        self.equalizeAttractor(a)
        self.colorizeAttractor(a)
        img = numpy.asarray(self.createImageArray(a)).astype(numpy.uint8)
        img = cv2.resize(img, tuple([int(v/self.downsampleRatio) for v in self.geometry[0:2]]), interpolation=cv2.INTER_CUBIC)
        self.logger.debug("Number of colors in attractor after downsampling: %d." % (len(set([ tuple(color) for row in img for color in row]))))

        return img

    def isNice(self, a, coverLimit=0.01):
        """
        Checks if the attractor passed is 'nice': currently nice means that the
        attractor covers more than coverLimit percent of the window.
        """
        if not a: return False
        nPoints = len(a)
        sSize   = self.geometry[0]*self.geometry[1]
        coverRatio = float(nPoints)/sSize
        self.logger.debug("Attractor cover ratio is %.2f%% (limit is %.2f%%)" % (100.0*coverRatio, 100.0*coverLimit))
        if coverRatio < coverLimit:
            return False

        return True

