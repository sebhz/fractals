#!/usr/bin/python3
"""
Generate an attractor each day. Put it in a nice
web page, or embed it in an email to send to
your friends.
"""
import os
import sys
import argparse
import logging
import smtplib
import random
import subprocess

from time import time
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from jinja2 import Environment, FileSystemLoader

from attractor import attractor, render, util
import cv2

REFERENCE_DATE = datetime(2016, 7, 27)
CURRENT_FILE = "strange_attractor.xhtml"
NUM_THREADS = 4
IMAGE_SUFFIX = ".png"

def setup_jinja_env():
    """
    Sets up Jinja2 environment for templating
    """
    env = Environment(
        loader=FileSystemLoader('./templates')
        )
    return env

def append_numeral(num):
    """
    Appends a numeral to number
    """
    suffix = ('th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th')
    return str(num) + suffix[num % 10]

def days_between(d_1, d_2):
    """
    Gives the number of days between
    two datetimes objects
    """
    return abs((d_2 - d_1).days)

def modify_previous_html(previous_fname, current_fname):
    """
    Modifies HTML file from the day before to
    reference newly generate HTML
    """
    logging.info("Modifying previous HTML (%s)", previous_fname)
    with open(previous_fname) as _file:
        page = _file.readlines()

    #TODO: simplify this
    out_page = ""
    for line in page:
        if '__next' in line:
            line = line.replace('#__next', current_fname)
        out_page += line

    with open(previous_fname, "w") as _file:
        _file.writelines(out_page)

def parse_args():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(description='generation of strange attractor web page')
    parser.add_argument('-a',
                        '--all',
                        help='Regenerates all pages from the beginning of time (2016-07-27)',
                        action='store_true',
                        default=False)
    parser.add_argument('-d', '--date', help='Forces date. Format of input: YYYY-MM-DD', type=str)
    parser.add_argument('-e',
                        '--ephemerous',
                        help='Ephemerous. Do not generate HTML, do not keep the attractor image',
                        action='store_true',
                        default=False)
    parser.add_argument('-f',
                        '--fromaddr',
                        help='From address',
                        type=str,
                        default='attractors@attractor.org')
    parser.add_argument('-j',
                        '--nthreads',
                        help='Number of threads to use',
                        type=int,
                        default=NUM_THREADS)
    parser.add_argument('-m',
                        '--mail',
                        help='Mail the attractor(s)',
                        action='store_true',
                        default=False)
    parser.add_argument('-n',
                        '--num',
                        help='Number of the attractor (in the series). Incompatible with --date.',
                        type=int)
    parser.add_argument('-r',
                        '--recipients',
                        help='Recipient list for mails (comma separated)',
                        type=str)
    parser.add_argument('-s', '--server', help='SMTP server to use', type=str)
    _args = parser.parse_args()
    return _args

def fill_template(template_name, keywords_map):
    """
    Fill variable fields in a template string
    """
    template = JENV.get_template(template_name)
    return template.render(keywords_map)

def generate_mail_text(keywords_map):
    """
    Generate attractor of the day mail
    in plain text format
    """
    return fill_template('daily_mail.txt', keywords_map)

def generate_mail_html(keywords_map):
    """
    Generate attractor of the day mail
    in plain html format
    """
    return fill_template('daily_mail.xhtml', keywords_map)

def send_mail(keywords_map, server, send_from, send_to, subject, files=None, multiple=False):
    """
    Send the attractor of the day mail
    """
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
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    text = generate_mail_text(keywords_map)
    html = generate_mail_html(keywords_map)
    msg_alternative.attach(MIMEText(text, 'plain'))
    msg_alternative.attach(MIMEText(html, 'html'))

    # Finally attach the image to the root message... this loop is overkill
    # and unnecessary, but will do for our case !
    for file_name in files or []:
        with open(file_name, "rb") as fil:
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
                refused_recipient = smtp.sendmail(send_from, dest, msg.as_string())
                refused.update(refused_recipient)
        else: # send only one message with everyone in To-List
            msg['To'] = COMMASPACE.join(send_to)
            refused = smtp.sendmail(send_from, send_to, msg.as_string())
    except smtplib.SMTPException as exception:
        logging.warning(sys.stderr, "Error sending mail: %s.", repr(exception))
    else:
        if refused:
            logging.warning(sys.stderr, "Some mails could not be delivered: %s.", str(refused))

    smtp.quit()

def process_html(att_num, keywords_map):
    """
    Writes attractor of the day web page, and
    modify previous page to point to the newly
    generated page.
    """
    out_page = fill_template('daily_web.xhtml', keywords_map)

    cur_name = str(att_num)+".xhtml"
    with open(cur_name, "w") as _file:
        _file.writelines(out_page)

    if os.path.islink(CURRENT_FILE):
        os.remove(CURRENT_FILE)
    os.symlink(cur_name, CURRENT_FILE)

    # Modify previous filename to point on the current one.
    for i in range(att_num-1, 0, -1):
        prev_name = "%d.xhtml" % (i)
        if os.path.isfile(prev_name):
            modify_previous_html(prev_name, cur_name)
            break

def process_mail(keywords_map, args):
    """
    Sends attractor of the day mail
    """
    if args.mail and args.recipients and args.server:
        logging.info("Sending emails to %s, using SMTP server %s.", args.recipients, args.server)
        toaddr = args.recipients.split(',') # Hopefully there won't be any comma in the addresses
        subject = "%s : Strange attractor of the day" % (keywords_map['date'])
        send_mail(keywords_map, args.server, args.fromaddr,
                  toaddr, subject, ("png/"+keywords_map['link'],), True)

def sec2hms(seconds):
    """
    Seconds to hourminutesseconds
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%dh%02dm%02ds" % (hours, minutes, seconds)

def create_attractor(attractor_type, attractor_order, attractor_dimension):
    """
    Gets a converging attractor
    """
    if attractor_type == 'dejong':
        att = attractor.DeJongAttractor()
    elif attractor_type == 'clifford':
        att = attractor.CliffordAttractor()
    elif attractor_type == 'icon':
        att = attractor.SymIconAttractor()
    else:
        att = attractor.PolynomialAttractor(order=attractor_order,
                                            dimension=attractor_dimension)
    att.explore()
    return att

def process_attractor(att_num, args):
    """
    Creates, renders and saves an attractor image
    """
    keywords_map = {
        'date' : datetime.today().strftime("%Y, %b %d"),
        'order': 2,
        'code' : "",
        'iterations' : 0,
        'dimension' : 2,
        'lyapunov' : 0.0,
        'link' : "",
        'text' : "",
        'x_equation' : "",
        'y_equation' : "",
        'z_equation' : "",
        'time' : "",
        'type' : "polynomial",
    }
    max_fname_length = os.statvfs('/').f_namemax
    cur_date = REFERENCE_DATE + timedelta(days=att_num-1)
    keywords_map['date'] = cur_date.strftime("%Y, %b %d")
    type_index = att_num % 7
    if type_index == 0:
        keywords_map['type'] = "dejong"
    elif type_index == 6:
        keywords_map['type'] = "clifford"
    elif type_index == 5:
        keywords_map['type'] = "icon"
    else:
        keywords_map['type'] = "polynomial"
    keywords_map['order'] = type_index + 1

    downsampling = 2 # odd numbers seem to create strange artifacts.
    #dimension = 2 if keywords_map['type'] == "dejong" or \
    #                 keywords_map['type'] == "clifford" or \
    #                 keywords_map['order'] > 4 \
    #              else random.choice((2,3))
    dimension = 2
    logging.info("Today is %s. %s attractor generation starts.",
                 keywords_map['date'], append_numeral(att_num))
    logging.info("We have a %s attractor%s (dimension %d).",
                 keywords_map['type'],
                 " of order %d" % (keywords_map['order']) \
                     if keywords_map['type'] == "polynomial" else "",
                 dimension)

    while True:
        done = False
        att = create_attractor(keywords_map['type'], keywords_map['order'], dimension)
        for parameters in ({'geometry': (1000, 1000), 'directory': '/tmp'},):
            t_0 = time()
            iterations = util.get_ideal_iteration_number(parameters['geometry'], downsampling)
            logging.debug("Num iterations: %d", iterations)
            att.iterations = iterations
            renderer = render.Renderer(bpc=8,
                                       geometry=parameters['geometry'],
                                       downsample_ratio=downsampling,
                                       dimension=dimension)
            att_map = att.create_frequency_map(renderer.geometry, args.nthreads)
            if not renderer.is_nice(att_map):
                logging.debug("Attractor too thin. Trying to find a better one.")
                break
            att.compute_fractal_dimension(att_map)
            img = renderer.render_attractor(att_map)

            if len(att.code) < max_fname_length - len(IMAGE_SUFFIX):
                file_path = att.code + IMAGE_SUFFIX
            else:
                file_path = att.code[:max_fname_length-len(IMAGE_SUFFIX)-1] + '#' + IMAGE_SUFFIX
            # TODO: we should check that full path is not too long
            fname = os.path.join(parameters['directory'], file_path)
            cv2.imwrite(fname, img)
            done = True
            t_1 = time()
        if done:
            break

    keywords_map['code'] = att.code
    if keywords_map['type'] == 'polynomial':
        keywords_map['text'] = "Polynomial (order " + str(att.order) + ")"
    elif keywords_map['type'] == 'icon':
        keywords_map['text'] = "Field/Golubitsky symmetrical icon"
    else:
        keywords_map['text'] = keywords_map['type']

    _v = att.human_readable(is_html=True) + [""]
    keywords_map['x_equation'] = _v[0]
    keywords_map['y_equation'] = _v[1]
    keywords_map['z_equation'] = _v[2]

    keywords_map['iterations'] = str(att.iterations)
    keywords_map['fractal_dimension'] = 'not computed' if dimension == 3 else "%.3f" % (att.fdim)
    keywords_map['lyapunov'] = "%.3f" % (att.lyapunov['ly'])
    keywords_map['link'] = file_path
    keywords_map['prev'] = "#" if att_num == 1 else "%d.xhtml" % (att_num-1)
    keywords_map['time'] = sec2hms(t_1 - t_0)
    return keywords_map

def process_thumbnails(keywords_map):
    """
    Creates a thumbnail of our newly generated attractor image
    """
    filename = keywords_map['code'] + IMAGE_SUFFIX
    radius = 15
    for thumb_def in (("960x960", "png"), ("600x600", "png_thumb"), ("128x128", "png_tile")):
        if not os.path.exists(thumb_def[1]):
            os.mkdir(thumb_def[1])
        elif not os.path.isdir(thumb_def[1]):
            logging.error("Output directory %s exists, but is a plain file. Ignoring it.",
                          thumb_def[1])
            continue

        (width, height) = thumb_def[0].split('x')
        round_corner_command = 'roundRectangle 0,0 %s,%s %d,%d' % (width, height, radius, radius)
        try:
            subprocess.call(["mogrify", "-resize", thumb_def[0], os.path.join("/tmp", filename)])
            subprocess.call(['convert',
                             '-size',
                             thumb_def[0],
                             'xc:none',
                             '-fill',
                             'white',
                             '-draw',
                             round_corner_command, os.path.join("/tmp", filename),
                             '-compose',
                             'SrcIn',
                             '-composite',
                             os.path.join(thumb_def[1], filename)])
        except OSError:
            logging.error("Cannot invoke convert or mogrify utility. Is ImageMagick installed ?")
            break

def remove_thumbnails(keywords_map):
    """
    Removes our newly generated attractor thumbnail image
    """
    filename = keywords_map['code'] + IMAGE_SUFFIX
    for thumb_dir in ("png", "png_thumb", "png_tile"):
        if not os.path.exists(thumb_dir) or not os.path.isdir(thumb_dir):
            continue
        os.remove(os.path.join(thumb_dir, filename))

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
random.seed()
ARGS = parse_args()
JENV = setup_jinja_env()

if ARGS.date and ARGS.num is not None:
    logging.error("Only one of --num and --date switch is allowed.")
    sys.exit()

if ARGS.date:
    ARG_DATE = datetime.strptime(ARGS.date, "%Y-%m-%d")
    ATTRACTOR_RANGE = (days_between(REFERENCE_DATE, ARG_DATE) + 1,)
elif ARGS.num is not None:
    if ARGS.num < 1:
        logging.error("Only strictly positive numbers are allowed for attractors.")
        sys.exit()
    ATTRACTOR_RANGE = (ARGS.num,)
else:
    DAY_NUM = days_between(REFERENCE_DATE, datetime.today()) + 1
    if not ARGS.all:
        ATTRACTOR_RANGE = (DAY_NUM,)
    else:
        ATTRACTOR_RANGE = list(range(1, DAY_NUM + 1))

for attractor_num in ATTRACTOR_RANGE:
    kw_map = process_attractor(attractor_num, ARGS)

    process_thumbnails(kw_map)
    if not ARGS.ephemerous:
        process_html(attractor_num, kw_map)

    process_mail(kw_map, ARGS)

    if ARGS.ephemerous:
        logging.info("Ephemerous mode chosen. \
                      Cleaning up attractors. Root attractor can still be found in %s",
                     os.path.join("/tmp", kw_map['code'] + IMAGE_SUFFIX))
        remove_thumbnails(kw_map)
