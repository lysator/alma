#!/opt/python/bin/python
# -*- coding: iso-8859-1 -*-
# $Id: alma.py,v 1.1 2004/12/07 20:24:54 kent Exp $
# Svenska almanackan
# Copyright 2004 Kent Engström. Released under GPL.

import time
from cStringIO import StringIO

import jddate; JD=jddate.FromYMD


#
# Data
#

# Månader (index 1..12)
month_names =   [None,
		 "Januari", "Februari", "Mars",
		 "April", "Maj", "Juni",
		 "Juli", "Augusti", "September",
		 "Oktober", "November", "December"]

# Veckodagar (index 1..7)
wday_names = [None, "Måndag", "Tisdag", "Onsdag",
	      "Torsdag", "Fredag", "Lördag", "Söndag"]


#
# Functions
#


# Beräkna vilken dag som är påsksöndag ett visst år 
# Algoritm: Meeus, Jean, Astronomical Formulae for Calculators, 2 ed, s 31

def easter_sunday(year):
    a = year % 19
    b , c = divmod(year, 100)
    d , e = divmod(b, 4)
    f = (b+8) / 25
    g = (b-f+1) / 3
    h = (19*a+b-d-g+15) % 30
    i, k = divmod(c, 4)
    l = (32+2*e+2*i-h-k) % 7
    m = (a+11*h+22*l) / 451
    n, p = divmod(h+l-7*m+114, 31)

    return JD(year, n, p+1)

# First weekday wd on or after y-m-d
def firstday(y, m, d, wd):
    jd = JD(y, m, d)
    (_, _, jdwd) = jd.GetYWD()
    diff = wd - jdwd
    if diff < 0: diff = diff + 7
    return jd + diff

#
# Classes
#

class DayCal:
    """Class to represent a single day."""
    def __init__(self, jd):
	self.jd = jd           # jddate

	(self.y,
	 self.m,
	 self.d) = self.jd.GetYMD()

	(self.wyear,
	 self.week,
	 self.wday) = self.jd.GetYWD()

	self.flag_day = False  # flaggdag?
	self.red_names = []    # heldagsnamn
	self.black_names = []  # andra namn (som ej gör dagen röd)
	self.names = []        # namnsdagsnamn
	self.wday_name = wday_names[self.wday]
	self.wday_name_short = self.wday_name[:3]

	if self.wday == 7:
	    self.red = True    # Alla söndagar är röda
	else:
	    self.red = False   # Alla andra dagar är svarta tillsvidare
 
    def add_info(self, red, flag, name):
	if red:
	    self.red = True
	    if name: self.red_names.append(name)
	else:
	    if name: self.black_names.append(name)
	
	if flag:
	    self.flag_day = True
    
    def set_names(self, names):
	self.names = names

    def __repr__(self):
	return "<Day %s>"  % self.jd.GetString_YYYY_MM_DD()

    def html_vertical(self, f):
	if self.red:
	    colour = "red"
	else:
	    colour = "black"

	f.write('<TR CLASS="v">')

	# Veckonr överst och varje måndag
	if self.d == 1 or self.wday == 1:
	    f.write('<TD CLASS="vweek_present">%d</TD>' % (self.week))
	else:
	    f.write('<TD CLASS="vweek_empty">&nbsp;</TD>')

	# Veckodagens tre först tecken
	f.write('<TD CLASS="vwday_%s">%s</TD>' % (colour, self.wday_name_short))

	# Dagens nummer
	f.write('<TD CLASS="vday_%s">%d</TD>' % (colour, self.d))

	# Flaggdag?
	if self.flag_day:
	    f.write('<TD CLASS="vflag"><IMG SRC="flag.gif"></TD>')
	else:
	    f.write('<TD CLASS="vflag">&nbsp;</TD>')

	# Dagens namn. Överst röda, svarta. Under namnsdagar
	redblack = []
	for name in self.red_names:
	    redblack.append('<SPAN CLASS="vname_red">%s</SPAN>' % name)
	for name in self.black_names:
	    redblack.append('<SPAN CLASS="vname_black">%s</SPAN>' % name)
	redblack_string = ", ".join(redblack)
	name_string = ", ".join(self.names)
	
	f.write('<TD CLASS="vnames">')
	f.write(redblack_string)
	if redblack_string and name_string: f.write('<BR>')
	f.write(name_string)
	f.write('&nbsp;</TD>')

	f.write('</TR>\n')

    def dump(self):
	"""Show in text format for debugging."""
	print "%s %3s %2d %s%s %s %s %s" % (self.jd.GetString_YYYY_MM_DD(),
					    self.wday_name_short,
					    self.week,
					    " *"[self.red],
					    " F"[self.flag_day],
					    self.red_names,
					    self.black_names,
					    self.names,
					    )

class YearCal:
    """Class to represent a whole year."""

    def __init__(self, year):
	self.year = year       # År (exv. 2004)
	self.jd_jan1 = JD(year, 1, 1)
	
	# Skapa alla dagar för året
	self.days = []
	jd = self.jd_jan1
	while True:
	    self.days.append(DayCal(jd))
	    jd = jd + 1
	    (y, _, _) = jd.GetYMD()
	    if y <> year: break

	# Skottår?
	if len(self.days) == 365:
	    self.leap_year = False
	elif len(self.days) == 366:
	    self.leap_year = True
	else:
	    assert ValueError, "bad number of days in a year"

	# Helgdagar, flaggdagar med mera
	self.place_names()

	# Namnsdagar
	if year >= 2001:
	    self.place_name_day_names("namnsdagar-2001.txt")
	elif year >= 1993:
	    self.place_name_day_names("namnsdagar-1993.txt")
	elif year >= 1986:
	    self.place_name_day_names("namnsdagar-1986.txt")

    def add_info_md(self, m, d, red, flag, name):
	dc = self.get_md(m, d)
	dc.add_info(red, flag, name)

    def add_info_jd(self, jd, red, flag, name):
	(y, m, d) = jd.GetYMD()
	assert y == self.year
	dc = self.get_md(m, d)
	dc.add_info(red, flag, name)

    def place_names(self):
	"""Place holidays etc. in the calendar."""

	# Fasta helgdagar och flaggdagar

	for (from_year, to_year, m, d, red, flag, name) in \
	    [(None, None,  1,  1, True , True,  "Nyårsdagen"),
	     (None, None,  1, 28, False, True,  None), # Konungens namnsdag
	     (None, None,  1,  5, False, False, "Trettondedagsafton"),
	     (None, None,  1,  6, True,  False, "Trettondedag Jul"),
	     (None, None,  1, 13, False, False, "Tjugondedag Knut"),
	     (None, None,  3, 12, False, True,  None), # Kronprinsessans namnsdag
	     (None, None,  4, 30, False, True,  "Valborgsmässoafton"), # + Konungens födelsedag
	     (None, None,  5,  1, True,  True,  "Första Maj"),
	     (None, 2004,  6,  6, False, True,  "Sveriges Nationaldag"),
	     (2005, None,  6,  6, True, True,  "Sveriges Nationaldag"),
	     (None, None,  6, 24, False, False, "Joh:s Döp:s dag"),
	     (None, None,  7, 14, False, True,  None), # Kronprinsessans födelsedag
	     (None, None,  8,  8, False, True,  None), # Drottningens namnsdag
	     (None, None, 10, 24, False, True,  "FN-dagen"),
	     (None, None, 11,  1, False, False, "Allhelgonadagen"),
	     (None, None, 11,  6, False, True,  None), # Gustav Adolfsdagen
	     (None, None, 12, 10, False, True,  "Nobeldagen"),
	     (None, None, 12, 23, False, True,  None), # Drottningens födelsedag
	     (None, None, 12, 24, False, False, "Julafton"),
	     (None, None, 12, 25, True,  True,  "Juldagen"),
	     (None, None, 12, 26, True,  False, "Annandag Jul"),
	     (None, None, 12, 28, False, False, "Menlösa barns dag"),
	     (None, None, 12, 31, False, False, "Nyårsafton"),
	     ]:
	    if from_year is not None and self.year < from_year: continue
	    if to_year is not None and self.year > to_year: continue
	    self.add_info_md(m, d, red, flag, name)

	# Skottdagen inföll den 24/2 -1996, infaller den 29/2 2000-
	if self.leap_year:
	    if self.year >= 2000:
		self.add_info_md(2, 29, False, False, "Skottdagen")
	    else:
		self.add_info_md(2, 24, False, False, "Skottdagen")

	# Påsksöndagen ligger till grund för det mesta
	pd = easter_sunday(self.year)

	# Söndagen efter nyår
	sen = firstday(self.year, 1, 2, 7) # Första söndagen 2/1-
	if sen < JD(self.year, 1 ,6):  # Slås ut av 13dagen och 1 e 13dagen
	    self.add_info_jd(sen, True, False, "Söndagen e Nyår")

	# Kyndelsmässodagen (Jungfru Marie Kyrkogångsdag)
	jmk = firstday(self.year, 2, 2 , 7)
	if jmk == pd - 49:
	    # Kyndelsmässodagen på fastlagssöndagen => Kyndelsmässodagen flyttas -1v
	    jmk = jmk -7
	self.add_info_jd(jmk, True, False, "Kyndelsmässodagen")

	# Söndagar efter Trettondedagen

	set = firstday(self.year, 1,7, 7)
	for i in range(1,7):
	    if set != jmk and set < pd -63:
		# Slås ut av Kyndelsmässodagen och allt påskaktigt
		self.add_info_jd(set, True, False, "%d e Trettondedagen" % i)
	    set = set + 7

	# Jungfru Marie Bebådelsedag
	jmb = firstday(self.year, 3, 25, 7)
	print jmb
	if jmb >= pd - 7 and jmb <= pd:
	    # Ej på påskdagen/palmsöndagen
	    jmb = pd - 14
	self.add_info_jd(jmb, True, False, "Jungfru Marie Bebådelsedag")

	# Fasta, Påsk, Kristi Himmelsfärd, Pingst

	if pd-63 != jmk:
	    self.add_info_jd(pd-63, True, False, "Septuagesima")
	if pd-56 != jmk:
	    self.add_info_jd(pd-56, True, False, "Sexagesima")
	self.add_info_jd(pd-49, True, False, "Fastlagssöndagen")
	self.add_info_jd(pd-47, False,False, "Fettisdagen")
	self.add_info_jd(pd-46, False,False, "Askonsdagen")
	self.add_info_jd(pd-42, True, False, "1 i Fastan")
	self.add_info_jd(pd-35, True, False, "2 i Fastan")
	self.add_info_jd(pd-28, True, False, "3 i Fastan")
	self.add_info_jd(pd-21, True, False, "Midfastosöndagen")
	if pd-14 != jmb:
	    self.add_info_jd(pd-14, True, False, "5 i Fastan")
	self.add_info_jd(pd- 7, True, False, "Palmsöndagen")
	self.add_info_jd(pd- 4, False,False, "Dymmelonsdagen")
	self.add_info_jd(pd- 3, False,False, "Skärtorsdagen")
	self.add_info_jd(pd- 2, True, False, "Långfredagen")
	self.add_info_jd(pd- 1, False,False, "Påskafton")
	self.add_info_jd(pd+ 0, True, True,  "Påskdagen")
	self.add_info_jd(pd+ 1, True, False, "Annandag Påsk")
	self.add_info_jd(pd+ 7, True, False, "1 e Påsk")
	self.add_info_jd(pd+14, True, False, "2 e Påsk")
	self.add_info_jd(pd+21, True, False, "3 e Påsk")
	self.add_info_jd(pd+28, True, False, "4 e Påsk")
	self.add_info_jd(pd+35, True, False, "Bönsöndagen")
	self.add_info_jd(pd+39, True, False, "Kristi Himmelsfärds dag")
	self.add_info_jd(pd+42, True, False, "6 e Påsk")
	self.add_info_jd(pd+48, False,False, "Pingstafton")
	self.add_info_jd(pd+49, True, True,  "Pingstdagen")
	if self.year < 2005:
	    self.add_info_jd(pd+50, True, False, "Annandag Pingst")
	else:
	    self.add_info_jd(pd+50, False,False, "Annandag Pingst")
	self.add_info_jd(pd+56, True,False, "Heliga Trefaldighets dag")

	# Midsommardagen

	msd = firstday(self.year, 6, 20, 6)
	self.add_info_jd(msd-1, False, False, "Midsommarafton")
	self.add_info_jd(msd+0, True,  True,  "Midsommardagen")
    
	# Alla Helgons dag

	ahd = firstday(self.year, 10, 31, 6)
	self.add_info_jd(ahd+0, True, False, "Alla Helgons dag")
	self.add_info_jd(ahd+1, True, False, "Söndagen e Alla Helgons dag")


    

    def place_name_day_names(self, filename):
	for line in open(filename):
	    (ms, ds, ns) = line.strip().split(None,2)
	    m = int(ms)
	    d = int(ds)
	    # Innan år 2000, då skottdagen var 24/2, så flyttades
	    # namnen till senare dagar i februari
	    if self.leap_year and self.year < 2000 and m == 2 and d >= 24: 
		d = d + 1
	    names = ns.split()
	    dc = self.get_md(m, d)
	    dc.set_names(names)

    def get_md(self, m, d):
	jd = JD(self.year, m, d)
	return self.days[jd - self.jd_jan1]

    def dump(self):
	"""Show in text format for debugging."""

	for m in range(1,13):
	    mc = MonthCal(self, m)
	    mc.dump()
	
class MonthCal:
    """Class to represent a month of a year."""

    def __init__(self, yearcal, month):
	self.yc = yearcal
	assert 1<= month <= 12
	self.month = month
	self.month_name = month_names[self.month]

	self.num_days = [None, 31, 28, 31, 30, 31, 30,
			 31, 31, 30, 31, 30, 31][self.month]
	if self.yc.leap_year and self.month == 2:
	     self.num_days = 29

    def generate(self):
	for d in range(1,self.num_days+1):
	    dc = self.yc.get_md(self.month, d)
	    yield dc

    def html_vertical(self, f):
	head = '%s %s' % (self.month_name, self.yc.year)

	f.write('<HEAD>')
	f.write('<TITLE>%s</TITLE>' % head)
	f.write('<LINK TYPE="text/css" REL="stylesheet" HREF="alma.css">')
	f.write('</HEAD>\n')

	f.write('<BODY>')
	f.write('<H1>%s</H1>\n' % head)

	# Länkar bakåt och framåt
	if self.month == 1:
	    pm = 12
	    py = self.yc.year - 1
	else:
	    pm = self.month - 1
	    py = self.yc.year

	if self.month == 12:
	    nm = 1
	    ny = self.yc.year +1
	else:
	    nm = self.month + 1
	    ny = self.yc.year

	f.write('<P>')
	f.write('<A HREF="?year=%d&month=%d">[%s %d]</A>' % (py, pm,
							   month_names[pm], py))
	f.write(' ~ ')
	f.write('<A HREF="?year=%d&month=%d">[%s %d]</A>' % (ny, nm,
							   month_names[nm], ny))
	f.write('</P>')

	# Tabellen med dagarna
	f.write('<TABLE CLASS="vtable">')
	for dc in self.generate():
	    dc.html_vertical(f)
	f.write('<TR CLASS="v"><TD CLASS="vlast" COLSPAN="5">&nbsp;</TD></TR>')
	f.write('</TABLE>')
	f.write('</BODY>')

    def dump(self):
	"""Show in text format for debugging."""
	print self.month_name
	print
	for dc in self.generate():
	    dc.dump()
	print

#
# CGI driver
#

def handle_cgi():
    print "Content-Type: text/html\r\n\r"

    import cgi
    import cgitb; cgitb.enable()
    form = cgi.FieldStorage()

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

    if year is not None and month is not None:
	yc = YearCal(year)
	mc = MonthCal(yc, month)
	mc.html_vertical(sys.stdout)
    else:
	print "<P>Fel"


#
# Invocation
#

if __name__ == '__main__':
    import sys
    handle_cgi()

    #yc = YearCal(int(sys.argv[1]))
    #yc.dump()
