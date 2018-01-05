
import os
from os.path import join, isdir
import shutil as sh
import re

# root_path = '/Users/duozhang007/Desktop/Zhaoying/Zhaoying Data/1'
root_path = '/Volumes/Seagate Backup Plus Drive/Zhaoying cell data/Zhaoying Data/2'
destination_path = '/Volumes/Seagate Backup Plus Drive/img/20171020_zhaoying/img/storage'

pattern = r'Sequence_001_Job 3_037_l(?P<frame>[0-9]+)_z(?P<z>[0-9]+)_ch(?P<channel>[0-9]+)\.tif'

for path in os.listdir(root_path):
    full_path = join(root_path, path)
    if not isdir(full_path) and '.DS' not in full_path:
        m = re.match(pattern, path)
        if m is not None:
            frame = int(m.group('frame'))
            z = int(m.group('z'))
            channel = int(m.group('channel'))

            # new path
            new_path = '20171020_zhaoying_s2_ch{}_t{}_z{}.tiff'.format(channel, frame, z)
            new_full_path = join(destination_path, new_path)

            # copy
            print(new_path)
            sh.copy2(full_path, new_full_path)
