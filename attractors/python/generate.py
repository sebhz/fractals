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

import attractor
import random
import argparse
import colorsys
import sys
import os
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
	'loglevel': 3,
	'threads': 1,
	'type': 'polynomial',
}

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
def postprocessAttractor(at):
	M = 0
	for v in at.values():
		M = max(M, v)

	# Now send the map in the [0, (1<<INTERNAL_BPC)-1] range
	for i, pt in at.iteritems():
		at[i] = int (pt * ((1<<INTERNAL_BPC)-1)/M)

	# Equalize the attractor (histogram equalization)
	equalizeAttractor(at)

	# Subsample here
	at = subsampleAttractor(at)

	# Colorize attractor
	colorizeAttractor(at)

	return at

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
	if v == None:
		logging.debug("Empty attractor. Trying to go on anyway.")
	else:
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
	SEQUENCE_STEP = 1024
	numAttractors = 1
	sequenceList = [None]*args.sequence

	attractorStart = createAttractor()
	bounds   = attractorStart.bound

	args.code = None
	for sequence in xrange(args.sequence):
		attractorEnd   = createAttractor()
		logging.info("Generating sequence between %s and %s." % (attractorStart.code, attractorEnd.code))
		sequenceList[sequence] = list()
		sequenceList[sequence].append([ x[:] for x in attractorStart.coef ])

		for n in xrange(1, SEQUENCE_STEP):
			currentCoef = [[xx + float(yy-xx)*n/SEQUENCE_STEP for xx,yy in zip(x, y)] for x,y in zip(sequenceList[sequence][0], attractorEnd.coef)]

			# Use attractorStart as temp storage !
			attractorStart.coef = currentCoef
			attractorStart.bound = None
			if attractorStart.checkConvergence(): # Will also update the attractor bounds
				sequenceList[sequence].append(currentCoef)
				bounds = (min(bounds[0], attractorStart.bound[0]), min(bounds[1], attractorStart.bound[1]), max(bounds[2], attractorStart.bound[2]), max(bounds[3], attractorStart.bound[3]))
				numAttractors += 1
		attractorStart = attractorEnd

		logging.info("Sequence %d generated. %d converging attractors found so far." % (sequence, numAttractors))
		logging.debug("Attractors bounding box: %s." % (str(bounds)))

	coefList = [ coefs for sequence in sequenceList for coefs in sequence ]
	for i, c in enumerate(coefList):
		attractorStart.coef = c
		attractorStart.bound = bounds
		a = walkthroughAttractor(attractorStart, screen_c)
		if not a : continue
		path = os.path.join(args.outdir, attractorStart.code + "_" + "%04d" % i + ".png")
		writeAttractor(a, path)

def createAttractor():
	if args.type == 'polynomial':
		at = attractor.PolynomialAttractor(**{'order': args.order,
	                'iter' : int(args.iter/args.threads),
	                'code' : args.code })
	else:
		at = attractor.DeJongAttractor(**{'iter' : int(args.iter/args.threads),
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
	parser.add_argument('-c', '--code',         help='attractor code', type=str)
	parser.add_argument('-g', '--geometry',     help='image geometry (XxY form - default = %s)' % defaultParameters['geometry'], default=defaultParameters['geometry'])
	parser.add_argument('-H', '--display_at',   help='Output parameters for post processing', action='store_true', default=False)
	parser.add_argument('-j', '--threads',      help='Number of threads to use (default = %d)' % defaultParameters['threads'], type=int, default=defaultParameters['threads'])
	parser.add_argument('-l', '--loglevel',     help='Sets log level (the higher the more verbose - default = %d)' % defaultParameters['loglevel'], default=defaultParameters['loglevel'], type=int, choices=range(len(LOGLEVELS)))
	parser.add_argument('-i', '--iter',         help='attractor number of iterations', type=int)
	parser.add_argument('-n', '--number',       help='number of attractors to generate (default = %d)' % defaultParameters['number'], default=defaultParameters['number'], type=int)
	parser.add_argument('-o', '--order',        help='attractor order (default = %d)' % defaultParameters['order'], default=defaultParameters['order'], type=int)
	parser.add_argument('-O', '--outdir',       help='output directory for generated image (default = %s)' % defaultParameters['outdir'], default=defaultParameters['outdir'], type=str)
	parser.add_argument('-q', '--sequence',     help='generate n following sequences of attractors', type=int)
	parser.add_argument('-r', '--render',       help='rendering mode (greyscale, color)', default = "color", type=str, choices=("greyscale", "color"))
	parser.add_argument('-s', '--subsample',    help='subsampling rate (default = %d)' % defaultParameters['sub'], default = defaultParameters['sub'], type=int, choices=(2, 3))
	parser.add_argument('-t', '--type',         help='attractor type (default = %s)' % defaultParameters['type'], default = defaultParameters['type'], type=str, choices=("polynomial", "dejong"))
	args = parser.parse_args()
	if args.code and args.code[0] == 'j': args.type = 'dejong'
	return args

# ----------------------------- Main loop ----------------------------- #

args = parseArgs()
logging.basicConfig(stream=sys.stderr, level=LOGLEVELS[args.loglevel])
random.seed()

g = args.geometry.split('x')
pxSize = args.subsample*args.subsample*int(g[0])*int(g[1])

idealIter = int(OVERITERATE_FACTOR*pxSize)
if args.type == 'dejong':
	idealIter *= 4
if args.iter == None:
	args.iter = idealIter
	logging.debug("Setting iteration number to %d." % (args.iter))
if args.iter < idealIter:
	logging.warning("For better rendering, you should use at least %d iterations." % idealIter)

screen_c = [0, 0] + [args.subsample*int(x) for x in g]

if args.code: args.number = 1

for i in xrange(0, args.number):
	generateAttractor()
