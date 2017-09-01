#!/usr/bin/python

import colorsys
import random
import logging

try:
	import png
except:
	import sys
	print >> sys.stderr, "this program requires the pyPNG module"
	print >> sys.stderr, "available at https://github.com/drj11/pypng"
	raise SystemExit

INTERNAL_BPC=16

defaultParameters = {
	'transparentbg': False,
	'mode': 'greyscale',
	'colormode': 'light',
	'subsample': 1,
	'bpc' : 8,
	'geometry' : (800, 600),
}

class Renderer(object):
	def __init__(self, **kwargs):
		getParam = lambda k: kwargs[k] if kwargs and k in kwargs else defaultParameters[k]

		self.logger     = logging.getLogger(__name__)
		self.bpc        = getParam('bpc')
		self.rendermode = getParam('mode')
		self.subsample  = getParam('subsample')
		self.geometry   = getParam('geometry')
		self.colormode  = getParam('colormode')
		self.transparentbg  = getParam('transparentbg')
		self.shift      = INTERNAL_BPC - self.bpc
		if self.rendermode == 'greyscale':
			self.backgroundColor = (1<<self.bpc) - 1 if self.colormode == 'light' else 0
		else:
			self.backgroundColor = (0xFF, 0xFF, 0xFF) if self.colormode == 'light' else (0, 0, 0)
		self.geometry   = [x*self.subsample for x in self.geometry]
		self.internalbg = 0xFFFF if self.colormode == 'light' else 0

	# Equalize and colorize attractor
	# attractor: attractor points: dict (X,Y) and containing frequency
	# Returns the attractor points: dict indexed by (X, Y) and containing COLOR, 
	def postprocessAttractor(self, at):
		M = max(at.values())

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
	def createImageArray(self, p, sd):
		w = int ((sd[0])/self.subsample)
		h = int ((sd[1])/self.subsample)

		if self.rendermode == 'greyscale':
			a = [self.backgroundColor]*w*h
		else:
			a = list(self.backgroundColor)*w*h

		for c, v in p.iteritems():
			offset = c[0] + c[1]*w
			try:
				if self.rendermode == 'greyscale':
					a[offset] = v >> self.shift
				else:
					a[3*offset:3*offset+3] = [x >> self.shift for x in v]
			except IndexError as e:
				# This can occur if the bounds were not correctly assessed
				# and a point of the atractor happens to fall out of them.
				logging.debug("Looks like a point fell out of our bounds. Ignoring it")
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

		# Now reapply the stretched values
		for k in p:
			if self.colormode == 'light': # invert the values so that high order pixels are dark
				p[k] = ((1<<INTERNAL_BPC)-1) - pools[p[k]]
			else:
				p[k] = pools[p[k]]

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

		w = png.Writer(size=[x/self.subsample for x in self.geometry], greyscale = True if self.rendermode=="greyscale" else False, bitdepth=self.bpc, interlace=True, transparent = self.backgroundColor if self.transparentbg else None)
		aa = w.array_scanlines(a)
		with open(filepath, "wb") as f:
			w.write(f, aa)

	def isNice(self, a, coverLimit=0.01):
		"""
		Checks if the attractor passed is 'nice': currently nice means that the
		attractors covers more than coverLimit percent of the window.
		"""
		if not a: return False
		nPoints = len(a.keys())
		sSize   = self.geometry[0]*self.geometry[1]
		coverRatio = float(nPoints)/sSize
		self.logger.debug("Attractor cover ratio is %.2f%%" % (100.0*coverRatio))
		if coverRatio < coverLimit:
			return False

		return True

