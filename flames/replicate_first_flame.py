#!/usr/bin/python3

import xml.etree.ElementTree as et
import sys

tree = et.parse(sys.argv[1])
root = tree.getroot()

# We want a full and exact copy... so it is OK to use the
# exact same reference. If we were to modify the element
# we would need copy / deepcopy
root.append(root[0])

tree.write("/tmp/new_points.xml")

