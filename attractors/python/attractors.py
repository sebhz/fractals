#!/usr/bin/python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# Generate and colorize various dimension polynomial strange attractors
# Algo taken from Julian Sprott's book: http://sprott.physics.wisc.edu/sa.htm
# Some coloring ideas (histogram equalization) taken from
# Ian Witham's blog
# http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/

import random
import math
import argparse
import colorsys
import sys
import os
import re
import logging
from time import time
from multiprocessing import Manager, Process

try:
    import png
except:
    print >> sys.stderr, "this program requires the pyPNG module"
    print >> sys.stderr, "available at https://github.com/drj11/pypng"
    raise SystemExit

INTERNAL_BPC=16
OVERITERATE_FACTOR=4
LOGLEVELS = (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET)

defaultParameters = {
	'iter': 1280*1024*OVERITERATE_FACTOR,
	'sub': 1,
	'bpc': 8,
	'geometry': "1280x1024",
	'number': 1,
	'order': 2,
	'outdir': "png",
	'loglevel':4,
	'threads':1,
	'type':'polynomial',
}

class Attractor(object):
	convDelay    = 128   # Number of points to ignore before checking convergence
	convMaxIter  = 16384 # Check convergence on convMaxIter points only
	epsilon      = 1e-6

	def __init__(self, **opt):
		self.iterations = defaultParameters['iter']
		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None
		if opt:
			self.iterations = opt['iter'] if 'iter' in opt else defaultParameters['iter']

	def __str__(self):
		return self.code

	def computeLyapunov(self, p, pe):
		p2   = self.getNextPoint(pe)
		if not p2: return pe
		dl   = [d-x for d,x in zip(p2, p)]
		dl2  = reduce(lambda x,y: x*x + y*y, dl)
		if dl2 == 0:
			logging.warning("Unable to compute Lyapunov exponent, but trying to go on...")
			return pe
		df = dl2/self.epsilon/self.epsilon
		rs = 1/math.sqrt(df)

		self.lyapunov['lsum'] += math.log(df, 2)
		self.lyapunov['nl']   += 1
		self.lyapunov['ly'] = self.lyapunov['lsum'] / self.lyapunov['nl']
		return [p[i]+rs*x for i,x in enumerate(dl)]

	def checkConvergence(self, initPoint=(0.1, 0.1)):
		self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
		pmin, pmax = ([100000,100000], [-100000,-100000])
		p = initPoint
		pe = [x + self.epsilon if i==0 else x for i,x in enumerate(p)]
		modulus = lambda x, y: abs(x) + abs(y)

		for i in range(self.convMaxIter):
			pnew = self.getNextPoint(p)
			if not pnew: return False
			if reduce(modulus, pnew, 0) > 1000000: # Unbounded - not an SA
				return False
			if reduce(modulus, [pn-pc for pn, pc in zip(pnew, p)], 0) < self.epsilon:
				return False
			# Compute Lyapunov exponent... sort of
			pe = self.computeLyapunov(pnew, pe)
			if self.lyapunov['ly'] < 0.005 and i > self.convDelay: # Limit cycle
				return False
			if i > self.convDelay:
				pmin = [min(pn, pm) for pn, pm in zip(pnew, pmin)]
				pmax = [max(pn, pm) for pn, pm in zip(pnew, pmax)]
			p = pnew
		if not self.bound:
			self.bound = [v for p in (pmin, pmax,) for v in p]
		return True

	def explore(self):
		n = 0;
		self.getRandomCoef()
		while not self.checkConvergence():
			n += 1
			self.getRandomCoef()
		# Found one -> create corresponding code
		logging.debug("Attractor found after %d trials." % (n+1))
		self.createCode()

	def iterateMap(self, screen_c, window_c, aContainer, index, initPoint=(0.1, 0.1)):
		a = dict()
		p = initPoint

		sh = screen_c[3]-screen_c[1]
		ratioY = sh/(window_c[3]-window_c[1])
		ratioX = (screen_c[2]-screen_c[0])/(window_c[2]-window_c[0])
		w_to_s = lambda p: (
			int(screen_c[0] + (p[0]-window_c[0])*ratioX),
			int(screen_c[1] + sh-(p[1]-window_c[1])*ratioY) )

		for i in range(self.iterations):
			pnew = self.getNextPoint(p)
			if not pnew:
				aContainer[index] = None
				return

			# Ignore the first points to get a proper convergence
			if i >= self.convDelay:
				projectedPixel = w_to_s(pnew)

				if projectedPixel:
					if projectedPixel in a:
						a[projectedPixel] += 1
					else:
						a[projectedPixel] = 0
			p = pnew

		aContainer[index] = a

	# An estimate of the Minkowski-Bouligand dimension (a.k.a box-counting)
	# See https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension
	def computeBoxCountingDimension(self, a, screen_c, window_c):
		if not self.bound: return None

		sideLength = 2 # Box side length, in pixels
		pixelSize = (window_c[2]-window_c[0])/(screen_c[2]-screen_c[0])

		boxes = dict()
		for pt in a.keys():
			boxCoordinates = (int(pt[0]/sideLength), int(pt[1]/sideLength))
			boxes[boxCoordinates] = True
		n = len(boxes.keys())

		self.fdim = math.log(n)/math.log(1/(sideLength*pixelSize))

	# An estimate of the correlation dimension computed "a la Julien Sprott"
	# Estimate the probability that 2 points in the attractor are close enough
	# We will make a small error because we resized things a bit, but not that much actually
	def computeCorrelationDimension(self, a, screen_c):
		base = 10
		radiusRatio = 0.001
		diagonal = (screen_c[2]-screen_c[0])**2 + (screen_c[3]-screen_c[1])**2
		d1 = 4*radiusRatio*diagonal
		d2 = float(d1)/base/base
		n1, n2 = (0, 0)
		points = a.keys()
		l = len(points)

		for p in points: # Iterate on each attractor point
			p2 = points[random.randint(0,l-1)] # Pick another point at random
			d = (p2[0]-p[0])**2 + (p2[1]-p[1])**2
			if d == 0: continue # Oops we picked the same point twice
			if d < d1: n2 += 1  # Distance within a big circle
			if d > d2: continue # But out of a small circle
			n1 += 1

		# and then...
		try:
			self.fdim = math.log(float(n2)/n1, base)
		except ZeroDivisionError:
			self.fdim = 0.0 # Impossible to find small circles... very scattered points

class PolynomialAttractor(Attractor):
	codelist     = range(48,58) + range(65,91) + range(97,123) # ASCII values for code
	codeStep     = .125 # Step to use to map ASCII character to coef

	def __init__(self, **opt):
		super(PolynomialAttractor, self).__init__(**opt)
		self.order      = defaultParameters['order']
		self.coef       = None
		self.code       = None
		if opt:
			self.order = opt['order'] if 'order' in opt else defaultParameters['order']
			if 'code' in opt and opt['code'] != None:
				self.code = opt['code']
				self.decodeCode() # Will populate order, polynom, length, polynom, coef and derive
		self.getPolynomLength()
	def decodeCode(self):
		self.order = int(self.code[1])
		self.getPolynomLength()

		d = dict([(self.codelist[i], i) for i in range(0, len(self.codelist))])
		self.coef = [[(d[ord(_)]-30)*self.codeStep for _ in self.code[3+__*self.pl:3+(__+1)*self.pl]] for __ in range(2)]

	def createCode(self):
		self.code = str(2)+str(self.order)
		self.code += "_"
		# ASCII codes of digits and letters
		cl = [self.codelist[int(x/self.codeStep)+30] for c in self.coef for x in c]
		self.code +="".join(map(chr,cl))

	# Outputs a human readable string of the polynom. If isHTML is True
	# outputs an HTML blurb of the equation. Else output a plain text.
	def humanReadable(self, isHTML):
		variables = ('xn', 'yn')
		equation = ["", ""]
		for v, c in enumerate(self.coef): # Iterate on each dimension
			n = 0
			equation[v] = variables[v]+"+1="
			for i in range(self.order+1):
				for j in range(self.order-i+1):
					if c[n] == 0:
						n+=1
						continue
					equation[v] += "%.3f*%s^%d*%s^%d+" % (c[n], variables[0], j, variables[1], i)
					n += 1
					continue
			# Some cleanup
			for r in variables:
				equation[v] = equation[v].replace("*%s^0" % (r), "")
				equation[v] = equation[v].replace("*%s^1" % (r), "*%s" % (r))
			equation[v] = equation[v].replace("+-", "-")
			equation[v] = equation[v][:-1]

			if isHTML: # Convert this in a nice HTML equation
				equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
				equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
				equation[v] = re.sub(r'(x|y)n',r'\1<sub>n</sub>', equation[v])

		return equation

	def getPolynomLength(self):
		self.pl = (self.order+2)*(self.order+1)/2

	def getRandomCoef(self):
		self.coef = [[random.randint(-30, 31)*self.codeStep for _ in range(0, self.pl)] for __ in range(2)]

	def getNextPoint(self, p):
		l = list()
		try:
			for c in self.coef:
				result = 0
				n = 0
				for i in range(self.order+1):
					for j in range(self.order-i+1):
						result += c[n]*(p[0]**j)*(p[1]**i)
						n += 1
				l.append(result)
		except OverflowError:
			logging.error("Overflow during attractor computation.")
			logging.error("Either this is a very slowly diverging attractor, or you used a wrong code")
			return None

		return l

	def computeFractalDimension(self, a, screen_c, window_c):
		super(PolynomialAttractor, self).computeBoxCountingDimension(a, screen_c, window_c)

class DeJongAttractor(Attractor):
	codelist     = range(48,58) + range(65,91) + range(97,123) # ASCII values for code
	codeStep     = .125 # Step to use to map ASCII character to coef

	def __init__(self, **opt):
		super(DeJongAttractor, self).__init__(**opt)
		if opt:
			if 'code' in opt and opt['code'] != None:
				self.code = opt['code']
				self.decodeCode() # Will populate coef

	def createCode(self):
		self.code = "j"
		# ASCII codes of digits and letters
		c = [self.codelist[int(x/self.codeStep)+30] for d in self.coef for x in d]
		self.code +="".join(map(chr,c))

	def decodeCode(self):
		d = dict([(self.codelist[i], i) for i in range(0, len(self.codelist))])
		self.coef = [ [(d[ord(_)]-30)*self.codeStep for _ in self.code[1+2*__:3+2*__]] for __ in range(2) ]
		print ">>", self.coef

	def getRandomCoef(self):
		self.coef = [[random.randint(-30, 31)*self.codeStep for _ in range(2)] for __ in range(2)]
		print ">>", self.coef

	def getNextPoint(self, p):
		return ( math.sin(self.coef[0][0]*p[1]) - math.cos(self.coef[0][1]*p[0]),
		         math.sin(self.coef[1][0]*p[0]) - math.cos(self.coef[1][1]*p[1]), )

	def humanReadable(self, isHTML):
		equation = list()
		equation.append('xn+1=sin(%.3f*yn)-cos(%.3f*xn)' % (self.coef[0][0], self.coef[0][1]))
		equation.append('yn+1=sin(%.3f*xn)-cos(%.3f*yn)' % (self.coef[1][0], self.coef[1][1]))

		if isHTML: # Convert this in a nice HTML equation
			for v in range(0,2):
				equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
				equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
				equation[v] = re.sub(r'(x|y)n',r'\1<sub>n</sub>', equation[v])

		return equation

	def computeFractalDimension(self, a, screen_c, window_c):
		super(DeJongAttractor, self).computeCorrelationDimension(a, screen_c)


# Enlarge attractor bounds so that it has the same aspect ratio as screen_c 
# sc: screen bound e.g. (0,0,800,600)
# wc: attractor bound (x0,y0,x1,y1)
def scaleBounds(wc, sc):
	# Enlarge window by 5% in both directions
	hoff = (wc[3]-wc[1])*0.025
	woff = (wc[2]-wc[0])*0.025
	nwc  = (wc[0]-woff, wc[1]-hoff, wc[2]+woff, wc[3]+hoff)

	wa = float(nwc[3]-nwc[1])/float(nwc[2]-nwc[0]) # New window aspect ratio
	sa = float(sc[3]-sc[1])/float(sc[2]-sc[0]) # Screen aspect ratio
	r = sa/wa

	if wa < sa: # Enlarge window height to get the right AR - keep it centered vertically
		yoff = (nwc[3]-nwc[1])*(r-1)/2
		return (nwc[0], nwc[1]-yoff, nwc[2], nwc[3]+yoff)
	elif wa > sa: # Enlarge window width to get the right AR - keep it centered horizontally
		xoff = (nwc[2]-nwc[0])*(1/r-1)/2
		return (nwc[0]-xoff, nwc[1], nwc[2]+xoff, nwc[3])

	return wc

# Equalize and colorize attractor
# attractor: attractor points: dict (X,Y) and containing frequency
# Returns the attractor points: dict indexed by (X, Y) and containing COLOR, 
def postprocessAttractor(attractor):
	M = 0
	for v in attractor.values():
		M = max(M, v)

	# Now send the map in the [0, (1<<INTERNAL_BPC)-1] range
	for i, pt in attractor.iteritems():
		attractor[i] = int (pt * ((1<<INTERNAL_BPC)-1)/M)

	# Equalize the attractor (histogram equalization)
	equalizeAttractor(attractor)

	# Subsample here
	attractor = subsampleAttractor(attractor)

	# Colorize attractor
	colorizeAttractor(attractor)

	return attractor

# Creates the final image array
def createImageArray(p, sc, background):
	w = int ((sc[2]-sc[0])/args.subsample)
	h = int ((sc[3]-sc[1])/args.subsample)

	a = background*w*h

	shift = INTERNAL_BPC-args.bpc

	for c, v in p.iteritems():
		offset = c[0] + c[1]*w
		if args.render == "greyscale":
			a[offset] = v >> shift
		else:
			a[3*offset:3*offset+3] = [x >> shift for x in v]

	return a

# Performs histogram equalization on the attractor pixels
def equalizeAttractor(p):
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
def colorizeAttractor(a):
	if args.render == "greyscale":
		return

	hues = { 'red': 0.0, 'yellow': 1.0/6, 'green': 2.0/6, 'cyan': 3.0/6, 'blue': 4.0/6, 'magenta':5.0/6 }
	hue = hues.keys()[random.randint(0, len(hues.keys())-1)]
	# logging.debug("Rendering attractor in %s." % (hue))
	h = hues[hue]

	pools=dict()
	for v in a.values():
		if v in pools: continue
		else: pools[v] = 1

	ncolors = len(pools.keys())
	logging.debug("%d points in attractor. %d unique %d-bpc colors in attractor. Coloring ratio: %1.2f%%." % (len(a.keys()), ncolors, INTERNAL_BPC, float(len(pools.keys()))/len(a.keys())*100))

	colormap = dict()

	# We want to create a gradient between orangish and yellowish, with a unique color mapping.
	for color in pools.keys():
		hh = 1.0/12 + float(color)*(1.0/8 - 1.0/12)/((1<<INTERNAL_BPC)-1)
		vv = 0.75 + 0.25*float(color)/((1<<INTERNAL_BPC)-1)
		hsv = (hh, 0.3, vv)
		colormap[color] = [int(((1<<INTERNAL_BPC)-1)*component) for component in colorsys.hsv_to_rgb(*hsv)]


	shift = INTERNAL_BPC - args.bpc
	dt = dict()
	for k in sorted(colormap.keys()):
		dt[k>>shift] = True
	logging.debug("%d unique %d-bpc greyscale." % (len(dt.keys()), args.bpc))

	dt = dict()
	for k in sorted(colormap.keys()):
		dt[tuple([v >> shift for v in colormap[k]])] = True
	logging.debug("%d unique %d-bpc color." % (len(dt.keys()), args.bpc))

	for v in a:
		a[v] = colormap[a[v]]

def subsampleAttractor(at):

	if args.subsample == 1: return at

	nat = dict()

	for pt, color in at.iteritems():
		xsub = int(pt[0]/args.subsample)
		ysub = int(pt[1]/args.subsample)
		if (xsub,ysub) in nat: # We already subsampled this square
			continue
		n = 0
		c = 0
		x0 = xsub*args.subsample
		y0 = ysub*args.subsample
		for x in range(x0, x0+args.subsample):
			for y in range(y0, y0+args.subsample):
				if (x, y) in at:
					n += 1
					c += at[(x, y)]
		# OK now we have accumulated all colors in the attractors
		# Time to weight with the background color
		v = 0xFFFF*(args.subsample*args.subsample-n)
		c += v
		c = int(c/(args.subsample*args.subsample))
		nat[(xsub,ysub)] = c

	return nat

def renderAttractor(a, screen_c):
	backgroundColor = [0xFF] if args.render == "greyscale" else [0xFF, 0xFF, 0xFF]
	p = postprocessAttractor(a)
	i = createImageArray(p, screen_c, backgroundColor)
	return i

def mergeAttractors(a):
	v = a[0]
	for vv in a[1:]:
		if vv == None: continue
		for k, e in vv.iteritems():
			if k in v:
				v[k] += e
			else:
				v[k] = e
	logging.debug("%d points in the attractor before any dithering done." % (len(v.keys())))
	return v

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

def walkthroughAttractor(at, screen_c):
	jobs = list()
	initPoints = getInitPoints(at, args.threads)
	logging.debug("Found converging attractor. Now computing it.")
	logging.debug("Attractor boundaries: %s" % (str(at.bound)))
	window_c = scaleBounds(at.bound, screen_c)

	manager = Manager()
	a = manager.list([None]*args.threads)
	for i in range(args.threads):
		job = Process(group=None, name='t'+str(i), target=at.iterateMap, args=(screen_c, window_c, a, i, initPoints[i]))
		jobs.append(job)
		job.start()

	for job in jobs:
		job.join()

	aMerge = mergeAttractors(a)
	if not aMerge: return aMerge
	at.computeFractalDimension(aMerge, screen_c, window_c)

	logging.debug("Time to render the attractor.")
	return renderAttractor(aMerge, screen_c)

def sec2hms(seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	return "%dh%02dm%02ds" % (h, m, s)

def writeAttractor(a, filepath):
	logging.debug("Now writing attractor %s on disk." % filepath)
	w = png.Writer(size=(int(g[0]), int(g[1])), greyscale = True if args.render == "greyscale" else False, bitdepth=args.bpc, interlace=True)
	aa = w.array_scanlines(a)
	with open(filepath, "wb") as f:
		w.write(f, aa)

def generateAttractorSequence():
	attractorStart = createAttractor()
	attractorEnd   = createAttractor()
	bounds   = attractorStart.bound
	coefList = list()
	coefList.append([ x[:] for x in attractorStart.coef ])
	numAttractors = 1

	for n in range(args.sequence):
		currentCoef = [[xx + float(yy-xx)*n/args.sequence for xx,yy in zip(x, y)] for x,y in zip(coefList[0], attractorEnd.coef)]

		# Use attractorStart as temp storage !
		attractor = attractorStart
		attractor.coef = currentCoef
		attractor.bound = None
		if attractor.checkConvergence(): # Will also update the attractor bounds
			coefList.append(attractorStart.coef)
			bounds = (min(bounds[0], attractor.bound[0]), min(bounds[1], attractor.bound[1]), max(bounds[2], attractor.bound[2]), max(bounds[3], attractor.bound[3]))
			numAttractors += 1

	logging.info("Sequence generated. %d converging attractors in sequence. Attractors bounding box: %s." % (numAttractors, str(bounds)))

	for i, c in enumerate(coefList):
		attractor.coef = c
		attractor.bound = bounds
		a = walkthroughAttractor(attractor, screen_c)
		if not a : continue
		path = os.path.join(args.outdir, attractor.code + "_" + "%04d" % i + ".png")
		writeAttractor(a, path)

def createAttractor():
	if args.type == 'polynomial':
		at = PolynomialAttractor(**{'order': args.order,
	                'iter' : int(args.iter/args.threads),
	                'code' : args.code })
	else:
		at = DeJongAttractor(**{'iter' : int(args.iter/args.threads),
	                'code' : args.code })

	if args.code:
		if not at.checkConvergence():
			logging.warning("Not an attractor it seems... but trying to display it anyway.")
	else:
		at.explore()

	return at

def generateAttractor():
	if args.sequence:
		generateAttractorSequence()
		return

	t0 = time()
	at = createAttractor()
	a = walkthroughAttractor(at, screen_c)
	if not a: return
	suffix = str(args.bpc)
	filepath = os.path.join(args.outdir, at.code + "_" + suffix + ".png")
	writeAttractor(a, filepath)
	t1 = time()

	logging.info("Attractor type: %s" % args.type)
	if args.type == 'polynomial':
		logging.info("Polynom order: %d" % int(at.code[1]))
	logging.info("Dimension: %.3f" % at.fdim)
	logging.info("Lyapunov exponent: %.3f" % at.lyapunov['ly'])
	logging.info("Code: %s" % at.code)
	logging.info("Iterations: %d" % args.iter)
	logging.info("Attractor generation and rendering took %s." % sec2hms(t1-t0))

	if args.display_at:
		p = at.humanReadable(True)
		print at, at.fdim, at.lyapunov['ly'], args.iter, p[0], p[1]

def parseArgs():
	parser = argparse.ArgumentParser(description='Playing with strange attractors')
	parser.add_argument('-b', '--bpc',          help='bits per component (default = %d)' % defaultParameters['bpc'], default=defaultParameters['bpc'], type=int, choices=(8, 16))
	parser.add_argument('-c', '--code',         help='attractor code')
	parser.add_argument('-g', '--geometry',     help='image geometry (XxY form - default = %s)' % defaultParameters['geometry'], default=defaultParameters['geometry'])
	parser.add_argument('-H', '--display_at',   help='Output parameters for post processing', action='store_true', default=False)
	parser.add_argument('-j', '--threads',      help='Number of threads to use (default=%d)' % defaultParameters['threads'], type=int, default=defaultParameters['threads'])
	parser.add_argument('-l', '--loglevel',     help='Sets log level (default %d)' % defaultParameters['loglevel'], default=defaultParameters['loglevel'], type=int, choices=range(0,len(LOGLEVELS)))
	parser.add_argument('-i', '--iter',         help='attractor number of iterations', type=int)
	parser.add_argument('-n', '--number',       help='number of attractors to generate (default = %d)' % defaultParameters['number'], default=defaultParameters['number'], type=int)
	parser.add_argument('-o', '--order',        help='attractor order (default = %d)' % defaultParameters['order'], default=defaultParameters['order'], type=int)
	parser.add_argument('-O', '--outdir',       help='output directory for generated image (default = %s)' % defaultParameters['outdir'], default=defaultParameters['outdir'], type=str)
	parser.add_argument('-q', '--sequence',     help='generate a sequence of attractors', type=int)
	parser.add_argument('-r', '--render',       help='rendering mode (greyscale, color)', default = "color", type=str, choices=("greyscale", "color"))
	parser.add_argument('-s', '--subsample',    help='subsampling rate (default = %d)' % defaultParameters['sub'], default = defaultParameters['sub'], type=int, choices=(2, 3))
	parser.add_argument('-t', '--type',         help='attractor type (default = %s)' % defaultParameters['type'], default = defaultParameters['type'], type=str, choices=("polynomial", "dejong"))
	args = parser.parse_args()
	return args

# ----------------------------- Main loop ----------------------------- #

args = parseArgs()
logging.basicConfig(stream=sys.stderr, level=LOGLEVELS[args.loglevel])
random.seed()

g = args.geometry.split('x')
pxSize = args.subsample*args.subsample*int(g[0])*int(g[1])

idealIter = int(OVERITERATE_FACTOR*pxSize)
if args.type == 'dejong':
	idealIter *= 2
if args.iter == None:
	args.iter = idealIter
	logging.debug("Setting iteration number to %d." % (args.iter))
if args.iter < idealIter:
	logging.warning("For better rendering, you should use at least %d iterations." % idealIter)

screen_c = [0, 0] + [args.subsample*int(x) for x in g]

if args.code: args.number = 1

for i in range(0, args.number):
	generateAttractor()
