#!/bin/python
"""
Adapted from https://github.com/Yelp/mrjob
"""

from mrjob.job import MRJob, MRStep
import numpy as np

TOP_25 = ['17031839100', '17031320100', '17031281900',
          '17031280100', '17031081500', '17031081403',
          '17031081800', '17031980000', '17031081700',
          '17031081401', '17031081300', '17031081201',
          '17031330100', '17031081600', '17031320400',
          '17031081000', '17031320600', '17031980100',
          '17031080100', '17031081402', '17031833100',
          '17031081100', '17031071500', '17031080202',
          '17031081202']

class MRGetAvg(MRJob):
    """Read off pickup census tract (6), dropoff census tract (7),
    pickup community area (8), dropoff community area (9),
    fare (10).

    Simply keep track of the census tract, as the fare should not
    change too much based on whether the ride is to or from the Loop."""
    def steps(self):
        return [MRStep(mapper=self.mapper0,
                       reducer=self.reducer0),
                MRStep(mapper=self.mapper1,
                       reducer=self.reducer1)]

    def mapper0(self, _, line):
        data = line.split(',')
        try:
            if data[8] == '32' and data[7] in TOP_25:
                yield (data[7], 'count'), 1
                fare = float(data[10][1:]) #omit $
                yield (data[7], 'fare'), fare
                yield (data[7], 'fare^2'), fare**2
            if data[9] == '32' and data[6] in TOP_25:
                yield (data[6], 'count'), 1
                fare = float(data[10][1:]) #omit $
                yield (data[6], 'fare'), fare
                yield (data[6], 'fare^2'), fare**2
        except Exception:
            pass #ignore this row

    def reducer0(self, key, values):
        yield key, sum(values)

    def mapper1(self, key, value):
        yield key[0], (key[1], value)

    def reducer1(self, key, values):
        for value in values:
            if value[0] == 'count':
                count = value[1]
            elif value[0] == 'fare':
                fare = value[1]
            elif value[0] == 'fare^2':
                fare2 = value[1]
        avg = fare / count
        std = (fare2 / count - avg**2)**0.5
        yield (key, 'avg'), avg
        yield (key, 'std'), std

if __name__ == '__main__':
    MRGetAvg.run()
