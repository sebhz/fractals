#!/usr/bin/python

import colorsys
import random
import logging

try:
	import png
except:
	import sys
	print("this program requires the pyPNG module", file=sys.stderr)
	print("available at https://github.com/drj11/pypng", file=sys.stderr)
	raise SystemExit

INTERNAL_BPC=16

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
		self.shift      = INTERNAL_BPC - self.bpc
		self.backgroundColor = (1<<self.bpc) - 1 if self.colormode == 'light' else 0
		self.geometry   = [x*self.subsample for x in self.geometry]
		self.internalbg = 0xFFFF if self.colormode == 'light' else 0
		if self.dimension < 2 or self.dimension > 3:
			self.logger.warning("Trying to create renderer with invalid dimension (" + self.dimension + "). Defaulting to 2.")
			self.dimension = 2

	# Equalize the attractor
	# attractor: attractor points: dict (X,Y) and containing :
	# - frequency for 2D
	# - Z for 3D
	# Returns the attractor points: dict indexed by (X, Y) and containing COLOR, 
	def postprocessAttractor(self, at):
		M = max(at.values())

		# Now send the map in the [0, (1<<INTERNAL_BPC)-1] range
		for i, pt in at.items():
			at[i] = int (pt * ((1<<INTERNAL_BPC)-1)/M)

		# Equalize the attractor (histogram equalization)
		self.equalizeAttractor(at)

		# Subsample here
		at = self.subsampleAttractor(at)

		return at

	# Creates the final image array
	def createImageArray(self, p, sd):
		w = int ((sd[0])/self.subsample)
		h = int ((sd[1])/self.subsample)

		a = [self.backgroundColor]*w*h

		for c, v in p.items():
			offset = c[0] + c[1]*w
			try:
				a[offset] = int(v) >> self.shift
			except IndexError as e:
				# This can occur if the bounds were not correctly assessed
				# and a point of the atractor happens to fall out of them.
				logging.debug("Looks like a point fell out of our bounds. Ignoring it")
		return a

	# Performs histogram equalization on the attractor pixels
	def equalizeAttractor(self, p):
		pools = [0]*(1<<INTERNAL_BPC)

		# Create cumulative distribution
		for v in p.values():
			pools[v] += 1
		for i in range(len(pools) - 1):
			pools[i+1] += pools[i]

		# Stretch the values to the [1, (1<<INTERNAL_BPC)-1] range
		for i, v in enumerate(pools):
			pools[i] = 1+((1<<INTERNAL_BPC)-2)*(pools[i]-pools[0])/(pools[-1]-pools[0])

		# Now reapply the stretched values
		if self.dimension == 2:
			for k in p:
				if self.colormode == 'light': # invert the values so that high order pixels are dark
					p[k] = ((1<<INTERNAL_BPC)-1) - pools[p[k]]
				else:
					p[k] = pools[p[k]]
		else:
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

		w = png.Writer(size=[int(x/self.subsample) for x in self.geometry], greyscale = True, bitdepth=self.bpc, interlace=True, transparent = self.backgroundColor if self.transparentbg else None)
		aa = w.array_scanlines(a)
		with open(filepath, "wb") as f:
			w.write(f, aa)

	def isNice(self, a, coverLimit=0.01):
		"""
		Checks if the attractor passed is 'nice': currently nice means that the
		attractors covers more than coverLimit percent of the window.
		"""
		if not a: return False
		nPoints = len(a)
		sSize   = self.geometry[0]*self.geometry[1]
		coverRatio = float(nPoints)/sSize
		self.logger.debug("Attractor cover ratio is %.2f%%" % (100.0*coverRatio))
		if coverRatio < coverLimit:
			return False

		return True

