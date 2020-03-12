#!/usr/bin/python3

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
from . import util
from multiprocessing import Manager, Process

LYAPUNOV_BOUND=100000

defaultParameters = {
    'iter' : 1280*1024*util.OVERITERATE_FACTOR,
    'order': 2,
    'code' : None,
    'dimension' : 2,
}
modulus   = lambda x,y,z: x*x + y*y + z*z
codelist  = list(range(48,58)) + list(range(65,91)) + list(range(97,123)) # ASCII values for code
coderange = (-int(len(codelist)/2)+1, int(len(codelist)/2))

class Attractor(object):
    """
    Base class representing an attractor. Should generally not be instanciated directly. Use one
    of its subclasses: PolyomialAttractor, DeJongAttractor or CliffordAttractor
    """
    convDelay    = 128   # Number of points to ignore before checking convergence
    convMaxIter  = 65536 # Check convergence on convMaxIter points only
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
        # If self.iterations is lower than convMaxIter...
        self.convMaxIter = min(self.convMaxIter, self.iterations)

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

        for i in range(self.convMaxIter):
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

        for i in range(self.iterations):
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

        for i in range(len(a)):
            if a[i] != None:
                v = a[i]
                break

        if v == None:
            self.logger.debug("Empty attractor. Trying to go on anyway.")
            return v

        for vv in a[i+1:]:
            if vv == None: continue
            for k, e in vv.items():
                if k in v:
                    if self.dimension == 2:
                        v[k] += e
                    elif e > v[k]:
                        v[k] = e
                else:
                    v[k] = e

        # For 3D, translate the Z buffer to have min equal to 0
        if self.dimension == 3:
            m = min(v.values())
            for k, e in v.items():
                v[k] -= m

        self.logger.debug("%d points in the attractor before any postprocessing." % (len(v)))
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
        #self.computeFractalDimension(aMerge)

        self.logger.debug("Time to render the attractor.")
        return aMerge

class PolynomialAttractor(Attractor):
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
        if self.dimension == 3: self.codeStep /= 4
        self.subtype = None

    def decodeCode(self):
        self.dimension = int(self.code[0])
        self.order = int(self.code[1])
        self.getPolynomLength()

        d = dict([(v, i) for i, v in enumerate(codelist)])
        self.coef = [[(d[ord(_)]-30)*self.codeStep for _ in self.code[3+__*self.pl:3+(__+1)*self.pl]] for __ in range(self.dimension)]
        self.subtype = self.getSubtype()

    def createCode(self):
        self.code = str(self.dimension)+str(self.order)
        self.code += "_"
        # ASCII codes of digits and letters
        cl = [codelist[int(x/self.codeStep)+30] for c in self.coef for x in c]
        self.code +="".join(map(chr,cl))

    # Outputs a human readable string of the polynom. If isHTML is True
    # outputs an HTML blurb of the equation. Else output a plain text.
    def humanReadable(self, isHTML=False):
        variables = ('xn', 'yn', 'zn')
        equation = [""]*self.dimension
        for v, c in enumerate(self.coef): # Iterate on each dimension
            n = 0
            equation[v] = variables[v]+"+1="
            for i in range(self.order+1):
                for j in range(self.order-i+1):
                    if c[n] == 0:
                        n+=1
                        continue
                    if self.dimension == 2:
                        equation[v] += "%.3f*%s^%d*%s^%d+" % (c[n], variables[0], j, variables[1], i)
                        n += 1
                        continue
                    # if dimension == 3 we should end up here
                    for k in range(self.order-i-j+1):
                        if c[n] == 0:
                            n+=1
                            continue
                        equation[v] += "%.3f*%s^%d*%s^%d*%s^%d+" % (c[n], variables[0], k, variables[1], j, variables[2], i)
                        n+=1

            # Some cleanup
            for r in variables:
                equation[v] = equation[v].replace("*%s^0" % (r), "")
                equation[v] = equation[v].replace("*%s^1" % (r), "*%s" % (r))
            equation[v] = equation[v].replace("+-", "-")
            equation[v] = equation[v][:-1]

            if isHTML: # Convert this in a nice HTML equation
                equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
                equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
                equation[v] = re.sub(r'(x|y|z)n',r'\1<sub>n</sub>', equation[v])

        return equation

    def getPolynomLength(self):
        self.pl = int(math.factorial(self.order+self.dimension)/math.factorial(self.order)/math.factorial(self.dimension))

    def getRandomCoef(self):
        self.coef = [[random.randint(-30, 31)*self.codeStep for _ in range(0, self.pl)] for __ in range(self.dimension)]
        self.subtype = self.getSubtype()

    def getSubtype(self):
        if self.dimension == 2:
            pass
            # Need to check self.coef for subtypes
            # Henon map: xn+1 = 1 -axn**2 + yn, yn+1 = bxn
            # Tinkerbell map: xn+1 = xn2 - yn2 + axn + byn, yn+1=2*xn*yn + cxn+dyn
        return None

    def getNextPoint(self, p):
        l = list()
        try:
            for c in self.coef:
                result = 0
                n = 0
                for i in range(self.order+1):
                    for j in range(self.order-i+1):
                        if self.dimension == 2:
                            result += c[n]*(p[0]**j)*(p[1]**i)
                            n += 1
                            continue
                        for k in range(self.order-i-j+1):
                            result += c[n]*(p[0]**k)*(p[1]**j)*(p[2]**i)
                            n+=1
                l.append(result)
        except OverflowError:
            self.logger.error("Overflow during attractor computation.")
            self.logger.error("Either this is a very slowly diverging attractor, or you used a wrong code")
            return None

        return l if self.dimension == 3 else l + [0]

    def computeFractalDimension(self, a):
        # We lost the 3rd dimension when computing a 3D attractor (directly computing a z-map)
        # So fractal dimension has no meaning for 3D attractors
        self.fdim = 0.0 if self.dimension == 3 else util.computeBoxCountingDimension(a)

class DeJongAttractor(Attractor):
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
        c = [codelist[int(_/self.codeStep)-coderange[0]] for _ in self.coef]
        self.code +="".join(map(chr,c))

    def decodeCode(self):
        d = dict([(v, i) for i, v in enumerate(codelist)])
        self.coef = [(d[ord(_)]+coderange[0])*self.codeStep for _ in self.code[1:]]

    def getRandomCoef(self):
        self.coef = [random.randint(*coderange)*self.codeStep for _ in range(4)]

    def getNextPoint(self, p):
        return ( math.sin(self.coef[0]*p[1]) - math.cos(self.coef[1]*p[0]),
                 math.sin(self.coef[2]*p[0]) - math.cos(self.coef[3]*p[1]),
                 0, )

    def humanReadable(self, isHTML=False):
        equation = list()
        equation.append('xn+1=sin(%.3f*yn)-cos(%.3f*xn)' % (self.coef[0], self.coef[1]))
        equation.append('yn+1=sin(%.3f*xn)-cos(%.3f*yn)' % (self.coef[2], self.coef[3]))

        if isHTML: # Convert this in a nice HTML equation
            for v in range(2):
                equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
                equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
                equation[v] = re.sub(r'(x|y)n',r'\1<sub>n</sub>', equation[v])

        return equation

    def computeFractalDimension(self, a):
        self.fdim = min(2.0, util.computeBoxCountingDimension(a))

class CliffordAttractor(Attractor):
    """ CliffordAttractor. Very similar to De Jong, so could have been
        a subclass of DeJongAttractor, but probably clearer to subclass
        Attractor altogether
    """
    codeStep     = .0625 # Step to use to map ASCII character to coef

    def __init__(self, **kwargs):
        super(CliffordAttractor, self).__init__(**kwargs)
        if kwargs:
            if 'code' in kwargs and kwargs['code'] != None:
                self.code = kwargs['code']
                self.decodeCode() # Will populate coef
        self.dimension = 2

    def createCode(self):
        self.code = "c"
        # ASCII codes of digits and letters
        c = [codelist[int(_/self.codeStep)-coderange[0]] for _ in self.coef]
        self.code +="".join(map(chr,c))

    def decodeCode(self):
        d = dict([(v, i) for i, v in enumerate(codelist)])
        self.coef = [(d[ord(_)]+coderange[0])*self.codeStep for _ in self.code[1:]]

    def getRandomCoef(self):
        self.coef = [random.randint(*coderange)*self.codeStep for _ in range(4)]

    def getNextPoint(self, p):
        return ( math.sin(self.coef[0]*p[1]) + self.coef[1]*math.cos(self.coef[0]*p[0]),
                 math.sin(self.coef[2]*p[0]) + self.coef[3]*math.cos(self.coef[2]*p[1]),
                 0, )

    def humanReadable(self, isHTML=False):
        equation = list()
        equation.append('xn+1=sin(%.4f*yn)+%.4f*cos(%.4f*xn)' % (self.coef[0], self.coef[1], self.coef[0]))
        equation.append('yn+1=sin(%.4f*xn)+%.4f*cos(%.4f*yn)' % (self.coef[2], self.coef[3], self.coef[2]))
        equation[0] = equation[0].replace("+-", "-")
        equation[1] = equation[1].replace("+-", "-")

        if isHTML: # Convert this in a nice HTML equation
            for v in range(2):
                equation[v] = re.sub(r'\^(\d+)',r'<sup>\1</sup>', equation[v])
                equation[v] = re.sub(r'n\+1=',r'<sub>n+1</sub>=', equation[v])
                equation[v] = re.sub(r'(x|y)n',r'\1<sub>n</sub>', equation[v])

        return equation

    def computeFractalDimension(self, a):
        self.fdim = min(2.0, util.computeBoxCountingDimension(a))

class SymIconAttractor(Attractor):
    """ Symmetric icon attractors
    """
    codeStep     = .0625 # Step to use to map ASCII character to coef

    def __init__(self, **kwargs):
        super(SymIconAttractor, self).__init__(**kwargs)
        if kwargs:
            if 'code' in kwargs and kwargs['code'] != None:
                self.code = kwargs['code']
                self.decodeCode() # Will populate coef
        self.dimension = 2

    def createCode(self):
        self.code = "s"
        # ASCII codes of digits and letters
        c = [codelist[int(_/self.codeStep)-coderange[0]] for _ in self.coef[0:5]]
        c.append(codelist[0]+self.coef[5])
        self.code +="".join(map(chr,c))

    def decodeCode(self):
        d = dict([(v, i) for i, v in enumerate(codelist)])
        self.coef = [(d[ord(_)]+coderange[0])*self.codeStep for _ in self.code[1:6]]
        self.coef.append(ord(self.code[6])-codelist[0])

    def getRandomCoef(self):
        self.coef = [random.randint(*coderange)*self.codeStep for _ in range(5)]
        self.coef.append(random.choice(list(range(3, 13, 2))))

    def getNextPoint(self, p):
        z0  = complex(*p[0:2])
        rho = self.coef[0]*abs(z0)**2+self.coef[1]
        z   = z0**(self.coef[5]-1)
        zn  = z.real*z0.real - z.imag*z0.imag
        rho += self.coef[2]*zn
        znew = (complex(0, 1)*self.coef[4] + rho)*z0 + self.coef[3]*z.conjugate()
        return ( znew.real, znew.imag, 0,)

    def humanReadable(self, isHTML=False):
        return ("NA", "NA")

    def computeFractalDimension(self, a):
        self.fdim = min(2.0, util.computeBoxCountingDimension(a))

