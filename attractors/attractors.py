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

		if self.opt.has_key('order'):
			self.order = self.opt['order']
		else:
			self.order = 2 # Quadratic by default

		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.bound     = [0]*4

	def getRandom(self):
		c = list()
		for i in range(self.order+1):
			c.append(random.uniform(-4, 4))
		return c

	def computeLyapunov(self, x):
		a = self.coef

		df = 0
		for i in range(len(a)-1, 1, -1):
			df = (df + i*a[i])*x
		df = df + a[1]
		df = abs(df)

		if df > 0:
			self.lyapunov['lsum'] = self.lyapunov['lsum'] + math.log(df)/math.log(2)
			self.lyapunov['nl']   = self.lyapunov['nl'] + 1
	
		self.lyapunov['ly'] = 0.721347 * self.lyapunov['lsum'] / self.lyapunov['nl']
		return self.lyapunov['ly']

	def checkConvergence(self):
		self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
		x = self.init
		a = self.coef
		
		for i in range(self.opt['iter']):
			xnew = 0
			for j in range(len(a)-1, 0, -1):
				xnew = (xnew + a[j])*x
			xnew = xnew + a[0]
			if abs(xnew) > 1000000: # Unbounded - not an SA
				return False
			if abs(xnew-x) < 0.000001: # Fixed point - not an SA
				return False
			if self.computeLyapunov(xnew) < 0.005 and i > 128: # Lyapunov exponent too small - limit cycle
				return False
			x = xnew
			
		return True
		
	def explore(self):
		found = False
		n = 0;

		while not found:
			n = n + 1
			self.coef = self.getRandom()
			found     = self.checkConvergence()

		print "Found in", n, "iterations:", self.coef, "(Lyapunov exponent:", self.lyapunov['ly'], ")"

	def iterateMap(self):
		l    = list()
		a    = self.coef
		x    = self.init
		prev = self.opt['depth']	
		mem = [x]*prev
		xmin, xmax = (1000000, -1000000)

		for i in range(self.opt['iter']):
			xnew = 0
			for j in range(len(a)-1, 0, -1):
				xnew = (xnew + a[j])*x
			xnew = xnew + a[0]
			if i >= prev-1:
				l.append((mem[(i-prev)%prev], xnew, i))
			mem[i%prev] = xnew;
			xmin, xmax = (min(xmin, x), max(xmax, x))
			x = xnew

		self.bound = (xmin, xmin, xmax, xmax)
		return l

class attractor2D(object):

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
			ymin, ymax = (1000000, -1000000)
			lsum, nl = (0, 0)
			xtmp = x
			ytmp = y
			xe = x + .000001
			ye = y

			for i in range(self.opt['iter']):
				xnew = ax[0] + ax[1]*xtmp + ax[2]*xtmp*xtmp + ax[3]*xtmp*ytmp + ax[4]*ytmp + ax[5]*ytmp*ytmp
				ynew = ay[0] + ay[1]*xtmp + ay[2]*xtmp*xtmp + ay[3]*xtmp*ytmp + ay[4]*ytmp + ay[5]*ytmp*ytmp
				if abs(xnew) + abs(ynew) > 1000000: # Unbounded - not an SA
					found = False
					break
				if abs(xnew-xtmp) + abs(ynew-ytmp) < 0.000001: # Fixed point - not an SA
					found = False
					break

				# Compute Lyapunov exponent... sort of
				xsave = xnew
				ysave = ynew
				xtmp = xe
				ytmp = ye
				xnew = ax[0] + ax[1]*xtmp + ax[2]*xtmp*xtmp + ax[3]*xtmp*ytmp + ax[4]*ytmp + ax[5]*ytmp*ytmp
				ynew = ay[0] + ay[1]*xtmp + ay[2]*xtmp*xtmp + ay[3]*xtmp*ytmp + ay[4]*ytmp + ay[5]*ytmp*ytmp
				dlx = xnew-xsave
				dly = ynew-ysave
				dl2 = dlx*dlx + dly*dly
				if dl2 == 0:
					print "Uh oh..."
				df = 1000000000000*dl2
				rs = 1/math.sqrt(df)
				xe = xsave + rs * dlx
				ye = ysave + rs * dly
				xnew = xsave
				ynew = ysave
				lsum = lsum + math.log(df)/math.log(2)
				nl = nl + 1
				ly = .721347*lsum/nl

				if ly < 0.005 and i > 128: # Lyapunov exponent too small - limit cycle
					found = False
					break
				xmin, xmax = (min(xmin, xtmp), max(xmax, xtmp))
				ymin, ymax = (min(ymin, ytmp), max(ymax, ytmp))
				xtmp = xnew
				ytmp = ynew
		print "Found in", n, "iterations:", a, "(Lyapunov exponent:", self.lyapunov['ly'], ")"
		self.bound = (xmin, xmax)

	def iterateQuadraticMap(self):
		l = list()
		ax = self.coef[0]
		ay = self.coef[1]
		x, y = self.init

		for i in range(self.opt['iter']):
			xnew = ax[0] + ax[1]*x + ax[2]*x*x + ax[3]*x*y + ax[4]*y + ax[5]*y*y
			ynew = ay[0] + ay[1]*x + ay[2]*x*x + ay[3]*x*y + ay[4]*y + ay[5]*y*y
			l.append(xnew, ynew, i)
			x, y = (xnew, ynew)

		return l

def w_to_s(wc, sc, x, y):

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
	cv = [0]*size

	im = Image.new("RGB", (w, h), None)
	for pt in l:
		xi, yi = w_to_s(wc, sc, pt[0], pt[1])
		cv[yi*w + xi] = toRGB(255, 255, 255)

	im.putdata(cv) 
	return im

screen_c = (0, 0, 1024, 768)

random.seed()

# The logistic parabola
at = attractor1D({'coef': (0, 4, -4), 'depth': 1})
if not at.checkConvergence():
	print "Looks like this is not an attractor"
else:
	l = at.iterateMap()
	window_c = scaleRatio(at.bound, screen_c)
	im = createImage(window_c, screen_c, l)
	im.show()

# A random 1D attractor of order 5
at = attractor1D({'order': 5, 'iter' : 8192})
at.explore()
l = at.iterateMap()
window_c = scaleRatio(at.bound, screen_c)
im = createImage(window_c, screen_c, l)
im.show()
