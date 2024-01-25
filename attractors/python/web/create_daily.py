#!/usr/bin/python3
"""
Generate an attractor, tagged by day.
"""
import os
import sys
import argparse
import logging
import random
import fileinput
import smtplib

from time import time
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from jinja2 import Environment, FileSystemLoader

from attractor import attractor, render, util

REFERENCE_DATE = datetime(2016, 7, 27)
NUM_THREADS = 4
IMAGE_SUFFIX = ".png"
PATH_GUARDBAND = 32
ATT_GEOMETRY = (1024, 1024)


def generate_mail_text(keywords_map):
    """
    Generate attractor of the day mail
    in plain text format
    """
    return fill_template("daily_mail.txt.j2", keywords_map)


def generate_mail_html(keywords_map):
    """
    Generate attractor of the day mail
    in plain html format
    """
    return fill_template("daily_mail.xhtml.j2", keywords_map)


def send_mail(
    keywords_map, server, send_from, send_to, subject, files=None, multiple=False
):
    """
    Send the attractor of the day mail
    """
    if not isinstance(send_to, list):
        logging.warning("Badly formed recipient list. Not sending any mail.")
        return

    # Root message
    msg = MIMEMultipart("related")
    msg["From"] = send_from
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    # Now create a multipart message below the root message
    # and attach both plain text and HTML version of the message to it.
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    text = generate_mail_text(keywords_map)
    html = generate_mail_html(keywords_map)
    msg_alternative.attach(MIMEText(text, "plain"))
    msg_alternative.attach(MIMEText(html, "html"))

    # Finally attach the image to the root message... this loop is overkill
    # and unnecessary, but will do for our case !
    for file_name in files or []:
        with open(file_name, "rb") as fil:
            part = MIMEImage(fil.read(), "png")
            # part['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(f)
            part.add_header("Content-ID", "<atImg>")
            msg.attach(part)

    try:
        smtp = smtplib.SMTP(server)
    except smtplib.SMTPConnectError:
        logging.warning("Unable to connect to SMTP server. Not sending any mail.")
        return

    send_to = list(set(send_to))  # Removes possible duplicates in to list
    try:
        refused = dict()
        if multiple:  # send one message per recipient
            for dest in send_to:
                if "To" in msg:
                    msg.replace_header("To", dest)
                else:
                    msg["To"] = dest
                refused_recipient = smtp.sendmail(send_from, dest, msg.as_string())
                refused.update(refused_recipient)
        else:  # send only one message with everyone in To-List
            msg["To"] = COMMASPACE.join(send_to)
            refused = smtp.sendmail(send_from, send_to, msg.as_string())
    except smtplib.SMTPException as exception:
        logging.warning(sys.stderr, "Error sending mail: %s.", repr(exception))
    else:
        if refused:
            logging.warning(
                sys.stderr, "Some mails could not be delivered: %s.", str(refused)
            )

    smtp.quit()


def process_mail(keywords_map, args):
    """
    Sends attractor of the day mail
    """
    assets_dir = os.path.join(args.root, "assets")
    if args.mail and args.recipients and args.server:
        logging.info(
            "Sending emails to %s, using SMTP server %s.", args.recipients, args.server
        )
        toaddr = args.recipients.split(
            ","
        )  # Hopefully there won't be any comma in the addresses
        subject = "%s : Strange attractor of the day" % (keywords_map["date"])
        send_mail(
            keywords_map,
            args.server,
            args.fromaddr,
            toaddr,
            subject,
            (os.path.join(assets_dir, keywords_map["link"]),),
            True,
        )


def setup_jinja_env():
    """
    Sets up Jinja2 environment for templating
    """
    env = Environment(loader=FileSystemLoader("./templates"))
    return env


def append_numeral(num):
    """
    Appends a numeral to number
    """
    suffix = ("th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th")
    return str(num) + suffix[num % 10]


def days_between(d_1, d_2):
    """
    Gives the number of days between
    two datetimes objects
    """
    return abs((d_2 - d_1).days)


def parse_args():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="generation of strange attractor web page"
    )
    parser.add_argument(
        "-a",
        "--all",
        help="Regenerates all pages from the beginning of time (2016-07-27)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-d", "--date", help="Forces date. Format of input: YYYY-MM-DD", type=str
    )

    parser.add_argument(
        "-j",
        "--nthreads",
        help="Number of threads to use",
        type=int,
        default=NUM_THREADS,
    )
    parser.add_argument(
        "-n",
        "--num",
        help="Number of the attractor (in the series). Incompatible with --date.",
        type=int,
    )
    parser.add_argument(
        "-R",
        "--root",
        help="root directory where images and pages will be stored (defaults to .)",
        type=str,
        default=".",
    )
    parser.add_argument(
        "-m", "--mail", help="Mail the attractor(s)", action="store_true", default=False
    )
    parser.add_argument(
        "-f",
        "--fromaddr",
        help="From address",
        type=str,
        default="attractors@attractor.org",
    )
    parser.add_argument(
        "-r",
        "--recipients",
        help="Recipient list for mails (comma separated)",
        type=str,
    )
    parser.add_argument("-s", "--server", help="SMTP server to use", type=str)
    _args = parser.parse_args()
    return _args


def fill_template(template_name, keywords_map):
    """
    Fill variable fields in a template string
    """
    template = JENV.get_template(template_name)
    return template.render(keywords_map)


def sec2hms(seconds):
    """
    Seconds to hourminutesseconds
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%dh%02dm%02ds" % (hours, minutes, seconds)


def get_attractor(attractor_type, attractor_order, attractor_dimension):
    """
    Gets a converging attractor
    """
    if attractor_type == "dejong":
        att = attractor.DeJongAttractor()
    elif attractor_type == "clifford":
        att = attractor.CliffordAttractor()
    elif attractor_type == "icon":
        att = attractor.SymIconAttractor()
    else:
        att = attractor.PolynomialAttractor(
            order=attractor_order, dimension=attractor_dimension
        )
    att.explore()
    return att


def create_attractor(att_num, args):
    """
    Creates and renders an attractor image
    """
    week_map = [
        "dejong",
        "polynomial",
        "polynomial",
        "polynomial",
        "polynomial",
        "clifford",
        "icon",
    ]
    keywords_map = {
        "date": datetime.today().strftime("%Y, %b %d"),
        "order": 2,
        "code": "",
        "iterations": 0,
        "dimension": 2,
        "lyapunov": 0.0,
        "link": "",
        "text": "",
        "equation": [],
        "time": "",
        "type": "polynomial",
    }
    cur_date = REFERENCE_DATE + timedelta(days=att_num - 1)
    keywords_map["date"] = cur_date.strftime("%Y, %b %d")
    type_index = att_num % 7
    keywords_map["type"] = week_map[type_index]
    keywords_map["order"] = type_index + 1

    att_downsampling = 2  # odd numbers seem to create strange artifacts.
    att_dimension = 2
    logging.info(
        "Today is %s. %s attractor generation starts.",
        keywords_map["date"],
        append_numeral(att_num),
    )
    logging.info(
        "We have a %s attractor%s (dimension %d).",
        keywords_map["type"],
        " of order %d" % (keywords_map["order"])
        if keywords_map["type"] == "polynomial"
        else "",
        att_dimension,
    )

    while True:
        att = get_attractor(keywords_map["type"], keywords_map["order"], att_dimension)
        t_0 = time()
        iterations = util.get_ideal_iteration_number(ATT_GEOMETRY, att_downsampling)
        logging.debug("Num iterations: %d", iterations)
        att.iterations = iterations
        renderer = render.Renderer(
            bpc=8,
            geometry=ATT_GEOMETRY,
            downsample_ratio=att_downsampling,
            dimension=att_dimension,
        )
        att_map = att.create_frequency_map(renderer.geometry, args.nthreads)
        if not renderer.is_nice(att_map):
            logging.debug("Attractor too thin. Trying to find a better one.")
            continue
        att.compute_fractal_dimension(att_map)
        img = renderer.render_attractor(att_map)
        t_1 = time()
        break

    keywords_map["code"] = att.code
    keywords_map["filename"] = get_filename(att.code, att_num)
    if keywords_map["type"] == "polynomial":
        keywords_map["text"] = "Polynomial (order " + str(att.order) + ")"
    elif keywords_map["type"] == "icon":
        keywords_map["text"] = "Field/Golubitsky symmetrical icon"
    else:
        keywords_map["text"] = keywords_map["type"]

    keywords_map["equation"] = att.human_readable(is_html=True)
    keywords_map["iterations"] = str(att.iterations)
    keywords_map["fractal_dimension"] = (
        "not computed" if att_dimension == 3 else "%.3f" % (att.fdim)
    )
    keywords_map["lyapunov"] = "%.3f" % (att.lyapunov["ly"])
    keywords_map["link"] = keywords_map["filename"]
    keywords_map["time"] = sec2hms(t_1 - t_0)
    return (keywords_map, img)


def get_filename(code, num):
    """
    Add image suffix to code string. If the resulting string is
    longer than the maximum filename allowed by the OS, minus
    a guardband for possibly prepending directories, shorten it.
    """
    max_fname_length = os.statvfs("/").f_namemax
    prefix = "%05s_" % (99999 - num)
    if len(code) < max_fname_length - len(IMAGE_SUFFIX) - len(prefix) - PATH_GUARDBAND:
        fname = prefix + code + IMAGE_SUFFIX
    else:
        fname = (
            prefix
            + code[
                : max_fname_length
                - len(IMAGE_SUFFIX)
                - len(prefix)
                - PATH_GUARDBAND
                - 1
            ]
            + "#"
            + IMAGE_SUFFIX
        )
    return fname


def write_attractor(img, keywords_map, args):
    """
    Write our attractor image in the assets directory
    """
    assets_dir = os.path.join(args.root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    fname = os.path.join(assets_dir, keywords_map["filename"])
    img.save(fname)


def append_attractor_metadata(keywords_map, args):
    """
    Update index file with the proper metadata
    """
    metadata = """- src: %s
  alt: %s attractor
  phototitle: %s attractor (%s)
""" % (
        keywords_map["filename"],
        keywords_map["text"],
        keywords_map["text"],
        keywords_map["date"],
    )

    index_header = """---
date: 2021-01-01T00:00:00-00:00
type: "noalbum"
resources:
---
"""
    content_dir = os.path.join(args.root, "content")
    os.makedirs(content_dir, exist_ok=True)
    index_file = os.path.join(content_dir, "_index.md")
    if not os.path.exists(index_file):
        with open(index_file, "w") as f:
            f.write(index_header)

    with fileinput.input(os.path.join(content_dir, "_index.md"), inplace=True) as f:
        for line in f:
            print(line, end="")
            if "resources:" in line:
                print(metadata, end="")


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
    (kw_map, image) = create_attractor(attractor_num, ARGS)
    write_attractor(image, kw_map, ARGS)
    process_mail(kw_map, ARGS)
    append_attractor_metadata(kw_map, ARGS)
