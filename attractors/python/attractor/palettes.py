#!/usr/bin/python3

pal_templates = (
    # From red to green/yellow
    { 'name'         : 'Flames',
      'colorspace'   : 'hsv',
      'background'   : (0, 0, 0), # (B, G, R)
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 33, 'start_color': (0.0, 1.0, 1.0),  'end_color': (1/12, 1.0, 1.0) },
                         { 'slice_percent': 67, 'start_color': (1/12, 1.0, 1.0), 'end_color': (1/6, 0.3, 1.0) } ]
    },
    # From blue to pinkish
    { 'name'         : 'Blue to pink',
      'colorspace'   : 'hsv',
      'background'   : (0, 0, 0), # (B, G, R)
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 33, 'start_color': (2/3, 1.0, 1.0), 'end_color': (1.0, 0.6, 1.0) },
                         { 'slice_percent': 67, 'start_color': (1.0, 0.6, 1.0), 'end_color': (1.0, 0.3, 1.0) }  ]
    },
    # From blue to yellow
    { 'name'         : 'Blue to yellow',
      'colorspace'   : 'rgb',
      'background'   : (0, 0, 0), # (B, G, R)
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.38, 1.0, 0.88), 'end_color': (0.94, 1.0, 0.13) } ]
    },
    # From green to red
    { 'name'         : 'Green to red',
      'colorspace'   : 'hsv',
      'background'   : (0, 0, 0), # (B, G, R)
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 12, 'start_color': (1/3, 1.0, 1.0), 'end_color': (1/6, 1.0, 1.0) },
                         { 'slice_percent': 88, 'start_color': (1/6, 1.0, 1.0), 'end_color': (0.0, 0.9, 1.0) }  ]

    },
    # Pure white (will become greyscale)
    { 'name'         : 'White on black',
      'colorspace'   : 'hsv',
      'background'   : (0, 0, 0), # (B, G, R)
      'value_offset' : 0.0,
      'invert_value' : False,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.0, 0.0, 1.0), 'end_color': (0.0, 0.0, 1.0) } ]
    },
    # Pure black (will become greyscale)
    { 'name'         : 'China ink',
      'colorspace'   : 'hsv',
      'background'   : (1.0, 1.0, 1.0), # (B, G, R)
      'value_offset' : 0.0,
      'invert_value' : True,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.0, 0.0, 1.0), 'end_color': (0.0, 0.0, 1.0) } ]
    },
    # Inverted red
    { 'name'         : 'Inverted red',
      'colorspace'   : 'hsv',
      'background'   : (215/255, 220/255, 253/255), # (B, G, R)
      'value_offset' : 0.4,
      'invert_value' : True,
      'gradient_map' : [ { 'slice_percent': 100, 'start_color': (0.0, 0.9, 1.0), 'end_color': (0.0, 1.0, 1.0) } ]
    }
)


