#!/usr/bin/python3

import os
import re
from datetime import datetime, timedelta

CURRENT_FILE = "strange_month.xhtml"
REFERENCE_DATE = datetime(2016, 7, 27)
ROW_WIDTH = 6

PAGE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

<head dir="ltr" id="head-id" lang="EN" profile="http://gmpg.org/xfn/11">
	<title>Strange attractors of the month</title>
	<link rel="stylesheet" href="css/stylesheet.css" type="text/css" media="all"/>
	<script src="js/navigation.js" type="text/javascript"></script>
</head>

<body>

<div class="box" id="main_div">
<div id="ctitle">Strange attractors of the month</div>
__date
<ul class="navbar">
<li><a href="201607.xhtml">|&lt;</a></li>
<li><a href="__prev">&lt;</a></li>
<li><a href="#" onclick="loadRandomMonth()">?</a></li>
<li><a href="__next">&gt;</a></li>
<li><a href="strange_month.xhtml">&gt;|</a></li>
</ul>
<div id="attractor_div">
__tiles
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
"""


def fillTemplate(template, MAP):
    out_page = ""
    for line in template.split("\n"):
        for k, v in MAP.items():
            if k in line:
                line = line.replace(k, str(v))
        out_page += line + "\n"

    return out_page


def getImage(num):
    filename = str(num) + ".xhtml"
    try:
        with open(filename, "r") as f:
            for line in f:
                if "png" in line:
                    m = re.search('alt="(([\dA-Za-z_])+)"', line)
                    if m:
                        return m.group(1)
    except Exception as e:
        print(e, "\nIgnoring it and trying to go on.")
        return None


def daysBetween(d1, d2):
    return abs((d2 - d1).days)


def createImageMap():
    h = dict()
    d = daysBetween(REFERENCE_DATE, datetime.today()) + 1
    for day in range(1, d + 1):
        dt = REFERENCE_DATE + timedelta(days=day - 1)
        if not (dt.year, dt.month) in h:
            h[(dt.year, dt.month)] = list()
        h[(dt.year, dt.month)].append(day)

    for (k, v) in sorted(h.items()):
        fl = [getImage(x) for x in v]
        h[k] = fl

    return h


def getPrev(date):
    if date == (2016, 7):
        return "#"
    return "%d%02d.xhtml" % (
        date[0] - 1 if date[1] == 1 else date[0],
        12 if date[1] == 1 else date[1] - 1,
    )


def getNext(date, maxDate):
    if date == maxDate:
        return "#"
    return "%d%02d.xhtml" % (
        date[0] + 1 if date[1] == 12 else date[0],
        1 if date[1] == 12 else date[1] + 1,
    )


def formatDate(date):
    month_map = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    return "%s %d" % (month_map[date[1] - 1], date[0])


def createTiles(tileList):
    v = ""
    for i, n in enumerate(tileList):
        if i % ROW_WIDTH == 0:
            v = v + '<div class="title_row">\n'
        v = (
            v
            + '<a href="png/%s_8.png"><img src="png_tile/%s_8.png" alt="%s" title="%s"></img></a>\n'
            % (n, n, n, n)
        )
        if i % ROW_WIDTH == ROW_WIDTH - 1:
            v = v + "</div>\n"

    if len(tileList) % ROW_WIDTH != 0:
        v = v + "</div>\n"
    return v


imageMap = createImageMap()
lastDate = sorted(imageMap.keys())[-1]
for (k, v) in sorted(imageMap.items()):
    if v == None:
        continue
    MAP = {
        "__date": formatDate(k),
        "__tiles": createTiles(v),
        "__prev": getPrev(k),
        "__next": getNext(k, lastDate),
    }
    pages = fillTemplate(PAGE_TEMPLATE, MAP)
    fname = "%4d%02d.xhtml" % (k[0], k[1])

    with open(fname, "w") as f:
        f.writelines(pages)

    if os.path.islink(CURRENT_FILE):
        os.remove(CURRENT_FILE)
    os.symlink("%d%02d.xhtml" % (lastDate[0], lastDate[1]), CURRENT_FILE)
