#!/usr/bin/python

# Generate and colorize various dimension strange attractors
# Algo taken from Julian Sprott's book: http://sprott.physics.wisc.edu/sa.htm
# Some coloring ideas (histogram equalization, gradient mapping) taken from
# Ian Whitham's blog
# http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/

import random
import math
import argparse

try:
    import Image
except:
    print "this program requires the PIL module"
    print "available at http://www.pythonware.com/library/pil"
    raise SystemExit

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
	def __init__(self, *opt):
		if opt:
			self.opt = opt[0]
		else:
			self.opt = dict()

		if not 'init' in self.opt:
			self.init = [0.1]*self.opt['dim']

		if not 'iter' in self.opt:
			self.opt['iter'] = 4096

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None

		if 'code' in self.opt and self.opt['code']:
			self.code = self.opt['code']
			self.decodeCode()
			return

		if not 'dim' in self.opt:
			self.opt['dim'] = 2
		
		if not 'depth' in self.opt:
			self.opt['depth'] = 5

		if 'order' in self.opt:
			self.order = self.opt['order']
		else:
			self.order = 2 # Quadratic by default

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
			# Need to override order here, or throw an error if not coherent

	def __str__(self):
		st = ""
		for p in self.coef:
			st += "coef: " + p.__str__() + "\n"
		st += "code: " + self.code + "\n"
		st += "Lyapunov exponent: " + str(self.lyapunov['ly']) + "\n"
		st += "Correlation dimension: " + str(self.fdim) + "\n"
		st += "Computed on " + str(self.opt['iter']) +  " points."
		return st

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
							n = n + 1
						elif self.opt['dim'] == 3:
							for k in range(self.order-i-j+1):
								result += c[n]*(p[0]**k)*(p[1]**j)*(p[2]**i)
								n = n + 1
				l.append(result)
		except OverflowError:
			print "Overflow during attractor computation."
			print "Either this is a very slowly diverging attractor, or you used a wrong code"
			return None

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

		# 16384 iterations should be more than enough to check for convergence !
		for i in range(16384):
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
			if self.lyapunov['ly'] < 0.005 and i > 128: # Limit cycle
				return False
			p = pnew

		return True

	def explore(self):
		n = 0;
		self.getRandom()
		while not self.checkConvergence():
			n = n + 1
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

			# Ignore the first 128 points to get a proper convergence
			if i >= 128:
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
	# point p and one of its 480 predecessors, ignoring the 20 points right before p
		if not self.bound: return None
		if len(l) <= 1024: return None

		n1, n2 = (0, 0)
		twod   = 2**self.opt['dim']
		dist = lambda x,y: x*x+y*y
		d2max = reduce(dist, [mx - mn for mn, mx in zip(*self.bound)], 0)

		for i in range(1524, len(l)): # Give 1024 iterations to avoid transients
			j  = random.randint(i-500, i-20) # Ignore 20 previous points (presumably highly correlated)
			d2 = reduce(dist, [x-y for x, y in zip(l[i], l[j])])
			if d2 < .001*twod*d2max:
				n2 += 1
			if d2 > .00001*twod*d2max:
				continue
			n1 += 1

		self.fdim = math.log10(n2/n1)

def w_to_s(wc, sc, p):
	x, y = p

	if x < wc[0] or x > wc[2] or y < wc[1] or y > wc[3]:
		return None
	
	return ( int(sc[0] + (x-wc[0])/(wc[2]-wc[0])*(sc[2]-sc[0])), 
			 int(sc[1] + (sc[3]-sc[1])- (y-wc[1])/(wc[3]-wc[1])*(sc[3]-sc[1])) )

# Enlarge window_c so that it has the same aspect ratio as screen_c 
def scaleRatio(wc, sc):
	# Enlarge window by 5% in both directions
	hoff = (wc[3]-wc[1])*0.025
	woff = (wc[2]-wc[0])*0.025
	nwc  = (wc[0]-woff, wc[1]-hoff, wc[2]+woff, wc[3]+hoff)
	
	wa = float(nwc[3]-nwc[1])/float(nwc[2]-nwc[0]) #New window aspect ratio
	sa = float(sc[3]-sc[1])/float(sc[2]-sc[0]) # Screen aspect ratio
	r = sa/wa
	
	if wa < sa: # Enlarge window height to get the right AR - keep it centered vertically
		yoff = (nwc[3]-nwc[1])*(r-1)/2
		return (nwc[0], nwc[1]-yoff, nwc[2], nwc[3]+yoff)
	elif wa > sa: # Enlarge window width to get the right AR - keep it centered horizontally
		xoff = (nwc[2]-nwc[0])*(1/r-1)/2
		return (nwc[0]-xoff, nwc[1], nwc[2]+xoff, nwc[3])
	
	return wc

def toRGB(r, g, b):
	return b*65536 + g*256 + r

def colorizeAttractor(lc):
	d = dict()

	# Number of time a pixel is redrawn
	for p in lc:
		if d.has_key(p):
			d[p] = d[p]+1
		else:
			d[p] = 1

	# Now convert this to an histogram of the image...
	h = [0]*(max(d.values())+1)
	for v in d.values():
		h[v] += 1

	# Equalize histogram:
	# First compute the cumulative distribution function
	cdf = [0]*len(h)
	for i in range(1, len(cdf)):
		cdf[i] = cdf[i-1]+h[i]

	# Then use the equalizing formula (http://en.wikipedia.org/wiki/Histogram_equalization)
	b = 2**8-1
	m  = cdf[i]
	mm = cdf[1]
	equalize = lambda x: int(math.floor(b*(cdf[x] - mm)/(m-mm)))
	h[1:]  = [equalize(x) for x in range(1, len(h))]

	# Move back the equalized/normalized values into the original dict, after lookup
	# Create a color gradient
	cg = createColorGradient((10, 10, 10), (255, 255, 255), b+1)
	for k, v in d.iteritems():
		d[k] = cg[h[v]]

	return d

def createColorGradient(start_color, end_color, length):
	l = list()

	step    = [float(e-s)/(length-1) for e, s in zip(end_color, start_color)]
	for i in range(length):
		r, g, b = [int(start + i*s) for start, s in zip(start_color, step)]
		l.append(toRGB(r, g, b))

	return l

def projectPoint(pt, *direction):
	return (pt[0], pt[1]) #Ignore Z for now

# Creates an image and fill it with an array of RGB values
def createImage(wc, sc, l):
	w = sc[2]-sc[0]
	h = sc[3]-sc[1]
	size = w*h
	cv = [toRGB(0, 0, 0)]*size

	im = Image.new("RGB", (w, h), None)
	lc = [w_to_s(wc, sc, projectPoint(pt)) for pt in l]
	d  = colorizeAttractor(lc)
	
	for pt,v in d.iteritems():
		xi, yi = projectPoint(pt)
		cv[yi*w + xi] = v

	im.putdata(cv) 
	return im

def projectBound(at):
	if at.opt['dim'] == 1:
		return (at.bound[0][0], at.bound[0][0], at.bound[1][0], at.bound[1][0])
	elif at.opt['dim'] == 2:
		return (at.bound[0][0], at.bound[0][1], at.bound[1][0], at.bound[1][1])
	elif at.opt['dim'] == 3: #For now, ignore the Z part
		return (at.bound[0][0], at.bound[0][1], at.bound[1][0], at.bound[1][1])

def renderAttractor(at, screen_c):
	window_c = scaleRatio(projectBound(at), screen_c)
	im = createImage(window_c, screen_c, l)
	return im

def parseArgs():
	parser = argparse.ArgumentParser(description='Playing with strange attractors')
	parser.add_argument('-c', '--code', help='attractor code')
	parser.add_argument('-d', '--dimension', help='attractor dimension', default=2, type=int, choices=range(1,4))
	parser.add_argument('-D', '--depth',     help='attractor depth (for 1D only)', default=5, type=int)
	parser.add_argument('-g', '--geometry',  help='image geometry (XxY form)', default='800x600')
	parser.add_argument('-i', '--iter',      help='attractor number of iterations', default=480000, type=int)
	parser.add_argument('-n', '--number',    help='number of attractors to generate', default=16, type=int)
	parser.add_argument('-o', '--order',     help='attractor order', default=2, type=int)
	parser.add_argument('-q', '--quiet',     help='shut up !', action='store_true', default=False)
	args = parser.parse_args()
	return args

# ----------------------------- Main loop ----------------------------- #
args = parseArgs()
screen_c = [0, 0] + [int(x) for x in args.geometry.split('x')]
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
		n = n + 1
		if n == args.number or args.code: break
		continue
	if not args.quiet: print at
	im = renderAttractor(at, screen_c)
	im.save("png/" + at.code + ".png", "PNG")
	n = n + 1
	if n == args.number or args.code: break
