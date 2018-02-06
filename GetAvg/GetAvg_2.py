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

#get threshold from 1st run
max_dict = {'17031071500': 145.79219608359998,
 '17031080100': 196.07726112089,
 '17031080202': 178.45570520811,
 '17031081000': 166.15515670759,
 '17031081100': 129.41022844018002,
 '17031081201': 140.17031297507,
 '17031081202': 174.08024900246,
 '17031081300': 116.20485559616,
 '17031081401': 138.90721055333,
 '17031081402': 185.09868298651,
 '17031081403': 177.73993787989002,
 '17031081500': 137.11494049415,
 '17031081600': 139.82668645507,
 '17031081700': 153.49949039487,
 '17031081800': 119.77578711077,
 '17031280100': 118.30525704215,
 '17031281900': 134.04540760745,
 '17031320100': 137.90130251585,
 '17031320400': 163.42664873411,
 '17031320600': 136.77105186456,
 '17031330100': 123.64499043366999,
 '17031833100': 145.7094456201,
 '17031839100': 139.88807868426,
 '17031980000': 194.4166465637,
 '17031980100': 169.96753967109998}

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
                fare = float(data[10][1:]) #omit $
                if fare < max_dict[data[7]]:
                    yield (data[7], 'count'), 1
                    yield (data[7], 'fare'), fare
                    yield (data[7], 'fare^2'), fare**2
            if data[9] == '32' and data[6] in TOP_25:
                fare = float(data[10][1:]) #omit $
                if fare < max_dict[data[6]]:
                    yield (data[6], 'count'), 1
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
