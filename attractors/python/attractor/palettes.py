#!/usr/bin/python3

rgb = lambda x: ( (x >> 16)/0xFF, ((x >> 8) & 0xFF)/0xFF, (x & 0xFF)/0xFF, )

# All colors are coded on 24 bits, RGB. Colorspace indication gives the type of gradient to generate.
pal_templates = (
    { 'name'         : 'Flames',
      'colorspace'   : 'hsv',
      'background'   : rgb(0x000000),
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 33, 'start_color': (0.0, 1.0, 1.0),  'end_color': (1/12, 1.0, 1.0) },
                         { 'slice_percent': 67, 'start_color': (1/12, 1.0, 1.0), 'end_color': (1/6, 0.3, 1.0) } ]
    },
    { 'name'         : 'Blue to pink',
      'colorspace'   : 'hsv',
      'background'   : rgb(0x000000),
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 33, 'start_color': (2/3, 1.0, 1.0), 'end_color': (1.0, 0.6, 1.0) },
                         { 'slice_percent': 67, 'start_color': (1.0, 0.6, 1.0), 'end_color': (1.0, 0.3, 1.0) }  ]
    },
    { 'name'         : 'light blue to yellow',
      'colorspace'   : 'rgb',
      'background'   : rgb(0x000000),
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': rgb(0x61FFE0), 'end_color': rgb(0xF0FF21) } ]
    },
    { 'name'         : 'Green to red',
      'colorspace'   : 'hsv',
      'background'   : rgb(0x000000),
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 12, 'start_color': (1/3, 1.0, 1.0), 'end_color': (1/6, 1.0, 1.0) },
                         { 'slice_percent': 88, 'start_color': (1/6, 1.0, 1.0), 'end_color': (0.0, 0.9, 1.0) }  ]
    },
    { 'name'         : 'White on black',
      'colorspace'   : 'hsv',
      'background'   : rgb(0x000000),
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.0, 0.0, 1.0), 'end_color': (0.0, 0.0, 1.0) } ]
    },
    { 'name'         : 'China ink',
      'colorspace'   : 'hsv',
      'background'   : rgb(0xFFFFFF),
      'value_offset' : 0.0,
      'invert_value' : True,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.0, 0.0, 1.0), 'end_color': (0.0, 0.0, 1.0) } ]
    },
    { 'name'         : 'Inverted red',
      'colorspace'   : 'hsv',
      'background'   : rgb(0xFFFFF0),
      'value_offset' : 0.4,
      'invert_value' : True,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.0, 0.9, 1.0), 'end_color': (0.0, 1.0, 1.0) } ]
    },
    { 'name'         : 'Blue sky',
      'colorspace'   : 'rgb',
      'background'   : rgb(0x000000),
      'value_offset' : 0.2,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 50, 'start_color': rgb(0x2980B9), 'end_color': rgb(0x6DD5FA) },
                         { 'slice_percent': 50, 'start_color': rgb(0x6DD5FA), 'end_color': rgb(0xFFFFFF) } ]
    },
    { 'name'         : 'Opa',
      'colorspace'   : 'rgb',
      'background'   : rgb(0x333333),
      'value_offset' : 0.2,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': rgb(0x3D7EAA), 'end_color': rgb(0xFFE47A) }]
    },
    { 'name'         : 'Dark blue to yellow',
      'colorspace'   : 'rgb',
      'background'   : rgb(0x444444),
      'value_offset' : 0.2,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': rgb(0x024EF8), 'end_color': rgb(0xFBFB00) } ]
    },
    { 'name'         : 'Purple to orange',
      'colorspace'   : 'rgb',
      'background'   : rgb(0x000000),
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': rgb(0x66008F), 'end_color': rgb(0xFEA610) } ]
    },
)

