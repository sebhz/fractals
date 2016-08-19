#!/usr/bin/python

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

try:
    import png
except:
    print >> sys.stderr, "this program requires the pyPNG module"
    print >> sys.stderr, "available at https://github.com/drj11/pypng"
    raise SystemExit

INTERNAL_BPC=16
OVERITERATE_FACTOR=4

defaultParameters = {
	'sub': 1,
	'bpc': 8,
	'dim': 2,
	'depth': 5,
	'geometry': "1280x1024",
	'number': 1,
	'order': 2,
	'outdir': "png",
	'loglevel':4
}

class log(object):
	LOG_VERBOSE=4
	LOG_DEBUG=3
	LOG_INFO=2
	LOG_WARNING=1
	LOG_ERROR=0

	def __init__(self, logLevel=4):
		if logLevel < self.LOG_ERROR: logLevel = self.LOG_ERROR
		if logLevel > self.LOG_VERBOSE: logLevel = self.LOG_VERBOSE
		self.logLevel = logLevel

	def v(self, string):
		if self.logLevel < self.LOG_VERBOSE: return
		print >> sys.stderr, string

	def d(self, string):
		if self.logLevel < self.LOG_DEBUG: return
		print >> sys.stderr, string

	def i(self, string):
		if self.logLevel < self.LOG_INFO: return
		print >> sys.stderr, string

	def w(self, string):
		if self.logLevel < self.LOG_WARNING: return
		print >> sys.stderr, string

	def e(self, string):
		if self.logLevel < self.LOG_ERROR: return
		print >> sys.stderr, string

class polynom(object):
	def __init__(self, a):
		self.a = a

	def derive(self):
		b = [i*c for i, c in enumerate(self.a)]
		return polynom(b[1:])

	def __call__(self, x):
		result = 0
		for c in reversed(self.a):
			result = result*x + c
		return result

	def __str__(self):
		return self.a.__str__()

class polynomialAttractor(object):

	convDelay    = 128   # Number of points to ignore before checking convergence
	convMaxIter  = 16384 # Check convergence on convMaxIter points only
	initVal      = 0.1   # Starting coordinate to use to check convergence
	codelist     = range(48,58) + range(65,91) + range(97,123) # ASCII values for code
	codeStep     = .125 # Step to use to map ASCII character to coef

	def __init__(self, *opt):
		if opt:
			self.opt = opt[0]
		else:
			self.opt = dict()

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None

		# Parameters not in the code first
		if not 'init' in self.opt:
			self.init = [self.initVal]*self.opt['dim']

		if not 'iter' in self.opt:
			self.opt['iter'] = defaultParameters['iter']

		# Then derive other parameters from code if a code is supplied
		if 'code' in self.opt and self.opt['code']:
			self.code = self.opt['code']
			self.decodeCode()
			return

		# If no code supplied parse options and derive the parameters from there
		if not 'dim' in self.opt:
			self.opt['dim'] = defaultParameters['dim']

		if not 'depth' in self.opt:
			self.opt['depth'] = defaultParameters['depth']

		if 'order' in self.opt:
			self.order = self.opt['order']
		else:
			self.order = defaultParameters['order'] # Quadratic by default

		if not 'coef' in self.opt:
			self.coef   = None
			self.derive = None
			self.code   = None
			self.getPolynomLength()
		else:
			self.coef   = self.opt['coef']
			self.derive = polynom(self.coef[0]).derive()
			self.code   = self.createCode()
			self.pl     = len(self.coef[0])
			# TODO: override order here, or throw an error if not coherent

	def __str__(self):
		return self.code

	# Project point on screen coordinate
	# its parent x coordinate
	# sc: screen bound (0,0,800,600)
	# wc: attractor bound (x0,y0,x1,y1)
	# p: point in the attractor (x, y, xfather)
	# Returns a tuple (x, y)
	def w_to_s(self, wc, sc, p):
		x, y = p

		if x < wc[0] or x > wc[2] or y < wc[1] or y > wc[3]:
			return None

		return ( (int(sc[0] + (x-wc[0])/(wc[2]-wc[0])*(sc[2]-sc[0])),
				  int(sc[1] + (sc[3]-sc[1])-(y-wc[1])/(wc[3]-wc[1])*(sc[3]-sc[1])),) )

	def decodeCode(self):
		self.opt['dim'] = int(self.code[0])
		self.order = int(self.code[1])
		if self.opt['dim'] == 1: self.opt['depth'] = int(self.code[2])
		self.getPolynomLength()

		d = dict([(self.codelist[i], i) for i in range(0, len(self.codelist))])
		self.coef = [[(d[ord(_)]-30)*self.codeStep for _ in self.code[3+__*self.pl:3+(__+1)*self.pl]] for __ in range(self.opt['dim'])]
		self.derive = polynom(self.coef[0]).derive()

	def createCode(self):
		self.code = str(self.opt['dim'])+str(self.order)
		if self.opt['dim'] == 1:
			 self.code += str(self.opt['depth'])
		else:
			self.code += "_"
		# ASCII codes of digits and letters
		c = [self.codelist[int(x/self.codeStep)+30] for c in self.coef for x in c]
		self.code +="".join(map(chr,c))

	# Outputs a human readable string of the polynom. If isHTML is True
	# outputs an HTML blurb of the equation. Else output a plain text.
	def humanReadablePolynom(self, isHTML):
		variables = ('x', 'y', 'z') # Limit ourselves to 3 dimensions for now
		equation = [""]*self.opt['dim']
		for v, c in enumerate(self.coef): # Iterate on each dimension
			n = 0
			equation[v] = variables[v]+"="
			for i in range(self.order+1):
				if self.opt['dim'] == 1:
					if c[n] == 0:
						n+=1
						continue
					equation[v] += "%.3f*%s^%d+" % (c[n], variables[0], i)
					n+=1
					continue
				for j in range(self.order-i+1):
					if self.opt['dim'] == 2:
						if c[n] == 0:
							n+=1
							continue
						equation[v] += "%.3f*%s^%d*%s^%d+" % (c[n], variables[0], j, variables[1], i)
						n += 1
						continue
						for k in range(self.order-i-j+1):
							if self.opt['dim'] == 3:
								if c[n] == 0:
									n+=1
									continue
								equation[v] += "%.3f*%s^%d*%s^%d*%s^d+" % (c[n], variables[0], k, variables[1], j, variables[2], i)
								n += 1
			# Some cleanup
			for r in variables:
				equation[v] = equation[v].replace("*%s^0" % (r), "")
				equation[v] = equation[v].replace("*%s^1" % (r), "*%s" % (r))
			equation[v] = equation[v].replace("+-", "-")
			equation[v] = equation[v][:-1]

			if isHTML: # Convert this in a nice HTML equation
				equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])

		return equation

	def getPolynomLength(self):
		self.pl = math.factorial(self.order+self.opt['dim'])/(
				  math.factorial(self.order)*math.factorial(self.opt['dim']))

	def getRandom(self):
		self.coef = [[random.randint(-30, 31)*self.codeStep for _ in range(0, self.pl)] for __ in range(self.opt['dim'])]
		if self.opt['dim'] == 1: self.derive = polynom(self.coef[0]).derive()

	def evalCoef(self, p):
		l = list()
		try:
			for c in self.coef:
				result = 0
				n = 0
				for i in range(self.order+1):
					for j in range(self.order-i+1):
						if self.opt['dim'] == 2:
							result += c[n]*(p[0]**j)*(p[1]**i)
							n += 1
				l.append(result)
		except OverflowError:
			Log.e("Overflow during attractor computation.")
			Log.e("Either this is a very slowly diverging attractor, or you used a wrong code")
			return None

		# Append the x father as extra coordinate, for colorization
		# l.append(p[0])
		return l

	def computeLyapunov(self, p, pe):
		if self.opt['dim'] == 1:
			df = abs(self.derive(p[0]))
			if df == 0:
				Log.w("Unable to compute Lyapunov exponent, but trying to go on...")
				return pe
		else:
			p2   = self.evalCoef(pe)
			if not p2: return pe
			dl   = [d-x for d,x in zip(p2, p)]
			dl2  = reduce(lambda x,y: x*x + y*y, dl)
			if dl2 == 0:
				Log.w("Unable to compute Lyapunov exponent, but trying to go on...")
				return pe
			df = 1000000000000*dl2
			rs = 1/math.sqrt(df)

		self.lyapunov['lsum'] += math.log(df, 2)
		self.lyapunov['nl']   += 1
		self.lyapunov['ly'] = self.lyapunov['lsum'] / self.lyapunov['nl']
		if self.opt['dim'] != 1:
			return [p[i]-rs*x for i,x in enumerate(dl)]

	def checkConvergence(self):
		self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
		pmin, pmax = ([1000000]*self.opt['dim'], [-1000000]*self.opt['dim'])
		p = self.init
		pe = [x + 0.000001 if i==0 else x for i,x in enumerate(p)]
		modulus = lambda x, y: abs(x) + abs(y)

		for i in range(self.convMaxIter):
			if self.opt['dim'] == 1:
				pnew = [polynom(self.coef[0])(p[0])]
			else:
				pnew = self.evalCoef(p)
				if not pnew: return False
			if reduce(modulus, pnew, 0) > 1000000: # Unbounded - not an SA
				return False
			if reduce(modulus, [pn-pc for pn, pc in zip(pnew, p)], 0) < 0.00000001:
				return False
			# Compute Lyapunov exponent... sort of
			pe = self.computeLyapunov(pnew, pe)
			if self.lyapunov['ly'] < 0.005 and i > self.convDelay: # Limit cycle
				return False
			if i > self.convDelay:
				pmin = [min(pn, pm) for pn, pm in zip(pnew, pmin)]
				pmax = [max(pn, pm) for pn, pm in zip(pnew, pmax)]
			p = pnew

		self.bound = (pmin, pmax)
		return True

	def explore(self):
		n = 0;
		self.getRandom()
		while not self.checkConvergence():
			n += 1
			self.getRandom()
		# Found one -> create corresponding code
		self.createCode()

	def iterateMap(self, screen_c, window_c):
		a = dict()
		p = self.init
		if self.opt['dim'] == 1:
			prev = self.opt['depth']
			mem  = [p]*prev

		for i in range(self.opt['iter']):
			if self.opt['dim'] == 1:
				pnew = [polynom(self.coef[0])(p[0])]
			else:
				pnew = self.evalCoef(p)
				if not pnew: return None

			# Ignore the first points to get a proper convergence
			if i >= self.convDelay:
				projectedPixel = None
				if self.opt['dim'] == 1:
					if i >= prev:
						projectedPixel = self.w_to_s(window_c, screen_c,(mem[(i-prev)%prev][0], pnew[0]))
				else:
					projectedPixel = self.w_to_s(window_c, screen_c, pnew)

				if projectedPixel and projectedPixel in a:
					a[projectedPixel] += 1
				else:
					a[projectedPixel] = 0

			if self.opt['dim'] == 1: mem[i%prev] = pnew
			p = pnew

		self.computeDimension(a, screen_c, window_c)
		return a

	# An estimate of the Minkowski-Bouligand dimension (a.k.a box-counting)
	# See https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension
	def computeDimension(self, a, screen_c, window_c):
		if not self.bound: return None

		sideLength = 2 # Box side length, in pixels
		pixelSize = (window_c[2]-window_c[0])/(screen_c[2]-screen_c[0])

		boxes = dict()
		for pt in a.keys():
			boxCoordinates = (int(pt[0]/sideLength), int(pt[1]/sideLength))
			boxes[boxCoordinates] = True
		n = len(boxes.keys())

		self.fdim = math.log(n)/math.log(1/(sideLength*pixelSize))


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

# Project bounds to screen... do we really need this anymore ?
def projectBounds(at):
	if at.opt['dim'] == 1:
		return (at.bound[0][0], at.bound[0][0], at.bound[1][0], at.bound[1][0])
	elif at.opt['dim'] == 2:
		return (at.bound[0][0], at.bound[0][1], at.bound[1][0], at.bound[1][1])

# Performs histogram equalization on the attractor pixels
def equalizeAttractor(p):
	pools = [0]*(1<<INTERNAL_BPC)

	# Create cumulative distribution
	for v in p.itervalues():
		pools[v] += 1
	for i in range(len(pools) - 1):
		pools[i+1] = pools[i+1] + pools[i]

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
	Log.v("Rendering attractor in %s." % (hue))
	h = hues[hue]

	pools=dict()
	for v in a.values():
		if v in pools: continue
		else: pools[v] = 1

	ncolors = len(pools.keys())
	Log.d("%d points in attractor. %d unique %d-bpc colors in attractor. Coloring ratio: %1.2f%%." % (len(a.keys()), ncolors, INTERNAL_BPC, float(len(pools.keys()))/len(a.keys())*100))

	colormap = dict()

	# Convert greyscale to a color, by choosing a hue and mapping greyscale directly on value 
	for color in pools.keys():
		hsv = list()
		hsv = (h, 0.3, float(color)/((1<<INTERNAL_BPC)-1))
		colormap[color] = [int(((1<<INTERNAL_BPC)-1)*component) for component in colorsys.hsv_to_rgb(*hsv)]


	shift = INTERNAL_BPC - args.bpc
	dt = dict()
	for k in sorted(colormap.keys()):
		dt[k>>shift] = True
	Log.d("%d unique %d-bpc greyscale." % (len(dt.keys()), args.bpc))

	dt = dict()
	for k in sorted(colormap.keys()):
		dt[tuple([v >> shift for v in colormap[k]])] = True
	Log.d("%d unique %d-bpc color." % (len(dt.keys()), args.bpc))

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

def walkthroughAttractor(at, screen_c):
	Log.v("Found converging attractor. Now computing it.")

	b = projectBounds(at)
	window_c = scaleBounds(b, screen_c)

	a = at.iterateMap(screen_c, window_c)
	if not a: return a

	if args.display_at:
		p = at.humanReadablePolynom(True)
		print at, at.fdim, at.lyapunov['ly'], args.iter, p[0], "" if args.dimension < 2 else p[1]

	Log.v("Time to render the attractor.")
	return renderAttractor(a, screen_c)


def parseArgs():
	parser = argparse.ArgumentParser(description='Playing with strange attractors')
	parser.add_argument('-b', '--bpc',          help='bits per component (default = %d)' % defaultParameters['bpc'], default=defaultParameters['bpc'], type=int, choices=(8, 16))
	parser.add_argument('-c', '--code',         help='attractor code')
	parser.add_argument('-d', '--dimension',    help='attractor dimension (defaut = %d)' % defaultParameters['dim'], default=defaultParameters['dim'], type=int, choices=range(1,3))
	parser.add_argument('-D', '--depth',        help='attractor depth (for 1D only - default = %d)' % defaultParameters['depth'], default=defaultParameters['depth'], type=int)
	parser.add_argument('-g', '--geometry',     help='image geometry (XxY form - default = %s)' % defaultParameters['geometry'], default=defaultParameters['geometry'])
	parser.add_argument('-H', '--display_at',   help='Output parameters for post processing', action='store_true', default=False)
	parser.add_argument('-l', '--loglevel',     help='Sets log level (default %d)' % defaultParameters['loglevel'], default=defaultParameters['loglevel'], type=int, choices=range(0,5))
	parser.add_argument('-i', '--iter',         help='attractor number of iterations', type=int)
	parser.add_argument('-n', '--number',       help='number of attractors to generate (default = %d)' % defaultParameters['number'], default=defaultParameters['number'], type=int)
	parser.add_argument('-o', '--order',        help='attractor order (default = %d)' % defaultParameters['order'], default=defaultParameters['order'], type=int)
	parser.add_argument('-O', '--outdir',       help='output directory for generated image (default = %s)' % defaultParameters['outdir'], default=defaultParameters['outdir'], type=str)
	parser.add_argument('-r', '--render',       help='rendering mode (greyscale, color)', default = "color", type=str, choices=("greyscale", "color"))
	parser.add_argument('-s', '--subsample',    help='subsampling rate (default  = %d)' % defaultParameters['sub'], default = defaultParameters['sub'], type=int, choices=(2, 3))
	args = parser.parse_args()
	return args

# ----------------------------- Main loop ----------------------------- #
args = parseArgs()
Log = log(args.loglevel)
random.seed()

g = args.geometry.split('x')
pxSize = args.subsample*args.subsample*int(g[0])*int(g[1])

if args.iter == None:
	args.iter = int(OVERITERATE_FACTOR*pxSize)
	Log.v("Setting iteration number to %d." % (args.iter))
if args.iter < int(OVERITERATE_FACTOR*pxSize):
	Log.w("For better rendering, you should use at least %d iterations." % (pxSize))

screen_c = [0, 0] + [args.subsample*int(x) for x in g]

if args.code: args.number = 1

for i in range(0, args.number):
	at = polynomialAttractor({'dim'  : args.dimension,
	                          'order': args.order,
	                          'iter' : args.iter,
	                          'depth': args.depth,
	                          'code' : args.code })

	if args.code:
		if not at.checkConvergence():
			Log.w("Not an attractor it seems... but trying to display it anyway.")
	else:
		at.explore()

	a = walkthroughAttractor(at, screen_c)
	if not a: continue

	Log.v("Now writing attractor on disk.")
	w = png.Writer(size=(int(g[0]), int(g[1])), greyscale = True if args.render == "greyscale" else False, bitdepth=args.bpc, interlace=True)
	aa = w.array_scanlines(a)
	suffix = str(args.bpc)
	filepath = os.path.join(args.outdir, at.code + "_" + suffix + ".png")
	with open(filepath, "wb") as f:
		w.write(f, aa)

	Log.i("Attractor type: polynomial")
	Log.i("Polynom order: %d" % (int(at.code[1])))
	Log.i("Minkowski-Bouligand dimension: %.3f" % (at.fdim))
	Log.i("Lyapunov exponent: %.3f" % (at.lyapunov['ly']))
	Log.i("Code: %s" % (at.code))
	Log.i("Iterations: %d" % (args.iter))
