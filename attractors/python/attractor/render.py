#!/usr/bin/python3
"""
Renderer module for attractors
Contains one single Renderer class
"""
import logging
import random
import colorsys
import numpy
import cv2
from . import palettes

DEF_PARAMS = {
    'downsample_ratio': 1,
    'bpc' : 8,
    'dimension' : 2,
    'geometry' : (800, 600),
    'palette_index': None
}
INTERNAL_BPC = 16
INTERNAL_COLOR_DEPTH = (1<<INTERNAL_BPC) - 1

def equalize_attractor(att):
    """
    Performs histogram equalization on the attractor
    frequency map. Equalized values will be used
    to modify the value field of hsv color components
    """
    pools = [0]*(1<<INTERNAL_BPC)

    # Create cumulative distribution
    for frequency in att.values():
        pools[frequency] += 1
    for i in range(len(pools) - 1):
        pools[i+1] += pools[i]

    # Stretch the values to the [1, (1<<INTERNAL_BPC)-1] range
    for i, cum_freq in enumerate(pools):
        pools[i] = 1 + (INTERNAL_COLOR_DEPTH - 1)*(cum_freq-pools[0])/(pools[-1]-pools[0])

    # Now reapply the stretched values
    for pixel, frequency in att.items():
        att[pixel] = round(pools[frequency])


class Renderer:
    """
    Renderer class.
    Set of methods to resize, colorize an attractor frequency map
    """
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)

        for kw_name, kw_def_value in DEF_PARAMS.items():
            setattr(self, kw_name, kw_def_value)

        for kw_name, kw_value in kwargs.items():
            if not kw_name in DEF_PARAMS:
                raise KeyError("Invalid parameter %s passed to %s" % (kw_name, __name__))
            setattr(self, kw_name, kw_value)

        self.geometry = [x*self.downsample_ratio for x in self.geometry]
        if self.dimension < 2 or self.dimension > 3:
            self.logger.warning("Trying to create renderer with invalid dimension (%d). \
                                 Defaulting to 2.", self.dimension)
            self.dimension = 2

        if self.palette_index is None:
            self.palette_index = random.choice(range(len(palettes.pal_templates)))
        self.palette = dict()

    def get_palette(self, frequencies):
        """
        Creates a color palette from a given template, and size it
        to the number of frequencies passed in argument.
        """
        self.logger.debug("Choosing palette %d (%s)",
                          self.palette_index,
                          palettes.pal_templates[self.palette_index]['name'])
        template = palettes.pal_templates[self.palette_index]
        gradient = palettes.getGradient(template['gradient_map'],
                                        len(frequencies),
                                        template['colorspace'])
        while len(gradient) < len(frequencies):
            gradient.append(gradient[-1])

        colormap = dict()
        for i, freq in enumerate(sorted(frequencies)):
            norm_freq = freq/INTERNAL_COLOR_DEPTH
            if template['invert_value']:
                norm_freq = 1.0 - norm_freq
            norm_freq = template['value_offset'] + norm_freq * (1-template['value_offset'])
            (r, g, b) = colorsys.hsv_to_rgb(gradient[i][0], gradient[i][1], norm_freq)
            colormap[freq] = tuple([round(component*((1<<self.bpc)-1)) for component in (b, g, r)])

        self.palette['background'] = tuple(reversed(\
                                     [round(component * ((1 << self.bpc)-1)) \
                                      for component in palettes.rgb_norm(template['background'])]))
        self.palette['colormap'] = colormap

    def colorize_attractor(self, att):
        """
        Get a palette and apply it to the attractor
        Attractor: dict indexed by pixel coord (X,Y) tuple
        containing frequency each pixel (=number of times
        a given pixel was hit during attractor iteration)
        """
        self.get_palette(list(set(att.values())))

        for pixel, frequency in att.items():
            att[pixel] = self.palette['colormap'][frequency]

        self.logger.debug("Number of unique colors in the attractor after colorization: %d.",
                          len(set(att.values())))

    # Creates the final image array
    def create_image_array(self, att):
        """
        Create the final image array (full array of pixels)
        from the attractor pixels and palette.
        We get a set of attractor point, we return a rectangular
        image where all the points not in the attractor have the
        palette background color.
        """
        (width, height) = self.geometry[0:2]

        img = [[list(self.palette['background']) for col in range(0, width)] \
               for row in range(0, height)]
        for pixel, frequency in att.items():
            (col, row) = pixel
            try:
                img[row][col] = list(frequency)
            except IndexError:
                # This can occur if the bounds were not correctly assessed
                # and a point of the attractor happens to fall out of them.
                self.logger.debug("Looks like a point fell out of our bounds. Ignoring it.")
        return img

    def render_attractor(self, att):
        """
        Render the attractor
            - attractor: attractor points: dict (X,Y) and containing :
                - frequency for 2D
                - Z for 3D

        1- Perform histogram equalization on the attractor frequency
        2- Colorize the attractor (map frequency to color gradient)
        3- if needed downsize the attractor
        """
        if not att:
            return None
        max_freq = max(att.values())

        self.logger.debug("Number of frequencies in attractor: %d", len(set(att.values())))
        # Now send the map in the [0, (1<<self.INTERNAL_BPC)-1] range
        for pixel, freq in att.items():
            att[pixel] = int(freq*INTERNAL_COLOR_DEPTH/max_freq)

        equalize_attractor(att)
        self.colorize_attractor(att)
        img = numpy.asarray(self.create_image_array(att)).astype(numpy.uint8)
        img = cv2.resize(img,
                         tuple([int(dimension/self.downsample_ratio) \
                                for dimension in self.geometry[0:2]]),
                         interpolation=cv2.INTER_CUBIC)
        self.logger.debug("Number of colors in attractor after downsampling: %d.",
                          len({tuple(color) for row in img for color in row}))

        return img

    def is_nice(self, att, cover_limit=0.01):
        """
        Checks if the attractor passed is 'nice': currently nice means that the
        attractor covers more than cover_limit percent of the window.
        """
        if not att:
            return False
        n_att_points = len(att)
        n_pixels = self.geometry[0]*self.geometry[1]
        cover_ratio = n_att_points/n_pixels
        self.logger.debug("Attractor cover ratio is %.2f%% (limit is %.2f%%)",
                          100.0*cover_ratio,
                          100.0*cover_limit)
        if cover_ratio < cover_limit:
            return False

        return True
