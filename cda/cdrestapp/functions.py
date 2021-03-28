import re

time_interval_re = re.compile(r'^(([0-1][0-9])|(2[0-3])):[0-5][0-9]-(([0-1][0-9])|(2[0-3])):[0-5][0-9]$')
WRONG_TIME_FORMAT_MESSAGE = 'Wrong time format. Use "HH:MM-HH:MM".'
WRONG_TIME_INTERVAL_ORDER = 'Provide a valid time interval with an end time greater than the start time'


def work_delivery_intersect(working_hours, delivery_hours):
    for dh in delivery_hours:
        for wh in working_hours:
            if dh.delivery_start <= wh.work_start < dh.delivery_end or \
                    wh.work_start <= dh.delivery_start < wh.work_end:
                return True
    return False
