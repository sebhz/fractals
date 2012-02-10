#!/usr/bin/python

import random
import math

try:
    import Image
except:
    print "this program requires the PIL module"
    print "available at http://www.pythonware.com/library/pil"
    raise SystemExit

# Screens coordinate conversion - aspect ratio not respected
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
def createImage(w, h, l):
	im = Image.new("RGB", (w, h), None)
	im.putdata(l) 
	return im

def plotFloat(x, y, wc, sc, l):
	xi, yi = w_to_s(wc, sc, x, y)
	l[yi*(sc[2]-sc[0]) + xi] = toRGB(255, 255, 255)
	
def iterateLogistic(x, r, wc, sc, l, iter, prev):
	if prev <= 0:
		return
		
	mem = [x]*prev
	for i in range(iter):
		xnew = r*x*(1-x)
		if i >= prev-1:
			plotFloat(mem[(i-prev)%prev], xnew, wc, sc, l)
		mem[i%prev] = xnew;
		x = xnew

def computeLyapunov(a, x, lsum, nl):
	df = abs(a[1] + 2*a[2]*x)
	if df > 0:
		lsum = lsum + math.log(df)
		nl = nl + 1
	
	return (0.721347 * lsum / nl, lsum, nl)
	
def explore1dQuadraticMap(x, iter):
	a = getQuadraticRandom()
	xmin, xmax = (1000000, -1000000)
	lsum, nl = (0, 0)
	for i in range(iter):
		xnew = a[0] + a[1]*x + a[2]*x*x
		if abs(xnew) > 1000000: # Unbounded - not an SA
			return None
		if abs(xnew-x) < 0.000001: # Fixed point - not an SA
			return None
		ly, lsum, nl = computeLyapunov(a, xnew, lsum, nl)
		if ly < 0.005 and i > 128: # Lyapunov exponent too small - limit cycle
			return None
		xmin, xmax = (min(xmin, x),    max(xmax, x))
		x = xnew
	print "Lyapunov exponent:", ly
	return a

def getQuadraticRandom():
	return (random.uniform(-4, 4), random.uniform(-4, 4), random.uniform(-4, 4))

def iterate1dQuadraticMap(x, wc, sc, l, iter, a, prev):
	if prev <= 0:
		return
		
	mem = [x]*prev
	for i in range(iter):
		xnew = a[0] + a[1]*x + a[2]*x*x
		if i >= prev-1:
			plotFloat(mem[(i-prev)%prev], xnew, wc, sc, l)
		mem[i%prev] = xnew;
		x = xnew

# Convert between real coordinates and screen coordinates
window_c = (-.1, -.1, 1.1, 1.1)
screen_c = (0, 0, 800, 600)
iter = 1024
xres = screen_c[2]-screen_c[0]
yres = screen_c[3]-screen_c[1]
size = xres*yres
l = [0]*size
n = 1
#window_c = scaleRatio(window_c, screen_c)
#iterateLogistic(.05, 4, window_c, screen_c, l, iter, 1)

random.seed()
a = explore1dQuadraticMap(0.1, iter)
while not a:
	n = n + 1
	a = explore1dQuadraticMap(0.1, iter)
print "Found after", n, "iterations:", a
iterate1dQuadraticMap(.1, window_c, screen_c, l, iter, a, 5)

im = createImage(xres, yres, l)
im.show()
