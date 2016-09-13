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

OVERITERATE_FACTOR=4

defaultParameters = {
	'iter': 1280*1024*OVERITERATE_FACTOR,
	'order': 2,
}

class Attractor(object):
	convDelay    = 128   # Number of points to ignore before checking convergence
	convMaxIter  = 16384 # Check convergence on convMaxIter points only
	epsilon      = 1e-6

	def __init__(self, **opt):
		self.iterations = defaultParameters['iter']
		self.lyapunov  = {'nl': 0, 'lsum': 0, 'ly': 0}
		self.fdim      = 0
		self.bound     = None
		if opt:
			self.iterations = opt['iter'] if 'iter' in opt else defaultParameters['iter']

	def __str__(self):
		return self.code if self.code else super(Attractor, self).__str__()

	def computeLyapunov(self, p, pe):
		p2   = self.getNextPoint(pe)
		if not p2: return pe
		dl   = [d-x for d,x in zip(p2, p)]
		dl2  = reduce(lambda x,y: x*x + y*y, dl)
		if dl2 == 0:
			logging.warning("Unable to compute Lyapunov exponent, but trying to go on...")
			return pe
		df = dl2/self.epsilon/self.epsilon
		rs = 1/math.sqrt(df)

		self.lyapunov['lsum'] += math.log(df, 2)
		self.lyapunov['nl']   += 1
		self.lyapunov['ly'] = self.lyapunov['lsum'] / self.lyapunov['nl']
		return [p[i]+rs*x for i,x in enumerate(dl)]

	def checkConvergence(self, initPoint=(0.1, 0.1)):
		self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
		pmin, pmax = ([100000,100000], [-100000,-100000])
		p = initPoint
		pe = [x + self.epsilon if i==0 else x for i,x in enumerate(p)]
		modulus = lambda x, y: abs(x) + abs(y)

		for i in xrange(self.convMaxIter):
			pnew = self.getNextPoint(p)
			if not pnew: return False
			if reduce(modulus, pnew, 0) > 1000000: # Unbounded - not an SA
				return False
			if reduce(modulus, [pn-pc for pn, pc in zip(pnew, p)], 0) < self.epsilon:
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
		logging.debug("Attractor found after %d trials." % (n+1))
		self.createCode()

	def iterateMap(self, screen_c, window_c, aContainer, index, initPoint=(0.1, 0.1)):
		a = dict()
		p = initPoint

		sh = screen_c[3]-screen_c[1]
		ratioY = sh/(window_c[3]-window_c[1])
		ratioX = (screen_c[2]-screen_c[0])/(window_c[2]-window_c[0])
		w_to_s = lambda p: (
			int(screen_c[0] + (p[0]-window_c[0])*ratioX),
			int(screen_c[1] + sh-(p[1]-window_c[1])*ratioY) )

		for i in xrange(self.iterations):
			pnew = self.getNextPoint(p)
			if not pnew:
				aContainer[index] = None
				return

			# Ignore the first points to get a proper convergence
			if i >= self.convDelay:
				projectedPixel = w_to_s(pnew)

				if projectedPixel in a:
					a[projectedPixel] += 1
				else:
					a[projectedPixel] = 0
			p = pnew

		aContainer[index] = a

	# An estimate of the Minkowski-Bouligand dimension (a.k.a box-counting)
	# See https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension
	def computeBoxCountingDimension(self, a, screen_c, window_c):
		sideLength = 2 # Box side length, in pixels
		pixelSize = (window_c[2]-window_c[0])/(screen_c[2]-screen_c[0])

		boxes = dict()
		for pt in a.keys():
			boxCoordinates = (int(pt[0]/sideLength), int(pt[1]/sideLength))
			boxes[boxCoordinates] = True
		n = len(boxes.keys())

		self.fdim = math.log(n)/math.log(1/(sideLength*pixelSize))

	# An estimate of the correlation dimension computed "a la Julien Sprott"
	# Estimate the probability that 2 points in the attractor are close enough
	# We will make a small error because we resized things a bit, but not that much
	# actually
	def computeCorrelationDimension(self, a, screen_c):
		base = 10
		radiusRatio = 0.001
		diagonal = (screen_c[2]-screen_c[0])**2 + (screen_c[3]-screen_c[1])**2
		d1 = 4*radiusRatio*diagonal
		d2 = float(d1)/base/base
		n1, n2 = (0, 0)
		points = a.keys()
		l = len(points)

		for p in points: # Iterate on each attractor point
			p2 = points[random.randint(0,l-1)] # Pick another point at random
			d = (p2[0]-p[0])**2 + (p2[1]-p[1])**2
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

	def __init__(self, **opt):
		super(PolynomialAttractor, self).__init__(**opt)
		self.order      = defaultParameters['order']
		self.coef       = None
		self.code       = None
		if opt:
			self.order = opt['order'] if 'order' in opt else defaultParameters['order']
			if 'code' in opt and opt['code'] != None:
				self.code = opt['code']
				self.decodeCode() # Will populate order, polynom, length, polynom, coef and derive
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
			logging.error("Overflow during attractor computation.")
			logging.error("Either this is a very slowly diverging attractor, or you used a wrong code")
			return None

		return l

	def computeFractalDimension(self, a, screen_c, window_c):
		super(PolynomialAttractor, self).computeBoxCountingDimension(a, screen_c, window_c)

class DeJongAttractor(Attractor):
	codelist     = range(48,58) + range(65,91) + range(97,123) # ASCII values for code
	codeStep     = .125 # Step to use to map ASCII character to coef

	def __init__(self, **opt):
		super(DeJongAttractor, self).__init__(**opt)
		if opt:
			if 'code' in opt and opt['code'] != None:
				self.code = opt['code']
				self.decodeCode() # Will populate coef

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
		         math.sin(self.coef[1][0]*p[0]) - math.cos(self.coef[1][1]*p[1]), )

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

	def computeFractalDimension(self, a, screen_c, window_c):
		super(DeJongAttractor, self).computeCorrelationDimension(a, screen_c)

