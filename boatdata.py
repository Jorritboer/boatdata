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
        accumulator = [0]*69
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
boathouse_occupation()


def fetch_count_reservations(start_time,end_time):
    q = 'SELECT count(*) FROM boat_reservations WHERE '
    q += 'begin_time >= \'{}\' and begin_time <= \'{}\''.format(start_time,end_time)
    q += 'AND removed_date IS NULL '
    q += 'AND boat_id IN (SELECT id FROM boats WHERE type_id in ({}))'.format(','.join([str(id) for id in BOAT_IDS]))

    return cursor.execute(q + ';').fetchone()[0]

def avg_temp(start_day,end_day):
    data = Daily(point, start_day, end_day)
    data = data.normalize()
    data = data.fetch()
    return data['tmax'].mean()

def reservations_per_week(year=2021):
    day = datetime(year=year,month=1,day=1)
    reservations = []
    dates = []
    temperatures = []
    for i in range(52):
        dates.append(day)
        reservations.append(fetch_count_reservations(day,day+timedelta(weeks=1)))
        temperatures.append(avg_temp(day,day+timedelta(weeks=1)))
        day+= timedelta(weeks=1)

    fig, ax1 = plt.subplots()
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)

    ax1.set_ylabel('Reservations')
    ax1.plot(dates,reservations, label='Reservations', color='green')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Avg Max Temperature')
    ax2.plot(dates, temperatures, label='Avg Max Temperature', color='red')

    fig.legend()
reservations_per_week()

connection.close()