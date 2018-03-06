#!/bin/python
"""
Adapted from https://github.com/Yelp/mrjob
"""

from mrjob.job import MRJob, MRStep

TOP_36 = ['17031839100', '17031281900', '17031320100', '17031081500',
          '17031081700', '17031081403', '17031280100', '17031081800',
          '17031081201', '17031330100', '17031833000', '17031081600',
          '17031980000', '17031081300', '17031320400', '17031081401',
          '17031081402', '17031320600', '17031833100', '17031071500',
          '17031081000', '17031081202', '17031080300', '17031839000',
          '17031980100', '17031081100', '17031080100', '17031838100',
          '17031071400', '17031080202', '17031841900', '17031842300',
          '17031842200', '17031841000', '17031243500', '17031080201'] 

class MRGroupBy(MRJob):
    """Read off pickup census tract (6), dropoff census tract (7),
    pickup community area (8), dropoff community area (9),
    fare (10). Also keep start time (2).

    Keep rides that connect the Loop (community area 32)
    with any of the TOP_25 census tracts, and group by
    time, to/from the Loop, and the other census tract."""

    def mapper(self, _, line):
        """yield (to/from, start time, census tract), 1"""
        data = line.split(',')
        try:
            if data[8] == '32' and data[7] in TOP_36:
                yield ('from', data[2], data[7]), 1
            if data[9] == '32' and data[6] in TOP_36:
                yield ('to', data[2], data[6]), 1
        except Exception:
            pass #ignore this row

    def reducer(self, key, values):
        yield key, sum(values)

if __name__ == '__main__':
    MRGroupBy.run()
