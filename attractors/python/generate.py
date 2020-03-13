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
# Some coloring ideas (histogram equalization) taken from
# Ian Witham's blog
# http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/

from attractor import attractor, render, util
from time import time

import random
import argparse
import sys
import os
import logging
import cv2

LOGLEVELS = (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET)

defaultParameters = {
    'bpc': 8,
    'geometry': '1280x1024',
    'iter': 1280*1024*util.OVERITERATE_FACTOR,
    'loglevel': 3,
    'number': 1,
    'order': 2,
    'outdir': 'png',
    'sub': 1,
    'threads': 1,
    'type': 'polynomial',
    'dimension': 2,
}

def sec2hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%dh%02dm%02ds" % (h, m, s)

def createAttractor():
    if args.type == 'dejong':
        at = attractor.DeJongAttractor(iter = int(args.iter/args.threads),
                    code = args.code)
    elif args.type == 'clifford':
        at = attractor.CliffordAttractor(iter = int(args.iter/args.threads),
                    code = args.code)
    elif args.type == 'icon':
        at = attractor.SymIconAttractor(iter = int(args.iter/args.threads),
                    code = args.code)
    else:
        at = attractor.PolynomialAttractor(order = args.order,
                    iter = int(args.iter/args.threads),
                    code = args.code, dimension = args.dimension)

    if args.code:
        if not at.checkConvergence():
            logging.warning("Not an attractor it seems... but trying to display it anyway.")
    else:
        at.explore()

    logging.debug("Converging attractor found. Boundaries: %s" % (str(at.bound)))

    return at

def getCloseCoef(a, step):
    coefMod=list()
    if args.type == 'polynomial':
        for d in range(a.dimension):
            coefMod.append((random.randint(0, a.pl-1), step*random.choice((-1, 1))))
    else:
        for d in range(2):
            coefMod.append((random.randint(0, 1), step*random.choice((-1, 1))))
    return coefMod

"""
Generate a sequence of converging attractors "close to each other"
"""
def generateAttractorSequence(r, nthreads):
    sequenceSize = args.sequence or 1024
    coefStep = 0.125/16
    coefList = list()

    # Find a nice attractor to start with !
    while True:
        at = createAttractor()
        a = at.createFrequencyMap(r.geometry, nthreads)
        # Will also test if a is null
        if r.isNice(a):
            break
    bounds   = at.bound
    args.code = None

    for num in range(sequenceSize):
        logging.debug("Attractor #%d in sequence." % (num))
        coefList.append([ x[:] for x in at.coef ])
        bounds = [min(x) for x in zip(bounds[0:3], at.bound[0:3])] + [max(x) for x in zip(bounds[3:6], at.bound[3:6])]
        currentCoef = at.coef
        # Modify the attractor coefficients. Backup and try gain until resulting attractor converges
        while True:
            coefMod = getCloseCoef(at, coefStep)
            at.bound = None # We only update bounds if they do not exist !
            for d in range(at.dimension):
                coefModPosition = coefMod[d][0]
                at.coef[d][coefModPosition] += coefMod[d][1]
            if at.checkConvergence():
                break
            # We did not converge: backup one step and try again
            at.coef = currentCoef

    logging.info("Attractor sequence generated. %d converging attractors in the sequence." % (sequenceSize))
    logging.debug("Attractors bounding box: %s." % (str(bounds)))

    for i, c in enumerate(coefList):
        at.coef  = c
        at.bound = bounds
        a        = at.createFrequencyMap(r.geometry, nthreads)
        img      = r.renderAttractor(a)

        path = os.path.join(args.outdir, at.code + "_" + "%04d" % i + ".png")
        cv2.imwrite(path, img)

def generateSingleAttractor(r, nthreads):
    t0 = time()
    while True:
        at = createAttractor()
        a = at.createFrequencyMap(r.geometry, nthreads)
        # Will also test if a is null
        if r.isNice(a) or args.code:
            at.computeFractalDimension(a)
            img = r.renderAttractor(a)
            break
    t1 = time()

    logging.info("Attractor type: %s" % args.type)
    if args.type == 'polynomial':
        logging.info("Polynom order: %d" % int(at.code[1]))
    logging.info("Dimension: %.3f" % at.fdim)
    logging.info("Lyapunov exponent: %.3f" % at.lyapunov['ly'])
    logging.info("Code: %s" % at.code)
    logging.info("Iterations: %d" % args.iter)
    logging.info("Attractor generation and rendering took %s." % sec2hms(t1-t0))

    if args.png:
        filepath = os.path.join(args.outdir, at.code + ".png")
        cv2.imwrite(filepath, img)
    else:
        cv2.imshow(at.code, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def generateAttractor(geometry, nthreads):
    if args.palette == None:
        args.palette = random.choice(range(len(render.Renderer.pal_templates)))

    r  = render.Renderer(bpc=args.bpc,
            geometry=geometry,
            downsampleRatio=args.downsample,
            dimension=args.dimension,
            paletteIndex=args.palette)

    try:
        os.makedirs(args.outdir)
    except OSError:
        if not os.path.isdir(args.outdir):
            raise

    if args.sequence:
        generateAttractorSequence(r, nthreads)
    else:
        generateSingleAttractor(r, nthreads)

def parseArgs():
    parser = argparse.ArgumentParser(description='Playing with strange attractors')
    parser.add_argument('-b', '--bpc',          help='bits per component (default = %d)' % defaultParameters['bpc'], default=defaultParameters['bpc'], type=int, choices=list(range(1, 17)))
    parser.add_argument('-c', '--code',         help='attractor code', type=str)
    parser.add_argument('-d', '--dimension',    help='attractor dimension (2 or 3)', type=int, choices=(2, 3), default=defaultParameters['dimension'])
    parser.add_argument('-g', '--geometry',     help='image geometry (XxY form - default = %s)' % defaultParameters['geometry'], default=defaultParameters['geometry'])
    parser.add_argument('-j', '--threads',      help='Number of threads to use (default = %d)' % defaultParameters['threads'], type=int, default=defaultParameters['threads'])
    parser.add_argument('-l', '--loglevel',     help='Sets log level (the higher the more verbose - default = %d)' % defaultParameters['loglevel'], default=defaultParameters['loglevel'], type=int, choices=list(range(len(LOGLEVELS))))
    parser.add_argument('-i', '--iter',         help='attractor number of iterations', type=int)
    parser.add_argument('-n', '--number',       help='number of attractors to generate (default = %d)' % defaultParameters['number'], default=defaultParameters['number'], type=int)
    parser.add_argument('-o', '--order',        help='attractor order (default = %d)' % defaultParameters['order'], default=defaultParameters['order'], type=int)
    parser.add_argument('-O', '--outdir',       help='output directory for generated image (default = %s)' % defaultParameters['outdir'], default=defaultParameters['outdir'], type=str)
    parser.add_argument('-p', '--png',          help='save the attractor in a png file', action='store_true')
    parser.add_argument('-P', '--palette',      help='color palette number', type=int, choices=range(len(render.Renderer.pal_templates)))
    parser.add_argument('-q', '--sequence',     help='generate a sequence of SEQUENCE attractors', type=int)
    parser.add_argument('-s', '--downsample',   help='downsample ratio (default = %d)' % defaultParameters['sub'], default = defaultParameters['sub'], type=int, choices=(2, 3, 4))
    parser.add_argument('-t', '--type',         help='attractor type (default = %s)' % defaultParameters['type'], default = defaultParameters['type'], type=str, choices=("polynomial", "dejong", "clifford", "icon"))
    args = parser.parse_args()
    if args.code:
        if args.code[0] == 'j':
            args.type = 'dejong'
        elif args.code[0] == 'c':
            args.type = 'clifford'
        elif args.code[0] == 's':
            args.type = 'icon'
    return args

# ----------------------------- Main loop ----------------------------- #

args = parseArgs()
logging.basicConfig(stream=sys.stderr, level=LOGLEVELS[args.loglevel])
random.seed()

g = [int(x) for x in args.geometry.split('x')]
#TODO - check validity of g

idealIter = util.getIdealIterationNumber(args.type, g, args.downsample)
if args.iter == None:
    args.iter = idealIter
    logging.debug("Setting iteration number to %d." % (args.iter))
elif args.iter < idealIter:
    logging.warning("For better rendering, you should use at least %d iterations." % idealIter)

if args.code or args.sequence: args.number = 1

for i in range(0, args.number):
    generateAttractor(g, args.threads)
