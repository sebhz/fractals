#!/usr/bin/python

import math
import cmath
import time
try:
    import Image
except:
    print "this program requires the PIL module"
    print "available at http://www.pythonware.com/library/pil"
    raise SystemExit

class fractal(object):
	def __init__(self, l, m, t):
		self.limit = l
		self.maxiter = m
		if t == "collatz":
			self.f = self.collatz
		elif t == "julia":
			self.f = self.julia
		elif t == "mandelbrot":
			self.f = self.mandelbrot
		else:
			print "Unsupported fractal type (", t, "), defaulting to collatz"
			self.f = self.collatz

	def collatz(self, c, *p):
		for i in range(0, self.maxiter):
			c = (2 + 7*c - (2 + 5*c)*cmath.cos(cmath.pi*c))/4;
			m = abs(c)
			if m > self.limit:
				break
		return i, m

	def julia(self, c, *p):
		for i in range(0, self.maxiter):
			c = c*c + p[0]
			m = abs(c)
			if m > self.limit:
				break
		return i, m

	def mandelbrot(self, c, *p):
		z = 0
		for i in range(0, self.maxiter):
			z = z*z + c
			m = abs(z)
			if m > self.limit:
				break
		return i, m

	def compute(self, center, xres, yres, xlength, *p):
		# set the center point in the center of the window, 
		# with an X axis of size xlength, and an orthogonal projection
		ratio = float(yres)/float(xres)
		xmin = center.real - xlength/2
		ymin = center.imag - xlength*ratio/2
		ylength = xlength*ratio
		l = list()

		for y in range(0,yres):
			for x in range(0,xres):
				c = complex(xmin + (float(x)-0.0)*xlength/xres,
				            ymin + (float(y)-0.0)*ylength/yres)
				l.append(self.f(c, *p))
		return l

# From 0->511 to 0->255 using a triangular map
def periodicColor(c):
	v = c+128 if c < 128 else 383-c if c < 384 else c-384
	return v

def colorize(l, ccoef, maxiter):
	lc = list()
	for item in l:
		if item[0] == maxiter - 1:
			lc.append(0)
		else:
			# OK for Mandelbrot and Julia - may generate exceptions for Collatz
			v = 8 * math.sqrt (item[0] + 3 \
			    - math.log((math.log (math.sqrt (item[1]))), 2));
			# OK for everything, but coloring is not smooth
			#v = 8 * math.sqrt(float(item[0]) + 2.0);
			lc.append(periodicColor(int(math.floor(v*ccoef[0]))%512)*(1<<16) + \
			          periodicColor(int(math.floor(v*ccoef[1]))%512)*(1<< 8) + \
					  periodicColor(int(math.floor(v*ccoef[2]))%512))
	return lc

def createImage(w, h, l):
	im = Image.new("RGB", (w, h), None)
	im.putdata(l)
	return im

limit, maxiter, w, h = (8, 128, 2048, 1536)
t1 = time.time()
c = fractal(limit, maxiter, "mandelbrot")
l = c.compute(complex(-0.5, 0.0), w, h, 3.4, None)
lc = colorize(l, (2, 3, 5), maxiter)
print "Time taken to compute and color set: %.3f secs" % float(time.time() - t1)
im = createImage(w, h, lc)
im.show()
im.save("fractal.png", "PNG")
