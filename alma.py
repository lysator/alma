#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# $Id: alma.py,v 1.30 2009/11/30 18:28:38 kent Exp $
# Svenska almanackan
# Copyright 2004 Kent Engström. Released under GPL.

import math
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
# Fram till ungefär 1872 användes de latinska formerna i almanackan, ihop med de gamla hedniska månadsnamnen.
month_old_names =   [None,
		 "Januarius &ndash; Thors-månad", "Februarius &ndash; Göjemånad", "Martius &ndash; Wårmånad",
		 "Aprilis &ndash; Gräsmånad", "Majus &ndash; Blomstermånad", "Junius &ndash; Sommarmånad",
		 "Julius &ndash; Hömånad", "Augustus &ndash; Skördemånad", "September &ndash; Höstmånad",
		 "October &ndash; Slagtmånad", "November &ndash; Wintermånad", "December &ndash; Julmånad"]

# Veckodagar (index 1..7)
wday_names = [None, "Måndag", "Tisdag", "Onsdag",
	      "Torsdag", "Fredag", "Lördag", "Söndag"]

# Klasser av dagar (uppdelning enligt intresse nedan är såklart väldigt godtycklig)

MRED   = 0 # Röd dag, av mera allmänt intresse (t.ex. juldagen)
RED    = 1 # Röd dag, ej av allmänt intresse (t.ex. domsöndagen)
MBLACK = 2 # Svart dag, av mera allmänt intresse (t.ex. julafton)
BLACK  = 3 # Svart dag, ej av allmänt intresse (t.ex. allhelgondagen)

# Tidszon (positivt åt öster)
TIMEZONE = 1

#
# Funktioner
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

    # Formeln ovan är gjord för den gregorianska kalendern.
    # Konverteringar görs för att omvandla ifall det är den
    # svenska kalendern eller julianska kalendern:

    # Plockar ut JD utifrån vårt gregorianska datum:
    jd = jddate.ymd_to_jd_gregorian(year,n,p+1)

    # Korrigerar för upptäckta fel mot verkliga kalendrar:
    # Sverige använde astronomisk påskräkning 1740-1844. Dock "fuskade"
    # man ett par gånger och följde den gregorianska påskuträkningen.
    if year==1802 or year==1805 or year==1818: jd += 7
    elif year==1744: jd -= 7

    # Plockar fram datum för den kalender som råkar gälla vid jd:
    # year ändras inte, då påsksöndagen aldrig är nära nyår:
    
    (year,month,day) = jddate.jd_to_ymd(jd)
    
    return JD(year, month, day)

# Beräkna JD då en viss månfas inträffar i en viss cykel
# Algoritm: Meeus, Jean, Astronomical Formulae for Calculators, 2 ed, s 159


def moonphase(cycle, phase):
    # Beräkna parametrar
    # phase: 0 är nymåne, 1 är växande halvmåne, 2 är fullmåne, 3 är avtagande halvmåne
    assert phase in [0,1,2,3]
    k = cycle + phase/4.0
    t  = k / 1236.85

    # Beräkna ursprunglig "gissning"

    jd = 2415020.75933 \
	+ 29.53058868 * k \
	+ 0.0001178 * t*t \
	- 0.000000155 * t*t*t \
	+ 0.00033 * math.sin(2.90702 + 2.31902 * t + 0.0001601 * t*t)

    # Beräkna positioner vid denna tidpunkt

    m  = 359.2242 +  29.10535608 * k - 0.0000333 * t*t - 0.00000347 * t*t*t
    mp = 306.0253 + 385.81691806 * k + 0.0107306 * t*t + 0.00001236 * t*t*t
    f  =  21.2964 + 390.67050646 * k - 0.0016528 * t*t - 0.00000239 * t*t*t
    m  *=  math.pi/180.0
    mp *=  math.pi/180.0
    f  *=  math.pi/180.0

    # Korrigera "gissningen" m a p dessa positioner

    if phase in [0, 2]: 
	# Nymåne och fullmåne
	jd += (0.1734 - 0.000393*t) * math.sin(m) \
	    + 0.0021 * math.sin(2*m) \
	    - 0.4068 * math.sin(mp) \
	    + 0.0161 * math.sin(2*mp) \
	    - 0.0004 * math.sin(3*mp) \
	    + 0.0104 * math.sin(2*f) \
	    - 0.0051 * math.sin(m+mp) \
	    - 0.0074 * math.sin(m-mp) \
	    + 0.0004 * math.sin(2*f+m) \
	    - 0.0004 * math.sin(2*f-m) \
	    - 0.0006 * math.sin(2*f+mp) \
	    + 0.0010 * math.sin(2*f-mp) \
	    + 0.0005 * math.sin(m+2*mp)
    else:
	# Växande och avtagande halvmåne
	  jd += (0.1721 - 0.0004*t) * math.sin(m) \
	      + 0.0021 * math.sin(2*m) \
	      - 0.6280 * math.sin(mp) \
	      + 0.0089 * math.sin(2*mp) \
	      - 0.0004 * math.sin(3*mp) \
	      + 0.0079 * math.sin(2*f) \
	      - 0.0119 * math.sin(m+mp) \
	      - 0.0047 * math.sin(m-mp) \
	      + 0.0003 * math.sin(2*f+m) \
	      - 0.0004 * math.sin(2*f-m) \
	      - 0.0006 * math.sin(2*f+mp) \
	      + 0.0021 * math.sin(2*f-mp) \
	      + 0.0003 * math.sin(m+2*mp) \
	      + 0.0004 * math.sin(m-2*mp) \
	      - 0.0003 * math.sin(2*m+mp)

	  if phase == 1:
	      jd += 0.0028 - 0.0004*math.cos(m) + 0.0003*math.cos(mp);
	  else:
	      jd -= (0.0028 - 0.0004*math.cos(m) + 0.0003*math.cos(mp));

    # Korrigera för:
    # 1) Resten av programmet har en lite annorlunda definition av JD.
    #    JD här = JD i resten - 0.5 dygn
    #  2) Tidszon

    jd = jd + 0.5 + TIMEZONE/24.0

    # Dela upp i dag, timme, minut

    day  = int(jd)
    rest = (jd - day) * 24
    hour = int(rest)
    min  = int((rest - hour) * 60);

    # Återvänd med datumtyp, kasta tillsvidare h och m
    return jddate.FromJD(day)


# Första veckodagen av visst slag på eller efter ett visst datum
def first_weekday(y, m, d, wd):
    jd = JD(y, m, d)
    (_, _, jdwd) = jd.GetYWD()
    diff = wd - jdwd
    if diff < 0: diff = diff + 7
    return jd + diff

def first_sunday(y, m, d):
    return first_weekday(y, m, d, 7)

def first_saturday(y, m, d):
    return first_weekday(y, m, d, 6)

# Föregående månad
def previous_month(y, m):
    if m == 1:
	return (y-1, 12)
    else:
	return (y, m-1)

# Nästa månad
def next_month(y, m):
    if m == 12:
	return (y+1, 1)
    else:
	return (y, m+1)

# Föregående vecka
def previous_week(y, w):
    jd = jddate.FromYWD(y, w, 1) - 7
    y, w, _ = jd.GetYWD()
    return y, w

# Nästa vecka
def next_week(y, w):
    jd = jddate.FromYWD(y, w, 1) + 7
    y, w, _ = jd.GetYWD()
    return y, w

# År och vecka --> År och månad
# (första dagen i veckan får bestämma)
def yw_to_ym(year, week):
    jd = jddate.FromYWD(year, week, 1)
    year, month, _ = jd.GetYMD()
    return year, month

# År och månad --> År och vecka
# (första dagen i månaden får bestämma)
def ym_to_yw(year, month):
    jd = jddate.FromYMD(year, month, 1)
    year, week, _ = jd.GetYWD()
    return year, week


#
# Klasser
#

class DayName:
    """Class to represent a day name and its importance."""
    def __init__(self, name, dayclass):
	self.name = name
	self.dayclass = dayclass
	self.is_red = dayclass <= RED

    def __repr__(self):
	return "<%s %d>" % (self.name, self.dayclass)

class DayCal:
    """Class to represent a single day."""
    def __init__(self, jd, mark_as_today = False):
	self.jd = jd           # jddate
        self.is_today = mark_as_today

	(self.y,
	 self.m,
	 self.d) = self.jd.GetYMD()

	(self.wyear,
	 self.week,
	 self.wday) = self.jd.GetYWD()

	# wday är alltid 1 för måndag ... 7 för söndag
	# wpos talar om positionen i veckan
	if self.y >= 1973:
	    self.wpos = self.wday # måndag först i veckan
	else:
	    if self.wday == 7:
		self.wpos = 1 # söndag först i veckan
	    else:
		self.wpos = self.wday + 1

	self.flag_day = False  # flaggdag?
	self.day_names = []    # röda och svarta dagsnamn, blandat (klass DayName)
	self.names = []        # namnsdagsnamn
	self.wday_name = wday_names[self.wday]
	self.wday_name_short = self.wday_name[:3]

	if self.wday == 7:
	    self.red = True    # Alla söndagar är röda
	else:
	    self.red = False   # Alla andra dagar är svarta tillsvidare

	self.moonphase = None  # Månfas (0 = nymåne, 1, 2 = fullmåne, 3)
 
    def add_info(self, dayclass, flag, name):
	assert MRED <= dayclass <= BLACK
	if dayclass <= RED:
	    self.red = True
	if name: self.day_names.append(DayName(name, dayclass))
	if flag:
	    self.flag_day = True
    
    def set_names(self, names):
	self.names = names

    def set_moonphase(self, moonphase):
	self.moonphase = moonphase

    def moonphase_name(self):
	if self.moonphase is None:
	    return ""
	else:
	    return ["Nymåne", "Första kvarteret", "Fullmåne", "Sista kvarteret"][self.moonphase]

    def __repr__(self):
	return "<Day %s>"  % self.jd.GetString_YYYY_MM_DD()

    def html_redblack(self, sep = ", "):
	redblack = []
	for dayclass in range(MRED,BLACK+1):
	    for dayname in self.day_names:
		if dayname.dayclass == dayclass:
		    if dayname.is_red:
			colour = "red"
		    else:
			colour = "black"
		    redblack.append('<SPAN CLASS="vname %s">%s</SPAN>' % (colour, dayname.name))
	return sep.join(redblack)

    def html_vertical(self, f, in_week_cal = False, for_printing = False):
	if self.red:
	    colour = "red"
	else:
	    colour = "black"

        if self.is_today and not for_printing:
            f.write('<TR CLASS="v today">')
        else:
            f.write('<TR CLASS="v">')

	# Veckan börjar på måndag fr o m 1973, innan på måndag
	# Dessutom "börjar" ju en vecka i början av varje månad.
	if self.d == 1 or self.wpos == 1:
            if in_week_cal:
                # I en veckokalender är det ju månaden som är intressant
                wtext = '<A CLASS="hidelink" HREF="?year=%d&month=%d&type=vertical">%s</A>' % (self.y,
                                                                                               self.m,
                                                                                               month_names[self.m][:3])
            else:
                # I månadskalender vill vi ha veckonumret
                if self.y >= 1973:
                    # Veckonummer relevant fr o m 1973
                    wtext = '<A CLASS="hidelink" HREF="?year=%d&week=%d&type=week">%s</A>' % (self.wyear,
                                                                                              self.week,
                                                                                              self.week)
                else:
                    wtext = "&nbsp;"
	    f.write('<TD CLASS="vweek_present leftmost">%s</TD>' % wtext)
	else:
	    f.write('<TD CLASS="vweek_empty leftmost">&nbsp;</TD>')

	# Veckodagens tre först tecken
	f.write('<TD CLASS="vwday %s">%s</TD>' % (colour, self.wday_name_short))

	# Dagens nummer
	f.write('<TD CLASS="vday %s">%d</TD>' % (colour, self.d))

	# Flaggdagar och månfaser
	f.write('<TD CLASS="vflag">')
	empty = True

	if self.flag_day:
	    f.write('<IMG SRC="flag.gif" ALT="Flaggdag" TITLE="Flaggdag">')
	    empty = False

	if self.moonphase is not None:
	    f.write('<IMG SRC="moonphase%d.gif" ALT="%s" TITLE="%s">' % (self.moonphase, self.moonphase_name(), self.moonphase_name()))
	    empty = False

	if empty:
	    f.write('&nbsp;')
	f.write('</TD>')

	# Dagens namn. Överst röda, svarta. Under namnsdagar
	redblack_string = self.html_redblack()
	name_string = ", ".join(self.names)
	
	if in_week_cal:
            f.write('<TD CLASS="vnames">')
        else:
            f.write('<TD CLASS="vnames rightmost">')
	f.write(redblack_string)
	if redblack_string and name_string: f.write('<BR>')
	f.write(name_string)
	f.write('&nbsp;</TD>')

        # Anteckningsutrymme i veckoalmanackan
        if in_week_cal:
            f.write('<TD CLASS="vnotes rightmost">&nbsp;</TD>')


	f.write('</TR>\n')

    def html_tabular(self, f, for_printing = False, high = False):
	if self.red:
	    colour = "red"
	else:
	    colour = "black"
	
        if self.is_today and not for_printing:
            f.write('<TD CLASS="tday today">')
        else:
            f.write('<TD CLASS="tday">')
	f.write('<TABLE>')

	# Dagens nummer
	f.write('<TR><TD CLASS="tdday %s">%d</TD>' % (colour, self.d))

	# Dagens namn
	f.write('<TD ROWSPAN="2" CLASS="tdnames">')
	redblack_string = self.html_redblack(sep="<BR>")
	name_string = ", ".join(self.names)
	f.write(redblack_string)
	if redblack_string and name_string: f.write('<BR>')
	f.write(name_string)
	f.write('&nbsp;</TD></TR>')

	# Flaggdagar
	f.write('<TR><TD CLASS="tdflag">')
	if self.flag_day:
	    f.write('<IMG SRC="flag.gif" ALT="Flaggdag" TITLE="Flaggdag">')
	if self.moonphase is not None:
	    f.write('<IMG SRC="moonphase%d.gif" ALT="%s" TITLE="%s">' % (self.moonphase, self.moonphase_name(), self.moonphase_name()))
	f.write('</TD></TR>')

        if high:
            f.write('<TR><TD CLASS="tdspacer">&nbsp;</TD></TR>')
            

	f.write('</TABLE>')
	f.write('</TD>')

    # Dagblocksliknande
    def html_day(self, f):
	if self.red:
	    colour = "red"
	else:
	    colour = "black"
	
	f.write('<LINK TYPE="text/css" REL="stylesheet" HREF="day.css">')
	f.write('<DIV CLASS="douter">')

	# Månad
        f.write('<DIV CLASS="dmonth">%s</DIV>' % month_names[self.m])

	# Dag
	f.write('<DIV CLASS="dday %s">%d</DIV>' % (colour, self.d))

	# Veckodag
	f.write('<DIV CLASS="dwday %s">%s v%d</DIV>' % (colour,
							self.wday_name,
							self.week))
	# Flaggdagar och månfaser
	f.write('<DIV CLASS="dflag">')
	if self.flag_day:
	    f.write('<IMG SRC="flag.gif">')
	if self.moonphase is not None:
	    f.write('<IMG SRC="moonphase%d.gif">' % self.moonphase)
	f.write('</DIV>')

	# Dagens namn
	f.write('<DIV CLASS="dnames">')
	redblack_string = self.html_redblack(sep="<BR>")
	name_string = ", ".join(self.names)
	f.write(redblack_string)
	if redblack_string and name_string: f.write('<BR>')
	f.write(name_string)
	f.write('&nbsp;</DIV>')

	f.write('</DIV>')


    def dump(self):
	"""Show in text format for debugging."""
	print "%s %4d-%02d-%1d %s%s <%s> <%s>" % (self.jd.GetString_YYYY_MM_DD(),
						  self.wyear, self.week, self.wday,
						  " R"[self.red],
						  " F"[self.flag_day],
						  ",".join(map(str,self.day_names)),
						  ",".join(self.names),
						  )

class YearCal:
    """Class to represent a whole year."""

    def __init__(self, year):
	self.year = year       # År (exv. 2004)
	self.jd_jan1 = JD(year, 1, 1)
	self.jd_dec31 = JD(year, 12, 31)

	# Skapa alla dagar för året
	self.days = []
        jd_today = jddate.FromToday()
	jd = self.jd_jan1
	while jd <= self.jd_dec31:
	    self.days.append(DayCal(jd, mark_as_today = (jd==jd_today)))
	    jd = jd + 1

	# Skottår?
	if len(self.days) == 365 or len(self.days) == 354:
	    self.leap_year = False
	elif len(self.days) == 366 or len(self.days) == 367:
	    self.leap_year = True
	else:
	    assert ValueError, "bad number of days in a year"

	# Helgdagar, flaggdagar med mera
	self.place_names()

	# Namnsdagar
	if year >= 2011:
		self.place_name_day_names("namnsdagar-2011.txt",
				      [(2015,  7, 23, ["Emma","Emmy"]),
				       (2015,  7, 26, ["Jesper","Jasmine"]),
				       (2018,  3,  8, ["Siv","Saga"]),
				       (2018,  9, 14, ["Ida","Ronja"]),
                                       (2022, 12,  3, ["Lydia", "Cornelia"]),
                                       (2022,  1, 19, ["Henrik", "Henry"]),
                                       (2022,  2, 28, ["Maria", "Maja"]),
                                       (2022,  3, 31, ["Ester", "Noa"]),
                                       (2022,  7, 29, ["Olof", "Olle"]),
                                       (2022,  3, 12, ["Viktoria", "Regina"]),
                                       (2022, 11,  2, ["Tobias", "Tim"]),
                                       ])
	elif year >= 2001:
	    self.place_name_day_names("namnsdagar-2001.txt")
	elif year >= 1993:
	    self.place_name_day_names("namnsdagar-1993.txt")
	elif year >= 1986:
	    self.place_name_day_names("namnsdagar-1986.txt")
	elif year >= 1901:
	    self.place_name_day_names("namnsdagar-1901.txt",
				      [(1905, 11,  4, ["Sverker"]),
				       (1907, 11, 27, ["Astrid"]),
                                       (1918,  4, 26, ["Teresia"]), # Teresia och Engelbrekt byter plats med varandra.
                                       (1918,  4, 27, ["Engelbrekt"]),
				       (1953,  3, 25, ["Marie Bebådelsedag"]),
				       (1953,  6, 24, ["Johannes Döparens dag"]),
				       (1934, 10, 20, ["Sibylla"])])
        elif year >=1800:
            self.place_name_day_names("namnsdagar-1800.txt",
                                      [(1883,  1,  2, ["Abel, Set"]),
                                       (1811,  1,  7, ["August"]),
                                       (1818,  1, 31, ["Vigilius"]),      # ersätter Wigilius
                                       (1823,  2,  1, ["Maximiliana"]),
                                       (1877,  2,  5, ["Agata"]), # ersätter Agatha
                                       (1877,  2,  6, ["Dorotea"]), # Dorothea
                                       (1812,  2, 10, ["Eugenia"]),
                                       (1872,  2, 14, ["Valentin"]), # Walentin
                                       (1851,  2, 17, ["Alexandra"]),
                                       (1806,  2, 28, ["Maria"]),
                                       (1830,  3,  1, ["Albin"]),
                                       (1830,  3,  2, ["Ernst"]),
                                       (1830,  3,  4, ["Adrian"]),
                                       (1898,  3,  6, ["Ebba"]),
                                       (1882,  3, 12, ["Viktoria"]),
                                       (1831,  3, 13, ["Nicephorus"]),
                                       (1882,  3, 13, ["Gregorius"]),
                                       (1883,  3, 14, ["Matilda"]),
                                       (1837,  3, 15, ["Christofer"]), # (3) Christopher
                                       (1873,  3, 18, ["Edvard"]),
                                       (1877,  3, 19, ["Josef"]),    # Joseph
                                       (1877,  3, 20, ["Joakim"]),   # Joachim
                                       (1877,  4,  6, ["Vilhelm"]),  # Wilhelm
                                       (1877,  4, 10, ["Hezekiel"]), # Hezechiel
                                       (1803,  4, 16, ["Patrik"]),   # Patrick
                                       (1837,  4, 18, ["Valerian"]), # (3) Walerian
                                       (1812,  4, 22, ["Bernhardina"]),
                                       (1865,  4, 27, ["Theresia"]),
                                       (1859,  4, 30, ["Mariana"]),
                                       (1831,  5, 10, ["Esbjörn"]),
                                       (1822,  5, 13, ["Servatius"]),
                                       (1877,  5, 17, ["Rebecka"]),    # Rebecca (två av tre kalendrar bytte till ck 1877)
                                       (1872,  5, 18, ["Erik"]),       # Eric
                                       (1877,  5, 21, ["Konstantin"]), # Constantin
                                       (1812,  5, 23, ["Desideria"]),
                                       (1877,  5, 26, ["Vilhelmina"]), # Wilhelmina
                                       (1898,  5, 28, ["Ingeborg"]),
                                       (1872,  6, 10, ["Svante"]),     # Swante
                                       (1806,  6, 13, ["Aqvilina"]),   # Aqwilina
                                       (1872,  6, 15, ["Vitus"]),      # Witus
                                       (1818,  6, 19, ["Gervasius"]),  # Efter Gerwasius
                                       (1877,  6, 23, ["Adolf"]),      # Adolph
                                       (1801,  6, 25, ["David"]),      # Dawid
                                       (1876,  7,  4, ["Ulrika"]),     # Ulrica
                                       (1820,  7,  5, ["Melcher"]),    # (2) Före: Melker
                                       (1874,  7, 18, ["Fredrik"]),    # (4) Före: Fredric
                                       (1877,  7, 20, ["Margareta"]),  # Margaretha
                                       (1827,  7, 23, ["Emma"]),
                                       (1883,  7, 26, ["Marta"]),
                                       (1876,  7, 27, ["7 sofvare"]),  # 7 sofware
                                       (1872,  7, 28, ["Botvid"]),     # Botwid
                                       (1876,  8, 17, ["Verner"]),     # Werner
                                       (1824,  8, 21, ["Josephina"]),
                                       (1859,  8, 22, ["Henrietta"]),
                                       (1877,  8, 23, ["Zacheus"]),     # Zachæus
                                       (1877,  8, 24, ["Bartholomeus"]),# Bartholomæus
                                       (1855,  8, 25, ["Lovisa"]),      # (5)
                                       (1801,  8, 28, ["Augustinus"]),  # Augustin
                                       (1890,  8, 30, ["Albert"]),
                                       (1872,  8, 31, ["Arvid"]),       # Arwid
                                       (1831,  9,  9, ["Augusta"]),
                                       (1883,  9, 15, ["Nicetas"]),
                                       (1876,  9, 19, ["Fredrika"]),   # Fredrica
                                       (1801,  9, 21, ["Mattheus"]),   # Matthæus
                                       (1806,  9, 21, ["Matthæus"]),   # Samma datum
                                       (1825,  9, 21, ["Mattheus"]),   # Efter 1821, senast 1829.
                                       (1837,  9, 21, ["Matthæus"]),   # Efter 1829, senast 1845.
                                       (1877,  9, 21, ["Mattheus"]),   #
                                       (1897,  9, 21,  ["Matteus"]),   # Vissa modernare kalendrar hade denna 1897.
                                       (1877,  9, 23, ["Tekla"]),    # Thecla
                                       (1804, 10,  2, ["Ludwik"]),  # Ludwig
                                       (1806, 10,  2, ["Ludwig"]),  # Samma datum
                                       (1811, 10,  2, ["Ludvig"]),  # Samma datum
                                       (1813, 10,  2, ["Ludwig"]),  # Samma datum
                                       (1818, 10,  2, ["Ludvig"]),  # Samma datum
                                       (1870, 10,  2, ["Ludwig"]),  # Samma datum                                       
                                       (1872, 10,  2, ["Ludvig"]),  # Samma datum
                                       (1876, 10,  3, ["Evald"]),   # Ewald
                                       (1812, 10,  4, ["Frans"]),   # Franciscus
                                       (1876, 10, 12, ["Valfrid"]), # Walfrid
                                       (1865, 10, 17, ["Antoinetta"]),
                                       (1877, 10, 20, ["Kasper"]),   # Casper
                                       (1812, 10, 22, ["Severus"]), #
                                       (1813, 10, 22, ["Sewerus"]), #
                                       (1818, 10, 22, ["Severus"]), #
                                       (1837, 10, 22, ["Sewerus"]), # (3)
                                       (1855, 10, 22, ["Severus"]), # (5) Därefter lite olika hos olika utgivare, men w är avtagande.
                                       (1812, 10, 23, ["Severin"]), # Sewerin
                                       (1813, 10, 23, ["Sewerin"]), # 
                                       (1818, 10, 23, ["Severin"]), # 
                                       (1829, 10, 23, ["Sewerin"]), # 
                                       (1872, 10, 23, ["Severin"]), # Lite blandat hos olika utgivare 1840-tal och framåt.
                                       (1812, 10, 24, ["Evergistus"]), # Ewergistus
                                       (1814, 10, 24, ["Ewergistus"]), #
                                       (1818, 10, 24, ["Evergistus"]), #
                                       (1829, 10, 24, ["Ewergistus"]), #
                                       (1872, 10, 24, ["Evergistus"]), #                                       
                                       (1806, 10, 31, ["Qvintinus"]),  #
                                       (1810, 10, 31, ["Qwintinus"]),  #
                                       (1811, 10, 31, ["Qvintinus"]),  #                                       
                                       (1828, 11,  5, ["Eugene"]),   # 
                                       (1874, 11,  5, ["Eugen"]),   # (4) # Samma datum igen
                                       (1837, 11,  6, ["Gustaf Adolf"]), # (3) Gustaf Adolph
                                       (1877, 11,  8, ["Villehad"]),   # Willehad
                                       (1837, 11, 10, ["Mårthen Luther"]), # (3) (lite osäkert, 1821 o 1829 förk. "Mårt. Luther")
                                       (1872, 11, 10, ["Mårten Luther"]),  # # Samma datum igen.
                                       (1837, 11, 11, ["Mårthen biskop"]), # (3) (lite osäkert, 1821 o 1829 förk. "Mårt. biskop")
                                       (1872, 11, 11, ["Mårten biskop"]),  # Samma datum igen.
                                       (1877, 11, 12, ["Kondrad"]),  # Conrad
                                       (1877, 11, 19, ["Elisabet"]), # Elisabeth
                                       (1812, 12,  1, ["Oscar"]),
                                       (1877, 12,  7, ["Agaton"]), # Agathon
                                       (1801, 12,  8, ["Marie aflelse"]), # Ersätter Mariæ (?) aflelse (?)
                                       (1801, 12, 10, ["Judith"]), # Judit
                                       (1877, 12, 10, ["Judit"]),  # Judith.
                                       (1803, 12, 24, ["Adam, Eva"]), #  Ersätter Adam, Ewa
                                       (1801, 12, 27, ["Johannes Evangelistus"]), # Ersätter Johannes Ewangelistus
                                       (1818, 12, 30, ["David"]), # Dawid
                                       (1874, 12, 31, ["Sylvester"])
])
            # (2) Denna stavning tog över år 1820 eller 1821.
            # (3) Denna stavning tog över mellan 1829 och 1845 (vi säger 1837)
            # (4) Denna stavning tog över åren 1874 eller 1875.
            # (5) Denna stavning tog över efter 1845 men senast 1865 (vi säger 1855).


	# Månfaser
	self.place_moonphases()

    # Hämta dag givet m, d
    def get_md(self, m, d):
	jd = JD(self.year, m, d)
	return self.days[jd - self.jd_jan1]

    # Hämta dag givet jd
    def get_jd(self, jd):
	(y, m, d) = jd.GetYMD()
	assert y == self.year
	return self.days[jd - self.jd_jan1]

    # Lägg till information för m, d
    def add_info_md(self, m, d, dayclass, flag, name):
	dc = self.get_md(m, d)
	dc.add_info(dayclass, flag, name)

    # Lägg till information för jd
    def add_info_jd(self, jd, dayclass, flag, name):
	dc = self.get_jd(jd)
	dc.add_info(dayclass, flag, name)

    # Generator för årets alla dagar
    def generate(self):
	for dc in self.days:
	    yield dc

    # Placera namn
    def place_names(self):
	"""Place holidays etc. in the calendar."""

	# Fasta helgdagar och flaggdagar

	for (from_year, to_year, m, d, dayclass, flag, name) in \
		[
	    # Fasta helgdagar
	    (None, 1938,  1,  1, MRED , False,  "Nyårsdagen"),
	    (1939, None,  1,  1, MRED , True,  "Nyårsdagen"),
	    (None, None,  1,  6, MRED,  False, "Trettondedag jul"),
	    (1939, None,  5,  1, MRED,  True,  "Första maj"), # 1939 blev 1 maj allmän helgdag.
	    (None, 1938, 12, 25, MRED,  False,  "Juldagen"),
	    (1939, None, 12, 25, MRED,  True,  "Juldagen"),
	    (None, 1923, 12, 26, MRED,  False, "Annandag jul"), # 1921 står denna form. 1925 har de med Stefanus med.
	    (1924, 1982, 12, 26, MRED,  False, "Den helige Stefanus' dag eller Annandag jul"), # Formen fanns kvar 1977, men ej 1983 måste undersökas mera.
	    (1983, None, 12, 26, MRED,  False, "Annandag jul"),
	    
	    # Fasta helgdagsaftnar
	    (None, None,  1,  5, MBLACK, False, "Trettondedagsafton"),
	    (None, None,  4, 30, MBLACK, False, "Valborgsmässoafton"),
	    (None, None, 12, 24, MBLACK, False, "Julafton"),
	    (None, None, 12, 31, MBLACK, False, "Nyårsafton"),
	    
	    # Dagar som vissa år varit "namnsdagar", andra inte
	    (1993, 2000,  2,  2, BLACK, False, "Kyndelsmässodagen"),  # Saknas som namnsdag dessa år
	    (1993, 2000,  3, 25, BLACK, False, "Marie Bebådelsedag"), # Saknas som namnsdag dessa år
	    (1993, 2000, 11,  1, BLACK, False, "Allhelgonadagen"),    # Saknas som namnsdag dessa år
	    
	    # Svenska flaggans dag och nationaldagen
	    (1939, 1981,  6,  6, MBLACK, True,  "Svenska flaggans dag"),
	    (1982, 2004,  6,  6, MBLACK, True,  "Sveriges nationaldag"),
	    (2005, None,  6,  6, MRED,   True,  "Sveriges nationaldag"),
	    
	    # Andra flaggdagar
	    (1982, None, 10, 24, BLACK, True,  "FN-dagen"), # Infördes i SFS1982:270 den 29 april 1982.
            (1939, None, 11,  6, BLACK, True,  "Gustav Adolfsdagen"), # Gustav Adolfsdagen
	    (1939, None, 12, 10, BLACK, True,  "Nobeldagen"),
	    (2018, None,  5, 29, BLACK, True, "Veterandagen"),
	    (2018, 2018,  12, 17, BLACK, True, "Minnesdag för demokratins genombrott"), # Tillfällig flaggdag 2018, enligt 2017/18:KU28

	    # Flaggdagar för regerande kungahuset
	    
	    # Victoria Ingrid Alice Désirée, kronprinsessa
	    # född 1977-07-14
	    # FIXME: Hon lär inte ha varit kronprinsessa innan successionsordningen
	    # ändrades, väl? SFS 1979:935
	    (1980, None,  7, 14, BLACK, True,  "Kronprinsessans födelsedag"), # födelsedag
	    (1980, None,  3, 12, BLACK, True,  "Kronprinsessans namnsdag"), # namnsdag "Viktoria"

	    # Silvia Renate Sommerlath
	    # född 1943-12-23, drottning 1976-06-19
	    (1976, None, 12, 23, BLACK, True,  "Drottningens födelsedag"), # födelsedag
	    (1976, None,  8,  8, BLACK, True,  "Drottningens namnsdag"), # namnsdag "Silvia"
	    
	    # Carl XVI Gustaf Folke Hubertus
	    # född 1946-04-30, kronprins 1950-10-29, kung 1973-09-15
	    (1951, 1972,  4, 30, BLACK, True,  "Kronprinsens födelsedag"), # födelsedag
	    (1973, None,  4, 30, BLACK, True,  "Konungens födelsedag"), # födelsedag
	    (1951, 1972,  1, 28, BLACK, True,  "Kronprinsens namnsdag"), # namnsdag "Karl"
	    (1973, None,  1, 28, BLACK, True,  "Konungens namnsdag"), # namnsdag "Karl"
	    
	    # Louise Alexandra Maria Irène
	    # född 1889-07-13, gift 1923-11-03, drottning 1950-10-29, död 1965-03-07
	    # FIXME: Första almanackan med flaggdagar utsatta 1939, sätter
	    # det som start. Flaggdag som kronprinsessa innan hon blev drottning.
	    (1939, 1950,  7, 13, BLACK, True,  "Kronprinsessans födelsedag"), # födelsedag
            (1951, 1964,  7, 13, BLACK, True,  "Drottningens födelsedag"), # födelsedag
	    (1939, 1950,  8, 25, BLACK, True,  "Kronprinsessans namnsdag"), # namnsdag "Lovisa"
            (1951, 1964,  8, 25, BLACK, True,  "Drottningens namnsdag"), # namnsdag "Lovisa"

	    # Oscar Fredrik Wilhelm Olaf Gustav VI Adolf
	    # född 1882-11-11, kung 1950-10-29, död 1973-09-15
	    # FIXME: Första almanackan med flaggdagar utsatta 1939, sätter
	    # det som start. Flaggdag som kronprins innan han blev kung.
	    (1939, 1949, 11, 11, BLACK, True,  "Kronprinsens födelsedag"), # födelsedag
            (1950, 1972, 11, 11, BLACK, True,  "Konungens födelsedag"), # födelsedag
	    (1939, 1950,  6,  6, BLACK, True,  "Konungens och kronprinsens namnsdag"), # namnsdag "Gustav". Ser styltigt upp att ha dem separat.
	    (1951, 1973,  6,  6, BLACK, True,  "Konungens namnsdag"), # namnsdag "Gustav"
	    
	    # Oscar Gustaf V Adolf
	    # född 1858-06-16, kung 1907-12-08, död 1950-10-29
	    # FIXME: Första almanackan med flaggdagar utsatta 1939, sätter
	    # det som start. Flaggdag som kronprins innan han blev kung?
	    (1939, 1950,  6, 16, BLACK, True,  "Kronprinsens födelsedag"), # födelsedag

	     ]:
	    if from_year is not None and self.year < from_year: continue
	    if to_year is not None and self.year > to_year: continue
	    self.add_info_md(m, d, dayclass, flag, name)

	# Dag för val till riksdagen är flaggdag från 29 april 1982.
        # Tredje söndagen i september vart tredje år från och med 1982 till 1994.
	if 1982 <= self.year <= 1991 and self.year % 3 == 2:
	    vd = first_sunday(self.year, 9, 15)
	    self.add_info_jd(vd, BLACK, True, "Val till riksdagen")
	# Tredje söndagen i september, vart fjärde år 1994-2013
	elif 1994 <= self.year < 2013 and self.year % 4 == 2:
	    vd = first_sunday(self.year, 9, 15)
	    self.add_info_jd(vd, BLACK, True, "Val till riksdagen")
	# Andra söndagen i september, vart fjärde år 2013-
	elif 2013 <= self.year and self.year % 4 == 2:
	    vd = first_sunday(self.year, 9, 8)
	    self.add_info_jd(vd, BLACK, True, "Val till riksdagen")

	# Skottdagen inföll den 24/2 -1996, infaller den 29/2 2000-
	if self.leap_year:
	    if self.year >= 2000:
		self.add_info_md(2, 29, BLACK, False, "Skottdagen")
	    else:
		self.add_info_md(2, 24, BLACK, False, "Skottdagen")
            if self.year == 1712:
                self.add_info_md(2, 30, BLACK, False, "Tillökad")

	# Påsksöndagen ligger till grund för de flesta kyrkliga helgdagarna
	# under året, så den behöver vi räkna ut redan här
	pd = easter_sunday(self.year)

	# Söndagen efter nyår
	sen = first_sunday(self.year, 1, 2) # Första söndagen 2/1-
	if sen < JD(self.year, 1 ,6):  # Slås ut av 13dagen och 1 e 13dagen
	    self.add_info_jd(sen, MRED, False, "Söndagen e nyår")

	# Kyndelsmässodagen (Jungfru Marie Kyrkogångsdag)
	jmk = first_sunday(self.year, 2, 2)
	if jmk == pd - 49 and self.year != 1845:
	    # Kyndelsmässodagen på fastlagssöndagen => Kyndelsmässodagen flyttas -1v
	    jmk = jmk -7
	# Vänta med att lägga dit namnet...

	# Söndagar efter Trettondedagen
	set = first_sunday(self.year, 1, 7)
	for i in range(1,7):
	    # Slås ut av Kyndelsmässodagen (efter 1983) och allt påskaktigt
	    if (set != jmk or self.year <= 1983) and set < pd-63:
		self.add_info_jd(set, RED, False, "%d e trettondedagen" % i)
	    set = set + 7

	# Jungfru Marie Bebådelsedag
	if self.year < 1953:
	    # Före reformen 25 mars
	    jmb = JD(self.year, 3, 25)
	else:
	    # Efter reformen den närmaste söndagen (vilket är 22-28 mars)
	    jmb = first_sunday(self.year, 3, 22)

	# Men: om Jungfru Marie Bebådelsedag hamnar på påskdagen eller
	# palmsöndagen, så flyttas den till söndagen innan
	# palmsöndagen (5 i fastan).
	if jmb >= pd - 7 and jmb <= pd:
	    jmb = pd - 14
	# Vänta med att lägga dit namnet...

	# Vissa dagar ska "slå ut" vanliga "N efter trefaldighet"
	# Håll reda på dem i en lista i den takt de räknas fram
	se3_stoppers = []	# Vissa dagar ska "slå ut" vanliga "N efter trefaldighet"

	# Vissa dagar ska "slå ut" vanliga "N efter påsk" och "N i fastan"
	# Håll reda på dem i en lista i den takt de räknas fram
	sep_stoppers = []

        #Bönsöndagar, beslutades ofta år för år. Ofta fyra bönsöndagar varje år. 
        forsta_bondagen = {
            1800:(3,8),
            1801:(3,7),
            1802:(3,6),
            1803:(3,5),
            1804:(3,3),
            1805:(3,2),
            1806:(3,1),
            1807:(3,7),
            1808:(3,6),
            1809:(3,5),
            1810:(3,11),
            1811:(3,3),
            1812:(3,1),
            1813:(3,7),
            1814:(3,6),
            1815:(3,12),
            1816:(3,3),
            1817:(3,2),
            1818:(3,8),
            1819:(3,7),
            1820:(3,5),
            1821:(3,11),
            1822:(3,3),
            1823:(3,9),
            1824:(3,7),
            1825:(3,6),
            1826:(3,12),
            1827:(3,11),
            1828:(3,2),
            1829:(3,8),
            1830:(3,7),
            1831:(3,6),
            1832:(3,11),
            1833:(3,3),
            1834:(3,2),
            1835:(3,8),
            1836:(3,6),
            1837:(3,12),
            1838:(3,11),
            1839:(3,10),
            1840:(3,8),
            1841:(3,7),
            1842:(3,6),
            1843:(3,5),
            1844:(3,3),
            1845:(3,2),
            1846:(3,8),
            1847:(3,7),
            1848:(3,12),
            1849:(3,4),
            1850:(3,3),
            1851:(3,9),
            1852:(3,8),
            1853:(3,6),
            1854:(3,5),
            1855:(3,4),
            1856:(3,2),
            1857:(3,8),
            1858:(3,7),
            1859:(3,13),
            1860:(3,4),
            1861:(3,3),
            1862:(3,9),
            1863:(3,1),
            1864:(3,6),
            1865:(3,5),
            1866:(3,4),
            1867:(3,10),
            1868:(3,8),
            1869:(3,7),
            1870:(3,6),
            1871:(3,5),
            1872:(3,3),
            1873:(3,2),
            1874:(3,1),
            1875:(3,7),
            1876:(3,5),
            1877:(3,4),
            1878:(3,3),
            1879:(3,2),
            1880:(3,1),
            1881:(3,6),
            1882:(3,5),
            1883:(3,4),
            1884:(3,2),
            1885:(3,1),
            1886:(3,14),
            1887:(3,13),
            1888:(3,4),
            1889:(3,10),
            1890:(3,9), # osäker
            1891:(3,15), # osäker
            1892:(3,13),
            1893:(3,12),
            1894:(3,4),
            1895:(3,3),
            1896:(3,1),
            1897:(3,7),
            1898:(3,6),
            1899:(3,5),
            1900:(3,4),
            1901:(3,3),
            1902:(3,2),
            1903:(3,8),
            1904:(3,6),
            1905:(3,12),
            1906:(3,4),
            1907:(3,3),
            1908:(3,8),
            1909:(3,7),
            1910:(3,13),
            1911:(3,12),
            1912:(3,10),
            1913:(3,9),
            1914:(3,15),
            1915:(3,7),
            1916:(3,12),
            1917:(3,11),
            1918:(3,17),
            1919:(3,9),
            1920:(3,14),
            1921:(3,13),
            1922:(3,12),
            1923:(3,11),
            1924:(3,9),
            1925:(3,15),
            1926:(3,14),
            1927:(3,13),
            1928:(3,11),
            1929:(3,17),
            1930:(3,9),
            1931:(3,15),
            1932:(2,21),
            1933:(3,12),
            1934:(3,4),
            1935:(3,10),
            1936:(3,8),
            1937:(2,28),
            1938:(3,6),
            1939:(3,12),
            1940:(2,18),
            1941:(3,16),
            1942:(2,22),
            1943:(2,28),
            1944:(3,5),
            1945:(3,4),
            1946:(3,10),
            1947:(3,9),
            1948:(2,22),
            1949:(3,13),
            1950:(2,26),
            1951:(2,25),
            1952:(3,2),
            1953:(3,1),
            1954:(3,7),
            1955:(3,6),
            1956:(2,19),
            1957:(2,24),
            1958:(2,23),
            1959:(2,22),
            1960:(3,6),
            1961:(3,5),
            1962:(3,11),
            1963:(3,10),
            1964:(3,1),
            1965:(3,14),
            1966:(3,13),
            1967:(2,19),
            1968:(3,17),
            1969:(3,2),
            1970:(3,1),
            1971:(3,7),
            1972:(3,5),
            1973:(3,11),
            1974:(3,17),
            1975:(2,23),
            1976:(3,21),
            1977:(2,27),
            1978:(2,26),
            1979:(3,11),
            1980:(3,9),
            1981:(3,8),
            1982:(3,14),
            1983:(2,27)
        }
        andra_bondagen = {
            1800:(4,26),
            1801:(4,18),
            1802:(4,3),
            1803:(4,23),
            1804:(4,22),
            1805:(5,5),
            1806:(4,20),
            1807:(4,19),
            1808:(5,8),
            1809:(4,30),
            1810:(4,29),
            1811:(4,21),
            1812:(4,26),
            1813:(5,9),
            1814:(5,8),
            1815:(4,23),
            1816:(4,21),
            1817:(4,20),
            1818:(4,19),
            1819:(5,9),
            1820:(4,30),
            1821:(4,29),
            1822:(4,28),
            1823:(4,27),
            1824:(5,9),
            1825:(5,8),
            1826:(4,23),
            1827:(4,29),
            1828:(4,27),
            1829:(5,10),
            1830:(5,9),
            1831:(5,8),
            1832:(4,29),
            1833:(4,28),
            1834:(4,27),
            1835:(5,10),
            1836:(5,15),
            1837:(5,7),
            1838:(5,6),
            1839:(5,12),
            1840:(5,10),
            1841:(5,9),
            1842:(5,8),
            1843:(5,7),
            1844:(5,5),
            1845:(5,4),
            1846:(5,10),
            1847:(5,2),
            1848:(5,7),
            1849:(5,6),
            1850:(4,28),
            1851:(5,11),
            1852:(5,9),
            1853:(5,8),
            1854:(5,7),
            1855:(5,6),
            1856:(5,4),
            1857:(5,10),
            1858:(4,25),
            1859:(5,8),
            1860:(5,6),
            1861:(5,12),
            1862:(5,4),
            1863:(4,26),
            1864:(5,8),
            1865:(5,7),
            1866:(4,29),
            1867:(5,5),
            1868:(5,10),
            1869:(5,9),
            1870:(5,8),
            1871:(5,7),
            1872:(4,28),
            1873:(5,4),
            1874:(5,3),
            1875:(5,9),
            1876:(5,7),
            1877:(5,13),
            1878:(5,12),
            1879:(5,4),
            1880:(5,9),
            1881:(5,8),
            1882:(5,7),
            1883:(5,6),
            1884:(5,4),
            1885:(4,26),
            1886:(5,2),
            1887:(5,8),
            1888:(5,13),
            1889:(5,12),
            1890:(4,27),
            1891:(5,3), #? osäker
            1892:(5,8),
            1893:(4,30),
            1894:(4,22),
            1895:(4,28),
            1896:(4,26),
            1897:(5,2),
            1898:(5,8),
            1899:(5,14),
            1900:(5,6),
            1901:(5,5),
            1902:(5,11),
            1903:(5,3),
            1904:(5,15),
            1905:(5,14),
            1906:(5,13),
            1907:(5,12),
            1908:(5,10),
            1909:(5,9),
            1910:(5,8),
            1911:(5,14),
            1912:(5,19),
            1913:(5,25),
            1914:(5,10),
            1915:(5,16),
            1916:(5,14),
            1917:(5,20),
            1918:(5,12),
            1919:(5,11),
            1920:(5,9),
            1921:(5,8),
            1922:(5,14),
            1923:(5,13),
            1924:(5,11),
            1925:(5,10),
            1926:(5,16),
            1927:(5,15),
            1928:(5,13),
            1929:(5,12),
            1930:(5,11),
            1931:(5,10),
            1932:(5,8),
            1933:(5,14),
            1934:(5,13),
            1935:(5,5),
            1936:(5,3),
            1937:(5,9),
            1938:(5,8),
            1939:(5,21),
            1940:(4,21),
            1941:(5,11),
            1942:(4,26),
            1943:(5,2),
            1944:(5,21),
            1945:(5,13),
            1946:(5,12),
            1947:(5,4),
            1948:(4,18),
            1949:(5,15),
            1950:(5,7),
            1951:(5,6),
            1952:(5,4),
            1953:(5,17),
            1954:(5,16),
            1955:(5,8),
            1956:(5,13),
            1957:(5,12),
            1958:(5,4),
            1959:(5,10),
            1960:(5,15),
            1961:(5,14),
            1962:(5,13),
            1963:(5,5),
            1964:(5,10),
            1965:(5,16),
            1966:(5,22),
            1967:(4,23),
            1968:(5,5),
            1969:(5,4),
            1970:(5,10),
            1971:(5,9),
            1972:(5,14),
            1973:(5,13),
            1974:(5,5),
            1975:(4,27),
            1976:(5,2),
            1977:(5,8),
            1978:(5,7),
            1979:(5,6),
            1980:(5,18),
            1981:(5,3),
            1982:(5,9),
            1983:(4,24)
        }
        tredje_bondagen = {
            1800:(6,14),
            1801:(6,13),
            1802:(5,8),
            1803:(6,11),
            1804:(6,3),
            1805:(6,30),
            1806:(6,15),
            1807:(6,21),
            1808:(6,26),
            1809:(6,18),
            1810:(7,1),
            1811:(6,16),
            1812:(6,21),
            1813:(6,20),
            1814:(6,26),
            1815:(6,18),
            1816:(6,16),
            1817:(6,15),
            1818:(6,21),
            1819:(6,27),
            1820:(6,18),
            1821:(7,1),
            1822:(6,16),
            1823:(6,22),
            1824:(6,20),
            1825:(6,26),
            1826:(6,18),
            1827:(6,17),
            1828:(6,15),
            1829:(6,21),
            1830:(6,27),
            1831:(6,26),
            1832:(7,1),
            1833:(6,16),
            1834:(6,15),
            1835:(6,21),
            1836:(7,3),
            1837:(7,2),
            1838:(7,1),
            1839:(7,7),
            1840:(7,5),
            1841:(6,27),
            1842:(7,3),
            1843:(7,2),
            1844:(7,7),
            1845:(7,6),
            1846:(7,5),
            1847:(6,27),
            1848:(7,2),
            1849:(7,8),
            1850:(7,7),
            1851:(7,6),
            1852:(6,27),
            1853:(7,3),
            1854:(7,2),
            1855:(7,1),
            1856:(7,6),
            1857:(7,12),
            1858:(7,11),
            1859:(7,10),
            1860:(7,8),
            1861:(7,7),
            1862:(7,6),
            1863:(7,12),
            1864:(7,10),
            1865:(7,9),
            1866:(7,8),
            1867:(7,7),
            1868:(7,5),
            1869:(7,4),
            1870:(7,10),
            1871:(7,2),
            1872:(7,7),
            1873:(7,6),
            1874:(7,12),
            1875:(7,11),
            1876:(7,16),
            1877:(7,15),
            1878:(7,14),
            1879:(7,13),
            1880:(7,11),
            1881:(7,17),
            1882:(7,16),
            1883:(7,15),
            1884:(7,20),
            1885:(7,19),
            1886:(7,18),
            1887:(7,27),
            1888:(7,15),
            1889:(7,21),
            1890:(7,20),
            1891:(7,17), #? fel? Fredag!
            1892:(7,17), 
            1893:(7,23),
            1894:(7,22),
            1895:(7,21),
            1896:(7,19),
            1897:(7,18),
            1898:(7,17),
            1899:(7,23),
            1900:(7,22),
            1901:(7,21),
            1902:(7,13),
            1903:(7,5),
            1904:(7,10),
            1905:(7,2),
            1906:(7,8),
            1907:(7,7),
            1908:(7,12),
            1909:(7,11),
            1910:(7,3),
            1911:(7,9),
            1912:(7,14),
            1913:(7,13),
            1914:(7,12),
            1915:(7,4),
            1916:(7,9),
            1917:(7,15),
            1918:(7,14),
            1919:(7,13),
            1920:(7,11),
            1921:(7,10),
            1922:(7,9),
            1923:(7,15),
            1924:(7,13),
            1925:(7,12),
            1926:(7,11),
            1927:(7,10),
            1928:(7,15),
            1929:(7,14),
            1930:(7,13),
            1931:(7,12),
            1932:(7,17),
            1933:(7,9),
            1934:(7,8),
            1935:(7,7),
            1936:(7,12),
            1937:(7,4),
            1938:(7,10),
            1939:(7,30),
            1940:(7,14),
            1941:(7,13),
            1942:(7,12),
            1943:(7,11),
            1944:(7,9),
            1945:(7,8),
            1946:(7,14),
            1947:(7,13),
            1948:(7,4),
            1949:(7,10),
            1950:(7,9),
            1951:(7,15),
            1952:(7,13),
            1953:(7,12),
            1954:(7,11),
            1955:(7,10),
            1956:(7,8),
            1957:(7,7),
            1958:(7,13),
            1959:(6,28),
            1960:(7,10),
            1961:(7,2),
            1962:(7,8),
            1963:(7,14),
            1964:(7,5),
            1965:(7,11),
            1966:(7,10),
            1967:(7,2),
            1968:(6,30),
            1969:(6,29),
            1970:(6,28),
            1971:(7,4),
            1972:(7,2),
            1973:(7,1),
            1974:(6,30),
            1975:(6,29),
            1976:(7,4),
            1977:(7,3),
            1978:(7,2),
            1979:(7,1),
            1980:(7,6),
            1981:(7,12),
            1982:(7,18),
            1983:(7,3)
        }
        fjarde_bondagen = {
            1800:(10,11),
            1801:(10,10),
            1802:(10,9),
            1803:(10,22),
            1804:(10,13),
            1805:(10,19),
            1806:(10,18),
            1807:(10,17),
            1808:(10,23),
            1809:(10,22),
            1810:(10,21),
            1811:(10,20),
            1812:(10,18),
            1813:(10,17),
            1814:(10,16),
            1815:(10,22),
            1816:(10,13),
            1817:(10,19),
            1818:(10,18),
            1819:(10,24),
            1820:(10,22),
            1821:(10,21),
            1822:(10,20),
            1823:(10,19),
            1824:(10,17),
            1825:(10,16),
            1826:(10,22),
            1827:(10,14),
            1828:(10,12),
            1829:(10,18),
            1830:(10,24),
            1831:(10,16),
            1832:(10,21),
            1833:(10,20),
            1834:(10,19),
            1835:(10,18),
            1836:(10,16),
            1837:(10,15),
            1838:(10,14),
            1839:(10,13),
            1840:(10,11),
            1841:(10,10),
            1842:(10,9),
            1843:(10,8),
            1844:(10,5),
            1845:(10,12),
            1846:(10,11),
            1847:(10,10),
            1848:(10,8),
            1849:(10,7),
            1850:(10,6),
            1851:(10,12),
            1852:(10,10),
            1853:(10,9),
            1854:(10,8),
            1855:(10,7),
            1856:(10,12),
            1857:(10,11),
            1858:(10,10),
            1859:(10,9),
            1860:(10,7),
            1861:(10,6),
            1862:(10,12),
            1863:(10,11),
            1864:(10,9),
            1865:(10,8),
            1866:(10,7),
            1867:(10,6),
            1868:(10,11),
            1869:(10,10),
            1870:(10,9),
            1871:(10,8),
            1872:(10,6),
            1873:(10,12),
            1874:(10,11),
            1875:(10,10),
            1876:(10,8),
            1877:(10,7),
            1878:(10,6),
            1879:(10,12),
            1880:(10,10),
            1881:(10,9),
            1882:(10,15),
            1883:(10,14),
            1884:(10,12),
            1885:(10,11),
            1886:(10,17),
            1887:(10,16),
            1888:(10,14),
            1889:(10,13),
            1890:(10,19),
            1891:(10,16),
            1892:(10,16),
            1893:(10,15),
            1894:(10,14),
            1895:(10,13),
            1896:(10,11),
            1897:(10,10),
            1898:(10,9),
            1899:(10,8),
            1900:(10,7),
            1901:(10,6),
            1902:(10,12),
            1903:(10,11),
            1904:(10,9),
            1905:(10,8),
            1906:(10,7),
            1907:(10,6),
            1908:(10,18),
            1909:(10,17),
            1910:(10,16),
            1911:(10,15),
            1912:(10,13),
            1913:(10,12),
            1914:(10,11),
            1915:(10,10),
            1916:(10,8),
            1917:(10,14),
            1918:(10,13),
            1919:(10,12),
            1920:(10,10),
            1921:(10,9),
            1922:(10,8),
            1923:(10,13),
            1924:(10,12),
            1925:(10,11),
            1926:(10,10),
            1927:(10,9),
            1928:(10,14),
            1929:(10,13),
            1930:(10,12),
            1931:(10,11),
            1932:(10,9),
            1933:(10,8),
            1934:(10,7),
            1935:(10,6),
            1936:(10,11),
            1937:(10,10),
            1938:(10,9),
            1939:(10,15),
            1940:(10,13),
            1941:(10,12),
            1942:(10,18),
            1943:(10,17),
            1944:(10,15),
            1945:(10,14),
            1946:(10,13),
            1947:(10,19),
            1948:(10,17),
            1949:(10,16),
            1950:(10,8),
            1951:(10,7),
            1952:(10,19),
            1953:(10,18),
            1954:(10,10),
            1955:(10,23),
            1956:(10,7),
            1957:(10,6),
            1958:(10,12),
            1959:(10,11),
            1960:(10,9),
            1961:(10,15),
            1962:(10,14),
            1963:(10,13),
            1964:(10,18),
            1965:(10,17),
            1966:(10,9),
            1967:(10,8),
            1968:(10,6),
            1969:(10,12),
            1970:(10,11),
            1971:(10,10),
            1972:(10,8),
            1973:(10,14),
            1974:(10,20),
            1975:(10,12),
            1976:(10,24),
            1977:(10,9),
            1978:(10,22),
            1979:(10,14),
            1980:(10,19),
            1981:(10,11),
            1982:(10,31),
            1983:(10,9)
        }

        if 1800 <= self.year < 1984:
            # Böndagarna bytte form och började "slå ut" andra dagar efter 1942, men senast 1945:
            # 1 böndagen / Botdagen
            bd1=JD(self.year, forsta_bondagen[self.year][0], forsta_bondagen[self.year][1])
            if self.year < 1945:
                self.add_info_jd(bd1, RED, False, "1 böndagen")
            else:
                self.add_info_jd(bd1, RED, False, "Botdagen (1 böndagen)")
                sep_stoppers.append(bd1)

            # 2 böndagen / Reformationsdagen
            bd2=JD(self.year, andra_bondagen[self.year][0], andra_bondagen[self.year][1])
            if self.year < 1945:
                self.add_info_jd(bd2, RED, False, "2 böndagen")
            else:
                self.add_info_jd(bd2, RED, False, "Reformationsdagen (2 böndagen)")
                sep_stoppers.append(bd2)

            # 3 böndagen / Missionsdagen
            bd3=JD(self.year, tredje_bondagen[self.year][0], tredje_bondagen[self.year][1])
            if self.year < 1945:
                self.add_info_jd(bd3, RED, False, "3 böndagen")
            else:
                self.add_info_jd(bd3, RED, False, "Missionsdagen (3 böndagen)") # fast 1983 står det bara "Missionsdagen".
                se3_stoppers.append(bd3)

            # 4 böndagen / Tacksägelsedagen
            bd4=JD(self.year, fjarde_bondagen[self.year][0], fjarde_bondagen[self.year][1])
            if self.year < 1945:
                self.add_info_jd(bd4, RED, False, "4 böndagen")
            else:
                self.add_info_jd(bd4, RED, False, "Tacksägelsedagen (4 böndagen)")
                se3_stoppers.append(bd4) # Böndagarna slår inte ut före 1942 iaf.




	# Fasta, Påsk, Kristi Himmelsfärd, Pingst

	# Dessa dagar slås ut av Kyndelsmässodagen
	# fast bara efter 1983
	# Tidigare så står båda namnen!
	for (jd, name) in [(pd-63, "Septuagesima"),
			   (pd-56, "Sexagesima")]:
	    if jd != jmk or self.year <= 1983:
		self.add_info_jd(jd, RED, False, name)

	# Lägg så dit Kyndelsmässodagen
	if self.year < 1901: # Ändrades mellan 1900 och 1905, troligen 1901.
	    self.add_info_jd(jmk, RED, False, "Marie kyrkogångsdag")
	elif self.year < 1924:
	    self.add_info_jd(jmk, RED, False, "Kyndelsmässosöndagen")
	elif self.year < 1943:
	    self.add_info_jd(jmk, RED, False, "Marie kyrkogångsdag eller Kyndelsmässodagen")
	else:
	    self.add_info_jd(jmk, RED, False, "Jungfru Marie Kyrkogångsdag eller Kyndelsmässodagen")

	# Fastlagssöndagen och icke-helgdagar efter den
	self.add_info_jd(pd-49, RED, False, "Fastlagssöndagen")
	self.add_info_jd(pd-47, BLACK,False, "Fettisdagen")
	self.add_info_jd(pd-46, BLACK,False, "Askonsdagen")

	# Dessa dagar slås ut av Jungfru Marie bebådelsedag,
	# fast bara efter 1983. Böndagar slår också ut detta.
	# 1952-1983 så står båda namnen!

	for (jd, name) in [(pd-42, "1 i fastan"),
			   (pd-35, "2 i fastan"),
			   (pd-28, "3 i fastan"),
			   (pd-21, "Midfastosöndagen"),
			   (pd-14, "5 i fastan")]:
	    if (jd != jmb or self.year <= 1983) and (jd not in sep_stoppers):
		self.add_info_jd(jd, RED, False, name)

	# Lägg så dit Jungfru Marie bebådelsedag
	self.add_info_jd(jmb, RED, False, "Jungfru Marie bebådelsedag")

	self.add_info_jd(pd- 7, RED,    False, "Palmsöndagen")
	self.add_info_jd(pd- 4, BLACK,  False, "Dymmelonsdagen")
	self.add_info_jd(pd- 3, MBLACK, False, "Skärtorsdagen")
	self.add_info_jd(pd- 2, MRED,   False, "Långfredagen")
	self.add_info_jd(pd- 1, MBLACK, False, "Påskafton")
        if self.year > 1938:
            self.add_info_jd(pd+ 0, MRED,   True,  "Påskdagen")
        else:
            self.add_info_jd(pd+ 0, MRED,  False,  "Påskdagen")

	self.add_info_jd(pd+ 1, MRED,   False, "Annandag påsk")
	if self.year < 2004:
            # Kollar så inget av dessa slås ut av en böndag:
            for (jd, name) in [(pd+ 7, "1 e påsk"),
                               (pd+14, "2 e påsk"),
                               (pd+21, "3 e påsk"),
                               (pd+28, "4 e påsk")]:
                if(jd not in sep_stoppers):
                    self.add_info_jd(jd, RED, False, name)

	else:
	    self.add_info_jd(pd+ 7, RED, False, "2 i påsktiden")
	    self.add_info_jd(pd+14, RED, False, "3 i påsktiden")
	    self.add_info_jd(pd+21, RED, False, "4 i påsktiden")
	    self.add_info_jd(pd+28, RED, False, "5 i påsktiden")
	self.add_info_jd(pd+35, RED, False, "Bönsöndagen")
	self.add_info_jd(pd+39, MRED, False, "Kristi himmelsfärds dag")
	if self.year < 2004:
            if pd+42 not in sep_stoppers:
                self.add_info_jd(pd+42, RED, False, "6 e påsk")
	else:
	    self.add_info_jd(pd+42, RED, False, "Söndagen f Pingst")
	self.add_info_jd(pd+48, MBLACK, False, "Pingstafton")
        if self.year > 1938:
            self.add_info_jd(pd+49, MRED, True,  "Pingstdagen")
        else:
            self.add_info_jd(pd+49, MRED, False,  "Pingstdagen")
	if self.year < 2005:
	    self.add_info_jd(pd+50, MRED, False, "Annandag pingst")
	else:
	    self.add_info_jd(pd+50, BLACK,False, "Annandag pingst")
	self.add_info_jd(pd+56, RED,False, "Heliga trefaldighets dag")

	# Midsommardagen
	if self.year < 1953:
	    # Före 1953 inföll midsommardagen alltid på 24/6
	    msd = JD(self.year, 6, 24)
	else:
	    # Från och med 1953 rörlig helgdag, lördag 20-26/6
	    msd = first_saturday(self.year, 6, 20)
        if self.year <1923: # Någon gång mellan 1921 och 1925 ändrades detta.
	    self.add_info_jd(msd+0, MRED,  False,  "Johannes Döparens dag") 
	elif self.year <2004:
  	    self.add_info_jd(msd-1, MBLACK, False, "Midsommarafton")
	    self.add_info_jd(msd+0, MRED,  True,  "Den helige Johannes Döparens dag eller Midsommardagen")
        else:
            self.add_info_jd(msd-1, MBLACK, False, "Midsommarafton")
	    self.add_info_jd(msd+0, MRED,  True,  "Midsommardagen")
	    self.add_info_jd(msd+1, RED,  False,  "Den helige Johannes Döparens dag")
	    se3_stoppers.append(msd+1)

	# Alla Helgons dag
	if self.year < 1953:
	    # NE: "Genom helgdagsreformen 1772 förlades firandet till
	    # första söndagen i november"
	    ahd = first_sunday(self.year, 11, 1)
	    # Vänta med att sätta ut namnet, som inte ska slå ut någon Söndag e Tref.
	else:
	    # NE: "År 1953 flyttades dagen i den svenska almanackan till
	    # den lördag som infaller 31 oktober till 6 november.
	    ahd = first_saturday(self.year, 10, 31)
	    # Vänta med att sätta ut namnet (för fallet ovan, egentligen)
	    if self.year > 1983:
		self.add_info_jd(ahd+1, RED, False, "Söndagen e alla helgons dag")
		se3_stoppers.append(ahd+1)

	# Advent (samt Domssöndagen och Söndagen före domssöndagen)
	adv1=first_sunday(self.year, 11, 27 )
        if self.year >= 1921:
            # Googlar man på "domsöndagen" och 1921 finner man många källor.
            self.add_info_jd(adv1-14, RED,  False, "Söndagen f domssöndagen")
            self.add_info_jd(adv1- 7, RED,  False, "Domssöndagen")
	self.add_info_jd(adv1+ 0, MRED, False, "1 i advent")
	self.add_info_jd(adv1+ 7, MRED, False, "2 i advent")
	self.add_info_jd(adv1+14, MRED, False, "3 i advent")
	self.add_info_jd(adv1+21, MRED, False, "4 i advent")


	# Söndagen e Jul
	sej=first_sunday(self.year, 12, 27)
	if sej <= self.jd_dec31:
	    self.add_info_jd(sej, RED, False, "Söndagen e jul")

	# Den helige Mikaels dag, söndag i tiden 29/9 till 5/10
	hmd = first_sunday(self.year, 9, 29)
        if self.year < 1901: # Denna form fanns kvar 1900, men var borta 1905. Stora ändringar gjordes 1901.
            self.add_info_jd(hmd, RED, False, "Michaelsdagen")
        elif self.year < 1924: # Någon gång efter 1921 men senast 1925 ändrades namnet.
            self.add_info_jd(hmd, RED, False, "Mikaelssöndagen")
        else:
            self.add_info_jd(hmd, RED, False, "Den helige Mikaels dag")
        if self.year > 1981: se3_stoppers.append(hmd) # Åtminstone fram till 1972 visades båda. I kalendrar 1982-1983 visas bara "Mikaels dag".

        if self.year > 1983:
            # Tacksägelsedagen, andra söndagen i oktober
            tsd = first_sunday(self.year, 10, 8)
            self.add_info_jd(tsd, RED, False, "Tacksägelsedagen")
            se3_stoppers.append(tsd)

	# Söndagarna efter Trefaldighet
	se3 = pd+63
	for i in range(1,28):
	    # Ska dagen vara en S e Tr?
	    if self.year >= 1921 and se3 >= adv1 - 14:
		# Inte lönt längre efter S f ds
		break
	    if self.year < 1921 and se3 >= adv1:
		# Inte lönt längre efter 1 adv. Före 1921 fanns inga domsöndagar.
		break
	    # Har dagen redan ett annat namn som har prioritet?
	    if se3 in se3_stoppers:
		se3 += 7
		continue

	    # Särskilda namn för vissa av dagarna
	    if self.year > 1983 and i == 5:
		name = "Apostladagen"
	    elif self.year >= 1923 and i == 7:  # Ändrades mellan 1921 och 1925.
		name = "Kristi förklarings dag"
	    else:
		name = "%d e trefaldighet" % i
	    
	    self.add_info_jd(se3, RED, False, name)
	    se3 += 7

	# Sätt ut A H D
	self.add_info_jd(ahd, MRED, False, "Alla helgons dag")

    def place_name_day_names(self, filename, patches = None):
	for line in open(filename):
	    (ms, ds, ns) = line.strip().split(None,2)
	    m = int(ms)
	    d = int(ds)
	    # Innan år 2000, då skottdagen var 24/2, så flyttades
	    # namnen till senare dagar i februari
	    if self.leap_year and self.year < 2000 and m == 2 and d >= 24: 
		d = d + 1
	    names = ns.split(",")
	    dc = self.get_md(m, d)
	    dc.set_names(names)
	if patches is not None:
	    for (from_year, m, d, names) in patches:
		if self.year >= from_year:
		    dc = self.get_md(m, d)
		    dc.set_names(names)
		    

    # Placera ut månfaserna i almanackan.
    # Algoritm: Meeus, Jean, Astronomical Formulae for Calculators, 2 ed, s 159
    def place_moonphases(self):
	# FIXME:
	# int midcycle,cycle;
	# moon_t phase;
	# int h,m;
	# day_cal *dcal;
	# jd_t jd1jan,jd31dec,jd;

	# Ta reda på en måncykel i mitten av året (ungefär)
	midcycle = int((self.year - 1900) * 12.3685) + 6

	# Arbeta bakåt mot början av året och placera ut månfaserna

	cycle = midcycle
	phase = 0 # Nymåne

	while True:
	    jd = moonphase(cycle, phase)
	    if jd < self.jd_jan1: break
	    
	    dc = self.get_jd(jd)
	    dc.set_moonphase(phase)

	    if phase == 0:
		phase = 3
		cycle = cycle - 1
	    else:
		phase = phase -1 

	# Arbeta framåt mot slutet av året och placera ut månfaserna

	cycle = midcycle
	phase = 0 # Nymåne

	while True:
	    jd = moonphase(cycle, phase)
	    if  jd > self.jd_dec31: break

	    dc = self.get_jd(jd)
	    dc.set_moonphase(phase)

	    if phase == 3:
		phase = 0
		cycle = cycle + 1
	    else:
		phase = phase + 1 

    def dump(self):
	"""Show in text format for debugging."""

	for dc in self.generate():
	    dc.dump()

    def month_cal(self, month):
        return MonthCal(self, month)
	
class MonthCal:
    """Class to represent a month of a year."""

    def __init__(self, yearcal, month):
	self.yc = yearcal
	assert 1<= month <= 12
	self.month = month
        if self.yc.year < 1872:
            self.month_name = month_old_names[self.month]
        else:
            self.month_name = month_names[self.month]

	self.num_days = [None, 31, 28, 31, 30, 31, 30,
			 31, 31, 30, 31, 30, 31][self.month]
	if self.yc.leap_year and self.month == 2:
	     self.num_days = 29
             
        if self.yc.year == 1753 and self.month == 2:
             self.num_days = 17

        if self.yc.year == 1712 and self.month == 2:
             self.num_days = 30

                 

    def generate(self):
	for d in range(1,self.num_days+1):
	    dc = self.yc.get_md(self.month, d)
	    yield dc

    def title(self):
        return '%s %s' % (self.month_name, self.yc.year)

    def html_vertical(self, f, for_printing = False):
	# Tabellen med dagarna
	f.write('<TABLE CLASS="vtable">')
	for dc in self.generate():
	    dc.html_vertical(f, for_printing = for_printing)
	f.write('<TR CLASS="v"><TD CLASS="vlast" COLSPAN="5">&nbsp;</TD></TR>')
	f.write('</TABLE>')

    def html_tabular_high(self, f, for_printing = False):
        self.html_tabular(f, for_printing = for_printing, high = True)

    def html_tabular(self, f, for_printing = False, high = False):
	# Tabellen
	f.write('<TABLE CLASS="ttable">')

	# Rubrikrad med veckodagarna
	f.write('<TR CLASS="twd">')
	if self.yc.year >= 1973:
	    days = wday_names[1:]
	else:
	    days = wday_names[7:] + wday_names[1:7]
	f.write('<TD CLASS="twno_empty">&nbsp;</TD>')
	for day in days:
	    f.write('<TD CLASS="twday">%s</TD>' % day)
	f.write('</TR>')
	
	for dc in self.generate():
	    # Börja ny rad på första dagen i månaden eller veckan
	    if dc.d == 1 or dc.wpos == 1:
		f.write('<TR CLASS="tw">')
		# Veckonummer relevant fr o m 1973
		if dc.y >= 1973:
		    wtext = '<A CLASS="hidelink" HREF="?year=%d&week=%d&type=week">%d</A>' % (dc.wyear,
                                                                                              dc.week,
                                                                                              dc.week)
		else:
		    wtext = "&nbsp;"
		f.write('<TD CLASS="twno">%s</TD>' %wtext)

	    # Fyll ut med tomdagar om det behövs i början
	    if dc.d == 1:
		for i in range(1, dc.wpos):
		    f.write('<TD CLASS="tday_empty">&nbsp;</TD>')

	    # Själva dagen
	    dc.html_tabular(f, for_printing = for_printing, high = high)

	    # Fyll ut med tomdagar om det behövs på slutet
	    if dc.d == self.num_days:
		for i in range(dc.wpos, 7):
		    f.write('<TD CLASS="tday_empty">&nbsp;</TD>')

	    # Avsluta sist i veckan och månaden
	    if dc.d == self.num_days or dc.wpos == 7:
		f.write('</TR>')

	f.write('</TABLE>')

class WeekCal:
    """Class to represent a week."""

    def __init__(self, week_year, week_no):
	assert 1<= week_no <= 53
        self.week_year = week_year
        self.week_no = week_no
        self.year_cals = {} # We may need more than one year!
        self.days = []

        for wd in range(1, 7+1):
            jd = jddate.FromYWD(self.week_year, self.week_no, wd)
            y, m, d = jd.GetYMD()
            if not y in self.year_cals:
                self.year_cals[y] = YearCal(y)
            self.days.append(self.year_cals[y].get_md(m, d))

    def title(self):
        return 'Vecka %d, %s' % (self.week_no, self.week_year)

    def html_vertical(self, f, for_printing = False):
	# Tabellen med dagarna
	f.write('<TABLE CLASS="vtable">')
	for dc in self.days:
	    dc.html_vertical(f, in_week_cal = True, for_printing = for_printing)
	f.write('<TR CLASS="v"><TD CLASS="vlast" COLSPAN="6">&nbsp;</TD></TR>')
	f.write('</TABLE>')



#
# Invocation
#

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
	year = int(sys.argv[1])
	yc = YearCal(year)
	yc.dump()
    else:
	for year in range(1901,2006):
	    yc = YearCal(year)
	    yc.dump()
