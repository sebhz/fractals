#!/usr/bin/python

def getIdealIterationNumber(AttractorType, screenDim, subsamplingRate):
	"""
	Computes the number of iterations necessary to have the attractor
	"look good", when rendered.

	Arguments:
		AttractorType: either 'polynomial' or 'dejong'. De Jong attractor typically
		               require more iterations
		screenDim: a (w,h) tuple giving the final picture width and height in pixels
		subsamplingRate: the oversampling rate (usually 1, 2 or 3)
	"""

	OVERITERATE_FACTOR=4
	pxSize = subsamplingRate*subsamplingRate*screenDim[0]*screenDim[1]

	idealIter = int(OVERITERATE_FACTOR*pxSize)
	if AttractorType == 'dejong':
		idealIter *=4

	return idealIter

def scaleBounds(wc, sd, pct=0.05):
	"""
	Pads and scale a window, keeping its aspect ratio to fit in a screen

	Arguments:
		wc: the window to scale, as a (x0, y0, x1, y1) tuple.
		    x0, y0 are the coordinates of the bottom left point
		    x1, y1 are the coordinates of the top right point
		sd: the screen dimension, as a (w, h) tuple
			w and h are respectively the width and height of the screen
		pct: the percentage of padding to be applied in both direction

	Returns a tuple (X0, Y0, X1, Y1) representing wc padded by pct % in
	both directions, and scaled to fit in sd (and be centered in it)
	"""

	hoff = (wc[3]-wc[1])*float(pct)/2
	woff = (wc[2]-wc[0])*float(pct)/2
	nwc  = (wc[0]-woff, wc[1]-hoff, wc[2]+woff, wc[3]+hoff)

	wa = float(nwc[3]-nwc[1])/float(nwc[2]-nwc[0]) # New window aspect ratio
	sa = float(sd[1])/float(sd[0]) # Screen aspect ratio
	r = sa/wa

	if wa < sa: # Enlarge window height to get the right AR - keep it centered vertically
		yoff = (nwc[3]-nwc[1])*(r-1)/2
		return (nwc[0], nwc[1]-yoff, nwc[2], nwc[3]+yoff)
	elif wa > sa: # Enlarge window width to get the right AR - keep it centered horizontally
		xoff = (nwc[2]-nwc[0])*(1/r-1)/2
		return (nwc[0]-xoff, nwc[1], nwc[2]+xoff, nwc[3])

	return wc

