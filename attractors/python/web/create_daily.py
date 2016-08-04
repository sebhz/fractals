#!/usr/bin/python

import os
import sys
import argparse
from random import randint
from datetime import datetime

MAP = {
	'__date' : datetime.today().strftime("%Y, %b %d"),
	'__order': randint(2, 7),
	'__code' : "",
	'__iterations' : 0,
	'__dimension' : 2,
	'__lyapunov' : 0.0,
	'__link' : "",
	'__x_polynom' : "",
	'__y_polynom' : "",
}

THUMB_CMD = "./attractors.py --geometry=800x600 --outdir=png_thumb --render=greyscale"
FINAL_CMD = "./attractors.py --geometry=1920x1080 --outdir=png --render=greyscale"
REFERENCE_DATE = datetime(2016, 7, 27)
CURRENT_FILE = "strange_attractor.xhtml"

PAGE_TEMPLATE='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head dir="ltr" id="head-id" lang="EN" profile="http://gmpg.org/xfn/11">
	<title>Strange attractor of the day</title>
	<link rel="stylesheet" href="css/stylesheet.css" type="text/css" media="all"/>
</head>

<body>
<div class="box" id="main_div">
<div id="ctitle">Strange attractor of the day</div>
__date
<ul class="navbar">
<li><a href="1.xhtml">|&lt;</a></li>
<li><a href="__prev">&lt;</a></li>
<li><a href="#__random">?</a></li>
<li><a href="#__next">&gt;</a></li>
<li><a href="strange_attractor.xhtml">&gt;|</a></li>
</ul>
<div id="attractor_div">
<a href="png/__link"><img src="png_thumb/__link" alt="__code" title="__code"></img></a>
</div>
<div id="info_div">
Polynom order: <span class="code">__order</span>
<br></br>
Correlation dimension: <span class="code">__dimension</span>
<br></br>
Number of iterations: <span class="code">__iterations</span>
<br></br>
Sprott's code:<br></br>
<div class="polynom_div">
<span class="code">__code</span>
<br></br>
</div>
Polynoms:
<div class="polynom_div">
<span class="code">
__x_polynom
</span>
<p class="code">
__y_polynom
</p>
</div>
</div>
</div>
<div class="box" id="uh_div">
<a href="attractors_explanation.xhtml">What is this all about ?</a>
</div>

<div id="footer_div">
<p>
	<a href="http://validator.w3.org/check?uri=referer">
	<img src="http://www.w3.org/Icons/valid-xhtml11" alt="Valid XHTML 1.1" height="31" width="88" />
	</a>
</p>
</div>
 </body>

</html>
'''

def daysBetween(d1, d2):
	return abs((d2 - d1).days)

def modifyPreviousFile(fileName, curName):
	print >> sys.stderr, "Modifying previous HTML (%s)" % (fileName)
	with open(fileName) as f:
		page = f.readlines()

	outPage = ""
	for line in page:
		if '__next' in line:
			line = line.replace('#__next', curName)
		outPage += line

	with open(fileName, "w") as f:
		f.writelines(outPage)

def parseArgs():
	parser = argparse.ArgumentParser(description='generation of strange attractor web page')
	parser.add_argument('-d', '--date',      help='Forces date. Format of input: YYYY-MM-DD', type=str)
	args = parser.parse_args()
	return args

os.chdir("/home/shaezebr/work/pjt/attractor_web")

args = parseArgs()
if args.date:
	d = datetime.strptime(args.date,"%Y-%m-%d")
	MAP['__date'] = d.strftime("%Y, %b %d")
	attractorNum = daysBetween(REFERENCE_DATE, d) + 1
else:
	attractorNum = daysBetween(REFERENCE_DATE, datetime.today()) + 1
print >> sys.stderr, "Today is %s. %dth attractor generation starts." % (MAP['__date'], attractorNum)
print >> sys.stderr, "Attractor order: %d" % MAP['__order']

with os.popen(THUMB_CMD + " --order=" + str(MAP['__order'])) as s:
	v = s.read()
print >> sys.stderr, "Thumbnail generated"

MAP['__code'], MAP['__dimension'], MAP['__lyapunov'], MAP['__iterations'], MAP['__x_polynom'], MAP['__y_polynom'] = v.split()

os.system(FINAL_CMD + " --order=" + str(MAP['__order']) + " --code=" + MAP['__code'] + " >/dev/null")
print >> sys.stderr, "Image generated"

MAP['__dimension'] = "%.3f" % (float(MAP['__dimension']))
MAP['__lyapunov'] = "%.3f" % (float(MAP['__lyapunov']))
MAP['__link'] = MAP['__code'] + "_8.png"
MAP['__prev'] = "#" if attractorNum == 1 else "%d.xhtml" % (attractorNum-1)

out_page=""
for line in PAGE_TEMPLATE.split('\n'):
	for k, v in MAP.iteritems():
		if k in line:
			line = line.replace(k, str(v))
	out_page += line

curName = str(attractorNum)+".xhtml"
with open(curName, "w") as f:
	f.writelines(out_page)

if os.path.islink(CURRENT_FILE):
	os.remove(CURRENT_FILE)
os.symlink(curName, CURRENT_FILE)

# Modify previous filename to point on the current one.
for i in range(attractorNum-1, 0, -1):
	prevName = "%d.xhtml" % (i)
	if os.path.isfile(prevName):
		modifyPreviousFile(prevName, curName)
		break

# Now we only have to upload the last two HTML files and the new images
