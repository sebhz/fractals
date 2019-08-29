#!/usr/bin/python3

import logging
import random
import math

"""
Ancillary functions used for attractor generation and rendering.
"""

modulus = lambda p: sum([v*v for v in p])
dist2 = lambda p1, p2: modulus([v[1]-v[0] for v in zip(p1, p2)])

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
	if AttractorType == 'dejong' or AttractorType == 'clifford':
		idealIter *=4

	return idealIter

def scaleBounds(wc, sd, pct=0.05):
	"""
	Pads and enlarges a window to center it in a larger window whose aspect ratio is given.

	Arguments:
		wc: the window to scale, as a (x0, y0, z0, x1, y1, z1) tuple.
		    x0, y0 are the coordinates of the bottom left point
		    x1, y1 are the coordinates of the top right point
		sd: the screen dimension, as a (w, h) tuple
			w and h are respectively the width and height of the screen
		pct: the percentage of padding to be applied in both direction

	Returns a tuple (X0, Y0, X1, Y1) representing wc padded by pct % in
	both directions, enlarged to have the same aspect ratio as sd, so that
	sc is now centered in the new window.
	"""
	hoff = (wc[4]-wc[1])*float(pct)/2
	woff = (wc[3]-wc[0])*float(pct)/2
	nwc  = (wc[0]-woff, wc[1]-hoff, wc[3]+woff, wc[4]+hoff)

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

def linearReg(x, y):
	n = len(x)
	sumxy = sum([v[0]*v[1] for v in zip(x, y)])
	sumx2 = sum(map(lambda v: v**2, x))
	sumy2 = sum(map(lambda v: v**2, y))
	sumx  = sum(x)
	sumy  = sum(y)

	slope   = (n*sumxy - sumx*sumy) / (n*sumx2 - sumx*sumx)
	rsquare = slope * math.sqrt((n*sumx2 - sumx*sumx) / (n*sumy2 - sumy*sumy))

	return (slope, rsquare)

def boxCount(a, origin, box_side):
	boxes = dict()
	for pt in a.keys():
		box_c = tuple([ int((pt[i]-origin[i])/box_side) for i in range(0, len(origin)) ])
		boxes[box_c] = True
	return boxes

def getAttractorBoundingBox(at):
    # Kludge: iterate over a.keys() but break after first iteration
    for k in at.keys():
        attractor_dimension = len(k)
        break

    # Bounding box of the attractor
    bb=[ [65535]*attractor_dimension, [-65535]*attractor_dimension ]
    for pt in at.keys():
        for i, v in enumerate(pt):
            bb[0][i] = min(bb[0][i], v)
            bb[1][i] = max(bb[1][i], v)

    return bb

def computeBoxCountingDimension(at, scaling_factor=1.5):
    """
    Computes an estimate of the Minkowski-Bouligand dimension (a.k.a box-counting)
    See https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension

    Algorithm:
        - Use cubic boxes
        - Start with boxes whose side S = bounding_box_diagonal/4
        - Until S < bounding_box_diagonal/256
            {
            * Choose a random origin inside the bounding box
            * Compute the number of boxes needed to cover the attractor (aligned on the origin)
            }
            In theory this should be done several time varying orientation and origin of
            the boxes, and we should get the minimum. We just take one box count for performance
            Store S, N
            S = S/scaling_factor
        - Perform a linear regression log(N), log(1/S). The slope is the dimension
    """
    bb = getAttractorBoundingBox(at)
    diagonal = math.sqrt(dist2(*bb))
    RATIO = 4
    BOXCOUNT_TRIALS = 1
    (logN, logInvS) = (list(), list())
    logging.debug("Starting box-counting dimension computation.")
    while RATIO < 256:
        S = int(diagonal/RATIO) # Round square side to ease visualization if needed
        N = len(at.keys())
        for iteration in range(0, BOXCOUNT_TRIALS):
            origin = [ random.randint(bb[0][i], bb[1][i]) for i in range(0, len(bb[0])) ]
            boxes = boxCount(at, origin, S)
            N = min(N, len(boxes))
        logN.append(math.log(N))
        logInvS.append(math.log(1/S))
        RATIO *= scaling_factor
    try:
        (slope, rsquare) = linearReg(logInvS, logN)
        logging.debug("Box-counting dimension: %.3f (rsquare: %.2f)" % (slope, rsquare))
        return slope
    except ValueError:
        logging.error("Math error when trying to compute box-counting dimension. Setting it to 0.")
        return 0.0

def computeCorrelationDimension(a):
    """
    Computes an estimate of the correlation dimension "a la Julien Sprott"
    Estimates the probability that 2 points in the attractor are close enough
    """
    base = 10
    radiusRatio = 0.001
    bb = getAttractorBoundingBox(a)
    diagonal = dist2(*bb)
    d1 = 4*radiusRatio*diagonal
    d2 = float(d1)/base/base
    n1, n2 = (0, 0)
    points = list(a.keys())
    l = len(points)

    for p in points: # Iterate on each attractor point
        p2 = points[random.randint(0, l-1)] # Pick another point at random
        d = dist2(p, p2)
        if d == 0: continue # Oops we picked the same point twice
        if d < d1: n2 += 1  # Distance within a big circle
        if d > d2: continue # But out of a small circle
        n1 += 1

    try:
        return math.log(float(n2)/n1, base)
    except ZeroDivisionError:
        logging.error("Math error when trying to compute dimension. Setting it to 0.")
        return 0.0 # Impossible to find small circles... very scattered points

def computeTrueCorrelationDimension(a, maxPoints=4096):
    """
    Computes an estimate of the correlation dimension with the naive
    algorithm. See https://en.wikipedia.org/wiki/Correlation_dimension 
    VERY inefficient and time consuming -> O(N²)
    """
    points = list(a.keys())
    bb = getAttractorBoundingBox(a)
    diagonal2 = dist2(*bb)

    BINRATIOS = (4, 8, 16, 32, 64, 128, 256, 512)
    bins_epsilon2 = [diagonal2/x/x for x in BINRATIOS]

    bins = dict()
    for epsilon2 in bins_epsilon2:
        bins[epsilon2] = 0

    l = min(maxPoints, len(points))
    logging.debug("Starting true correlation dimension computation on %d points." % (l))

    for i in range(0, l-1):
        p1 = points[i]
        for j in range(i+1, l):
            p2 = points[j]
            d2 = dist2(p2, p1)
            for epsilon2 in bins_epsilon2:
                if d2 < epsilon2:
                    bins[epsilon2] += 1

    bins_log = dict()
    for k, v in bins.items():
        try:
            bins_log[math.log(math.sqrt(k))] = math.log(v/l/l)
        except ValueError:
            pass # if a bin is empty

    (slope, rsquare) = linearReg(list(bins_log.keys()), list(bins_log.values()))
    logging.debug("Correlation dimension: %.3f (rsquare: %.2f)" % (slope, rsquare))

    return slope

