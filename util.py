import datetime
global NUM_DAY_PER_WEEK
global NUM_DAY_PER_WK
global NUM_HOUR_PER_DAY
global NUM_HR_PER_DAY
global NUM_MINUTE_PER_HOUR
global NUM_MIN_PER_HR
global NUM_SECONDS_PER_MINUTE
global NUM_SEC_PER_MIN

NUM_DAY_PER_WEEK = 7.0
NUM_DAY_PER_WK = NUM_DAY_PER_WEEK

NUM_HOUR_PER_DAY = 24.0
NUM_HR_PER_DAY = NUM_HOUR_PER_DAY

NUM_MINUTE_PER_HOUR = 60.0
NUM_MIN_PER_HR = NUM_MINUTE_PER_HOUR

NUM_SECONDS_PER_MINUTE = 60.0
NUM_SEC_PER_MIN = NUM_SECONDS_PER_MINUTE

def mo2sec(nMo):
    return day2sec(30.0 * float(nMo))

def wk2sec(nWeeks):
    global NUM_DAY_PER_WK
    return day2sec(float(nWeeks) * NUM_DAY_PER_WK)

def day2sec(nDays):
    global NUM_HR_PER_DAY
    global NUM_MIN_PER_HR
    global NUM_SEC_PER_MIN

    return float(nDays) * NUM_HR_PER_DAY * NUM_MIN_PER_HR * NUM_SEC_PER_MIN

def sec2day(nSec):
    global NUM_HR_PER_DAY
    global NUM_MIN_PER_HR
    global NUM_SEC_PER_MIN

    return float(nSec) / NUM_SEC_PER_MIN / NUM_MIN_PER_HR / NUM_HR_PER_DAY
    

''' Get human-readable date string from epoch stamp. '''
def beaut(epoch, short=True):
   return datetime.datetime.fromtimestamp(epoch).strftime('%m/%d' + ('/%Y %H:%M:%S' if not short else ''))


