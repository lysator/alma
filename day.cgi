#!/opt/python/bin/python
# -*- coding: iso-8859-1 -*-
# $Id: day.cgi,v 1.1 2004/12/14 19:40:03 kent Exp $
# Svenska almanackan
# Copyright 2004 Kent Engström. Released under GPL.

import time
import sys
import cgi
import cgitb; cgitb.enable()

import jddate
import alma

#
# CGI driver
#

def handle_cgi():
    print "Content-Type: text/html\r\n\r"
    form = cgi.FieldStorage()
    
    # Argument?
    datestring = form.getfirst("date")
    if datestring is not None:
	date = jddate.FromString(datestring)
	if date.IsValid():
	    do_calendar(date)
	else:
	    print "Felaktigt datum"
	return

    # Idag
    lt = time.localtime()
    date = jddate.FromYMD(lt.tm_year, lt.tm_mon, lt.tm_mday)
    do_calendar(date)

def do_calendar(date):
    (y, m, d) = date.GetYMD()
    yc = alma.YearCal(y)
    dc = yc.get_md(m, d)
    dc.html_day(sys.stdout)

#
# Invocation
#

if __name__ == '__main__':
    handle_cgi()
