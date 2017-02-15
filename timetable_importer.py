#!/usr/bin/python
# -*- coding: utf-8 -*-
# myUNSW to Google Calendar Timetable Importer
# More or less written by Chris Lam

try:
    from xml.etree import ElementTree  # for Python 2.5 users
except ImportError:
    from elementtree import ElementTree

from BeautifulSoup import BeautifulSoup
import re
import urllib2
import cookielib
import re
import urllib

from datetime import *
import pprint

days = {
    'Mon': 0,
    'Tue': 1,
    'Wed': 2,
    'Thu': 3,
    'Fri': 4,
    }


def export(source):
    f = source.replace('\r', '')

    if 'sectionHeading' not in f:
        return 'Bad timetable source, possibly incorrect login details or myunsw daily dose of downtime (12am-2am or whatever)'

  # parsing shit

    s = BeautifulSoup(f.replace('\n', ''))
    sem = '17s1'
    title = sem + ' Timetable'

    if not re.match(r'\d\ds\d', sem):
        current_time = datetime.datetime.now()
        sem = '%ds%d' % (current_time.year % 100,
                         (1 if current_time.month < 7 else 2))

  # make gcal calendar

    calendar = {'summary': title, 'timeZone': 'Australia/Sydney'}

  # Summer courses have N1 and N2 right after each other

    if s.find(text='N1').findNext('table').findNext('td').text == 'N2':
        week_after_midsem_break = int(s.find(text='N2').findNext('table'
                ).findNext('td').text)
    else:
        week_after_midsem_break = int(s.find(text='N1').findNext('table'
                ).findNext('td').text)

    courses = [x.contents[0] for x in s.findAll('td',
               {'class': 'sectionHeading'})]

    print 'Parsing calendar to make events'

    allEvents = []

    for course in courses:

    # FINGERS CROSSED THAT THE TIMETABLE PAGE NEVER CHANGES

        classes = s.find(text=course).findNext('table').findAll('tr',
                {'class': re.compile('data')})
        (
            ctype,
            code,
            day,
            tim,
            weeks,
            place,
            t,
            ) = ['' for x in xrange(7)]
        for c in classes:
            a = [(x.contents[0] if x.contents else '') for x in
                 c.findAll('td', recursive=False)]
            g = (t for t in a)

            t = g.next()

            if t.strip() != ' ':
                ctype = t

            t = g.next()
            if t.strip() not in days:
                code = t
                day = g.next().strip()
            else:
                day = t.strip()
            tim = g.next()
            weeks = g.next()
            place = g.next()
            t = ' '.join(g.next().findAll(text=True))

            if tim.find(' - ') == -1:
                continue
            (start, end) = tim.split(' - ')

            course = course.split()[0]

            w = []
            for r in weeks.split(','):
                if 'N' in r:
                    print 'Did not process %s %s %s because of non-integer week'
                    continue
                if '-' in r:
                    w += range(int(r.split('-')[0]), int(r.split('-'
                               )[1]) + 1)
                else:
                    w += [int(r)]

            thisEvent = {
                'location': place,
                'day': days[day],
                'time_start': int( datetime.strftime(datetime.strptime(start,
                        '%I:%M%p'), '%H')),
                'time_end': int( datetime.strftime(datetime.strptime(end,
                        '%I:%M%p'), '%H')),
                'event': {
                    'course': course,
                    'type': ctype,
                    'instructor': t.strip(),
                    'code': code,
                    },
                }

            allEvents += [thisEvent]

    pp = pprint.PrettyPrinter(indent=4)
    print pp.pprint(allEvents)
    return allEvents


from tabulate import tabulate
f = open("timetable.htm")
allEvents = export(f.read())

times = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
days = [0, 1, 2, 3, 4]
allEv = []
for hour in times:
    ev = []
    for day in days:
        events_now = []
        for event in allEvents:
            if hour >= event['time_start'] and hour < event['time_end'] and event['day'] == day:
                events_now += [event]
        if(len(events_now)>0):
            ev += [events_now[0]['event']['course']]
        else:
            ev += ['Nothing']
    allEv += [ev]

print tabulate(allEv, tablefmt="fancy_grid")