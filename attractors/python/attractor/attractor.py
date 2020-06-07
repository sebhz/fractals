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

"""
Classes to generate and iterate several flavors of strange attractors
"""
import random
import math
import re
import logging
from multiprocessing import Manager, Process
from . import util

LYAPUNOV_BOUND = 100000

DEF_PARAMS = {
    'code' : None,
    'dimension' : 2,
    'iter' : 1280*1024*util.OVERITERATE_FACTOR,
    'order' : 2,
}
MODULUS = lambda x, y, z: x*x + y*y + z*z

CODELIST = [ord(c) for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"]
CODEDICT = {ascii_code: index for index, ascii_code in enumerate(CODELIST)}
CODERANGE = (-int(len(CODELIST)/2)+1, int(len(CODELIST)/2))
EPSILON = 1e-6

class Attractor:
    """
    Base class representing an attractor. Should generally not be instanciated directly. Use one
    of its subclasses: PolyomialAttractor, DeJongAttractor, CliffordAttractor or SymIconAttractor
    """
    conv_delay = 128     # Number of points to ignore before checking convergence
    # Check convergence on conv_max_iter points only...
    # ...but we need quite a lot of points to get bounds right.
    conv_max_iter = 4*65536

    def __init__(self, **kwargs):
        get_param = lambda k: kwargs[k] if kwargs and k in kwargs else \
                              DEF_PARAMS[k] if k in DEF_PARAMS else \
                              None
        self.logger = logging.getLogger(__name__)
        self.lyapunov = {'nl': 0, 'lsum': 0, 'ly': 0}
        self.fdim = 0
        self.bound = None
        # TODO: type checking on parameters
        self.iterations = get_param('iter')
        self.dimension = get_param('dimension')
        if self.dimension < 2 or self.dimension > 3:
            self.logger.warning("Invalid dimension value %d. Forcing 2D.", self.dimension)
            self.dimension = 2
        # If self.iterations is lower than conv_max_iter...
        self.conv_max_iter = min(self.conv_max_iter, self.iterations)

    def __str__(self):
        try:
            return self.code
        except AttributeError: # No code attribute - fallback on basic __str__()
            return super(Attractor, self).__str__()

    def compute_lyapunov(self, cur_p, eps_p):
        """
        Computes an estimate of the attractor Lyapunov exponent.
        See J. Sprott book for an explanation of the method
        """
        new_eps_p = self.get_next_point(eps_p)
        if not new_eps_p:
            return eps_p
        displacement = [new_eps_coord - cur_coord \
                        for new_eps_coord, cur_coord in zip(new_eps_p, cur_p)]
        displacement_sq = MODULUS(*displacement)
        if displacement_sq == 0:
            self.logger.warning("Unable to compute Lyapunov exponent, but trying to go on...")
            return eps_p
        displacement_sq_deriv = displacement_sq/EPSILON/EPSILON
        relative_disp = 1/math.sqrt(displacement_sq_deriv)

        self.lyapunov['lsum'] += math.log(displacement_sq_deriv, 2)
        self.lyapunov['nl'] += 1
        self.lyapunov['ly'] = self.lyapunov['lsum'] / self.lyapunov['nl']
        return [cur_p[i]+relative_disp*x for i, x in enumerate(displacement)]

    def check_convergence(self, init_point=(0.1, 0.1, 0.0)):
        """
        Check if an attractor converges by estimating
        its Lyapunov exponent
        """
        self.lyapunov['lsum'], self.lyapunov['nl'] = (0, 0)
        min_p, max_p = ([LYAPUNOV_BOUND]*3, [-LYAPUNOV_BOUND]*3)
        cur_p = init_point
        eps_p = [x + EPSILON if i == 0 else x for i, x in enumerate(cur_p)]

        for i in range(self.conv_max_iter):
            new_p = self.get_next_point(cur_p)
            if not new_p:
                return False
            if MODULUS(*new_p) > 1000000: # Unbounded - not an SA
                return False
            if MODULUS(*[new_coord-cur_coord for new_coord, cur_coord in zip(new_p, cur_p)]) \
               < EPSILON:
                return False
            # Compute Lyapunov exponent... sort of
            eps_p = self.compute_lyapunov(new_p, eps_p)
            if self.lyapunov['ly'] < 0.005 and i > self.conv_delay: # Limit cycle
                return False
            if i > self.conv_delay:
                min_p = [min(new_coord, min_coord) for new_coord, min_coord in zip(new_p, min_p)]
                max_p = [max(new_coord, max_coord) for new_coord, max_coord in zip(new_p, max_p)]
            cur_p = new_p

        if not self.bound:
            self.bound = [coord for limit_point in (min_p, max_p) for coord in limit_point]
        return True

    def explore(self):
        """
        Find a set of random coefficients yielding a
        converging attractor
        """
        num = 1
        self.set_random_coef()
        while not self.check_convergence():
            num += 1
            self.set_random_coef()
        # Found one -> create corresponding code
        self.logger.debug("Attractor found after %d trials.", num)
        self.coef_to_code()

    def get_init_points(self, num_p):
        """
        Returns a set of random points inside an attractor bounding box,
        suitable as initial points (e.g. when iterating from
        the init points, the attractor converges).
        """
        init_points = list()

        while len(init_points) < num_p:
            if not self.bound:
                cur_p = (random.random(), random.random(), 0)
            else:
                x = self.bound[0] + random.random()*(self.bound[3]-self.bound[0])
                y = self.bound[1] + random.random()*(self.bound[4]-self.bound[1])
                z = self.bound[2] + random.random()*(self.bound[5]-self.bound[2])
                cur_p = (x, y, z)
            if self.check_convergence(cur_p):
                init_points.append(cur_p)

        return init_points

    def iterate_map(self,
                    window_geometry,
                    attractor_scaled_bb,
                    attractor_pieces,
                    index,
                    lock,
                    init_point=(0.1, 0.1, 0.0)):
        """
        Creates a frequency map of the attractor by iterating on its equation
        The map is a dictionary, indexed by pixel coordinate tuple (x, y).
        For 2D attractors, each dict entry contains the number of times
        the pixel was hit when iterating the attractor.
        For 3D attractors, each entry contains the Z buffer coordinate
        window_geometry is the (width, height) of the attractor rendering
        window, in pixels.
        """
        attractor_map = dict()
        cur_p = init_point

        ratio_x = (window_geometry[0]-1)/(attractor_scaled_bb[2]-attractor_scaled_bb[0])
        ratio_y = (window_geometry[1]-1)/(attractor_scaled_bb[3]-attractor_scaled_bb[1])
        # Scale real attractor point coordinates to pixel coordinates
        w_to_s = lambda p: (
            int((p[0] - attractor_scaled_bb[0])*ratio_x),
            int(window_geometry[1]-1 - (p[1]-attractor_scaled_bb[1])*ratio_y))

        for i in range(self.iterations):
            new_p = self.get_next_point(cur_p)
            if not new_p:
                attractor_pieces[index] = None
                return

            # Ignore the first points to get a proper convergence
            if i >= self.conv_delay:
                projected_pixel = w_to_s(new_p)

                if projected_pixel in attractor_map:
                    if self.dimension == 2:
                        attractor_map[projected_pixel] += 1
                    elif new_p[2] > attractor_map[projected_pixel]:
                        attractor_map[projected_pixel] = new_p[2]
                else:
                    if self.dimension == 2:
                        attractor_map[projected_pixel] = 1
                    else:
                        attractor_map[projected_pixel] = new_p[2]
            cur_p = new_p
        with lock:
            attractor_pieces[index] = attractor_map

    def merge_attractors(self, attractor_pieces):
        """
        Merge several attractors into one. Usually
        used to merged pieces of the same attractor
        generated by different threads.
        """
        merged_attractor = None
        i = 0

        for i, attractor_piece in enumerate(attractor_pieces):
            if attractor_piece is not None:
                merged_attractor = attractor_piece
                break

        if merged_attractor is None:
            self.logger.debug("Empty attractor. Trying to go on anyway.")
            return merged_attractor

        for attractor_piece in attractor_pieces[i+1:]:
            if attractor_piece is None:
                continue
            for pixel, value in attractor_piece.items():
                if pixel in merged_attractor:
                    if self.dimension == 2:
                        merged_attractor[pixel] += value
                    elif value > merged_attractor[pixel]:
                        merged_attractor[pixel] = value
                else:
                    merged_attractor[pixel] = value

        # For 3D, translate the Z buffer to have min equal to 0
        if self.dimension == 3:
            min_z = min(merged_attractor.values())
            for pixel in merged_attractor.keys():
                merged_attractor[pixel] -= min_z

        self.logger.debug("%d points in the attractor before any postprocessing.",
                          len(merged_attractor))
        return merged_attractor

    def create_frequency_map(self, window_geometry, nthreads):
        """
        Creates a frequency map of the attractor.
        This function spawns multiple threads, each iterating
        the attractor equation with a different initial points,
        then merges all the attractors pieces into one
        single attractor.
        """
        jobs = list()
        init_p = self.get_init_points(nthreads)

        # Scaled bounding box of the attractor
        attractor_scaled_bb = util.scale_bounds(self.bound, window_geometry)
        with Manager() as manager:
            attractor_pieces = manager.list([None]*nthreads)
            lock = manager.RLock()
            for i in range(nthreads):
                job = Process(group=None,
                              name='t'+str(i),
                              target=self.iterate_map,
                              args=(window_geometry,
                                    attractor_scaled_bb,
                                    attractor_pieces,
                                    i,
                                    lock,
                                    init_p[i]))
                jobs.append(job)
                job.start()

            for job in jobs:
                job.join()

            merged_attractor = self.merge_attractors(attractor_pieces)

        if not merged_attractor:
            return merged_attractor
        #self.compute_fractal_dimension(merged_attractor)

        self.logger.debug("Time to render the attractor.")
        return merged_attractor

    def get_next_point(self, cur_p):
        """
        Virtual method. Must be implemented by derived class
        """
        raise NotImplementedError()

    def coef_to_code(self):
        """
        Virtual method. Must be implemented by derived class
        """
        raise NotImplementedError()

    def set_random_coef(self):
        """
        Virtual method. Must be implemented by derived class
        """
        raise NotImplementedError()

class PolynomialAttractor(Attractor):
    """
    Polynomial attractor. See get_next_point method for the
    equations
    """
    code_step = .125 # Step to use to map ASCII character to coef

    def __init__(self, **kwargs):
        get_param = lambda k: kwargs[k] if kwargs and k in kwargs else \
                              DEF_PARAMS[k] if k in DEF_PARAMS else \
                              None
        super(PolynomialAttractor, self).__init__(**kwargs)
        self.code = get_param('code')
        if self.code:
            self.code_to_coef() # Will populate order, length and coef
        else:
            self.order = get_param('order')
            self.coef = None
            self.set_polynom_length()
        if self.dimension == 3:
            self.code_step /= 4

    def code_to_coef(self):
        """
        Convert a Sprott (=ASCII) code to a set
        of real coefficients for the attractor
        """
        self.dimension = int(self.code[0])
        self.order = int(self.code[1])
        self.set_polynom_length()

        self.coef = [[(CODEDICT[ord(_)]+CODERANGE[0])*self.code_step for _ in \
                      self.code[3+__*self.poly_length:3+(__+1)*self.poly_length]] \
                     for __ in range(self.dimension)]

    def coef_to_code(self):
        """
        Convert a set of real coefficients to
        a Sprott (=ASCII) code.
        """
        self.code = str(self.dimension)+str(self.order)
        self.code += "_"
        # ASCII codes of digits and letters
        ascii_codes = [CODELIST[int(x/self.code_step)-CODERANGE[0]] for c in self.coef for x in c]
        self.code += "".join(map(chr, ascii_codes))

    def human_readable(self, is_html=False):
        """
        Return human readable (=string form) equations of
        the attractor, either in plain text or in html.
        """
        variables = ('xn', 'yn', 'zn')
        equation = [""]*self.dimension
        for coord, coef_list in enumerate(self.coef): # Iterate on each dimension
            cur_coef = 0
            equation[coord] = variables[coord] + "+1="
            for i in range(self.order+1):
                for j in range(self.order-i+1):
                    if coef_list[cur_coef] == 0:
                        cur_coef += 1
                        continue
                    if self.dimension == 2:
                        equation[coord] += "%.3f*%s^%d*%s^%d+" % \
                                           (coef_list[cur_coef], variables[0], j, variables[1], i)
                        cur_coef += 1
                        continue
                    # if dimension == 3 we should end up here
                    for k in range(self.order-i-j+1):
                        if coef_list[cur_coef] == 0:
                            cur_coef += 1
                            continue
                        equation[coord] += "%.3f*%s^%d*%s^%d*%s^%d+" % \
                                           (coef_list[cur_coef], \
                                            variables[0], k, \
                                            variables[1], j, \
                                            variables[2], i)
                        cur_coef += 1

            # Some cleanup
            for variable in variables:
                equation[coord] = equation[coord].replace("*%s^0" % (variable), "")
                equation[coord] = equation[coord].replace("*%s^1" % (variable), "*%s" % (variable))
            equation[coord] = equation[coord].replace("+-", "-")
            equation[coord] = equation[coord][:-1]

            if is_html: # Convert this in a nice HTML equation
                equation[coord] = re.sub(r'\^(\d+)', r'<sup>\1</sup>', equation[coord])
                equation[coord] = re.sub(r'n\+1=', r'<sub>n+1</sub>=', equation[coord])
                equation[coord] = re.sub(r'(x|y|z)n', r'\1<sub>n</sub>', equation[coord])

        return equation

    def set_polynom_length(self):
        """
        Return the number of coefficient of a polynom
        depending on its order and dimension (C(n, p))
        """
        self.poly_length = int(math.factorial(self.order+self.dimension) /\
                               math.factorial(self.order)/math.factorial(self.dimension))

    def set_random_coef(self):
        """
        Generate a set of random coefficients
        for the attractor
        """
        self.coef = [[random.randint(*CODERANGE)*self.code_step for _ in range(self.poly_length)] \
                     for __ in range(self.dimension)]

    def get_next_point(self, cur_p):
        """
        Computes next point of the attractor by
        applying the attractor equation on current point.

        Equations:
            x(n+1) = Px(x(n), y(n), z(n)),
            y(n+1) = Py(x(n,) y(n), z(n)),
            z(n+1) = Pz(x(n), y(n), z(n))
        with Px, Py and Pz polynoms.
        """
        next_p = list()
        try:
            for cur_coef_list in self.coef:
                result = 0
                cur_coef = 0
                for i in range(self.order+1):
                    for j in range(self.order-i+1):
                        if self.dimension == 2:
                            result += cur_coef_list[cur_coef]*(cur_p[0]**j)*(cur_p[1]**i)
                            cur_coef += 1
                            continue
                        for k in range(self.order-i-j+1):
                            result += cur_coef_list[cur_coef]*(cur_p[0]**k)*\
                                      (cur_p[1]**j)*(cur_p[2]**i)
                            cur_coef += 1
                next_p.append(result)
        except OverflowError:
            self.logger.error("Overflow during attractor computation.")
            self.logger.error("This is a slowly diverging attractor, or you used a wrong code.")
            return None

        return next_p if self.dimension == 3 else next_p + [0]

    def compute_fractal_dimension(self, a_map):
        """
        Compute an estimate of the attractor fractal dimension
        using box-counting (=Minkowski-Bouligand) method.
        Work on the attractor map (using window coordinates)
        """
        # We lost the 3rd dimension when computing a 3D attractor (directly computing a z-map)
        # So fractal dimension has no meaning for 3D attractors
        self.fdim = 0.0 if self.dimension == 3 else util.compute_box_counting_dimension(a_map)

class DeJongAttractor(Attractor):
    """
    Peter De Jong Attractor. See get_next_point method for the
    equations
    """
    code_step = .125 # Step to use to map ASCII character to coef

    def __init__(self, **kwargs):
        super(DeJongAttractor, self).__init__(**kwargs)
        self.coef = None
        if kwargs:
            if 'code' in kwargs and kwargs['code'] is not None:
                self.code = kwargs['code']
                self.code_to_coef() # Will populate coef
        self.dimension = 2

    def coef_to_code(self):
        """
        Convert a set of real coefficients to
        a Sprott (=ASCII) code.
        """
        self.code = "j"
        # ASCII codes of digits and letters
        ascii_codes = [CODELIST[int(_/self.code_step)-CODERANGE[0]] for _ in self.coef]
        self.code += "".join(map(chr, ascii_codes))

    def code_to_coef(self):
        """
        Convert a Sprott (=ASCII) code to a set
        of real coefficients for the attractor
        """
        self.coef = [(CODEDICT[ord(_)]+CODERANGE[0])*self.code_step for _ in self.code[1:]]

    def set_random_coef(self):
        """
        Generate a set of random coefficients
        for the attractor
        """
        self.coef = [random.randint(*CODERANGE)*self.code_step for _ in range(4)]

    def get_next_point(self, cur_p):
        """
        Computes next point of the attractor by
        applying the attractor equation on current point.

        Equations:
            x(n+1) = sin(a*y(n)) - cos(b*x(n))
            y(n+1) = sin(c*x(n)) - cos(d*y(n))
        """
        return (math.sin(self.coef[0]*cur_p[1]) - math.cos(self.coef[1]*cur_p[0]),
                math.sin(self.coef[2]*cur_p[0]) - math.cos(self.coef[3]*cur_p[1]),
                0,)

    def human_readable(self, is_html=False):
        """
        Return human readable (=string form) equations of
        the attractor, either in plain text or in html.
        """
        equation = list()
        equation.append('xn+1=sin(%.3f*yn)-cos(%.3f*xn)' % (self.coef[0], self.coef[1]))
        equation.append('yn+1=sin(%.3f*xn)-cos(%.3f*yn)' % (self.coef[2], self.coef[3]))

        if is_html: # Convert this in a nice HTML equation
            for coord in range(2):
                equation[coord] = re.sub(r'\^(\d+)', r'<sup>\1</sup>', equation[coord])
                equation[coord] = re.sub(r'n\+1=', r'<sub>n+1</sub>=', equation[coord])
                equation[coord] = re.sub(r'(x|y)n', r'\1<sub>n</sub>', equation[coord])

        return equation

    def compute_fractal_dimension(self, a_map):
        """
        Compute an estimate of the attractor fractal dimension
        using box-counting (=Minkowski-Bouligand) method
        Work on the attractor map (using window coordinates)
        """
        self.fdim = min(2.0, util.compute_box_counting_dimension(a_map))

class CliffordAttractor(Attractor):
    """
    CliffordAttractor. Very similar to De Jong, so could have been
    a subclass of DeJongAttractor, but probably clearer to subclass
    Attractor altogether
    """
    code_step = .0625 # Step to use to map ASCII character to coef

    def __init__(self, **kwargs):
        super(CliffordAttractor, self).__init__(**kwargs)
        self.coef = None
        if kwargs:
            if 'code' in kwargs and kwargs['code'] is not None:
                self.code = kwargs['code']
                self.code_to_coef() # Will populate coef
        self.dimension = 2

    def coef_to_code(self):
        """
        Convert a set of real coefficients to
        a Sprott (=ASCII) code.
        """
        self.code = "c"
        # ASCII codes of digits and letters
        ascii_codes = [CODELIST[int(_/self.code_step)-CODERANGE[0]] for _ in self.coef]
        self.code += "".join(map(chr, ascii_codes))

    def code_to_coef(self):
        """
        Convert a Sprott (=ASCII) code to a set
        of real coefficients for the attractor
        """
        self.coef = [(CODEDICT[ord(_)] + CODERANGE[0]) * self.code_step for _ in self.code[1:]]

    def set_random_coef(self):
        """
        Generate a set of random coefficients
        for the attractor
        """
        self.coef = [random.randint(*CODERANGE) * self.code_step for _ in range(4)]

    def get_next_point(self, cur_p):
        """
        Computes next point of the attractor by
        applying the attractor equation on current point.

        Equations:
            x(n+1) = sin(a*y(n)) + b*cos(a*x(n))
            y(n+1) = sin(c*x(n)) + d*cos(c*y(n))
        """
        return (math.sin(self.coef[0]*cur_p[1]) + self.coef[1]*math.cos(self.coef[0]*cur_p[0]),
                math.sin(self.coef[2]*cur_p[0]) + self.coef[3]*math.cos(self.coef[2]*cur_p[1]),
                0, )

    def human_readable(self, is_html=False):
        """
        Return human readable (=string form) equations of
        the attractor, either in plain text or in html.
        """
        equation = list()
        equation.append('xn+1=sin(%.4f*yn)+%.4f*cos(%.4f*xn)' % \
                        (self.coef[0], self.coef[1], self.coef[0]))
        equation.append('yn+1=sin(%.4f*xn)+%.4f*cos(%.4f*yn)' % \
                        (self.coef[2], self.coef[3], self.coef[2]))
        equation[0] = equation[0].replace("+-", "-")
        equation[1] = equation[1].replace("+-", "-")

        if is_html: # Convert this in a nice HTML equation
            for coord in range(2):
                equation[coord] = re.sub(r'\^(\d+)', r'<sup>\1</sup>', equation[coord])
                equation[coord] = re.sub(r'n\+1=', r'<sub>n+1</sub>=', equation[coord])
                equation[coord] = re.sub(r'(x|y)n', r'\1<sub>n</sub>', equation[coord])

        return equation

    def compute_fractal_dimension(self, a_map):
        """
        Compute an estimate of the attractor fractal dimension
        using box-counting (=Minkowski-Bouligand) method
        Work on the attractor map (using window coordinates)
        """
        self.fdim = min(2.0, util.compute_box_counting_dimension(a_map))

class SymIconAttractor(Attractor):
    """ Symmetric icon attractors
    """
    code_step = .125 # Step to use to map ASCII character to coef

    def __init__(self, **kwargs):
        super(SymIconAttractor, self).__init__(**kwargs)
        self.w_i = 0
        self.coef = None
        if kwargs:
            if 'code' in kwargs and kwargs['code'] is not None:
                self.code = kwargs['code']
                self.code_to_coef() # Will populate coef
        self.dimension = 2

    def coef_to_code(self):
        """
        Convert a set of real coefficients to
        a Sprott (=ASCII) code.
        """
        self.code = "s"
        # ASCII codes of digits and letters
        ascii_codes = [CODELIST[int(_/self.code_step)-CODERANGE[0]] for _ in self.coef[0:5]]
        ascii_codes.append(CODELIST[0] + self.coef[5])
        self.code += "".join(map(chr, ascii_codes))

    def code_to_coef(self):
        """
        Convert a Sprott (=ASCII) code to a set
        of real coefficients for the attractor
        """
        self.coef = [(CODEDICT[ord(_)]+CODERANGE[0])*self.code_step for _ in self.code[1:6]]
        self.coef.append(ord(self.code[6])-CODELIST[0])
        self.w_i = self.coef[1] + complex(0, 1)*self.coef[4]

    def set_random_coef(self):
        """
        Generate a set of random coefficients
        for the attractor
        """
        self.coef = [random.randint(*CODERANGE)*self.code_step for _ in range(5)]
        self.coef.append(random.choice(list(range(3, 9))))
        self.w_i = self.coef[1] + complex(0, 1)*self.coef[4]

    def get_next_point(self, cur_p):
        """
        Computes next point of the attractor by
        applying the attractor equation on current point.

        Equation (complex):
            z(n+1) = (lambda + i.omega + alpha.z(n).z(n)bar +
                     beta.re(z(n)**m)).z(n) + gamma.z(n)**(m-1)bar
        """
        z = complex(*cur_p[0:2])
        zmminus = z**(self.coef[5]-1)
        rezm = (z*zmminus).real
        znew = (self.w_i + self.coef[0]*z*z.conjugate() + self.coef[2]*rezm)*z + \
               self.coef[3]*zmminus.conjugate()
        return (znew.real, znew.imag, 0,)

    def human_readable(self, is_html=False):
        """
        Return human readable (=string form) equations of
        the attractor, either in plain text or in html.
        """
        equation = list()
        if is_html:
            equation.append('z<sub>n+1</sub>=(&lambda; + i&omega; + \
                             &alpha;z<sub>n</sub>conj(z<sub>n</sub>) + \
                             &beta;Re(z<sub>n</sub><sup>m</sup>))z<sub>n</sub> + \
                             &gamma;conj(z<sub>n</sub><sup>m-1</sup>)')
            equation.append('&lambda;=%.3f - &alpha;=%.3f - &beta;=%.3f - \
                             &gamma;=%.3f - &omega;=%.3f - m=%d' % \
                            (self.coef[1], self.coef[0], self.coef[2], \
                             self.coef[3], self.coef[4], self.coef[5]))
        else:
            equation.append('zn+1 = (lambda + i.omega + alpha.zn.znbar + \
                             beta.re(zn**m)).z + gamma.zn**(m-1)bar')
            equation.append('Lambda=%.3f - Alpha=%.3f - Beta=%.3f - Gamma=%.3f - \
                             Omega=%.3f - m=%d' % \
                            (self.coef[1], self.coef[0], self.coef[2], \
                             self.coef[3], self.coef[4], self.coef[5]))
        return equation

    def compute_fractal_dimension(self, a_map):
        """
        Compute an estimate of the attractor fractal dimension
        using box-counting (=Minkowski-Bouligand) method
        Work on the attractor map (using window coordinates)
        """
        self.fdim = min(2.0, util.compute_box_counting_dimension(a_map))
