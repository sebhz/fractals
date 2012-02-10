#!/usr/bin/python

import random
import math

try:
    import Image
except:
    print "this program requires the PIL module"
    print "available at http://www.pythonware.com/library/pil"
    raise SystemExit

class attractor1D(object):
	def __init__(self, *opt):
		if opt:
			self.opt = opt[0]
		else:
			self.opt = dict()

		if not self.opt.has_key('iter'):
			self.opt['iter'] = 4096
		
		if not self.opt.has_key('depth'):
			self.opt['depth'] = 5

		if not self.opt.has_key('coef'):
			self.coef = None
		else:
			self.coef = self.opt['coef']

		if not self.opt.has_key('init'):
			self.init = 0.1

		if not self.opt.has_key('order'):
			self.order = 2 # Quadratic by default

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.bound     = [0]*2

	def getRandom(self):
		c = list()
		for i in range(self.order+1):
			c.append(random.uniform(-4, 4))
		return c

	def computeLyapunov(self, x):
		a = self.coef
		df = abs(a[1] + 2*a[2]*x)
		if df > 0:
			self.lyapunov['lsum'] = self.lyapunov['lsum'] + math.log(df)
			self.lyapunov['nl']   = self.lyapunov['nl'] + 1
	
		self.lyapunov['ly'] = 0.721347 * self.lyapunov['lsum'] / self.lyapunov['nl']
		return self.lyapunov['ly']

	def explore(self):
		found = False
		n = 0;
		x = self.init

		while not found:
			n = n + 1
			a = self.getRandom()
			self.coef = a
			found = True
			xmin, xmax = (1000000, -1000000)
			self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
			xtmp = x

			for i in range(self.opt['iter']):
				xnew = a[0] + a[1]*xtmp + a[2]*xtmp*xtmp
				if abs(xnew) > 1000000: # Unbounded - not an SA
					found = False
					break	
				if abs(xnew-x) < 0.000001: # Fixed point - not an SA
					found = False
					break
				self.computeLyapunov(xnew)
				if self.lyapunov['ly'] < 0.005 and i > 128: # Lyapunov exponent too small - limit cycle
					found = False
					break
				xmin, xmax = (min(xmin, xtmp), max(xmax, xtmp))
				xtmp = xnew

		print "Found in", n, "iterations:", a
		self.bound = (xmin, xmax)

	def iterateMap(self):
		l    = list()
		a    = self.coef
		x    = self.init
		prev = self.opt['depth']	
		mem = [x]*prev

		for i in range(self.opt['iter']):
			xnew = a[0] + a[1]*x + a[2]*x*x
			if i >= prev-1:
				l.append((mem[(i-prev)%prev], xnew, i))
			mem[i%prev] = xnew;
			x = xnew

		return l

def w_to_s(wc, sc, x, y):

	if x < wc[0] or x > wc[2] or y < wc[1] or y > wc[3]:
		return None
	
	return ( int(sc[0] + (x-wc[0])/(wc[2]-wc[0])*(sc[2]-sc[0])), 
			 int(sc[1] + (sc[3]-sc[1])- (y-wc[1])/(wc[3]-wc[1])*(sc[3]-sc[1])) )

# Enlarge window_c so that it has the same aspect ratio as screen_c 
def scaleRatio(wc, sc):
	wa = float(wc[3]-wc[1])/float(wc[2]-wc[0]) # Window aspect ratio
	sa = float(sc[3]-sc[1])/float(sc[2]-sc[0]) # Screen aspect ratio
	r = sa/wa
	
	if wa < sa: # Enlarge window height to get the right AR - keep it centered vertically
		yoff = (wc[3]-wc[1])*(r-1)/2
		return (wc[0], wc[1]-yoff, wc[2], wc[3]+yoff)
	elif wa > sa: # Enlarge window width to get the right AR - keep it centered horizontally
		xoff = (wc[2]-wc[0])*(1/r-1)/2
		return (wc[0]-xoff, wc[1], wc[2]+xoff, wc[3])
	
	return wc

def toRGB(r, g, b):
	return r*65536 + g*256 + r

# Creates an image and fill it with an array of RGB values
def createImage(wc, sc, l):
	w = sc[2]-sc[0]
	h = sc[3]-sc[1]
	size = w*h
	cv = [0]*size

	im = Image.new("RGB", (w, h), None)
	for pt in l:
		xi, yi = w_to_s(wc, sc, pt[0], pt[1])
		cv[yi*w + xi] = toRGB(255, 255, 255)

	im.putdata(cv) 
	return im

screen_c = (0, 0, 800, 600)

random.seed()
#at = attractor1D({'coef': (0, 4, -1)})
at = attractor1D()
at.explore()
l = at.iterateMap()
window_c = scaleRatio((at.bound[0]-0.1*abs(at.bound[0]), at.bound[0]-0.1*abs(at.bound[0]), at.bound[1]+0.1*abs(at.bound[1]), at.bound[1]+0.1*abs(at.bound[1])), screen_c)
im = createImage(window_c, screen_c, l)
im.show()
