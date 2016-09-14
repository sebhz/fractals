#!/usr/bin/python

import os
import sys
import argparse
import smtplib

from time import time
from random import randint
from datetime import datetime, timedelta
from os.path import basename
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from subprocess import Popen, PIPE, STDOUT

TYPES = ('polynomial', 'dejong')
THUMB_CMD = ['./generate.py', '--geometry=800x600', '--outdir=png_thumb', '--render=greyscale', '--subsample=3', '-H', '--loglevel=0', '--threads=4']
FINAL_CMD = ['./generate.py', '--geometry=1920x1080', '--outdir=png', '--render=greyscale', '--subsample=3', '-H', '--loglevel=0', '--threads=4']
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
Attractor type: <span class="code">__type</span>
<br></br>
Polynom order: <span class="code">__order</span>
<br></br>
Fractal dimension: <span class="code">__dimension</span>
<br></br>
Number of iterations: <span class="code">__iterations</span>
<br></br>
Sprott's code:<br></br>
<div class="polynom_div">
<span class="code">__code</span>
<br></br>
</div>
Equations:
<div class="polynom_div">
<span class="code">
__x_polynom
</span>
<p class="code">
__y_polynom
</p>
</div>
<div>
Generation and rendering time: __time
</div>
<p>For polynomial attractors, the dimension is an estimate of the <a href="https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension">Minkowski-Bouligand (=box counting) dimension</a>. For De Jong attractors, it is an estimate of the <a href="https://en.wikipedia.org/wiki/Correlation_dimension">correlation dimension</a>.</p>
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

MAIL_HTML_TEMPLATE='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head dir="ltr" id="head-id" lang="EN" profile="http://gmpg.org/xfn/11">
	<title>Strange attractor of the day</title>
	<style media="screen" type="text/css">
	.code {
	font-family: Courier;
	font-variant: normal;
    }
    body {
	font-size:11px;
	font-variant:small-caps;
	font-family:Lucida,Helvetica,sans-serif;
	font-weight:500;
	text-decoration: none;
	line-height: 1.2em;
	position: absolute;
    }
	.polite {
	font-variant:normal;
	}
</style>
</head>

<body>
<p class="polite">Please find your strange attractor !</p>
<p></p>
<div id="info_div">
Attractor type: <span class="code">__type</span>
<br></br>
Polynom order: <span class="code">__order</span>
<br></br>
Fractal dimension: <span class="code">__dimension</span>
<br></br>
Number of iterations: <span class="code">__iterations</span>
<br></br>
Equations:
<div>
<span class="code">
__x_polynom
</span>
<p class="code">
__y_polynom
</p>
</div>
<div>
Generation and rendering time: __time
</div>
</div>
<p class="polite">Have a good day.</p>
<p class="polite">For polynomial attractors, the dimension is an estimate of the <a href="https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension">Minkowski-Bouligand (=box counting) dimension</a>. For De Jong attractors, it is an estimate of the <a href="https://en.wikipedia.org/wiki/Correlation_dimension">correlation dimension</a>.</p>
</body>
</html>
'''

MAIL_TXT_TEMPLATE = '''Please find your strange attractor.

	- Type: __type
	- Order: __order
	- # Iterations: _iterations
	- Fractal dimension: __dimension [1]
	- Generation and rendering time: __time

Have a good day.

[1] for polynomial attractors, the dimension is an estimate of the Minkowski-Bouligand (=box counting) dimension. For De Jong attractors, it is an estimate of the correlation dimension.
'''

def numeral(n):
	suffix = ('th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th')
	return str(n) + suffix[n%10]

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
	parser.add_argument('-a', '--all',  help='Regenerates all pages from the beginning on time (2016-07-27) until today', action='store_true', default=False)
	parser.add_argument('-d', '--date', help='Forces date. Format of input: YYYY-MM-DD', type=str)
	parser.add_argument('-m', '--mail', help='Mail the attractor(s)', action='store_true', default=False)
	parser.add_argument('-r', '--recipients', help='Recipient list for mails (comma separated)', type=str)
	parser.add_argument('-s', '--server', help='SMTP server to use', type=str)
	args = parser.parse_args()
	return args

def fillTemplate(template, MAP):
	out_page=""
	for line in template.split('\n'):
		for k, v in MAP.iteritems():
			if k in line:
				line = line.replace(k, str(v))
		out_page += line + '\n'

	return out_page

def getMailText(MAP):
	return (fillTemplate(MAIL_TXT_TEMPLATE, MAP))

def getMailHTML(MAP):
	return (fillTemplate(MAIL_HTML_TEMPLATE, MAP))

def send_mail(MAP, server, send_from, send_to, subject, files=None):
	if not isinstance(send_to, list):
		print >> sys.stderr, "Badly formed recipient list. Not sending any mail."
		return

	msg = MIMEMultipart('alternative')
	msg['From'] = send_from
	msg['To'] = COMMASPACE.join(send_to)
	msg['Date'] = formatdate(localtime=True)
	msg['Subject'] = subject

	text = getMailText(MAP)
	html = getMailHTML(MAP)
	msg.attach(MIMEText(text, 'plain'))
	msg.attach(MIMEText(html, 'html'))

	for f in files or []:
		with open(f, "rb") as fil:
			part = MIMEImage(
				fil.read(),
				"png"
			)
			part['Content-Disposition'] = 'attachment; filename=%s' % basename(f)
			msg.attach(part)

	try:
		smtp = smtplib.SMTP(server)
	except smtplib.SMTPConnectError:
		print >> sys.stderr, "Unable to connect to SMTP server. Not sending any mail."
		return

	try:
		refused = smtp.sendmail(send_from, send_to, msg.as_string())
	except smtplib.SMTPException as e:
		print >> sys.stderr, "Error sending mail:", repr(e)
	else:
		if refused:
			print >> sys.stderr, "Some mails could not be delivered:", refused

	smtp.quit()

def processHTML(attractorNum, MAP):
	out_page = fillTemplate(PAGE_TEMPLATE, MAP)

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

def processMail(MAP):
	if args.mail and args.recipients and args.server:
		print >> sys.stderr, "Sending emails to %s, using SMTP server %s." % (args.recipients, args.server)
		fromaddr = 'strangeattractor@attractor.org'
		toaddr   = args.recipients.split(',') # Hopefully there won't be any comma in the addresses
		subject  = "%s : Strange attractor of the day" % (MAP['__date'])
		send_mail(MAP, args.server, fromaddr, toaddr, subject, ("png/"+MAP['__link'],))

def sec2hms(seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	return "%dh%02dm%02ds" % (h, m, s)

#
# Main program
#
args = parseArgs()
if args.date:
	d = datetime.strptime(args.date,"%Y-%m-%d")
	attractorRange = (daysBetween(REFERENCE_DATE, d) + 1,)
else:
	d = daysBetween(REFERENCE_DATE, datetime.today()) + 1
	if not args.all:
		attractorRange = (d,)
	else:
		attractorRange = range(1, d+1)

for attractorNum in attractorRange:

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
		'__time' : "",
		'__type' : "polynomial",
	}

	MAP['__type'] = TYPES[0]

	dt = REFERENCE_DATE + timedelta(days=attractorNum-1)
	MAP['__date'] = dt.strftime("%Y, %b %d")

	print >> sys.stderr, "Today is %s. %s attractor generation starts." % (MAP['__date'], numeral(attractorNum))

	if MAP['__type'] == 'polynomial':
		cmd = THUMB_CMD + ["--order=" + str(MAP['__order']), "--type=" + str(MAP['__type'])]
	else:
		cmd = THUMB_CMD + ["--type=" + str(MAP['__type'])]

	p = Popen(cmd, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	MAP['__code'], MAP['__dimension'], MAP['__lyapunov'], MAP['__iterations'], MAP['__x_polynom'], MAP['__y_polynom'] = stdout.split()
	print >> sys.stderr, "Thumbnail generated"

	if MAP['__type'] == 'polynomial':
		cmd = FINAL_CMD + ["--order=" + str(MAP['__order']), "--type=" + str(MAP['__type']), "--code=" + MAP['__code']]
	else:
		cmd = FINAL_CMD + ["--type=" + str(MAP['__type']), "--code=" + MAP['__code']]

	t0 = time()
	p = Popen(cmd, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	t1 = time()
	MAP['__code'], MAP['__dimension'], MAP['__lyapunov'], MAP['__iterations'], MAP['__x_polynom'], MAP['__y_polynom'] = stdout.split()
	print >> sys.stderr, "Image generated"

	MAP['__dimension'] = "%.3f" % (float(MAP['__dimension']))
	MAP['__lyapunov'] = "%.3f" % (float(MAP['__lyapunov']))
	MAP['__link'] = MAP['__code'] + "_8.png"
	MAP['__prev'] = "#" if attractorNum == 1 else "%d.xhtml" % (attractorNum-1)
	MAP['__time'] = sec2hms(t1-t0)

	if MAP['__type'] == 'dejong':
		MAP['__order'] = "irrelevant"

	processHTML(attractorNum, MAP)
	processMail(MAP)

