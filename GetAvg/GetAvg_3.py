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
max_dict = {'17031071500': 16.658083518022071,
 '17031080100': 15.055989471882919,
 '17031080202': 14.501906252990885,
 '17031081000': 13.492134762961909,
 '17031081100': 13.631155193555028,
 '17031081201': 14.022649306368837,
 '17031081202': 15.276380773245943,
 '17031081300': 14.573808764916045,
 '17031081401': 13.435642427212862,
 '17031081402': 13.447529212811357,
 '17031081403': 13.375240392960709,
 '17031081500': 13.342910193185176,
 '17031081600': 12.819757753907112,
 '17031081700': 12.324432973387236,
 '17031081800': 13.098765618152104,
 '17031280100': 11.848864808291001,
 '17031281900': 12.143828220173045,
 '17031320100': 16.776396142079779,
 '17031320400': 17.037726875163791,
 '17031320600': 18.085091051554585,
 '17031330100': 16.612926217499577,
 '17031833100': 13.726865356792612,
 '17031839100': 15.279299862399313,
 '17031980000': 57.796836584911631,
 '17031980100': 42.412742689303784}

min_dict = {'17031071500': 3.2758434602900008,
 '17031080100': 2.433205605006167,
 '17031080202': 2.2912679131864913,
 '17031081000': 1.7033738961399365,
 '17031081100': 1.9407466122339221,
 '17031081201': 1.4041214872654377,
 '17031081202': 1.0618546210307045,
 '17031081300': 1.004954917066109,
 '17031081401': 1.0719056115836656,
 '17031081402': 1.5459674941169359,
 '17031081403': 0,
 '17031081500': 0,
 '17031081600': 0,
 '17031081700': 0.13919781310069457,
 '17031081800': 0.35927220451814801,
 '17031280100': 0.61094206466147227,
 '17031281900': 0.36274248630344097,
 '17031320100': 0,
 '17031320400': 0,
 '17031320600': 0,
 '17031330100': 0.55870632340301718,
 '17031833100': 0.91828331730227664,
 '17031839100': 0,
 '17031980000': 22.000388002944348,
 '17031980100': 14.756345677526955}

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
                if fare < max_dict[data[7]] and fare > min_dict[data[7]]:
                    yield (data[7], 'count'), 1
                    yield (data[7], 'fare'), fare
                    yield (data[7], 'fare^2'), fare**2
            if data[9] == '32' and data[6] in TOP_25:
                fare = float(data[10][1:]) #omit $
                if fare < max_dict[data[6]] and fare > min_dict[data[6]]:
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
