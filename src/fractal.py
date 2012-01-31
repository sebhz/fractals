#!/usr/bin/python

import math
import cmath
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
			if abs(c) > self.limit:
				break
		return i

	def julia(self, c, *p):
		for i in range(0, self.maxiter):
			c = c*c + p[0]
			if abs(c) > self.limit:
				break
		return i

	def mandelbrot(self, c, *p):
		z = 0
		for i in range(0, self.maxiter):
			z = z*z + c
			if abs(z) > self.limit:
				break
		return i

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
				c = complex(xmin + (float(x)-0.0)*xlength/xres, ymin + (float(y)-0.0)*ylength/yres)
				l.append(self.f(c, *p))
		
		return l
		
# From 0->511 to 0->255 using a triangular map
def periodicColor(c):
	v = c+128 if c < 128 else 383-c if c < 384 else c-384
	return v
	
def colorize(l, ccoef, maxiter):
	lc = list()
	for item in l:
		v = int(math.floor(8*math.sqrt(float(item) + 2.0)));
		if item == maxiter - 1:
			lc.append(0)
		else:
			lc.append((periodicColor(v*ccoef[0])%512)*65536 + periodicColor((v*ccoef[1])%512)*256 + periodicColor((v*ccoef[2])%512))
	return lc
	
def createImage(w, h, l):
	im = Image.new("RGB", (w, h), None)
	im.putdata(l) 
	return im

limit, maxiter, w, h = (2.1, 128, 1280, 1024)

c = fractal(limit, maxiter, "mandelbrot")
l = c.compute(complex(-0.5, 0.0), w, h, 3.4, None)
lc = colorize(l, (4, 6, 6), maxiter)
im = createImage(w, h, lc)
im.show()
im.save("fractal.png", "PNG")
