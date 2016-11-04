#!/usr/bin/python

import logging

"""
Ancillary functions used for attractor generation and rendering.
"""

def getIdealIterationNumber(AttractorType, geometry, subsamplingRate=1):
	"""
	Computes the number of iterations necessary to have the attractor
	"look good", when rendered.

	Arguments:
		AttractorType: either 'polynomial' or 'dejong'. De Jong attractors typically
		               require more iterations
		geometry: a (w,h) tuple giving the final picture width and height in pixels
		subsamplingRate: the oversampling rate (usually 1, 2 or 3)

	Returns the correct number of iteration to have the attractor look reasonably good.
	"""

	OVERITERATE_FACTOR=4
	pxSize = subsamplingRate*subsamplingRate*geometry[0]*geometry[1]

	idealIter = int(OVERITERATE_FACTOR*pxSize)
	if AttractorType == 'dejong':
		idealIter *=4

	return idealIter

def scaleBounds(wc, sd, pct=0.05):
	"""
	Pads and enlarges a window to center it in a larger window whose aspect ratio is given.

	Arguments:
		wc: the window to scale, as a (x0, y0, x1, y1) tuple.
		    x0, y0 are the coordinates of the bottom left point
		    x1, y1 are the coordinates of the top right point
		sd: the screen dimension, as a (w, h) tuple
			w and h are respectively the width and height of the screen
		pct: the percentage of padding to be applied in both direction

	Returns a tuple (X0, Y0, X1, Y1) representing wc padded by pct % in
	both directions, enlarged to have the same aspect ratio as sd, so that
	sc is now centered in the new window.
	"""

	hoff = (wc[3]-wc[1])*float(pct)/2
	woff = (wc[2]-wc[0])*float(pct)/2
	nwc  = (wc[0]-woff, wc[1]-hoff, wc[2]+woff, wc[3]+hoff)

	wa = float(nwc[3]-nwc[1])/float(nwc[2]-nwc[0]) # New window aspect ratio
	sa = float(sd[1])/float(sd[0]) # Screen aspect ratio
	try:
		r = sa/wa
	except ZeroDivisionError as e:
		logging.debug("Exception caught when enlarging window")
		logging.debug("Window: %s - screen: %s - hoff: %f - woff: %f - nwc: %s - wa: %f" % (str(wc), str(sd), hoff, woff, str(nwc), wa))
		raise e

	if wa < sa: # Enlarge window height to get the right AR - keep it centered vertically
		yoff = (nwc[3]-nwc[1])*(r-1)/2
		return (nwc[0], nwc[1]-yoff, nwc[2], nwc[3]+yoff)
	elif wa > sa: # Enlarge window width to get the right AR - keep it centered horizontally
		xoff = (nwc[2]-nwc[0])*(1/r-1)/2
		return (nwc[0]-xoff, nwc[1], nwc[2]+xoff, nwc[3])

	return wc

