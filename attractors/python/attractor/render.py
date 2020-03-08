#!/usr/bin/python

import logging
import random
import math
import colorsys
import random

try:
    import png
except:
    import sys
    print("this program requires the pyPNG module", file=sys.stderr)
    print("available at https://github.com/drj11/pypng", file=sys.stderr)
    raise SystemExit

defaultParameters = {
    'transparentbg': False,
    'subsample': 1,
    'bpc' : 8,
    'dimension' : 2,
    'geometry' : (800, 600),
}

class Renderer(object):
    def __init__(self, **kwargs):
        getParam = lambda k: kwargs[k] if kwargs and k in kwargs else defaultParameters[k]

        self.INTERNAL_BPC=16
        self.fullRange  = (1<<self.INTERNAL_BPC)-1
        self.logger     = logging.getLogger(__name__)
        self.bpc        = getParam('bpc')
        self.shift      = self.INTERNAL_BPC - self.bpc
        self.subsample  = getParam('subsample')
        self.geometry   = getParam('geometry')
        self.negative   = True
        self.dimension  = getParam('dimension')
        self.transparentbg  = getParam('transparentbg')
        self.geometry   = [x*self.subsample for x in self.geometry]
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
        templates = (( [ (0.0, 1.0, 0.9), (1/3, 0.5, 1.0) ], (0, 0, 0), False ),   # From red to yellow
                     ( [ (2/3, 1.0, 1.0), (1.0, 0.4, 1.0) ], (0, 0, 0), False ),   # From blue to red
                     ( [ (0.0, 0.0, 1.0), (0.0, 0.0, 1.0) ], (0, 0, 0), False ),   # Pure white (will become greyscale)
                     ( [ (0.0, 0.0, 1.0), (0.0, 0.0, 1.0) ], (1, 1, 1), True ),    # Pure black (will become greyscale)
                    )
        template = random.choice(templates)
#        template = templates[0]
        gradient = self.getGradient(template[0], len(frequencies))
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
        return tuple([round(x*((1 << self.bpc)-1)) for x in (r, g, b)])

    def colorizeAttractor(self, p):
        frequencies  = list(set(p.values()))
        self.palette = self.getRandomPalette(frequencies)
        self.palette['background'] = tuple([round(component * ((1 << self.bpc)-1)) for component in self.palette['background']])

        for c, v in p.items():
            p[c] = self.colorize_pixel(v)

        self.logger.debug("Number of unique colors in the attractor after colorization: %d." % (len(list(set(p.values())))))

    # Attractor subsampling. Will have weird effects on color attractors !
    def subsampleAttractor(self, at):
        nat = dict()

        for pt, color in at.items():
            xsub = int(pt[0]/self.subsample)
            ysub = int(pt[1]/self.subsample)
            if (xsub,ysub) in nat: # We already subsampled this square
                continue
            n = 0
            c = 0
            x0 = xsub*self.subsample
            y0 = ysub*self.subsample
            for x in range(x0, x0+self.subsample):
                for y in range(y0, y0+self.subsample):
                    if (x, y) in at:
                        n += 1
                        c += at[(x, y)]
            # OK now we have accumulated all colors in the attractors
            # The pixels on the edge should be weighted with black (no color)
            v = 0*(self.subsample*self.subsample-n) # In case we want to change the color someday
            c += v
            # Time to weight with the background color
            c = round(c/(self.subsample*self.subsample))
            nat[(xsub,ysub)] = c

        return nat

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

    # Postprocess the attractor
    # attractor: attractor points: dict (X,Y) and containing :
    # - frequency for 2D
    # - Z for 3D
    #
    # 1- Perform histogram equalization on the attractor frequency
    # 2- If needed subsample the frequencies (to smooth transitions)
    # 3- Colorize the attractor
    def postprocessAttractor(self, at):
        M = max(at.values())

        self.logger.debug("Number of frequencies in attractor (before subsampling): %d" % (len(list(set(at.values())))))
        # Now send the map in the [0, (1<<self.INTERNAL_BPC)-1] range
        for i, pt in at.items():
            at[i] = int (pt*self.fullRange/M)

        self.equalizeAttractor(at)
        if self.subsample > 1:
            at = self.subsampleAttractor(at)
            self.logger.debug("Number of frequencies in attractor (after subsampling): %d" % (len(list(set(at.values())))))
        self.colorizeAttractor(at)
        return at

    # Creates the final image array
    def createImageArray(self, p, sd):
        (w, h) = [ int(coord/self.subsample) for coord in sd[0:2] ]

        img = [ list(self.palette['background'])*w for y in range(0,h) ]
        for c, v in p.items():
            (col, row) = c
            try:
                img[row][col*3:(col+1)*3] = v
            except IndexError as e:
                # This can occur if the bounds were not correctly assessed
                # and a point of the attractor happens to fall out of them.
                self.logger.debug("Looks like a point fell out of our bounds. Ignoring it.")
        return img

    def renderAttractor(self, a):
        if not a: return None
        p = self.postprocessAttractor(a)
        i = self.createImageArray(p, self.geometry)
        return i

    def writeAttractorPNG(self, a, filepath):
        self.logger.debug("Now writing attractor %s on disk." % filepath)

        w = png.Writer(size=[int(x/self.subsample) for x in self.geometry], bitdepth=self.bpc, interlace=True, greyscale = False, transparent = self.palette['background'] if self.transparentbg else None)

        with open(filepath, "wb") as f:
            w.write(f, a)

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

