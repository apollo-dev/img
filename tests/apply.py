
from os.path import join
import numpy as np
from scipy.misc import imread

proximity = '/Users/duozhang007/Desktop/img/20171020_zhaoying/proximity'
proximity_clean = imread(join(proximity, 'clean.png'))
proximity_img = imread(join(proximity, 'proximity.png'))

metadata = {
    'rmop': 0.7576,
    'cmop':	0.7576,
    'zmop': 0.988,
    'tpf_in_seconds': 684.5,
    'rs': 1024,
    'cs': 1024,
    'zs': 29,
    'ts': 70,
}

header = []
with open(join(proximity, '20171020_zhaoying_s3_91A3X1N8_output.csv'), 'r') as data:
    with open(join(proximity, 'output.csv'), 'w+') as out:
        for i, line in enumerate(data.readlines()):
            if i>0:
                tokens = line.rstrip().split(',')
                r, c = int(float(tokens[4]) / 0.7576), int(float(tokens[5]) / 0.7576)

                r = (r if r >= 0 else 0) if r < 1024 else 1023
                c = (c if c >= 0 else 0) if c < 1024 else 1023
                proximity_d = proximity_img[r, c] * 0.7576

                tokens.append(str(proximity_d))
                out.write(','.join(tokens) + '\n')
            else:
                headers = line.rstrip().split(',')
                headers.append('proximity')
                out.write(','.join(headers) + '\n')
