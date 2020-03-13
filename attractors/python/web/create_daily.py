#!/usr/bin/python3

import os
import sys
import argparse
import logging
import smtplib
import random
import subprocess
import cv2

from attractor import attractor, render, util
from time import time
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

REFERENCE_DATE = datetime(2016, 7, 27)
CURRENT_FILE = "strange_attractor.xhtml"
NUM_THREADS = 4
IMAGE_SUFFIX = ".png"

PAGE_TEMPLATE='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head dir="ltr" id="head-id" lang="EN" profile="http://gmpg.org/xfn/11">
    <title>Strange attractor of the day</title>
    <link rel="stylesheet" href="css/stylesheet.css" type="text/css" media="all"/>
    <link rel="shortcut icon" href="icons/favicon.ico" type="image/x-icon" id="favicon" />
    <link rel="icon" type="image/png" href="icons/favicon-16x16.png" sizes="16x16"/>
    <link rel="icon" type="image/png" href="icons/favicon-32x32.png" sizes="32x32"/>
    <link rel="icon" type="image/png" href="icons/favicon-48x48.png" sizes="48x48"/>
    <link rel="icon" type="image/png" href="icons/favicon-96x96.png" sizes="96x96"/>
    <script src="js/navigation.js" type="text/javascript"></script>
</head>

<body>
<div class="box" id="main_div">
<div id="ctitle">Strange attractor of the day</div>
__date
<ul class="navbar">
<li><a href="1.xhtml">|&lt;</a></li>
<li><a href="__prev">&lt;</a></li>
<li><a href="#" onclick="loadRandomPage()">?</a></li>
<li><a href="#__next">&gt;</a></li>
<li><a href="strange_attractor.xhtml">&gt;|</a></li>
</ul>
<div id="attractor_div">
<a href="png/__link"><img src="png_thumb/__link" alt="__code" title="__code"></img></a>
</div>
<div id="info_div">
Attractor type: <span class="code">__type</span>
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
<p class="code">
__z_polynom
</p>
</div>
<div>
Generation and rendering time: __time
</div>
<p>The fractal dimension is an estimate of the <a href="https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension">Minkowski-Bouligand (=box counting) dimension</a>.</p>
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
    .attractor_image {
    text-align:center;
    }
</style>
</head>

<body>
<p class="polite">Please find your strange attractor !</p>
<div class="attractor_image">
<img src="cid:atImg" alt="__code">
</div>
<div id="info_div">
Attractor type: <span class="code">__type</span>
<br></br>
Fractal dimension: <span class="code">__dimension</span>
<br></br>
Sprott's code: <span class="code">__code</span>
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
<p class="code">
__z_polynom
</p>
</div>
<div>
Generation and rendering time: __time
</div>
</div>
<p class="polite">Have a good day.</p>
<p class="polite">The fractal dimension is an estimate of the <a href="https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension">Minkowski-Bouligand (=box counting) dimension</a>.</p>
</body>
</html>
'''

MAIL_TXT_TEMPLATE = '''Please find your strange attractor.

    - Type: __type
    - # Iterations: _iterations
    - Fractal dimension: __dimension [1]
    - Generation and rendering time: __time

Have a good day.

[1] The fractal dimension is an estimate of the Minkowski-Bouligand (=box counting) dimension.
'''

def numeral(n):
    suffix = ('th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th')
    return str(n) + suffix[n%10]

def daysBetween(d1, d2):
    return abs((d2 - d1).days)

def modifyPreviousFile(fileName, curName):
    logging.info("Modifying previous HTML (%s)" % (fileName))
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
    parser.add_argument('-a', '--all',  help='Regenerates all pages from the beginning of time (2016-07-27) until today', action='store_true', default=False)
    parser.add_argument('-d', '--date', help='Forces date. Format of input: YYYY-MM-DD', type=str)
    parser.add_argument('-e', '--ephemerous', help='Ephemerous. Do not generate HTML, do not keep the attractor image', action='store_true', default=False)
    parser.add_argument('-f', '--fromaddr', help='From address', type=str, default='attractors@attractor.org')
    parser.add_argument('-j', '--nthreads', help='Number of threads to use', type=int, default=NUM_THREADS)
    parser.add_argument('-m', '--mail', help='Mail the attractor(s)', action='store_true', default=False)
    parser.add_argument('-n', '--num', help='Number of the attractor (in the series). Incompatible with --date.', type=int)
    parser.add_argument('-r', '--recipients', help='Recipient list for mails (comma separated)', type=str)
    parser.add_argument('-s', '--server', help='SMTP server to use', type=str)
    args = parser.parse_args()
    return args

def fillTemplate(template, MAP):
    out_page=""
    for line in template.split('\n'):
        for k, v in MAP.items():
            if k in line:
                line = line.replace(k, str(v))
        out_page += line + '\n'

    return out_page

def getMailText(MAP):
    return (fillTemplate(MAIL_TXT_TEMPLATE, MAP))

def getMailHTML(MAP):
    return (fillTemplate(MAIL_HTML_TEMPLATE, MAP))

def send_mail(MAP, server, send_from, send_to, subject, files=None, multiple=False):
    if not isinstance(send_to, list):
        logging.warning("Badly formed recipient list. Not sending any mail.")
        return

    # Root message
    msg = MIMEMultipart('related')
    msg['From'] = send_from
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    # Now create a multipart message below the root message
    # and attach both plain text and HTML version of the message to it.
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)
    text = getMailText(MAP)
    html = getMailHTML(MAP)
    msgAlternative.attach(MIMEText(text, 'plain'))
    msgAlternative.attach(MIMEText(html, 'html'))

    # Finally attach the image to the root message... this loop is overkill
    # and unnecessary, but will do for our case !
    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEImage(
                fil.read(),
                "png"
            )
            #part['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(f)
            part.add_header('Content-ID', '<atImg>')
            msg.attach(part)

    try:
        smtp = smtplib.SMTP(server)
    except smtplib.SMTPConnectError:
        logging.warning("Unable to connect to SMTP server. Not sending any mail.")
        return

    send_to = list(set(send_to)) # Removes possible duplicates in to list
    try:
        refused = dict()
        if multiple: # send one message per recipient
            for dest in send_to:
                if 'To' in msg:
                    msg.replace_header('To', dest)
                else:
                    msg['To'] = dest
                d = smtp.sendmail(send_from, dest, msg.as_string())
                refused.update(d)
        else: # send only one message with everyone in To-List
            msg['To'] = COMMASPACE.join(send_to)
            refused = smtp.sendmail(send_from, send_to, msg.as_string())
    except smtplib.SMTPException as e:
        logging.warning(sys.stderr, "Error sending mail: %s." % (repr(e)))
    else:
        if refused:
            logging.warning(sys.stderr, "Some mails could not be delivered: %s.", str(refused))

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
        logging.info("Sending emails to %s, using SMTP server %s." % (args.recipients, args.server))
        toaddr   = args.recipients.split(',') # Hopefully there won't be any comma in the addresses
        subject  = "%s : Strange attractor of the day" % (MAP['__date'])
        send_mail(MAP, args.server, args.fromaddr, toaddr, subject, ("png/"+MAP['__link'],), True)

def sec2hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%dh%02dm%02ds" % (h, m, s)

def createAttractor(AttractorType, AttractorOrder, AttractorDimension):
    if AttractorType == 'dejong':
        at = attractor.DeJongAttractor()
    elif AttractorType == 'clifford':
        at = attractor.CliffordAttractor()
    elif AttractorType == 'icon':
        at = attractor.SymIconAttractor()
    else:
        at = attractor.PolynomialAttractor(order = AttractorOrder, dimension = AttractorDimension)
    at.explore()
    return at

def processAttractor(AttractorNum):
    MAP = {
        '__date' : datetime.today().strftime("%Y, %b %d"),
        '__order': 2,
        '__code' : "",
        '__iterations' : 0,
        '__dimension' : 2,
        '__lyapunov' : 0.0,
        '__link' : "",
        '__x_polynom' : "",
        '__y_polynom' : "",
        '__z_polynom' : "",
        '__time' : "",
        '__type' : "polynomial",
    }
    maxFileNameLength = os.statvfs('/').f_namemax
    dt = REFERENCE_DATE + timedelta(days=attractorNum-1)
    MAP['__date'] = dt.strftime("%Y, %b %d")
    t = AttractorNum % 7
    if t == 0:
        MAP['__type'] = "dejong"
    elif t == 6:
        MAP['__type'] = "clifford"
    elif t == 5:
        MAP['__type'] = "icon"
    else:
        MAP['__type'] = "polynomial"
    MAP['__order'] = t + 1

    downsampling = 2 # odd numbers seem to create strange artifacts. Keep it safe :-)
    #dimension = 2 if MAP['__type'] == "dejong" or MAP['__type'] == "clifford" or MAP['__order'] > 4 else random.choice((2,3))
    dimension = 2
    logging.info("Today is %s. %s attractor generation starts." % (MAP['__date'], numeral(attractorNum)))
    logging.info("We have a %s attractor%s (dimension %d)." % (MAP['__type'], " of order %d" % (MAP['__order']) if MAP['__type'] == "polynomial" else "", dimension))

    while True:
        done = False
        at = createAttractor(MAP['__type'], MAP['__order'], dimension)
        for parameters in ( {'geometry': (1000, 1000), 'directory': '/tmp'}, ):
            t0 = time()
            iterations = util.getIdealIterationNumber(MAP['__type'], parameters['geometry'], downsampling)
            logging.debug("Num iterations: %d", iterations)
            at.iterations = iterations
            r = render.Renderer(bpc=8,
                geometry=parameters['geometry'],
                downsampleRatio=downsampling,
                dimension=dimension)
            a = at.createFrequencyMap(r.geometry, args.nthreads)
            if not r.isNice(a):
                logging.debug("Attractor too thin. Trying to find a better one.")
                break
            at.computeFractalDimension(a)
            img = r.renderAttractor(a)

            if len(at.code) < maxFileNameLength - len(IMAGE_SUFFIX):
                filePath = at.code + IMAGE_SUFFIX
            else:
                filePath = at.code[:maxFileNameLength-len(IMAGE_SUFFIX)-1] + '#' + suffix
            # TODO: we should check that full path is not too long
            fname = os.path.join(parameters['directory'], filePath)
            cv2.imwrite(fname, img)
            done = True
            t1 = time()
        if done: break

    MAP['__code'] = at.code
    if MAP['__type'] == 'polynomial':
        MAP['__type'] += " (order " + str(at.order) + ")"
    elif MAP['__type'] == 'icon':
        MAP['__type'] = "Sprott / Field / Golubitsky symmetrical icon"

    if dimension == 3:
        MAP['__x_polynom'], MAP['__y_polynom'], MAP['__z_polynom'] = at.humanReadable(isHTML=True)
    else:
        MAP['__x_polynom'], MAP['__y_polynom'] = at.humanReadable(isHTML=True)

    MAP['__iterations'] = str(at.iterations)
    MAP['__dimension'] = 'not computed' if dimension == 3 else "%.3f" % (at.fdim)
    MAP['__lyapunov'] = "%.3f" % (at.lyapunov['ly'])
    MAP['__link'] = filePath
    MAP['__prev'] = "#" if attractorNum == 1 else "%d.xhtml" % (attractorNum-1)
    MAP['__time'] = sec2hms(t1-t0)
    return MAP

def processThumbnails(MAP):
    filename = MAP['__code'] + IMAGE_SUFFIX
    radius = 15
    for d in (("960x960", "png"), ("600x600", "png_thumb"), ("128x128", "png_tile")):
        if not os.path.exists(d[1]):
            os.mkdir(d[1])
        elif not os.path.isdir(d[1]):
            logging.error("Output directory " + d[1] + " exists, but is a plain file. Ignoring it.")
            continue

        (w, h) = d[0].split('x')
        roundedCornerCommand = 'roundRectangle 0,0 %s,%s %d,%d' % (w, h, radius, radius)
        try:
            subprocess.call(["mogrify", "-resize", d[0], os.path.join("/tmp", filename)])
            subprocess.call(['convert', '-size', d[0], 'xc:none', '-fill', 'white', '-draw', roundedCornerCommand, os.path.join("/tmp", filename), '-compose', 'SrcIn', '-composite', os.path.join(d[1], filename)])
        except OSError:
            logging.error("Problem invoking convert or mogrify utility. Is ImageMagick installed ?")
            break

def removeThumbnails(MAP):
    filename = MAP['__code'] + IMAGE_SUFFIX
    for d in ("png", "png_thumb", "png_tile"):
        if not os.path.exists(d) or not os.path.isdir(d):
            continue
        os.remove(os.path.join(d, filename))

#
# Main program
#
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
args = parseArgs()
random.seed()

if args.date and args.num != None:
    logging.error("Only one of --num and --date switch is allowed.")
    sys.exit()

if args.date:
    d = datetime.strptime(args.date,"%Y-%m-%d")
    attractorRange = (daysBetween(REFERENCE_DATE, d) + 1,)
elif args.num != None:
    if args.num < 1:
        logging.error("Only positive and non zero numbers are allowed for attractors.")
        sys.exit()
    attractorRange = (args.num,)
else:
    d = daysBetween(REFERENCE_DATE, datetime.today()) + 1
    if not args.all:
        attractorRange = (d,)
    else:
        attractorRange = list(range(1, d+1))

for attractorNum in attractorRange:
    MAP = processAttractor(attractorNum)

    processThumbnails(MAP)
    if not args.ephemerous:
        processHTML(attractorNum, MAP)

    processMail(MAP)

    if args.ephemerous:
        logging.info("Ephemerous mode chosen. Cleaning up attractors. Root attractor can still be found in %s" % (os.path.join("/tmp", MAP['__code'] + IMAGE_SUFFIX)))
        removeThumbnails(MAP)

