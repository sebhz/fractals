#!/usr/bin/python

# Generate and colorize various dimension polynomial strange attractors
# Algo taken from Julian Sprott's book: http://sprott.physics.wisc.edu/sa.htm
# Some coloring ideas (histogram equalization, gradient mapping) taken from
# Ian Whitham's blog
# http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/

import random
import math
import argparse
import colorsys

try:
    import png
except:
    print "this program requires the pyPNG module"
    print "available at https://github.com/drj11/pypng"
    raise SystemExit

defaultParameters = {
	'bpc': 8,
	'dim': 2,
	'depth': 5,
	'iter': 65536,
	'geometry': "800x600",
	'number': 16,
	'order': 2
}

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
	dimTransient = 1024  # Ignore the first dimTransient points when computing dimension
	dimDepth     = 500   # Use the dimDepth predecessors of each point to compute the dimension
	dimIgnore    = 20    # but ignore dimIgnore predecessors (presumably too correlated)

	def __init__(self, *opt):
		if opt:
			self.opt = opt[0]
		else:
			self.opt = dict()

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None	# Parameters not in the code first

		if not 'init' in self.opt:
			self.init = [self.initVal]*self.opt['dim']

		if not 'iter' in self.opt:
			self.opt['iter'] = defaultParameters['iter']

	# Then derive other parameters from code if a code is supplied
		if 'code' in self.opt and self.opt['code']:
			self.code = self.opt['code']
			self.decodeCode()
			return

	# If no code supplied parse options qnd derive the parameters from there
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
			self.coef = self.opt['coef']
			self.derive = polynom(self.coef[0]).derive()
			self.code   = self.createCode()
			self.pl     = len(self.coef[0])
			# TODO: override order here, or throw an error if not coherent

	def __str__(self):
		return self.code

	def decodeCode(self):
		self.opt['dim'] = int(self.code[0])
		self.order = int(self.code[1])
		if self.opt['dim'] == 1: self.opt['depth'] = int(self.code[2])
		self.getPolynomLength()

		codelist = range(48,58) + range(65,91) + range(97,123)
		d = dict([(codelist[i], i) for i in range(0, len(codelist))])
		self.coef = [[(d[ord(_)]-30)*.08 for _ in self.code[3+__*self.pl:3+(__+1)*self.pl]] for __ in range(self.opt['dim'])]	
		self.derive = polynom(self.coef[0]).derive()

	def createCode(self):
		self.code = str(self.opt['dim'])+str(self.order)
		if self.opt['dim'] == 1:
			 self.code += str(self.opt['depth'])
		else:
			self.code += "_"
		# ASCII codes of digits and letters
		codelist = range(48,58) + range(65,91) + range(97,123)
		c = [codelist[int(x/0.08+30)] for c in self.coef for x in c]
		self.code +="".join(map(chr,c))

	def getPolynomLength(self):
		self.pl = math.factorial(self.order+self.opt['dim'])/(
				  math.factorial(self.order)*math.factorial(self.opt['dim']))

	def getRandom(self):
		self.coef = [[random.randint(-30, 31)*0.08 for _ in range(0, self.pl)] for __ in range(self.opt['dim'])]
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
						elif self.opt['dim'] == 3:
							for k in range(self.order-i-j+1):
								result += c[n]*(p[0]**k)*(p[1]**j)*(p[2]**i)
								n += 1
				l.append(result)
		except OverflowError:
			print "Overflow during attractor computation."
			print "Either this is a very slowly diverging attractor, or you used a wrong code"
			return None

		# Append the x father as extra coordinate, for colorization
		l.append(p[0])
		return l

	def computeLyapunov(self, p, pe):
		if self.opt['dim'] == 1:
			df = abs(self.derive(p[0]))
		else:
			p2   = self.evalCoef(pe)
			if not p2: return pe
			dl   = [d-x for d,x in zip(p2, p)]
			dl2  = reduce(lambda x,y: x*x + y*y, dl)
			if dl2 == 0:
				print "Unable to compute Lyapunov exponent, but trying to go on..."
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
			p = pnew

		return True

	def explore(self):
		n = 0;
		self.getRandom()
		while not self.checkConvergence():
			n += 1
			self.getRandom()
		# Found one -> create corresponding code
		self.createCode()

	def iterateMap(self):
		l = list()
		p = self.init
		pmin, pmax = ([1000000]*self.opt['dim'], [-1000000]*self.opt['dim'])
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
				if self.opt['dim'] == 1:
					if i >= prev:
						l.append((mem[(i-prev)%prev][0], pnew[0]))
				else:
					l.append(pnew)
				pmin = [min(pn, pm) for pn,pm in zip(pnew, pmin)]
				pmax = [max(pn, pm) for pn,pm in zip(pnew, pmax)]

			if self.opt['dim'] == 1: mem[i%prev] = pnew
			p = pnew

		self.bound = (pmin, pmax)
		self.computeDimension(l)

		return l

	def computeDimension(self, l):
	# An estimate of the correlation dimension: accumulate the values of the distances between
	# point p and one of its predecessors, ignoring the points right before p
		if not self.bound: return None
		if len(l) <= self.dimTransient+self.dimDepth: return None

		n1, n2 = (0, 0)
		twod   = 2**self.opt['dim']
		dist = lambda x,y: x*x+y*y
		d2max = reduce(dist, [mx - mn for mn, mx in zip(*self.bound)], 0)

		for i in range(self.dimTransient + self.dimDepth, len(l)):
			j  = random.randint(i-self.dimDepth, i-self.dimIgnore)
			d2 = reduce(dist, [x-y for x, y in zip(l[i], l[j])])
			if d2 < .001*twod*d2max:
				n2 += 1
			if d2 > .00001*twod*d2max:
				continue
			n1 += 1

		self.fdim = math.log10(n2/n1)

# Project point on windows coordinate, and compute its color based on
# its parent x coordinate
# sc: screen bound (0,0,800,600)
# wc: attractor bound (x0,y0, x1, y1)
# p: point in the attractor (x, y, xfather)
# bounds: bounds of the attractor
# Returns a triplet (x, y, color)
def w_to_s(wc, sc, p, bounds):
	x, y, c = p

	if x < wc[0] or x > wc[2] or y < wc[1] or y > wc[3]:
		return None
	
	# Move c in the [0,1] range
	c = (c-bounds[0])/(bounds[2]-bounds[0])
    
	cc = [int((1<<(args.bpc-3)-1)*z) for z in colorsys.hsv_to_rgb(c, 0.8, 1.0)]

	return ( int(sc[0] + (x-wc[0])/(wc[2]-wc[0])*(sc[2]-sc[0])), 
			 int(sc[1] + (sc[3]-sc[1])- (y-wc[1])/(wc[3]-wc[1])*(sc[3]-sc[1])),
			 cc)

# Enlarge window_c so that it has the same aspect ratio as screen_c 
# sc: screen bound e.g. (0,0,800,600)
# wc: attractor bound (x0,y0, x1, y1)
def scaleRatio(wc, sc):
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

def projectPoint(pt, dim, *direction):
	return (pt[0], pt[1], pt[dim]) # Ignore Z for now

# Creates an image array and fill it with an array of RGB values
# sc: screen bound e.g. (0,0,800,600)
# wc: window containing attractor bound (x0,y0, x1, y1)
# l : attractor points (list of x, y, [z], x_parent)
# bounds: attractor bounds (xx0, yy0, xx1, yy1)
def createImageArray(wc, sc, l, dim, bounds):
	w = sc[2]-sc[0]
	h = sc[3]-sc[1]
	size = w*h*3

	# Black pixels in all the window
	cv = [0]*size

	lc = [w_to_s(wc, sc, projectPoint(pt, dim), bounds) for pt in l]
	
	for pt in lc:
		offset = 3*(pt[1]*w + pt[0])
		for o in range(3):
			cv[offset+o] += pt[2][o]
			if cv[offset+o] >= (1 << args.bpc): cv[offset+o] = (1 << args.bpc) - 1
 
	return cv

def projectBound(at):
	if at.opt['dim'] == 1:
		return (at.bound[0][0], at.bound[0][0], at.bound[1][0], at.bound[1][0])
	elif at.opt['dim'] == 2:
		return (at.bound[0][0], at.bound[0][1], at.bound[1][0], at.bound[1][1])
	elif at.opt['dim'] == 3: # For now, ignore the Z part
		return (at.bound[0][0], at.bound[0][1], at.bound[1][0], at.bound[1][1])

def renderAttractor(at, l, screen_c):
	b = projectBound(at)
	window_c = scaleRatio(b, screen_c)
	a = createImageArray(window_c, screen_c, l, at.opt['dim'], b)
	return a

def parseArgs():
	parser = argparse.ArgumentParser(description='Playing with strange attractors')
	parser.add_argument('-b', '--bpc', help='bits per component (default = %d)' % defaultParameters['bpc'], default=defaultParameters['bpc'], type=int, choices=(8, 16))
	parser.add_argument('-c', '--code', help='attractor code')
	parser.add_argument('-d', '--dimension', help='attractor dimension (defaut = %d)' % defaultParameters['dim'], default=defaultParameters['dim'], type=int, choices=range(1,4))
	parser.add_argument('-D', '--depth',     help='attractor depth (for 1D only - default = %d)' % defaultParameters['depth'], default=defaultParameters['depth'], type=int)
	parser.add_argument('-g', '--geometry',  help='image geometry (XxY form - default = %s)' % defaultParameters['geometry'], default=defaultParameters['geometry'])
	parser.add_argument('-i', '--iter',      help='attractor number of iterations (default = %d)' % defaultParameters['iter'], default=defaultParameters['iter'], type=int)
	parser.add_argument('-n', '--number',    help='number of attractors to generate (default = %d)' % defaultParameters['number'], default=defaultParameters['number'], type=int)
	parser.add_argument('-o', '--order',     help='attractor order (default = %d)' % defaultParameters['order'], default=defaultParameters['order'], type=int)
	parser.add_argument('-q', '--quiet',     help='shut up !', action='store_true', default=False)
	args = parser.parse_args()
	return args

# ----------------------------- Main loop ----------------------------- #
args = parseArgs()
g = args.geometry.split('x')
screen_c = [0, 0] + [int(x) for x in g]

random.seed()
n = 0
while True: # args.number = 0 -> infinite loop
	at = polynomialAttractor({'dim':args.dimension,
                              'order':args.order,
							  'iter':args.iter,
							  'depth': args.depth,
							  'code' : args.code })
	if args.code:
		if not at.checkConvergence():
			print "Not an  attractor it seems... but trying to display it anyway."
	else:
		at.explore()
	l = at.iterateMap()
	if not l:
		n += 1
		if n == args.number or args.code: break
		continue
	if not args.quiet: print at, at.lyapunov['ly']
	a = renderAttractor(at, l, screen_c)
	w = png.Writer(size=(int(g[0]), int(g[1])), bitdepth=args.bpc)
	aa = w.array_scanlines(a)
	f = open("png/" + at.code + "_" + str(args.bpc) + ".png", "wb")
	w.write(f, aa)
	n += 1
	if n == args.number or args.code: break
