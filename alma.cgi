#!/opt/python/bin/python
# -*- coding: iso-8859-1 -*-
# $Id: alma.cgi,v 1.14 2009/11/30 18:28:38 kent Exp $
# Svenska almanackan
# Copyright 2004 Kent Engström. Released under GPL.

import time
import cgi
import cgitb; cgitb.enable()

import alma

# Auxiliary routines
def guarded_int(s, min = None, max = None):
    try:
	n = int(s)
	if min is not None and n < min: return None
	if max is not None and n > max: return None
	return n
    except TypeError:
	return None

def selected(bool):
    if bool:
	return "SELECTED"
    else:
	return ""
#
# CGI driver
#

def handle_cgi():
    form = cgi.FieldStorage()

    # Är det här en begäran om vCalendar-data, som hanteras separat?
    if form.getfirst("vcal_preview") is not None or form.getfirst("vcal_generate") is not None:
	return handle_vcal(form)

    # Nähä, då kan vi utgå från att det blir en vanlig webbsida...
    so = sys.stdout
    so.write("Content-Type: text/html; charset=iso-8859-1\r\n\r\n")

    # Kalendertyp
    calendar_type = form.getfirst("type","vertical")
    if calendar_type in ["vertical", "tabular", "tabular_high"]:
        month_based = True 
        base_name = "månad"
    elif calendar_type in ["week"]:
        month_based = False
        base_name = "vecka"
    else:
	so.write("<P>Fel kalendertyp!\n")
	return

    # Utskriftsformat?
    print_format = form.getfirst("print") is not None

    # Ta reda på år, månad och veckonummer
    # (vi förväntar oss år + månad eller år + veckonummer)
    year_string = form.getfirst("year")
    month_string = form.getfirst("month")
    week_string = form.getfirst("week")

    # Om både år och månad saknas: låt dessa bli nuvarande värden
    if year_string is None and month_string is None:
	year_string = str(time.localtime().tm_year)
	month_string = str(time.localtime().tm_mon)

    # Omvandla till heltal och kolla gränser
    year = guarded_int(year_string, min=1754)
    month = guarded_int(month_string, min=1, max=12)
    week = guarded_int(week_string, min=1, max=53)

    # Vi kan inte vara utan år nu!
    if year is None:
	so.write("<P>År måste anges!\n")
	return

    # Vi måste ha minst en av månad och veckonummmer
    if month is None and week is None:
	so.write("<P>Månad eller vecka måste anges!\n")
	return

    # Vi kan inte ha månad och veckonummer samtidigt
    if month is not None and week is not None:
	so.write("<P>Månad och vecka får inte anges samtidigt!\n")
	return

    # Nu ska vi ta hand om ev övergångar mellan månadsbaserad
    # och veckobaserat!
    if month_based and month is None:
        year, month = alma.yw_to_ym(year, week)
    elif not month_based and week is None:
        year, week = alma.ym_to_yw(year, month)

    # Om användaren valt f.g. eller nästa: justera
    if form.getfirst("prev") is not None:
        if month_based:
            year, month = alma.previous_month(year, month)
        else:
            year, week = alma.previous_week(year, week)
    elif form.getfirst("next") is not None:
        if month_based:
            year, month = alma.next_month(year, month)
        else:
            year, week = alma.next_week(year, week)

    # Ingen veckobaserad före 1973 så jag slipper klura på 
    # layouten då :-)
    if not month_based and year < 1973:
	so.write("<P>Ingen veckokalender tidigare än 1973!\n")
	return
        

    # Generera almanackan
    if month_based:
        cal = alma.YearCal(year).month_cal(month)
    else:
        cal = alma.WeekCal(year, week)

    # Visa huvud
    title = cal.title()
    so.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
    so.write('<HEAD>')
    so.write('<TITLE>%s</TITLE>' % title)
    so.write('<LINK TYPE="text/css" REL="stylesheet" HREF="alma.css">')
    so.write('</HEAD>\n')
    
    so.write('<BODY>')

    # Navigering
    if not print_format:
        so.write('<FORM METHOD="POST" ACTION="">')

        if month_based:
            # Månad
            so.write('<SELECT NAME="month" onChange="this.form.submit();">')
            for m in range(1,13):
                so.write('<OPTION VALUE="%d" %s>%s</OPTION>' % (m, selected(m == month), alma.month_names[m]))
            so.write('</SELECT>\n')
        else:
            # Vecka
            so.write('Vecka <INPUT TYPE="TEXT" NAME="week" VALUE="%d" SIZE="2" onChange="this.form.submit();">\n' % (week))

        # År
        so.write('<INPUT TYPE="TEXT" NAME="year" VALUE="%d" SIZE="4" onChange="this.form.submit();">\n' % (year))

        # Typ
        so.write('<SELECT NAME="type" onChange="this.form.submit();">')
        for (value, label) in (("vertical", "Vertikal"),
			       ("tabular",  "Tabell"),
			       ("tabular_high",  "Tabell (hög)"),
                               ("week",  "Vecka")):
	    so.write('<OPTION VALUE="%s" %s>%s</OPTION>' % (value, selected(calendar_type == value), label))
        so.write('</SELECT>\n')

        # Uppdatera
        so.write('<INPUT TYPE="SUBMIT" NAME="go" VALUE="Uppdatera">\n')

        # Utskrift (= ingen navigering)
        so.write('<INPUT TYPE=SUBMIT NAME="print" VALUE="Visa för utskrift">\n')

        # vCalendar
        so.write('<INPUT TYPE=SUBMIT NAME="vcal_preview" VALUE="vCalendar">\n')

        so.write(" ~ ")

        # Snabblänkar till föregående och nästa {månad, vecka}
        so.write('<INPUT TYPE=SUBMIT NAME="prev" VALUE="Föregående %s">\n' % base_name)
        so.write('<INPUT TYPE=SUBMIT NAME="next" VALUE="Nästa %s">\n' % base_name)

        so.write('</FORM>')
    
    # Rubrik
    if calendar_type.startswith("tabular"):
	so.write('<H1 CLASS="centered">%s</H1>\n' % title)
    else:
        # "vertical" eller "week"
	so.write('<H1>%s</H1>\n' % title)

    # Visa almanackan
    if calendar_type in ["vertical", "week"]:
        method = cal.html_vertical
    elif calendar_type in ["tabular"]:
        method = cal.html_tabular
    elif calendar_type in ["tabular_high"]:
        method = cal.html_tabular_high
    else:
        method = None
    method(sys.stdout, for_printing = print_format)

    # Disclaimer
    if not print_format:
	so.write('''<DIV CLASS="disclaimer">Vi kan inte lämna några garantier
för att almanackan är fullständig och korrekt. Från och med 1983 bör det
emellertid inte finnas några större felaktigheter.
Vi försöker att göra så gott vi kan och tar tacksamt emot synpunkter till
<A HREF="mailto:kent@lysator.liu.se">kent@lysator.liu.se</A>.
</DIV>''')
	
    # Slut
    so.write('</BODY>')


def handle_vcal(form):
    so = sys.stdout

    # Ta reda på år
    year_string = form.getfirst("year")
    if year_string is None:
	year_string = str(time.localtime().tm_year)
    year = guarded_int(year_string, min=1754)

    # Förhandsvisning eller generering?
    preview = form.getfirst("vcal_preview")

    if preview:
	so.write('Content-Type: text/html; charset=iso-8859-1\r\n')
    else:
	so.write('Content-Type: text/x-vCalendar\r\n')
	so.write('Content-disposition: attachment; filename=%d.vcs\r\n' % year)
	
    so.write('\r\n')

    # Generera almanackan
    yc = alma.YearCal(year)

    # Huvud med val av vad som ska visas
    if preview:
	so.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
	so.write('<HEAD><TITLE>%d</TITLE></HEAD>\n' % year)
	so.write('<BODY><H1>vCalendar-fil för år %d</H1>\n' % year)

	so.write('<P>Välj nedan vilken information som ska med i vCalendar-filen. ')
	so.write('Begär sedan en ny förhandsvisning eller tryck direkt på knappen ')
	so.write('för att ladda ner vCalendar-filen. ')

	so.write('<FORM METHOD="POST" ACTION=""><TABLE>\n')

    # Val av vad som ska visas
    pdict = {}
    nodefaults = form.getfirst("vcal_nodefaults")
    for (param, default, text) in [(str(alma.MRED),   True,  "Visa viktiga röda dagar"),
				   (str(alma.RED),    False, "Visa mindre viktiga röda dagar"),
				   (str(alma.MBLACK), True,  "Visa viktiga svarta dagar"),
				   (str(alma.BLACK),  False, "Visa mindre viktiga svarta dagar"),
				   ("red",            False, "Markera röda dagar"),
				   ("names",          False, "Visa namnsdagsnamn"),
				   ("moon",           False, "Visa månfaser"),
				   ("flag",           False, "Visa flaggdagar"),
				   ("end",            False, "Ta med DTEND-post 23:59:59"),
				   ]:
	# Ta hand om inskickat värde
	if nodefaults:
	    value = form.getfirst("vcal_" + param)
	    if value == "yes":
		pdict[param] = True
	    else:
		pdict[param] = False
	else:
	    pdict[param] = default
    
	# Erbjud uppdatering
	if preview:
	    if pdict[param]:
		checked = " CHECKED"
	    else:
		checked = ""
		
	    so.write('<TR><TD><INPUT TYPE="CHECKBOX" NAME="vcal_%s" VALUE="yes" %s></TD><TD>%s</TD></TR>\n' % (param, checked, text))

    # Slut på huvud
    if preview:
	so.write('</TABLE><P>\n')
	so.write('<INPUT TYPE="HIDDEN" NAME="year" VALUE="%d">\n' % year)
	so.write('<INPUT TYPE="HIDDEN" NAME="vcal_nodefaults" VALUE="yes">\n')
	so.write('<INPUT TYPE="SUBMIT" NAME="vcal_preview" VALUE="Uppdatera förhandsvisning">\n')
	so.write('<INPUT TYPE="SUBMIT" NAME="vcal_generate" VALUE="Ladda ner vCalendar-fil">\n')
	so.write('</FORM>\n')

    # Kalender (förhandsvisning eller på riktigt)
    if preview:
	so.write('<P>Förhandsvisning av information som exporteras till vCalendar-filen:\n')
	so.write('<PRE>\n')
    else:
	so.write('BEGIN:VCALENDAR\n')
	so.write('VERSION:1.0\n')
	so.write('PRODID:alma.cgi\n')
	
    for dc in yc.generate():
	ymd = "%04d-%02d-%02d" % (dc.y, dc.m, dc.d)
	dtstart = "%04d%02d%02dT000000" % (dc.y, dc.m, dc.d)
	dtend   = "%04d%02d%02dT235959" % (dc.y, dc.m, dc.d)

	show = False
	parts = []

	# Röda och svarta dagar
	for dayclass in range(alma.MRED, alma.BLACK+1):
	    if pdict[str(dayclass)]:
		for dayname in dc.day_names:
		    if dayname.dayclass == dayclass:
			name = dayname.name
			if pdict["red"] and dayname.is_red:
			    name = name + " (röd)"
			parts.append(name)

	# Namnsdagar
	if pdict["names"]:
	    parts.extend(dc.names)

	# Månfaser
	if pdict["moon"]:
	    phase = dc.moonphase_name()
	    if phase:
		parts.append(phase)

	# Månfaser
	if pdict["flag"]:
	    if dc.flag_day:
		parts.append("flaggdag")
	
	# Visa dagen?
	if parts:
	    text = ", ".join(parts)
	    if preview:
		so.write("%-10s %s\n" % (ymd, text))
	    else:
		so.write('BEGIN:VEVENT\n')
		so.write('SUMMARY;CHARSET=ISO-8859-1:%s\n' % text)
		so.write('DTSTART:%s\n' % dtstart)
		if pdict["end"]:
		    so.write('DTEND:%s\n' % dtend)
		so.write('END:VEVENT\n')


    # Slut på kalendern
    if preview:
	so.write('</PRE>\n')
    else:
	so.write('END:VCALENDAR\n')

    # Slut på sidan
    if preview:
	so.write('</BODY>\n')


#
# Invocation
#

if __name__ == '__main__':
    import sys
    handle_cgi()
