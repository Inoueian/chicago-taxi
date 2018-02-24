#!/bin/python
"""
Adapted from https://github.com/Yelp/mrjob
"""

from mrjob.job import MRJob, MRStep
import numpy as np

TOP_36 = ['17031839100', '17031281900', '17031320100', '17031081500',
          '17031081700', '17031081403', '17031280100', '17031081800',
          '17031081201', '17031330100', '17031833000', '17031081600',
          '17031980000', '17031081300', '17031320400', '17031081401',
          '17031081402', '17031320600', '17031833100', '17031071500',
          '17031081000', '17031081202', '17031080300', '17031839000',
          '17031980100', '17031081100', '17031080100', '17031838100',
          '17031071400', '17031080202', '17031841900', '17031842300',
          '17031842200', '17031841000', '17031243500', '17031080201']

#get threshold from 1st run
max_dict = {'17031071400': 18.279395493103369,
 '17031071500': 16.658083518024235,
 '17031080100': 15.055989471884603,
 '17031080201': 14.433857863460865,
 '17031080202': 14.50190625299085,
 '17031080300': 15.41455983977413,
 '17031081000': 13.492134762962918,
 '17031081100': 13.631155193555978,
 '17031081201': 14.022649306370351,
 '17031081202': 15.276380773245641,
 '17031081300': 14.57380876491662,
 '17031081401': 13.435642427212862,
 '17031081402': 13.447529212812347,
 '17031081403': 13.375240392959718,
 '17031081500': 13.342910193184128,
 '17031081600': 12.819757753907131,
 '17031081700': 12.324432973389785,
 '17031081800': 13.098765618152013,
 '17031243500': 16.833191529831108,
 '17031280100': 11.848864808288033,
 '17031281900': 12.143828220173363,
 '17031320100': 16.77639614207957,
 '17031320400': 17.037726875165305,
 '17031320600': 18.085091051553988,
 '17031330100': 16.612926217498934,
 '17031833000': 13.497756670456504,
 '17031833100': 13.726865356792999,
 '17031838100': 18.217160880511887,
 '17031839000': 14.313108520637485,
 '17031839100': 15.279299862403782,
 '17031841000': 18.386944569071787,
 '17031841900': 16.291438498579318,
 '17031842200': 17.471352670877039,
 '17031842300': 19.701872641362591,
 '17031980000': 57.796836584919184,
 '17031980100': 42.412742689306647}

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
            if data[8] == '32' and data[7] in TOP_36:
                fare = float(data[10][1:]) #omit $
                if fare < max_dict[data[7]]:
                    yield (data[7], 'count'), 1
                    yield (data[7], 'fare'), fare
                    yield (data[7], 'fare^2'), fare**2
            if data[9] == '32' and data[6] in TOP_36:
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
