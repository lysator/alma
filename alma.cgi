#!/opt/python/bin/python
# -*- coding: iso-8859-1 -*-
# $Id: alma.cgi,v 1.1 2004/12/13 19:32:40 kent Exp $
# Svenska almanackan
# Copyright 2004 Kent Engström. Released under GPL.

import time
import cgi
import cgitb; cgitb.enable()

import alma

#
# CGI driver
#

def handle_cgi():
    print "Content-Type: text/html\r\n\r"

    form = cgi.FieldStorage()

    # Ta reda på år och månad
    year_string = form.getfirst("year")
    month_string = form.getfirst("month")
    if year_string is None and month_string is None:
	year_string = str(time.localtime().tm_year)
	month_string = str(time.localtime().tm_mon)

    try:
	year = int(year_string)
    except TypeError:
	year = None

    try:
	month = int(month_string)
	if month < 1: month = 1
	if month > 12: month = 12
    except TypeError:
	month = None

    # Ta reda på kalendertyp
    tabular_string = form.getfirst("tabular")
    tabular = (tabular_string == "1")

    if year is not None and month is not None:
	yc = alma.YearCal(year)
	mc = alma.MonthCal(yc, month)
	if tabular:
	    mc.html_tabular(sys.stdout)
	else:
	    mc.html_vertical(sys.stdout)
    else:
	print "<P>Fel"


#
# Invocation
#

if __name__ == '__main__':
    import sys
    handle_cgi()
