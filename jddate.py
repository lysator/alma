# -*- encoding: iso-8859-1 -*-
# Date class for Python
# Copyright 1997, 1998, 2000, 2004 Kent Engström.

# Released under the GNU GPL.

import time
import string
import re


# Convert JD -> YMD

def jd_to_ymd(jd):
    if jd >= 2361390: return jd_to_ymd_gregorian(jd)
    elif jd>2342041 and jd<2346426: return jd_to_ymd_swedish(jd)
    else: return jd_to_ymd_julian(jd)

# Algorithm from:
# https://en.wikipedia.org/wiki/Julian_day#Calculation
def jd_to_ymd_julian(jd):
    y=4716
    j=1401
    m=2
    n=12
    r=4
    p=1461
    v=3
    u=5
    s=153
    w=2
    B=274277
    C=-38
    # for gregorian, one can use:
    # f=jd + j + (((4*jd + B) // 146097) * 3) // 4 + C
    f = jd + j
    e = r*f+v
    g=e%p//r
    h=u*g+w
    D=(h%s)//u+1
    M=(h//s+m)%n+1
    Y=(e//p)-y+(n+m-M)//n
    
    return(Y,M,D)

def jd_to_ymd_swedish(jd):
    if jd == 2346425:
      ymd=(1712,02,30)
    else:
      ymd = jd_to_ymd_julian(jd+1)
    return ymd
#
# AUXILIARY ROUTINES
#
# Most important algorithms are from:
# Meeus, Jean, Astronomical Formulae for Calculators, 2 ed
#

def jd_to_ymd_gregorian(jd):
    alpha = int((100*jd - 186721625L)/3652425L)
    a = jd + 1 + alpha - alpha/4
    b = a + 1524
    c = int(100*b - 12210)/36525
    d = int((36525L*c)/100)
    e = int((10000L*b-10000L*d)/306001L)
    res_d = b - d - int((306001L*e)/10000L)
    if e<14:
	res_m=e-1
    else:
	res_m=e-13
    if res_m<3:
	res_y=c-4715
    else:
	res_y=c-4716

    return (res_y,res_m,res_d)

# Convert YMD -> JD 

def ymd_to_jd(y,m,d):
    if y>1753 or (y==1753 and m>2) or (y==1753 and m==2 and d>17):
        return ymd_to_jd_gregorian(y,m,d)
    elif (y>1700 or (y==1700 and m>2)) and (y<1712 or (y==1712 and m<3)):
        return ymd_to_jd_swedish(y,m,d)
    else:
        return ymd_to_jd_julian(y,m,d)

# Algorithm from:
# https://en.wikipedia.org/wiki/Julian_day#Calculation
def ymd_to_jd_julian(year,month,day):
    a=(14-month)//12
    y=year+4800-a
    m=month+12*a-3
    return day + (153*m+2)//5+365*y+y//4-32083

def ymd_to_jd_swedish(year,month,day):
    return ymd_to_jd_julian(year,month,day)-1

def ymd_to_jd_gregorian(y,m,d):
    if m<3: y=y-1; m=m+12
    a = y/100;
    return 1720995 + d + 2 - a + (a/4) + (36525*y)/100 + (306001*(m+1))/10000;

# Get weekday from JD (Monday = 1, ..., Sunday = 7)

def jd_to_weekday(jd):
    return jd%7+1

# Convert YMD -> YWD

def ymd_to_ywd(y,m,d):
     jd=ymd_to_jd(y,m,d)
     jd1jan=ymd_to_jd(y,1,1)

     wd1jan=jd_to_weekday(jd1jan)
     if wd1jan<=4:
	 jd1mon=jd1jan+1-wd1jan
     else:
	 jd1mon=jd1jan+8-wd1jan

     if jd<jd1mon:
	 res_y=y-1
	 if jd_to_weekday(ymd_to_jd(y-1,1,1))<=4:
	     res_w=53
	 else:
	     res_w=52
     else:
	 res_y=y
	 res_w=(jd-jd1mon)/7+1
	 if m==12 and d>=29:
	     wd1jannext=jd_to_weekday(ymd_to_jd(y+1,1,1))
	     if wd1jannext<=4 and wd1jannext+d>=33:
		 res_y=y+1
		 res_w=1

     return (res_y,res_w,jd_to_weekday(jd))

# Convert YWD -> JD

def ywd_to_jd(y,w,d):
    jd1jan = ymd_to_jd(y,1,1)
    wd1jan = jd_to_weekday(jd1jan)
    if wd1jan <= 4:
	jd1mon = jd1jan + 1 - wd1jan
    else:
	jd1mon = jd1jan + 8 - wd1jan;

    return jd1mon + w * 7 + d - 8


# Convert YWD -> YMD (internally via JD)

def ywd_to_ymd(y,w,d):
    return jd_to_ymd(ywd_to_jd(y,w,d))


#
# THE DATE CLASS
#

class Date:
    # Initializing and printing

    def __init__(self): # New instances should be invalid!
	self.__valid = 0

    def __repr__(self):
	if self.__valid:
	    return "<Date %04d-%02d-%02d>"%(self.__y, self.__m, self.__d)
	else:
	    return "<Date invalid>"
    
    def __hash__(self):
	if self.__valid:
	    return ymd_to_jd(self.__y, self.__m, self.__d)
	else:
	    return 0

    def IsValid(self):
	return self.__valid

    # Setting the date in different formats

    def SetJD(self, jd): # Julian date
	if type(jd) == type(0):
	    (self.__y, self.__m, self.__d) = jd_to_ymd(jd)
	    self.__valid = 1
	else:
	    self.__valid = 0

    def SetYMD(self, y, m, d): # Year, month, date
	# Controversial issue: how are we to handle two-digit dates?
	# For the moment being, we choose the same approach as in
	# the Fuego module.
	if y >= 0 and y < 80:
	    y = y + 2000
	elif y >= 80 and y < 100:
	    y = y + 1900

	# Check this date by converting to JD and back.
	# This could be done faster but not simpler :-)
	jd = ymd_to_jd(y, m, d)
	(y2, m2, d2) = jd_to_ymd(jd)
	if y == y2 and m == m2 and d == d2:
	    (self.__y, self.__m, self.__d) = (y, m, d)
	    self.__valid = 1
	else:
	    self.__valid = 0
	
    def SetYWD(self, y, w, d): # Year, week, (week)day
	(y2, m2, d2) = ywd_to_ymd(y, w, d)
	self.SetYMD(y2, m2, d2) 
	# Check validity by convering back to YWD
	if self.__valid:
	    (y3, w3, d3) = self.GetYWD()
	    if y3 <> y or w3 <> w or d3 <> d:
		self.__valid = 0

    # Getting (parts of) the date in different formats

    def GetJD(self): # Julian date
	if self.__valid:
	    return ymd_to_jd(self.__y, self.__m, self.__d)
	else:
	    raise ValueError

    def GetYMD(self): # Year, month, date
	if self.__valid:
	    return (self.__y, self.__m, self.__d)
	else:
	    raise ValueError

    def GetYWD(self): # Year, week, (week)day
	if self.__valid:
	    return ymd_to_ywd(self.__y, self.__m, self.__d)
	else:
	    raise ValueError

    # Getting some common string formats

    def GetString_YYYY_MM_DD(self):
	return "%04d-%02d-%02d"%(self.GetYMD())

    def GetString_YYYYMMDD(self):
	return "%04d%02d%02d"%(self.GetYMD())

    def GetString_YY_MM_DD(self):
	(y, m, d) = self.GetYMD()
	return "%02d-%02d-%02d"%(y % 100, m, d)

    def GetString_YYMMDD(self):
	(y, m, d) = self.GetYMD()
	return "%02d%02d%02d"%(y % 100, m, d)

    # Getting some other dates from the current
    
    def GetYearStart(self):
        return FromYMD(self.__y, 1, 1)
    
    def GetYearEnd(self):
        return FromYMD(self.__y + 1, 12, 31)
    
    def GetMonthStart(self):
        return FromYMD(self.__y, self.__m, 1)
    
    def GetMonthEnd(self):
        m = self.__m + 1
        if m > 12:
            m = m - 12 
            y = self.__y + 1
        else:
            y = self.__y
        return FromYMD(y, m, 1) - 1
 
    def GetWeekStart(self):
        # Monday is the first day of the week
        (y, w, d) = self.GetYWD()
        return self - d + 1
    
    def GetWeekEnd(self):
        # Sunday is the last day of the week
        (y, w, d) = self.GetYWD()
        return self + 7 - d
    
   # Adding an integer: step that many days into the future

    def __add__(self, days):
	return FromJD(self.GetJD() + days)

    def __radd__(self, days):
	return FromJD(self.GetJD() + days)

    # Subtracting an integer: step that many days into the past
    # Subtracting two dates: get difference in days

    def __sub__(self, other):
	if type(other) == type(0):
	    return FromJD(self.GetJD() - other)
	else: 
	    return self.GetJD()-other.GetJD()

    # Comparison between two dates: compare the JDs

    def __cmp__(self, other):
	return cmp(self.GetJD(), other.GetJD())

#
# INITIALIZERS FOR THE DATE CLASS
#
# These are the functions you should call to get new instances of
# the Date class

def FromJD(jd):
    newdate = Date()
    newdate.SetJD(jd)
    return newdate

def FromYMD(y, m, d):
    newdate = Date()
    newdate.SetYMD(y, m, d)
    return newdate

def FromYWD(y, w, d):
    newdate = Date()
    newdate.SetYWD(y, w, d)
    return newdate

def FromToday():
    (dy,dm,dd,th,tm,ts,wd,dayno,ds)=time.localtime(time.time())
    return FromYMD(dy,dm,dd)

def FromUnixTime(t):
    (dy,dm,dd,th,tm,ts,wd,dayno,ds)=time.localtime(t)
    return FromYMD(dy,dm,dd)

rx_dashed=re.compile("^([0-9]+)-([0-9]+)-([0-9]+)$")
rx_yyyymmdd=re.compile("^([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])$")
rx_yymmdd=re.compile("^([0-9][0-9])([0-9][0-9])([0-9][0-9])$")
    
def FromString(str):
    newdate = Date() # Allocates an invalid date
    m = rx_dashed.match(str)
    if m:
	newdate.SetYMD(string.atoi(m.group(1)),
		       string.atoi(m.group(2)),
		       string.atoi(m.group(3)))
        return newdate

    m = rx_yyyymmdd.match(str)
    if m:
	newdate.SetYMD(string.atoi(m.group(1)),
		       string.atoi(m.group(2)),
		       string.atoi(m.group(3)))
        return newdate

    m = rx_yymmdd.match(str)
    if m:
	newdate.SetYMD(string.atoi(m.group(1)),
		       string.atoi(m.group(2)),
		       string.atoi(m.group(3)))
        return newdate

    return newdate
