#!/usr/bin/python

import logging
import random
import math
import colorsys
import random
import numpy
import cv2

defaultParameters = {
    'downsampleRatio': 1,
    'bpc' : 8,
    'dimension' : 2,
    'geometry' : (800, 600),
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
        self.geometry        = [x*self.downsampleRatio for x in self.geometry]
        if self.dimension < 2 or self.dimension > 3:
            self.logger.warning("Trying to create renderer with invalid dimension (" + self.dimension + "). Defaulting to 2.")
            self.dimension = 2

    # TODO: put palette and gradients in their own module
    def getGradient(self, controlColors, n, reverse=False, space="hsv"):
        grad = list()
        l = len(controlColors)
        nInSlice = int(n/(l-1))
        for i, color in enumerate(controlColors):
            if i == l-1: break
            startColor = color
            endColor = controlColors[i+1]
            add = [(x-y)/nInSlice for (x, y) in zip(endColor, startColor)]
            for s in range(0, nInSlice):
                color = [x+s*y for (x,y) in zip(startColor, add)]
                if space == "hsv":
                    hsv_color = color
                else:
                    hsv_color = colorsys.rgb_to_hsv(*color)
                grad.append(tuple(hsv_color))
        if reverse:
            grad=list(reversed(grad))
        return grad

    def getRandomPalette(self, frequencies):
        templates = (( [ (0.0, 1.0, 0.9), (1/3, 0.5, 1.0) ], (0, 0, 0), False, "hsv" ),     # From red to green
                     ( [ (2/3, 1.0, 1.0), (1.0, 0.4, 1.0) ], (0, 0, 0), False, "hsv" ),     # From blue to red
                     ( [ (0.0, 0.0, 1.0), (0.0, 0.0, 1.0) ], (0, 0, 0), False, "hsv" ),     # Pure white (will become greyscale)
                     ( [ (0.0, 0.0, 1.0), (0.0, 0.0, 1.0) ], (1, 1, 1), True,  "hsv" ),     # Pure black (will become greyscale)
                     ( [ (0.38, 0.0, 0.88), (0.94, 1.0, 0.13) ], (0, 0, 0), False, "rgb" ), # From blue to yellow
                     ( [ (0.4, 1.0, 0.5), (0.0, 0.5, 1.0) ], (0, 0, 0), False, "hsv" ),     # From green to red
                    )
        template = random.choice(templates)
        #template = templates[-1]
        gradient = self.getGradient(template[0], len(frequencies), space=template[3])
        while len(gradient) < len(frequencies):
            gradient.append(gradient[-1])

        colormap = dict()
        for i, freq in enumerate(sorted(frequencies)):
            colormap[freq] = gradient[i]

        palette = dict()
        palette['colormap']   = colormap
        palette['background'] = template[1]
        palette['negative']   = template[2]

        return palette

    def colorize_pixel(self, pixel):
        # We extract the current pixel HSV to reuse the Value component.
        (h, s, v) = colorsys.rgb_to_hsv(pixel/self.fullRange, pixel/self.fullRange, pixel/self.fullRange)
        if self.palette['negative']: v = 1.0-v
        (r, g, b) = colorsys.hsv_to_rgb(self.palette['colormap'][pixel][0], self.palette['colormap'][pixel][1], v)
        return tuple([round(x*((1 << self.bpc)-1)) for x in (b, g, r)])

    def colorizeAttractor(self, p):
        frequencies  = list(set(p.values()))
        self.palette = self.getRandomPalette(frequencies)
        self.palette['background'] = tuple([round(component * ((1 << self.bpc)-1)) for component in self.palette['background']])

        for c, v in p.items():
            p[c] = self.colorize_pixel(v)

        self.logger.debug("Number of unique colors in the attractor after colorization: %d." % (len(list(set(p.values())))))

    # Creates the final image array
    def createImageArray(self, p):
        (w, h) = self.geometry[0:2]

        img = [ [list(self.palette['background']) for col in range(0, w) ] for row in range(0,h) ]
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
            pools[i] = 1+(self.fullRange-1)*(pools[i]-pools[0])/(pools[-1]-pools[0])

        # Now reapply the stretched values
        for k in p:
            p[k] = pools[p[k]]

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

        self.logger.debug("Number of frequencies in attractor: %d" % (len(list(set(a.values())))))
        # Now send the map in the [0, (1<<self.INTERNAL_BPC)-1] range
        for i, pt in a.items():
            a[i] = int (pt*self.fullRange/M)

        self.equalizeAttractor(a)
        self.colorizeAttractor(a)
        img = numpy.asarray(self.createImageArray(a)).astype(numpy.uint8)
        img = cv2.resize(img, tuple([int(v/self.downsampleRatio) for v in self.geometry[0:2]]), interpolation=cv2.INTER_CUBIC)

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

