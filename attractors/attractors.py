#!/usr/bin/python

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

		if not self.opt.has_key('coef'):
			self.coef = None
			self.derive = None
		else:
			self.coef = self.opt['coef']
			self.derive = polynom(self.coef[0]).derive()

		if not self.opt.has_key('init'):
			self.init = [0.1]*self.opt['dim']

		if self.opt.has_key('order'):
			self.order = self.opt['order']
		else:
			self.order = 2 # Quadratic by default

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None

	def __str__(self):
		st = ""
		for p in self.coef:
			st = st + "coef: " + p.__str__() + "\n"
		st = st + "Lyapunov exponent: " + str(self.lyapunov['ly']) + "\n"
		st = st + "Fractal dimension: " + str(self.fdim) + "\n"
		st = st + "Computed on " + str(self.opt['iter']) +  " points.\n"
		return st

	def getRandom(self):
		l = self.order + 1
		for i in range(2, self.opt['dim']+1):
			l = l * (self.order+i)
		l = l / self.opt['dim']

		c = [[random.uniform(-2, 2) for _ in range(l)] for __ in range(self.opt['dim'])]

		if self.opt['dim'] == 1: self.derive = polynom(c[0]).derive()

		return c

	def evalCoef(self, p):
		l = list()
		for c in self.coef:
			result = 0
			n = 0
			for i in range(self.order+1):
					for j in range(i+1):
						result = result + c[n]*(p[0]**j)*(p[1]**(i-j))
						n = n + 1
			l.append(result)
		return l

	def computeLyapunov(self, p, pe):
		if self.opt['dim'] == 1:
			df = abs(self.derive(p[0]))
		else:
			p2   = self.evalCoef(pe)
			dl   = [p2[i]-x for i,x in enumerate(p)]
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
			if reduce(modulus, [c-p[index] for index,c in enumerate(pnew)], 0) < 0.00000001:
				return False
			# Compute Lyapunov exponent... sort of
			pe = self.computeLyapunov(pnew, pe)
			if self.lyapunov['ly'] < 0.005 and i > 128: # Limit cycle
				return False
			p = pnew

		return True

	def explore(self):
		n = 0;
		self.coef = self.getRandom()
		while not self.checkConvergence():
			n = n + 1
			self.coef = self.getRandom()

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
				pmin = [min(pnew[j], pm) for j,pm in enumerate(pmin)]
				pmax = [max(pnew[j], pm) for j,pm in enumerate(pmax)]

			if self.opt['dim'] == 1:
				mem[i%prev] = pnew
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

# Creates an image and fill it with an array of RGB values
def createImage(wc, sc, l):
	w = sc[2]-sc[0]
	h = sc[3]-sc[1]
	size = w*h
	cv = [toRGB(255,250,205)]*size # Lemon chiffon RGB code

	im = Image.new("RGB", (w, h), None)
	for pt in l:
		xi, yi = w_to_s(wc, sc, pt)
		cv[yi*w + xi] = toRGB(0, 0, 0)

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
	im.show()
	return im
	
screen_c = (0, 0, 1024, 768)
random.seed()

# The logistic parabola
at = polynomialAttractor({'coef': [(0, 4, -4)], 'dim': 1, 'depth': 1})
print at
if not at.checkConvergence():
	print "Looks like this is not an attractor"
else:
	showAttractor(at, screen_c)

# A few 1D and 2D attractors
for i in range(32):
	at = polynomialAttractor({'dim':1,'iter':16384})
	at.explore()
	print at
	im = showAttractor(at, screen_c)
	at = polynomialAttractor({'dim':2,'iter':16384})
	at.explore()
	print at
	im = showAttractor(at, screen_c)
	#im.save("png/fractal"+str(i)+".png", "PNG")
