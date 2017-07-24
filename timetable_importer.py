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
                if(ctype[0] == '&'):
                    ctype = allEvents[-1]['event']['type']

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

    #   allEvents += [{
    #       'location': "Civil Eng. 102",
    #       'day': 0,
    #       'time_start':13,
    #       'time_end':14,
    #       'event':  {
    #           'course': 'COMP3231',
    #           'type': 'Tutoring'
    #           }
    #       }]

    #   allEvents += [{
    #       'location': "Civil Eng. 102",
    #       'day': 1,
    #       'time_start':14,
    #       'time_end':15,
    #       'event':  {
    #           'course': 'COMP3231',
    #           'type': 'Tutoring'
    #           }
    #       }]

    pp = pprint.PrettyPrinter(indent=4)
    #print pp.pprint(allEvents)
    return allEvents


from tabulate import tabulate
import time
f = open("/home/seb/dev/timetable_tools/timetable.htm")
allEvents = export(f.read())

current_hour = int(time.strftime("%H"))
current_day = datetime.today().weekday()

times = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
days = [0, 1, 2, 3, 4]
allEv = []
for hour in times:
    prettyHour = (str(hour)+":00") if hour <= 12 else (str(hour-12)+":00")
    if hour == current_hour:
        prettyHour = "\033[1;31m" + prettyHour +"\033[0;0m"
    ev = [prettyHour]
    for day in days:
        events_now = []
        for event in allEvents:
            if hour >= event['time_start'] and hour < event['time_end'] and event['day'] == day:
                events_now += [event]
        evStart = ""
        evEnd = ""
        if current_hour == hour:
            evStart = "\033[1;34m"
            evEnd = "\033[0;0m"
        if current_day == day:
            evStart = "\033[1;34m"
            evEnd = "\033[0;0m"
        if day == current_day and current_hour == hour:
            evStart = "\033[1;31m"
            evEnd = "\033[0;0m"
        evStr = evStart
        if(len(events_now)>0):
            evStr += events_now[0]['event']['course']
            evStr += " <" + events_now[0]['event']['type'][:3] + ">"
            #evStr += events_now[0]['location']
        else:
            evStr += '[     :)     ]'
        evStr += evEnd
        ev += [evStr]
    allEv += [ev]

header_days=["TIME", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
header_days[current_day+1] = "\033[1;31m" + header_days[current_day+1] + "\033[0;0m"

print tabulate(allEv, headers=header_days, tablefmt="fancy_grid")

currentEvent = [event for event in allEvents if
        event['day'] == current_day and current_hour >= event['time_start']
        and current_hour < event['time_end']]

if len(currentEvent) > 0:
    e = currentEvent[0]
    hour = e['time_start']
    prettyHour = (str(hour)+":00") if hour <= 12 else (str(hour-12)+":00")
    print "NOW:\n  " + prettyHour + ' - ' + e['event']['course'] + ' at ' + e['location'] + " (" + str(e['time_end']-e['time_start']) + " hour " + e['event']['type'] + ")"

goodEvents = [event for event in allEvents if
        event['day'] == current_day and event['time_start'] > current_hour]

goodEvents = sorted(goodEvents,key=lambda e:e['time_start'])

if len(goodEvents) > 0:
    print "COMING UP:"

for e in goodEvents:
    hour = e['time_start']
    prettyHour = (str(hour)+":00") if hour <= 12 else (str(hour-12)+":00")
    print "  " + prettyHour + ' - ' + e['event']['course'] + ' at ' + e['location'] + " (" + str(e['time_end']-e['time_start']) + " hour " + e['event']['type'] + ")"
