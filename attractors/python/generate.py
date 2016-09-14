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

from attractor import attractor, render
import random
import argparse
import sys
import os
import logging
from time import time

try:
    import png
except:
    print >> sys.stderr, "this program requires the pyPNG module"
    print >> sys.stderr, "available at https://github.com/drj11/pypng"
    raise SystemExit

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

	logging.debug("Converging attractor found. Boundaries: %s" % (str(at.bound)))

	return at

def generateAttractorSequence(r):
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
		a = r.walkthroughAttractor(attractorStart)
		if not a : continue
		path = os.path.join(args.outdir, attractorStart.code + "_" + "%04d" % i + ".png")
		writeAttractor(a, path)

def generateAttractor(screenDim):
	r  = render.Renderer(**{'bpc' : args.bpc,
			'mode' : args.render,
			'screenDim' : screenDim,
			'subsample' : args.subsample,
			'threads': args.threads})

	if args.sequence:
		generateAttractorSequence(r)
		return

	t0 = time()
	at = createAttractor()
	a = r.walkthroughAttractor(at)
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

if args.code or args.sequence: args.number = 1

for i in xrange(0, args.number):
	generateAttractor([int(x) for x in g])
