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
    'colormode': 'light',
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
        self.colormode  = getParam('colormode')
        self.dimension  = getParam('dimension')
        self.transparentbg  = getParam('transparentbg')
        self.backgroundColor = (1<<self.bpc) - 1 if self.colormode == 'light' else 0
        self.geometry   = [x*self.subsample for x in self.geometry]
        self.internalbg = 0
        if self.dimension < 2 or self.dimension > 3:
            self.logger.warning("Trying to create renderer with invalid dimension (" + self.dimension + "). Defaulting to 2.")
            self.dimension = 2

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

    def getRandomGradient(self, n):
        niceGradients = ([ (0.0, 1.0, 0.9), (1/3, 0.5, 1.0) ],   # From red to yellow
                         [ (2/3, 1.0, 1.0), (1.0, 0.4, 1.0) ],   # From blue to red
                        )
        gradient = self.getGradient(random.choice(niceGradients), n)
        while len(gradient) < n:
            gradient.append(gradient[-1])
        return gradient

    # Equalize the attractor
    # attractor: attractor points: dict (X,Y) and containing :
    # - frequency for 2D
    # - Z for 3D
    # Returns the attractor points: dict indexed by (X, Y) and containing COLOR, 
    def postprocessAttractor(self, at):
        M = max(at.values())

        self.logger.debug("Number of frequencies in attractor (before subsampling): %d" % (len(list(set(at.values())))))
        # Now send the map in the [0, (1<<self.INTERNAL_BPC)-1] range
        for i, pt in at.items():
            at[i] = int (pt*self.fullRange/M)

        # Equalize the attractor (histogram equalization)
        self.equalizeAttractor(at)

        # Subsample here
        at = self.subsampleAttractor(at)
        self.logger.debug("Number of frequencies in attractor (after subsampling): %d" % (len(list(set(at.values())))))

        return at

    def colorize_pixel(self, pixel, gradient_map):
        if self.colormode == 'color':
            # We extract the current pixel HSV to reuse the Value component.
            (h, s, v) = colorsys.rgb_to_hsv(pixel/self.fullRange, pixel/self.fullRange, pixel/self.fullRange)
            # TODO: change background color based on gradient
            # TODO: harmonize generation of B&W and color images by using a specific gradient for B&W
            (r, g, b) = colorsys.hsv_to_rgb(gradient_map[pixel][0], gradient_map[pixel][1], v)
            return tuple([round(x*255) for x in (r, g, b)])
        else:
            if self.colormode == 'light':
                v_tmp = (self.fullRange - round(pixel)) >> self.shift
            else:
                v_tmp = round(pixel) >> self.shift
            return (v_tmp, v_tmp, v_tmp,)

    # Creates the final image array
    def createImageArray(self, p, sd):
        w = int ((sd[0])/self.subsample)
        h = int ((sd[1])/self.subsample)

        frequencies = list(set(p.values()))
        grd = self.getRandomGradient(len(frequencies))
        gradient = dict()
        for i, freq in enumerate(sorted(frequencies)):
            gradient[freq] = grd[i]

        a = [ (self.backgroundColor, self.backgroundColor, self.backgroundColor) ]*w*h
        # TODO: generate directly pyPNG-friendly format
        for c, v in p.items():
            offset = c[0] + c[1]*w
            try:
                a[offset] = self.colorize_pixel(v, gradient)
            except IndexError as e:
                # This can occur if the bounds were not correctly assessed
                # and a point of the attractor happens to fall out of them.
                self.logger.debug("Looks like a point fell out of our bounds. Ignoring it.")

        self.logger.debug("Number of unique colors in the attractor after colorization: %d." % (len(list(set(a)))))
        # Now reformat the array to please latest pypng versions
        # pypng now expects a table of one flat array per row
        b = []
        for row in range(0, h):
            b.append([component for rgb_color in a[row*w:(row+1)*w] for component in rgb_color])
        return b

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

    def subsampleAttractor(self, at):

        if self.subsample == 1: return at

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
            # Time to weight with the background color
            v = self.internalbg*(self.subsample*self.subsample-n)
            c += v
            c = int(c/(self.subsample*self.subsample))
            nat[(xsub,ysub)] = c

        return nat

    def renderAttractor(self, a):
        if not a: return None
        p = self.postprocessAttractor(a)
        i = self.createImageArray(p, self.geometry)
        return i

    def writeAttractorPNG(self, a, filepath):
        self.logger.debug("Now writing attractor %s on disk." % filepath)

        w = png.Writer(size=[int(x/self.subsample) for x in self.geometry], bitdepth=self.bpc, interlace=True, greyscale = False, transparent = self.backgroundColor if self.transparentbg else None)

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

