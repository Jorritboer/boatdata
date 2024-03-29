import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from meteostat import Point, Daily

# boat_type ids associated with boats
BOAT_IDS = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,17,19]
# boat _type ids associated with ergos
ERGO_IDS = [15,18]
#other ids, e.g. megafoon, swapfiets
OTHER_IDS = [30,21,29,31,32,33,34,35]

# used for weather station closed to boathouse. This station is in Volkel
point = Point(51.808470, 5.815918)

connection = sqlite3.connect('boatdata.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
cursor = connection.cursor()

def fetch_reservations(start_time,end_time,type):
    q = 'SELECT begin_time as "[timestamp]", end_time as "[timestamp]" FROM boat_reservations WHERE '
    q += 'begin_time >= \'{}\' and begin_time <= \'{}\''.format(start_time,end_time)
    q += 'AND removed_date IS NULL '
    if type == "boats":
        q += 'AND boat_id IN (SELECT id FROM boats WHERE type_id in ({}))'.format(','.join([str(id) for id in BOAT_IDS]))
    elif type == "ergos":
        q += 'AND boat_id IN (SELECT id FROM boats WHERE type_id in ({}))'.format(','.join([str(id) for id in ERGO_IDS]))

    return cursor.execute(q + ';').fetchall()

def accumulate(data, timeslots, accumulator):
    if not accumulator:
        accumulator = [0]*len(timeslots)
    for i,ts in enumerate(timeslots):
        for bt, et in data:
            if bt<=ts and et> ts:
                accumulator[i]+=1
    return accumulator

def boathouse_occupation(day=datetime(2021, 10, 12), days=1):
    accumulator_boats = []
    accumulator_ergos = []
    for i in range(days):
        timeslots = [day + timedelta(hours=6,minutes=15*x) for x in range(69)]
        # timeslots = [day + timedelta(hours=6+x) for x in range(18)]

        data = fetch_reservations(day, day+timedelta(days=1), type="boats")
        accumulator_boats = accumulate(data,timeslots,accumulator_boats)

        data = fetch_reservations(day,day+timedelta(days=1), type="ergos")
        accumulator_ergos = accumulate(data,timeslots,accumulator_ergos)
        day += timedelta(days=1)

    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(mticker.MultipleLocator(4))
    plt.xticks(rotation=45)
    ax.bar([t.strftime("%H:%M")for t in timeslots], accumulator_boats, align='edge',width=1, color='b', label='boats')
    ax.bar([t.strftime("%H:%M")for t in timeslots], accumulator_ergos, align='edge',width=1,bottom=accumulator_boats, color='y',label='ergos')
    plt.legend()

    return (timeslots,accumulator_boats,accumulator_ergos)
boathouse_occupation()


def fetch_count_reservations(start_time,end_time,type='boat'):
    q = 'SELECT count(*) FROM boat_reservations WHERE '
    q += 'begin_time >= \'{}\' and begin_time <= \'{}\''.format(start_time,end_time)
    q += 'AND removed_date IS NULL '
    if type == "boats":
        q += 'AND boat_id IN (SELECT id FROM boats WHERE type_id in ({}))'.format(','.join([str(id) for id in BOAT_IDS]))
    elif type == "ergos":
        q += 'AND boat_id IN (SELECT id FROM boats WHERE type_id in ({}))'.format(','.join([str(id) for id in ERGO_IDS]))
    elif type == 'either':
        q += 'AND boat_id IN (SELECT id FROM boats WHERE type_id in ({}))'.format(','.join([str(id) for id in ERGO_IDS+BOAT_IDS]))

    return cursor.execute(q + ';').fetchone()[0]

def avg_temp(start_day,end_day):
    data = Daily(point, start_day, end_day)
    data = data.normalize()
    data = data.fetch()
    return data['tmax'].mean()

def reservations_per_week(year=2021):
    day = datetime(year=year,month=1,day=1)
    boat_reservations = []
    ergo_reservations = []
    dates = []
    temperatures = []
    for i in range(52):
        dates.append(day)
        boat_reservations.append(fetch_count_reservations(day,day+timedelta(weeks=1),type='either'))
        # ergo_reservations.append(fetch_count_reservations(day,day+timedelta(weeks=1),type='ergos'))
        temperatures.append(avg_temp(day,day+timedelta(weeks=1)))
        day+= timedelta(weeks=1)

    fig, ax1 = plt.subplots()
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)

    ax1.set_ylabel('Reservations')
    ax1.plot(dates,boat_reservations, label='Boats', color='green')
    # ax1.plot(dates,ergo_reservations, label='Ergos', color='blue')

    # ax2 = ax1.twinx()
    # ax2.set_ylabel('Avg Max Temperature')
    # ax2.plot(dates, temperatures, label='Avg Max Temperature', color='red')

    fig.legend()
    return (dates,boat_reservations,ergo_reservations)
reservations_per_week()

def boat_reservations_per_week_all():
    boat_reservations = [0]*52
    ergo_reservations = [0]*52
    dates = [0]*52
    for j in range(9):
        day = datetime(year=2011+j,month=1,day=1)
        for i in range(52):
            dates[i] = day
            boat_reservations[i] += fetch_count_reservations(day,day+timedelta(weeks=1),type='either')
            # ergo_reservations[i] += fetch_count_reservations(day,day+timedelta(weeks=1),type='ergos')
            day+= timedelta(weeks=1)

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    ax.set_ylabel('Reservations')
    ax.plot(dates,boat_reservations, label='Boats', color='green')
    # ax.plot(dates,ergo_reservations, label='Ergos', color='blue')
    return (dates,boat_reservations,ergo_reservations)
boat_reservations_per_week_all()

def peak_hour(day=datetime(2021, 10, 12), days=1):
    accumulator = []
    for i in range(days):
        timeslots = [day + timedelta(hours=6+x) for x in range(18)]

        data = fetch_reservations(day, day+timedelta(days=1), type='boats')
        accumulator = accumulate(data,timeslots,accumulator)
        day += timedelta(days=1)

    return timeslots[accumulator.index(max(accumulator))].time()
peak_hour()

def peak_hour_per_week(year=2021):
    day = datetime(year=year,month=1,day=1)
    dates = []
    peak_hours = []
    for i in range(52):
        peak_hours.append(peak_hour(day,7).hour)
        dates.append(day)
        day += timedelta(weeks=1)

    fig, ax = plt.subplots()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    ax.plot(dates,peak_hours)
peak_hour_per_week()

#DataDonderdag 1
x,boats,ergos = boathouse_occupation(day=datetime(2010,4,27),days=4100)
print(boats)
print(ergos)
print([t.strftime("%H:%M") for t in x])

#DataDonderdag 2
x,boats_total,_ = boat_reservations_per_week_all()
_,boats_2020,_ = reservations_per_week(2020)
print([t.strftime("%d-%m") for t in x])
print(boats_total)
print(boats_2020)

connection.close()