#!/usr/bin/python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# Generate and colorize various dimension polynomial strange attractors
# Algo taken from Julian Sprott's book: http://sprott.physics.wisc.edu/sa.htm

import random
import math
import re
import logging
import util
from multiprocessing import Manager, Process

OVERITERATE_FACTOR=4
LYAPUNOV_BOUND=100000

defaultParameters = {
	'iter' : 1280*1024*OVERITERATE_FACTOR,
	'order': 2,
	'code' : None,
	'dimension' : 2,
}
modulus = lambda x,y,z: x*x + y*y + z*z

class Attractor(object):
	"""
	Base class representing an attractor. Should generally not be instanciated directly. Use one
	of its subclasses: PolyomialAttractor or DeJongAttractor.
	"""
	convDelay    = 128   # Number of points to ignore before checking convergence
	convMaxIter  = 16384 # Check convergence on convMaxIter points only
	epsilon      = 1e-6

	def __init__(self, **kwargs):
		getParam = lambda k: kwargs[k] if kwargs and k in kwargs else defaultParameters[k] if k in defaultParameters else None

		self.logger = logging.getLogger(__name__)
		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None
		# TODO: type checking on parameters
		self.iterations = getParam('iter')
		self.dimension  = getParam('dimension')
		if self.dimension < 2 or self.dimension > 3:
			self.logger.warning("Invalid dimension value " + self.dimension + ". Forcing 2D.")
			self.dimension = 2

	def __str__(self):
		return self.code if self.code else super(Attractor, self).__str__()

	def computeLyapunov(self, p, pe):
		p2   = self.getNextPoint(pe)
		if not p2: return pe
		dl   = [d-x for d,x in zip(p2, p)]
		dl2  = modulus(*dl)
		if dl2 == 0:
			self.logger.warning("Unable to compute Lyapunov exponent, but trying to go on...")
			return pe
		df = dl2/self.epsilon/self.epsilon
		rs = 1/math.sqrt(df)

		self.lyapunov['lsum'] += math.log(df, 2)
		self.lyapunov['nl']   += 1
		self.lyapunov['ly'] = self.lyapunov['lsum'] / self.lyapunov['nl']
		return [p[i]+rs*x for i,x in enumerate(dl)]

	def checkConvergence(self, initPoint=(0.1, 0.1, 0.0)):
		self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
		pmin, pmax = ([LYAPUNOV_BOUND]*3, [-LYAPUNOV_BOUND]*3)
		p = initPoint
		pe = [x + self.epsilon if i==0 else x for i, x in enumerate(p)]

		for i in xrange(self.convMaxIter):
			pnew = self.getNextPoint(p)
			if not pnew: return False
			if modulus(*pnew) > 1000000: # Unbounded - not an SA
				return False
			if modulus(*[pn-pc for pn, pc in zip(pnew, p)]) < self.epsilon:
				return False
			# Compute Lyapunov exponent... sort of
			pe = self.computeLyapunov(pnew, pe)
			if self.lyapunov['ly'] < 0.005 and i > self.convDelay: # Limit cycle
				return False
			if i > self.convDelay:
				pmin = [min(pn, pm) for pn, pm in zip(pnew, pmin)]
				pmax = [max(pn, pm) for pn, pm in zip(pnew, pmax)]
			p = pnew
		if not self.bound:
			self.bound = [v for p in (pmin, pmax) for v in p]
		return True

	def explore(self):
		n = 0;
		self.getRandomCoef()
		while not self.checkConvergence():
			n += 1
			self.getRandomCoef()
		# Found one -> create corresponding code
		self.logger.debug("Attractor found after %d trials." % (n+1))
		self.createCode()

	def getInitPoints(self, n):
		initPoints = list()
		i = 0
		while True:
			if not self.bound:
				p = (random.random(), random.random(), 0)
			else:
				rx = self.bound[0] + random.random()*(self.bound[3]-self.bound[0])
				ry = self.bound[1] + random.random()*(self.bound[4]-self.bound[1])
				rz = self.bound[2] + random.random()*(self.bound[5]-self.bound[2])
				p = (rx, ry, rz)
			if self.checkConvergence(p):
				initPoints.append(p)
				i += 1
			if i == n: return initPoints

	def iterateMap(self, screenDim, windowC, aContainer, index, lock, initPoint=(0.1, 0.1, 0.0)):
		a = dict()
		p = initPoint

		ratioX = (screenDim[0]-1)/(windowC[2]-windowC[0])
		ratioY = (screenDim[1]-1)/(windowC[3]-windowC[1])
		maxY = screenDim[1]-1
		w_to_s = lambda p: (
			int(       (p[0]-windowC[0])*ratioX),
			int(maxY - (p[1]-windowC[1])*ratioY) )

		for i in xrange(self.iterations):
			pnew = self.getNextPoint(p)
			if not pnew:
				aContainer[index] = None
				return

			# Ignore the first points to get a proper convergence
			if i >= self.convDelay:
				projectedPixel = w_to_s(pnew)

				if projectedPixel in a:
					if self.dimension == 2:
						a[projectedPixel] += 1
					elif pnew[2] > a[projectedPixel]:
						a[projectedPixel] = pnew[2]
				else:
					if self.dimension == 2:
						a[projectedPixel] = 1
					else:
						a[projectedPixel] = pnew[2]
			p = pnew
		with lock:
			aContainer[index] = a

	def mergeAttractors(self, a):
		v = None

		for i in xrange(len(a)):
			if a[i] != None:
				v = a[i]
				break

		if v == None:
			self.logger.debug("Empty attractor. Trying to go on anyway.")
			return v

		for vv in a[i+1:]:
			if vv == None: continue
			for k, e in vv.iteritems():
				if k in v:
					if self.dimension == 2:
						v[k] += e
					elif e > v[k]:
						v[k] = e
				else:
					v[k] = e

		self.logger.debug("%d points in the attractor before any dithering done." % (len(v.keys())))
		return v

	def createFrequencyMap(self, screenDim, nthreads):
		jobs = list()
		initPoints = self.getInitPoints(nthreads)

		windowC = util.scaleBounds(self.bound, screenDim)
		with Manager() as manager:
			a = manager.list([None]*nthreads)
			l = manager.Lock()
			for i in range(nthreads):
				job = Process(group=None, name='t'+str(i), target=self.iterateMap, args=(screenDim, windowC, a, i, l, initPoints[i]))
				jobs.append(job)
				job.start()

			for job in jobs:
				job.join()

			aMerge = self.mergeAttractors(a)

		if not aMerge: return aMerge
		self.computeFractalDimension(aMerge, screenDim, windowC)

		self.logger.debug("Time to render the attractor.")
		return aMerge

	def computeBoxCountingDimension(self, a, screenDim, windowC):
		"""
		Computes an estimate of the Minkowski-Bouligand dimension (a.k.a box-counting)
		See https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension
		"""
		sideLength = 2 # Box side length, in pixels
		pixelSize = (windowC[2]-windowC[0])/screenDim[0]

		boxes = dict()
		for pt in a.keys():
			boxCoordinates = (int(pt[0]/sideLength), int(pt[1]/sideLength))
			boxes[boxCoordinates] = True
		n = len(boxes.keys())

		try:
			self.fdim = math.log(n)/math.log(1/(sideLength*pixelSize))
		except ValueError:
			self.logger.error("Math error when trying to compute dimension. Setting it to 0")
			self.fdim = 0

	def computeCorrelationDimension(self, a, screenDim):
		"""
		Computes an estimate of the correlation dimension computed "a la Julien Sprott"
		Estimate the probability that 2 points in the attractor are close enough
		"""
		base = 10
		radiusRatio = 0.001
		diagonal = modulus(*screenDim)
		d1 = 4*radiusRatio*diagonal
		d2 = float(d1)/base/base
		n1, n2 = (0, 0)
		points = a.keys()
		l = len(points)

		for p in points: # Iterate on each attractor point
			p2 = points[random.randint(0,l-1)] # Pick another point at random
			d = modulus(p2[0]-p[0], p2[1]-p[1], 0)
			if d == 0: continue # Oops we picked the same point twice
			if d < d1: n2 += 1  # Distance within a big circle
			if d > d2: continue # But out of a small circle
			n1 += 1

		try:
			self.fdim = math.log(float(n2)/n1, base)
		except ZeroDivisionError:
			self.fdim = 0.0 # Impossible to find small circles... very scattered points

class PolynomialAttractor(Attractor):
	codelist     = range(48,58) + range(65,91) + range(97,123) # ASCII values for code
	codeStep     = .125 # Step to use to map ASCII character to coef

	def __init__(self, **kwargs):
		getParam = lambda k: kwargs[k] if kwargs and k in kwargs else defaultParameters[k] if k in defaultParameters else None
		super(PolynomialAttractor, self).__init__(**kwargs)
		self.code       = getParam('code')
		if self.code:
			self.decodeCode() # Will populate order, length and coef
		else:
			self.order      = getParam('order')
			self.coef       = None
			self.getPolynomLength()

	def decodeCode(self):
		self.order = int(self.code[1])
		self.getPolynomLength()

		d = dict([(v, i) for i, v in enumerate(self.codelist)])
		self.coef = [[(d[ord(_)]-30)*self.codeStep for _ in self.code[3+__*self.pl:3+(__+1)*self.pl]] for __ in range(2)]

	def createCode(self):
		self.code = str(2)+str(self.order)
		self.code += "_"
		# ASCII codes of digits and letters
		cl = [self.codelist[int(x/self.codeStep)+30] for c in self.coef for x in c]
		self.code +="".join(map(chr,cl))

	# Outputs a human readable string of the polynom. If isHTML is True
	# outputs an HTML blurb of the equation. Else output a plain text.
	def humanReadable(self, isHTML):
		variables = ('xn', 'yn')
		equation = ["", ""]
		for v, c in enumerate(self.coef): # Iterate on each dimension
			n = 0
			equation[v] = variables[v]+"+1="
			for i in range(self.order+1):
				for j in range(self.order-i+1):
					if c[n] == 0:
						n+=1
						continue
					equation[v] += "%.3f*%s^%d*%s^%d+" % (c[n], variables[0], j, variables[1], i)
					n += 1
					continue
			# Some cleanup
			for r in variables:
				equation[v] = equation[v].replace("*%s^0" % (r), "")
				equation[v] = equation[v].replace("*%s^1" % (r), "*%s" % (r))
			equation[v] = equation[v].replace("+-", "-")
			equation[v] = equation[v][:-1]

			if isHTML: # Convert this in a nice HTML equation
				equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
				equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
				equation[v] = re.sub(r'(x|y)n',r'\1<sub>n</sub>', equation[v])

		return equation

	def getPolynomLength(self):
		self.pl = (self.order+2)*(self.order+1)/2

	def getRandomCoef(self):
		self.coef = [[random.randint(-30, 31)*self.codeStep for _ in range(0, self.pl)] for __ in range(2)]

	def getNextPoint(self, p):
		l = list()
		try:
			for c in self.coef:
				result = 0
				n = 0
				for i in range(self.order+1):
					for j in range(self.order-i+1):
						result += c[n]*(p[0]**j)*(p[1]**i)
						n += 1
				l.append(result)
		except OverflowError:
			self.logger.error("Overflow during attractor computation.")
			self.logger.error("Either this is a very slowly diverging attractor, or you used a wrong code")
			return None

		return l + [0.0]

	def computeFractalDimension(self, a, screenDim, windowC):
		self.computeBoxCountingDimension(a, screenDim, windowC)

class DeJongAttractor(Attractor):
	codelist     = range(48,58) + range(65,91) + range(97,123) # ASCII values for code
	codeStep     = .125 # Step to use to map ASCII character to coef

	def __init__(self, **kwargs):
		super(DeJongAttractor, self).__init__(**kwargs)
		if kwargs:
			if 'code' in kwargs and kwargs['code'] != None:
				self.code = kwargs['code']
				self.decodeCode() # Will populate coef
		self.dimension = 2

	def createCode(self):
		self.code = "j"
		# ASCII codes of digits and letters
		c = [self.codelist[int(x/self.codeStep)+30] for d in self.coef for x in d]
		self.code +="".join(map(chr,c))

	def decodeCode(self):
		d = dict([(v, i) for i, v in enumerate(self.codelist)])
		self.coef = [ [(d[ord(_)]-30)*self.codeStep for _ in self.code[1+2*__:3+2*__]] for __ in range(2) ]

	def getRandomCoef(self):
		self.coef = [[random.randint(-30, 31)*self.codeStep for _ in range(2)] for __ in range(2)]

	def getNextPoint(self, p):
		return ( math.sin(self.coef[0][0]*p[1]) - math.cos(self.coef[0][1]*p[0]),
		         math.sin(self.coef[1][0]*p[0]) - math.cos(self.coef[1][1]*p[1]),
				 0, )

	def humanReadable(self, isHTML):
		equation = list()
		equation.append('xn+1=sin(%.3f*yn)-cos(%.3f*xn)' % (self.coef[0][0], self.coef[0][1]))
		equation.append('yn+1=sin(%.3f*xn)-cos(%.3f*yn)' % (self.coef[1][0], self.coef[1][1]))

		if isHTML: # Convert this in a nice HTML equation
			for v in range(2):
				equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
				equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
				equation[v] = re.sub(r'(x|y)n',r'\1<sub>n</sub>', equation[v])

		return equation

	def computeFractalDimension(self, a, screenDim, windowC):
		self.computeCorrelationDimension(a, screenDim + [0])

