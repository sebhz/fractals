#!/usr/bin/python

import colorsys
import random
import logging
from multiprocessing import Manager, Process

try:
    import png
except:
    print >> sys.stderr, "this program requires the pyPNG module"
    print >> sys.stderr, "available at https://github.com/drj11/pypng"
    raise SystemExit


INTERNAL_BPC=16

defaultParameters = {
	'mode': 'greyscale',
	'subsample': 1,
	'bpc' : 8,
	'nthreads' : 1,
	'screenDim' : (800, 600),
}

def getInitPoints(at, n):
	initPoints = list()
	i = 0
	while True:
		if not at.bound:
			p = (random.random(), random.random())
		else:
			rx = at.bound[0] + random.random()*(at.bound[2]-at.bound[0])
			ry = at.bound[1] + random.random()*(at.bound[3]-at.bound[1])
			p = (rx, ry)
		if at.checkConvergence(p):
			initPoints.append(p)
			i += 1
		if i == n: return initPoints

# sd: screen dimension e.g (800,600)
# wc: attractor bound (x0,y0,x1,y1)
def scaleBounds(wc, sd):
	# Enlarge window by 5% in both directions
	hoff = (wc[3]-wc[1])*0.025
	woff = (wc[2]-wc[0])*0.025
	nwc  = (wc[0]-woff, wc[1]-hoff, wc[2]+woff, wc[3]+hoff)

	wa = float(nwc[3]-nwc[1])/float(nwc[2]-nwc[0]) # New window aspect ratio
	sa = float(sd[1])/float(sd[0]) # Screen aspect ratio
	r = sa/wa

	if wa < sa: # Enlarge window height to get the right AR - keep it centered vertically
		yoff = (nwc[3]-nwc[1])*(r-1)/2
		return (nwc[0], nwc[1]-yoff, nwc[2], nwc[3]+yoff)
	elif wa > sa: # Enlarge window width to get the right AR - keep it centered horizontally
		xoff = (nwc[2]-nwc[0])*(1/r-1)/2
		return (nwc[0]-xoff, nwc[1], nwc[2]+xoff, nwc[3])

	return wc

class Renderer(object):
	def __init__(self, **kwargs):
		getParam = lambda k: kwargs[k] if kwargs and k in kwargs else defaultParameters[k]

		self.logger     = logging.getLogger(__name__)
		self.bpc        = getParam('bpc')
		self.rendermode = getParam('mode')
		self.subsample  = getParam('subsample')
		self.nthreads   = getParam('threads')
		self.screenDim  = getParam('screenDim')
		self.shift      = INTERNAL_BPC - self.bpc
		self.screenDim  = [x*self.subsample for x in self.screenDim]
	# Equalize and colorize attractor
	# attractor: attractor points: dict (X,Y) and containing frequency
	# Returns the attractor points: dict indexed by (X, Y) and containing COLOR, 
	def postprocessAttractor(self, at):
		M = 0
		for v in at.values():
			M = max(M, v)

		# Now send the map in the [0, (1<<INTERNAL_BPC)-1] range
		for i, pt in at.iteritems():
			at[i] = int (pt * ((1<<INTERNAL_BPC)-1)/M)

		# Equalize the attractor (histogram equalization)
		self.equalizeAttractor(at)

		# Subsample here
		at = self.subsampleAttractor(at)

		# Colorize attractor
		self.colorizeAttractor(at)

		return at

	# Creates the final image array
	def createImageArray(self, p, sd, background):
		w = int ((sd[0])/self.subsample)
		h = int ((sd[1])/self.subsample)

		a = background*w*h

		for c, v in p.iteritems():
			offset = c[0] + c[1]*w
			if self.rendermode == "greyscale":
				a[offset] = v >> self.shift
			else:
				a[3*offset:3*offset+3] = [x >> self.shift for x in v]

		return a

	# Performs histogram equalization on the attractor pixels
	def equalizeAttractor(self, p):
		pools = [0]*(1<<INTERNAL_BPC)

		# Create cumulative distribution
		for v in p.itervalues():
			pools[v] += 1
		for i in range(len(pools) - 1):
			pools[i+1] += pools[i]

		# Stretch the values to the [1, (1<<INTERNAL_BPC)-1] range
		for i, v in enumerate(pools):
			pools[i] = 1+((1<<INTERNAL_BPC)-2)*(pools[i]-pools[0])/(pools[-1]-pools[0])

		# Now reapply the stretched values (inverting them so that high order pixels are darker
		# when viewed in greyscale)
		for k in p:
			p[k] = ((1<<INTERNAL_BPC)-1) - pools[p[k]]

	# Colorize the attractor
	# Input: a dict of attractor pixels, indexed by (X,Y) containing equalized color between
	# 0 and 1<<INTERNAL_BPC-1
	# Output: same dict as input, containing (R,G,B) colors between 0 and 1<<INTERNAL_BPC
	def colorizeAttractor(self, a):
		if self.rendermode == "greyscale":
			return

		hues = { 'red': 0.0, 'yellow': 1.0/6, 'green': 2.0/6, 'cyan': 3.0/6, 'blue': 4.0/6, 'magenta':5.0/6 }
		hue = hues.keys()[random.randint(0, len(hues.keys())-1)]
		h = hues[hue]

		pools=dict()
		for v in a.values():
			if v in pools: continue
			else: pools[v] = 1

		ncolors = len(pools.keys())
		self.logger.debug("%d points in attractor. %d unique %d-bpc colors in attractor. Coloring ratio: %1.2f%%." % (len(a.keys()), ncolors, INTERNAL_BPC, float(len(pools.keys()))/len(a.keys())*100))

		colormap = dict()

		# We want to create a gradient between orangish and yellowish, with a unique color mapping.
		for color in pools.keys():
			hh = 1.0/12 + float(color)*(1.0/8 - 1.0/12)/((1<<INTERNAL_BPC)-1)
			vv = 0.75 + 0.25*float(color)/((1<<INTERNAL_BPC)-1)
			hsv = (hh, 0.3, vv)
			colormap[color] = [int(((1<<INTERNAL_BPC)-1)*component) for component in colorsys.hsv_to_rgb(*hsv)]

		dt = dict()
		for k in sorted(colormap.keys()):
			dt[k>>self.shift] = True
		self.logger.debug("%d unique %d-bpc greyscale." % (len(dt.keys()), self.bpc))

		dt = dict()
		for k in sorted(colormap.keys()):
			dt[tuple([v >> self.shift for v in colormap[k]])] = True
		self.logger.debug("%d unique %d-bpc color." % (len(dt.keys()), self.bpc))

		for v in a:
			a[v] = colormap[a[v]]

	def subsampleAttractor(self, at):

		if self.subsample == 1: return at

		nat = dict()

		for pt, color in at.iteritems():
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
			v = 0xFFFF*(self.subsample*self.subsample-n)
			c += v
			c = int(c/(self.subsample*self.subsample))
			nat[(xsub,ysub)] = c

		return nat

	def renderAttractor(self, a):
		backgroundColor = [0xFF] if self.rendermode == "greyscale" else [0xFF, 0xFF, 0xFF]
		p = self.postprocessAttractor(a)
		i = self.createImageArray(p, self.screenDim, backgroundColor)
		return i

	def mergeAttractors(self, a):
		v = None

		for i in xrange(len(a)):
			if a[i] != None:
				v = a[i]
				break

		if v == None:
			self.logger.debug("Empty attractor. Trying to go on anyway.")
			return v

		for vv in a[i+1:]:
			if vv == None: continue
			for k, e in vv.iteritems():
				if k in v:
					v[k] += e
				else:
					v[k] = e

		self.logger.debug("%d points in the attractor before any dithering done." % (len(v.keys())))
		return v

	def walkthroughAttractor(self, at):
		jobs = list()
		initPoints = getInitPoints(at, self.nthreads)
		window_c = scaleBounds(at.bound, self.screenDim)

		manager = Manager()
		a = manager.list([None]*self.nthreads)
		for i in range(self.nthreads):
			job = Process(group=None, name='t'+str(i), target=at.iterateMap, args=(self.screenDim, window_c, a, i, initPoints[i]))
			jobs.append(job)
			job.start()

		for job in jobs:
			job.join()

		aMerge = self.mergeAttractors(a)
		if not aMerge: return aMerge
		at.computeFractalDimension(aMerge, self.screenDim, window_c)

		self.logger.debug("Time to render the attractor.")
		return self.renderAttractor(aMerge)

	def writeAttractorPNG(self, a, filepath):
		self.logger.debug("Now writing attractor %s on disk." % filepath)
		w = png.Writer(size=[x/self.subsample for x in self.screenDim], greyscale = True if self.rendermode == "greyscale" else False, bitdepth=self.bpc, interlace=True)
		aa = w.array_scanlines(a)
		with open(filepath, "wb") as f:
			w.write(f, aa)

