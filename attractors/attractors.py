#!/usr/bin/python

# Generate and colorize various dimension strange attractors
# Algo taken from Julian Sprott's book: http://sprott.physics.wisc.edu/sa.htm
# Some coloring ideas (histogram equalization, gradient mapping) taken from
# Ian Whitham's blog
# http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/

import random
import math

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

		if not self.opt.has_key('dim'):
			self.opt['dim'] = 2

		if not self.opt.has_key('iter'):
			self.opt['iter'] = 4096
		
		if not self.opt.has_key('depth'):
			self.opt['depth'] = 5

		if self.opt.has_key('order'):
			self.order = self.opt['order']
		else:
			self.order = 2 # Quadratic by default

		if not self.opt.has_key('coef'):
			self.coef   = None
			self.derive = None
			self.code   = None
		else:
			self.coef = self.opt['coef']
			self.derive = polynom(self.coef[0]).derive()
			self.code   = self.createCode()
			# Need to override order here, or throw an error if not coherent

		if not self.opt.has_key('init'):
			self.init = [0.1]*self.opt['dim']

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None

	def __str__(self):
		st = ""
		for p in self.coef:
			st += "coef: " + p.__str__() + "\n"
		st += "code: " + self.code + "\n"
		st += "Lyapunov exponent: " + str(self.lyapunov['ly']) + "\n"
		st += "Fractal dimension: " + str(self.fdim) + "\n"
		st += "Computed on " + str(self.opt['iter']) +  " points.\n"
		return st

	def createCode(self):
		# ASCII codes of digits and letters
		codelist = range(48,58) + range(65,91) + range(97,123)
		self.code = [codelist[int(x/0.08+25)] for c in self.coef for x in c]
		self.code = "".join(map(chr,self.code))

	def getRandom(self):
		l = self.order + 1
		for i in range(2, self.opt['dim']+1):
			l *= self.order+i
		l /= self.opt['dim']

		self.coef = [[random.randint(-25, 25)*0.08 for _ in range(l)] for __ in range(self.opt['dim'])]

		if self.opt['dim'] == 1: self.derive = polynom(c[0]).derive()

	def evalCoef(self, p):
		l = list()
		for c in self.coef:
			result = 0
			n = 0
			for i in range(self.order+1):
					for j in range(i+1):
						result += c[n]*(p[0]**j)*(p[1]**(i-j))
						n = n + 1
			l.append(result)
		return l

	def computeLyapunov(self, p, pe):
		if self.opt['dim'] == 1:
			df = abs(self.derive(p[0]))
		else:
			p2   = self.evalCoef(pe)
			dl   = [d-x for d,x in zip(p2, p)]
			dl2  = reduce(lambda x,y: x*x + y*y, dl)
			if dl2 == 0:
				print "Unable to compute Lyapunov exponent, but trying to go on..."
				return pe
			df = 1000000000000*dl2
			rs = 1/math.sqrt(df)

		self.lyapunov['lsum'] = self.lyapunov['lsum'] + math.log(df)/math.log(2)
		self.lyapunov['nl']   = self.lyapunov['nl'] + 1
		self.lyapunov['ly'] = 0.721347 * self.lyapunov['lsum'] / self.lyapunov['nl']
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
		return l

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
	return r*65536 + g*256 + r

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
	for i in range(0, len(cdf)):
		cdf[i] = cdf[i-1]+h[i]

	# Then use the equalizing formula (http://en.wikipedia.org/wiki/Histogram_equalization)
	b = 2**8-1
	m  = cdf[i]
	mm = cdf[1]
	equalize = lambda x: int(math.floor(b*(cdf[x] - mm)/(m-mm)))
	h[1:]  = [equalize(x) for x in range(1, len(h))]
	h[1]   = int(h[2]/2) # Formula above makes first value black - make it only darker

	# Move back the equalized/normalized values into the original dict
	for k, v in d.iteritems():
		d[k] = h[v]

	print len(d.keys()), "unique points in the display window."

	return d

# Creates an image and fill it with an array of RGB values
def createImage(wc, sc, l):
	w = sc[2]-sc[0]
	h = sc[3]-sc[1]
	size = w*h
	cv = [toRGB(0, 0, 0)]*size

	im = Image.new("RGB", (w, h), None)
	lc = [w_to_s(wc, sc, pt) for pt in l]
	d  = colorizeAttractor(lc)
	
	for pt,v in d.iteritems():
		xi, yi = pt
		cv[yi*w + xi] = toRGB(0, v, 0)

	im.putdata(cv) 
	return im

def projectBound(at):
	if at.opt['dim'] == 1:
		return (at.bound[0][0], at.bound[0][0], at.bound[1][0], at.bound[1][0])
	elif at.opt['dim'] == 2:
		return (at.bound[0][0], at.bound[0][1], at.bound[1][0], at.bound[1][1])

def showAttractor(at, screen_c):
	l = at.iterateMap()
	window_c = scaleRatio(projectBound(at), screen_c)
	im = createImage(window_c, screen_c, l)
	#im.show()
	return im
	
screen_c = (0, 0, 1600, 1200)
random.seed()

# The logistic parabola
#at = polynomialAttractor({'coef': [(0, 4, -4)], 'dim': 1, 'depth': 1})
#print at
#if not at.checkConvergence():
#	print "Looks like this is not an attractor"
#else:
#	showAttractor(at, screen_c)

# A few 1D and 2D attractors
for i in range(16):
#	at = polynomialAttractor({'dim':1,'iter':163840})
#	at.explore()
#	print at
#	im = showAttractor(at, screen_c)
	at = polynomialAttractor({'dim':2, 'order':3, 'iter':1600*1200 })
	at.explore()
	print at
	im = showAttractor(at, screen_c)
	im.save("png/" + at.code + ".png", "PNG")
