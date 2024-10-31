#!/usr/bin/python3

import copy
import xml.etree.ElementTree as et
import sys

# process_flame -d points.xml -> duplicate first flame at the end (looping flame)
# process_flame -x points.xml -> extract last flame
# process_flame -i points.xml flame.xml -> insert flame.xml in first position in points.xml


def renumber_flames(root_el):
    i = 0
    for flame in root_el.iter("flame"):
        flame.set("time", str(i))
        i += 1


if len(sys.argv) not in range(3, 5) or sys.argv[1] not in ("-d", "-x", "-i"):
    sys.exit(-1)


try:
    tree = et.parse(sys.argv[2])
except FileNotFoundError as e:
    sys.exit(-1)

if sys.argv[1] in ("-i"):
    try:
        flame = et.parse(sys.argv[3]).getroot()
    except FileNotFoundError as e:
        sys.exit(-2)

root = tree.getroot()

# Extract last frame
if sys.argv[1] == "-x":
    et.dump(root[-1])
    sys.exit(0)

# Duplicate first frame at the end of the sequence
if sys.argv[1] == "-d":
    new_flame = copy.deepcopy(root[0])
    root.append(new_flame)
# Append flame passed as parameter before the first flame of the sequence
elif sys.argv[1] == "-i":
    index = 0
    for i, element in enumerate(root):
        if element.tag == "flame":
            index = i
            break
    root.insert(index, flame)

renumber_flames(root)
et.dump(root)
