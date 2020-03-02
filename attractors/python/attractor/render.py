#!/usr/bin/python

import logging
import random
import math

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

        self.logger     = logging.getLogger(__name__)
        self.bpc        = getParam('bpc')
        self.subsample  = getParam('subsample')
        self.geometry   = getParam('geometry')
        self.colormode  = getParam('colormode')
        self.dimension  = getParam('dimension')
        self.transparentbg  = getParam('transparentbg')
        self.backgroundColor = (1<<self.bpc) - 1 if self.colormode == 'light' else 0
        self.geometry   = [x*self.subsample for x in self.geometry]
        self.internalbg = 0xFFFF if self.colormode == 'light' else 0
        if self.dimension < 2 or self.dimension > 3:
            self.logger.warning("Trying to create renderer with invalid dimension (" + self.dimension + "). Defaulting to 2.")
            self.dimension = 2

        if self.colormode == 'color':
            self.INTERNAL_BPC=11
        else:
            self.INTERNAL_BPC=16

        self.shift      = self.INTERNAL_BPC - self.bpc

    # Equalize the attractor
    # attractor: attractor points: dict (X,Y) and containing :
    # - frequency for 2D
    # - Z for 3D
    # Returns the attractor points: dict indexed by (X, Y) and containing COLOR, 
    def postprocessAttractor(self, at):
        M = max(at.values())

        # Now send the map in the [0, (1<<self.INTERNAL_BPC)-1] range
        for i, pt in at.items():
            at[i] = int (pt * ((1<<self.INTERNAL_BPC)-1)/M)

        # Equalize the attractor (histogram equalization)
        self.equalizeAttractor(at)

        # Subsample here
        at = self.subsampleAttractor(at)

        return at

    def colorize_pixel(self, v, coef, ncol_base, ncol_shift):
        if self.colormode == 'color':
            self.logger.debug("Color coefficients: (R, G, B) = (%d, %d, %d)" % coef)
            # Ramp mapping 0->512 to 0->256
            per_color = lambda x: 128 + x if x < 128 else 383 - x if x < 384 else x - 384
            sqv = 2*math.sqrt(v)
            r = per_color(int(math.floor(sqv * coef[0])) % 512)
            g = per_color(int(math.floor(sqv * coef[1])) % 512)
            b = per_color(int(math.floor(sqv * coef[2])) % 512)
            return (r, g, b,)
        else:
            if self.colormode == 'light':
                v_tmp = (((1<<self.INTERNAL_BPC)-1) - int(v)) >> self.shift
            else:
                v_tmp = int(v) >> self.shift
            ncol_base[int(v)] = 1
            ncol_shift[v_tmp] = 1
            return (v_tmp, v_tmp, v_tmp,)

    # Creates the final image array
    def createImageArray(self, p, sd):
        w = int ((sd[0])/self.subsample)
        h = int ((sd[1])/self.subsample)

        (ncol_base, ncol_shift) = (dict(), dict())
        coef = (random.randint(1,4), random.randint(1,4), random.randint(1,4),)
        a = [ (self.backgroundColor, self.backgroundColor, self.backgroundColor) ]*w*h
        for c, v in p.items():
            offset = c[0] + c[1]*w
            try:
                a[offset] = self.colorize_pixel(v, coef, ncol_base, ncol_shift)
            except IndexError as e:
                # This can occur if the bounds were not correctly assessed
                # and a point of the attractor happens to fall out of them.
                self.logger.debug("Looks like a point fell out of our bounds. Ignoring it.")

        self.logger.debug("Number of unique colors in the attractor: %d before shift, %d after shift." % (len(ncol_base), len(ncol_shift)))
        return a

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
            pools[i] = 1+((1<<self.INTERNAL_BPC)-2)*(pools[i]-pools[0])/(pools[-1]-pools[0])

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

        w = png.Writer(size=[int(x/self.subsample) for x in self.geometry], bitdepth=self.bpc, interlace=True, transparent = self.backgroundColor if self.transparentbg else None)

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
        self.logger.debug("Attractor cover ratio is %.2f%%" % (100.0*coverRatio))
        if coverRatio < coverLimit:
            return False

        return True

