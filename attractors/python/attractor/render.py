#!/usr/bin/python3

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
    'paletteIndex': None
}

class Renderer(object):
    # Gradient template, colorspace, Bg color (BGR), negative, value offset
    pal_templates = (# From red to green/yellow
                     ( [ (0, 0.0, 1.0, 1.0), (1, 1/3, 0.5, 1.0) ], "hsv", (0, 0, 0), False, 0 ),
                     # From blue to pinkish
                     ( [ (0, 2/3, 1.0, 1.0), (0.5, 1.0, 0.6, 1.0), (1, 1.0, 0.4, 1.0) ], "hsv", (0, 0, 0), False, 0 ),
                     # From blue to yellow
                     ( [ (0, 0.38, 0.0, 0.88), (1, 0.94, 1.0, 0.13) ], "rgb", (0, 0, 0), False, 0 ),
                     # From green to red
                     ( [ (0, 0.4, 1.0, 1.0), (0.5, 0.1, 1.0, 1.0), (1, -0.2, 0.9, 1.0) ], "hsv", (0, 0, 0), False, 0 ),
                     # Pure white (will become greyscale)
                     ( [ (0, 0.0, 0.0, 1.0), (1, 0.0, 0.0, 1.0) ], "hsv", (0, 0, 0), False, 0 ),
                     # Pure black (will become greyscale
                     ( [ (0, 0.0, 0.0, 1.0), (1, 0.0, 0.0, 1.0) ], "hsv", (1, 1, 1), True, 0 ),
                     # Inverted red
                     ( [ (0, 0.0, 0.9, 1.0), (1, 0.0, 1.0, 1.0) ], "hsv", (91/255, 159/255, 184/255), True, 0.4 ),
                     # Inverted blue
                     ( [ (0, 2/3, 0.9, 1.0), (1, 2/3, 1.0, 1.0) ], "hsv", (184/255, 159/255, 91/255), True, 0.4 ),
                     # Full rainbow
                     ( [ (0, 0.5, 1.0, 1.0), (1, 1.5, 0.6, 1.0) ], "hsv", (184/255, 159/255, 91/255), True, 0.4 ),
                    )

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
            self.paletteIndex = random.choice(range(len(self.pal_templates)))

    # TODO: put palette and gradients in their own module, or at least their own class
    def getGradient(self, controlColors, n, space="hsv"):
        grad = list()
        l = len(controlColors)
        for i, color in enumerate(controlColors):
            if i == l-1: break
            nInSlice = int(n/((l-1)*(controlColors[i+1][0]-color[0])))
            startColor = color[1:]
            endColor = controlColors[i+1][1:]
            add = [(x-y)/nInSlice for (x, y) in zip(endColor, startColor)]
            for s in range(0, nInSlice):
                cur_color = [x+s*y for (x,y) in zip(startColor, add)]
                if space == "hsv":
                    hsv_color = cur_color
                else:
                    hsv_color = colorsys.rgb_to_hsv(*cur_color)
                grad.append(tuple(hsv_color))
        return grad

    def getPalette(self, frequencies):
        self.logger.debug("Choosing palette %d" % (self.paletteIndex))
        template = self.pal_templates[self.paletteIndex]
        gradient = self.getGradient(template[0], len(frequencies), space=template[1])
        while len(gradient) < len(frequencies):
            gradient.append(gradient[-1])

        colormap = dict()
        for i, freq in enumerate(sorted(frequencies)):
            colormap[freq] = gradient[i]

        palette = dict()
        palette['colormap']   = colormap
        palette['background'] = template[2]
        palette['negative']   = template[3]
        palette['voffset']    = template[4]

        return palette

    def colorize_pixel(self, level):
        # We use level of pixel (equalized frequency) as Value component.
        v = level/self.fullRange
        if self.palette['negative']: v = 1.0-v
        v = self.palette['voffset'] + v*(1-self.palette['voffset'])
        (r, g, b) = colorsys.hsv_to_rgb(self.palette['colormap'][level][0], self.palette['colormap'][level][1], v)
        return tuple([round(x*((1 << self.bpc)-1)) for x in (b, g, r)])

    def colorizeAttractor(self, p):
        frequencies  = list(set(p.values()))
        self.palette = self.getPalette(frequencies)
        self.palette['background'] = tuple([round(component * ((1 << self.bpc)-1)) for component in self.palette['background']])

        for c, v in p.items():
            p[c] = self.colorize_pixel(v)

        self.logger.debug("Number of unique colors in the attractor after colorization: %d." % (len(set(p.values()))))

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
            pools[i] = 1 + (self.fullRange - 1)*(pools[i]-pools[0])/(pools[-1]-pools[0])

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

