#!/usr/bin/python3

# All colors are coded in RGB888. Colorspace indication gives the type of gradient to generate.
pal_templates = (
    { 'name'         : 'Flames',
      'colorspace'   : 'hsv_cw',
      'background'   : 0x000000,
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 33, 'start_color': 0xFF0000, 'end_color': 0xFF8000 },
                         { 'slice_percent': 67, 'start_color': 0xFF8000, 'end_color': 0xFFFFB3 } ]
    },
    { 'name'         : 'Blue to pink',
      'colorspace'   : 'hsv_cw',
      'background'   : 0x000000,
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 33, 'start_color': 0x0000FF, 'end_color': 0xFF6666 },
                         { 'slice_percent': 67, 'start_color': 0xFF6666, 'end_color': 0xFFB3B3 }  ]
    },
    { 'name'         : 'light blue to yellow',
      'colorspace'   : 'rgb',
      'background'   : 0x000000,
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0x61FFE0, 'end_color': 0xF0FF21 } ]
    },
    { 'name'         : 'Green to red',
      'colorspace'   : 'hsv_cc',
      'background'   : 0x000000,
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 12, 'start_color': 0x00FF00, 'end_color': 0xFFFF00 },
                         { 'slice_percent': 88, 'start_color': 0xFFFF00, 'end_color': 0xFF1919 }  ]
    },
    { 'name'         : 'White on black',
      'colorspace'   : 'rgb',
      'background'   : 0x000000,
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0xFFFFFF, 'end_color': 0xFFFFFF } ]
    },
    { 'name'         : 'China ink',
      'colorspace'   : 'rgb',
      'background'   : 0xFFFFFF,
      'value_offset' : 0.0,
      'invert_value' : True,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0xFFFFFF, 'end_color': 0xFFFFFF } ]
    },
    { 'name'         : 'Inverted red',
      'colorspace'   : 'hsv_cw',
      'background'   : 0xFFFFF0,
      'value_offset' : 0.4,
      'invert_value' : True,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0xFF1919, 'end_color': 0xFF0000 } ]
    },
    { 'name'         : 'Blue sky',
      'colorspace'   : 'rgb',
      'background'   : 0x000000,
      'value_offset' : 0.2,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 50, 'start_color': 0x2980B9, 'end_color': 0x6DD5FA },
                         { 'slice_percent': 50, 'start_color': 0x6DD5FA, 'end_color': 0xFFFFFF } ]
    },
    { 'name'         : 'Opa',
      'colorspace'   : 'rgb',
      'background'   : 0x333333,
      'value_offset' : 0.2,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0x3D7EAA, 'end_color': 0xFFE47A }]
    },
    { 'name'         : 'Dark blue to yellow',
      'colorspace'   : 'rgb',
      'background'   : 0x444444,
      'value_offset' : 0.2,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0x024EF8, 'end_color': 0xFBFB00 } ]
    },
    { 'name'         : 'Purple to orange',
      'colorspace'   : 'rgb',
      'background'   : 0x000000,
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': 0x66008F, 'end_color': 0xFEA610 } ]
    },
)

