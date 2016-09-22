#!/usr/bin/python

OVERITERATE_FACTOR=4

def getIdealIterationNumber(AttractorType, screenDim, subsamplingRate):
	pxSize = subsamplingRate*subsamplingRate*screenDim[0]*screenDim[1]

	idealIter = int(OVERITERATE_FACTOR*pxSize)
	if AttractorType == 'dejong':
		idealIter *=4

	return idealIter

def scaleBounds(wc, sd, pct=0.05):
	# Enlarge window by 5% in both directions
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

