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
"""
Example script using the attractor lib to create and display attractors
"""
import random
import argparse
import sys
import os
import logging
from time import time

from attractor import attractor, render, util, palettes

LOGLEVELS = (logging.CRITICAL,
             logging.ERROR,
             logging.WARNING,
             logging.INFO,
             logging.DEBUG,
             logging.NOTSET)

DFT_OPTS = {
    'bpc': 8,
    'geometry': '1280x1024',
    'iterations': 1280*1024*util.OVERITERATE_FACTOR,
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
    """
    Converts a seconds value in an "HMS" string
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%dh%02dm%02ds" % (hours, minutes, seconds)

def create_attractor(options):
    """
    Find and returns a converging attractor
    """
    if options.type == 'dejong':
        att = attractor.DeJongAttractor(iterations=int(options.iterations/options.threads),
                                        code=options.code)
    elif options.type == 'clifford':
        att = attractor.CliffordAttractor(iterations=int(options.iterations/options.threads),
                                          code=options.code)
    elif options.type == 'icon':
        att = attractor.SymIconAttractor(iterations=int(options.iterations/options.threads),
                                         code=options.code)
    else:
        att = attractor.PolynomialAttractor(order=options.order,
                                            iterations=int(options.iterations/options.threads),
                                            code=options.code,
                                            dimension=options.dimension)

    if options.code:
        if not att.check_convergence():
            logging.warning("The specified attractor does not seem to converge. Bailing out.")
            sys.exit()
    else:
        att.explore()

    logging.debug("Converging attractor found.")
    if options.dimension == 3:
        logging.debug("Boundaries: (%.3f, %.3f, %.3f) (%.3f, %.3f, %.3f)", *att.bound)
    else:
        logging.debug("Boundaries: (%.3f, %.3f) (%.3f, %.3f)",
                      *(att.bound[0:2]+att.bound[3:5]))
    return att

def generate_attractor(geometry, options):
    """
    Generate and display an attractor
    """
    if options.palette is None:
        options.palette = random.choice(range(len(palettes.pal_templates)))

    renderer = render.Renderer(bpc=options.bpc,
                               geometry=geometry,
                               downsample_ratio=options.downsample,
                               dimension=options.dimension,
                               palette_index=options.palette)

    try:
        os.makedirs(options.outdir)
    except OSError:
        if not os.path.isdir(options.outdir):
            raise

    t_0 = time()
    while True:
        att = create_attractor(options)
        att_map = att.create_frequency_map(renderer.geometry, options.threads)
        # Will also test if a is null
        if renderer.is_nice(att_map) or options.code:
            att.compute_fractal_dimension(att_map)
            img = renderer.render_attractor(att_map)
            break
    t_1 = time()

    logging.info("Attractor type: %s %s",
                 options.type,
                 "(order = %d)" % (int(att.code[1])) if options.type == 'polynomial' else
                 "(symmetry = %d)" % (int(att.coef[5])) if options.type == 'icon' else
                 "")
    if options.type == 'polynomial':
        logging.info("Polynom order: %d", int(att.code[1]))
    logging.info("Dimension: %.3f", att.fdim)
    logging.info("Lyapunov exponent: %.3f", att.lyapunov['ly'])
    logging.info("Code: %s", att.code)
    logging.info("Iterations: %d", options.iterations)
    logging.info("Attractor generation and rendering took %s.", sec2hms(t_1-t_0))

    if options.png:
        filepath = os.path.join(options.outdir, att.code + ".png")
        img.save(filepath)
    else:
        img.show(att.code)

def parse_args():
    """
    Parses our glorious arguments - or assign sensible default values to them
    """
    parser = argparse.ArgumentParser(description='Playing with strange attractors')
    parser.add_argument('-b', '--bpc',
                        help='bits per component (default = %d)' % DFT_OPTS['bpc'],
                        default=DFT_OPTS['bpc'],
                        type=int, choices=list(range(1, 17)))
    parser.add_argument('-c', '--code',
                        help='attractor code', type=str)
    parser.add_argument('-d', '--dimension',
                        help='attractor dimension (2 or 3)',
                        type=int,
                        choices=(2, 3), default=DFT_OPTS['dimension'])
    parser.add_argument('-g', '--geometry',
                        help='image geometry (XxY form - default = %s)' % DFT_OPTS['geometry'],
                        default=DFT_OPTS['geometry'])
    parser.add_argument('-j', '--threads',
                        help='Number of threads to use (default = %d)' % DFT_OPTS['threads'],
                        type=int,
                        default=DFT_OPTS['threads'])
    parser.add_argument('-l', '--loglevel',
                        help='log level (high is verbose - default = %d)' % DFT_OPTS['loglevel'],
                        default=DFT_OPTS['loglevel'],
                        type=int,
                        choices=list(range(len(LOGLEVELS))))
    parser.add_argument('-i', '--iterations',
                        help='attractor number of iterations', type=int)
    parser.add_argument('-n', '--number',
                        help='number of attractors to generate (default %d)' % DFT_OPTS['number'],
                        default=DFT_OPTS['number'],
                        type=int)
    parser.add_argument('-o', '--order',
                        help='attractor order (default = %d)' % DFT_OPTS['order'],
                        default=DFT_OPTS['order'],
                        type=int)
    parser.add_argument('-O', '--outdir',
                        help='output dir for image (default = %s)' % DFT_OPTS['outdir'],
                        default=DFT_OPTS['outdir'],
                        type=str)
    parser.add_argument('-p', '--png',
                        help='save the attractor in a png file',
                        action='store_true')
    parser.add_argument('-P', '--palette',
                        help='color palette number',
                        type=int,
                        choices=range(len(palettes.pal_templates)))
    parser.add_argument('-s', '--downsample',
                        help='downsample ratio (default = %d)' % DFT_OPTS['sub'],
                        default=DFT_OPTS['sub'],
                        type=int,
                        choices=(2, 3, 4))
    parser.add_argument('-t', '--type',
                        help='attractor type (default = %s)' % DFT_OPTS['type'],
                        default=DFT_OPTS['type'],
                        type=str, choices=("polynomial", "dejong", "clifford", "icon"))
    _args = parser.parse_args()
    if _args.code:
        _args.number = 1
        if _args.code[0] == 'j':
            _args.type = 'dejong'
        elif _args.code[0] == 'c':
            _args.type = 'clifford'
        elif _args.code[0] == 's':
            _args.type = 'icon'
    return _args

# ----------------------------- Main loop ----------------------------- #

random.seed()
ARGS = parse_args()
logging.basicConfig(stream=sys.stderr, level=LOGLEVELS[ARGS.loglevel])

try:
    WINDOW_GEOMETRY = [int(x) for x in ARGS.geometry.split('x')]
except ValueError:
    logging.error("Bad geometry string. Exiting.")
    sys.exit(1)

if len(WINDOW_GEOMETRY) != 2 or WINDOW_GEOMETRY[0] <= 0 or WINDOW_GEOMETRY[1] <= 0:
    logging.error("Bad geometry string. Exiting.")
    sys.exit(1)

IDEAL_ITER = util.get_ideal_iteration_number(WINDOW_GEOMETRY, ARGS.downsample)
if ARGS.iterations is None:
    ARGS.iterations = IDEAL_ITER
    logging.debug("Setting iteration number to %d.", ARGS.iterations)
elif ARGS.iterations < IDEAL_ITER:
    logging.warning("For better rendering, you should use at least %d iterations.", IDEAL_ITER)

for i in range(0, ARGS.number):
    generate_attractor(WINDOW_GEOMETRY, ARGS)
