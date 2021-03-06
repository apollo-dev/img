# woot.apps.img.models

# django
from django.db import models

# local
from apps.expt.models import Experiment, Series
from apps.expt.util import generate_id_token, str_value, random_string
from apps.expt.data import *
from apps.img import algorithms

# util
import os
import re
from scipy.misc import imread, imsave, toimage
from scipy.ndimage import label
from skimage import exposure
import numpy as np
from PIL import Image, ImageDraw
from scipy.stats.mstats import mode

### Models
# http://stackoverflow.com/questions/19695249/load-just-part-of-an-image-in-python
class Composite(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='composites')
	series = models.ForeignKey(Series, related_name='composites')

	# properties
	id_token = models.CharField(max_length=8)
	current_region_unique = models.CharField(max_length=8)
	current_zedge_unique = models.CharField(max_length=8)

	# methods
	def __str__(self):
		return '{}, {} > {}'.format(self.experiment.name, self.series.name, self.id_token)

	def save_data_file(self):
		# save data on all cell instances
		# data_file_name =
		# with op
		pass

	def get_or_create_data_file(self, root, file_name):

		# metadata
		template = self.templates.get(name='data')
		metadata = template.dict(file_name)

		if self.series.name == metadata['series']:
			data_file, data_file_created = self.data_files.get_or_create(experiment=self.experiment, series=self.series, template=template, id_token=metadata['id'], data_type=metadata['type'], url=os.path.join(root, file_name), file_name=file_name)
			return data_file, data_file_created, 'created.' if data_file_created else 'already exists.'
		else:
			return None, False, 'does not match series.'

	def shape(self, d=2):
		return self.series.shape(d)

class Template(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='templates')

	# properties
	name = models.CharField(max_length=255)
	rx = models.CharField(max_length=255)
	rv = models.CharField(max_length=255)

	# methods
	def __str__(self):
		return '{}: {}'.format(self.name, self.rx)

	def match(self, string):
		return re.match(self.rx, string)

	def dict(self, string):
		return self.match(string).groupdict()

### GONS
class Channel(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='channels')

	# properties
	name = models.CharField(max_length=255)

	# methods
	def __str__(self):
		return '{} > {}'.format(self.composite.id_token, self.name)

	def segment(self, marker_channel_name='-zcomp', threshold_correction_factor=1.2, background=True):

		unique = random_string() # defines a single identifier for this run
		unique_key = '{}{}-{}'.format(marker_channel_name, self.name, unique)

		# setup
		print('getting marker channel')
		marker_channel = self.composite.channels.get(name=marker_channel_name)

		# 1. create primary from markers with marker_channel
		print('running primary')
		marker_channel_primary_name = marker_channel.primary(unique=unique)

		# 2. create pipeline and run
		print('run pipeline')
		self.composite.experiment.save_marker_pipeline(series_name=self.composite.series.name, primary_channel_name=marker_channel_primary_name, secondary_channel_name=self.name, threshold_correction_factor=threshold_correction_factor, background=background, unique=unique, unique_key=unique_key)
		self.composite.experiment.run_pipeline(series_ts=self.composite.series.ts)

		print('import masks')
		# 3. import masks and create new mask channel
		cp_out_file_list = [f for f in os.listdir(self.composite.experiment.cp_path) if (unique_key in f and '.tiff' in f)]
		# make new channel that gets put in mask path
		cp_template = self.composite.templates.get(name='cp')
		mask_template = self.composite.templates.get(name='mask')
		mask_channel = self.composite.mask_channels.create(name=unique_key)
		region_mask_channel = self.composite.mask_channels.filter(name__contains=self.composite.current_region_unique)[0]

		for cp_out_file in cp_out_file_list:
			array = imread(os.path.join(self.composite.experiment.cp_path, cp_out_file))
			metadata = cp_template.dict(cp_out_file)
			mask_channel.get_or_create_mask(array, int(metadata['t']))

		print('import data files')
		# 4. import datafiles and access data
		data_file_list = [f for f in os.listdir(self.composite.experiment.cp_path) if (unique in f and '.csv' in f)]
		for df_name in data_file_list:
			data_file, data_file_created, status = self.composite.get_or_create_data_file(self.composite.experiment.cp_path, df_name)

		# 5. create cells and cell instances from tracks
		cell_data_file = self.composite.data_files.get(id_token=unique, data_type='Cells')
		data = cell_data_file.load()

		# load masks and associate with grayscale id's
		for t in range(self.composite.series.ts):
			mask_mask = mask_channel.masks.get(t=t)
			mask = mask_mask.load()

			# load region mask
			region_mask_mask = region_mask_channel.masks.get(t=t)
			region_mask = region_mask_mask.load()

			t_data = list(filter(lambda d: int(d['ImageNumber'])-1==t, data))

			markers = marker_channel.markers.filter(track_instance__t=t)
			for marker in markers:
				# 1. create cell
				cell, cell_created = self.composite.experiment.cells.get_or_create(series=self.composite.series, track=marker.track)

				# 2. create cell instance
				cell_instance, cell_instance_created = cell.instances.get_or_create(experiment=cell.experiment,
																																						series=cell.series,
																																						track_instance=marker.track_instance)

				# 3. create cell mask
				marker.r = (marker.r if marker.r >= 0 else 0) if marker.r < mask.shape[1] else mask.shape[1]-1
				marker.c = (marker.c if marker.c >= 0 else 0) if marker.c < mask.shape[0] else mask.shape[0]-1
				gray_value_id = mask[marker.r, marker.c]
				region_gray_value_id = region_mask[marker.r, marker.c]
				region_instance = self.composite.series.region_instances.filter(region_track_instance__t=t, mode_gray_value_id=region_gray_value_id)
				if region_instance:
					region_instance = region_instance[0]
				else:
					region_instance = None
					for ri in self.composite.series.region_instances.filter(region_track_instance__t=t):
						gray_value_ids = [ri_mask.gray_value_id for ri_mask in ri.masks.all()]
						if region_instance is None and region_gray_value_id in gray_value_ids:
							region_instance = ri

				if gray_value_id!=0:
					cell_mask = cell_instance.masks.create(experiment=cell.experiment,
																								 series=cell.series,
																								 cell=cell,
																								 region=region_instance.region if region_instance is not None else None,
																								 region_instance=region_instance if region_instance is not None else None,
																								 channel=mask_channel,
																								 mask=mask_mask,
																								 marker=marker,
																								 gray_value_id=gray_value_id)

					cell_mask_data = list(filter(lambda d: int(d['ObjectNumber'])==cell_mask.gray_value_id, t_data))[0]

					# 4. assign data
					cell_mask.r = cell_mask.marker.r
					cell_mask.c = cell_mask.marker.c
					cell_mask.t = t
					cell_mask.AreaShape_Area = float(cell_mask_data['AreaShape_Area']) if str(cell_mask_data['AreaShape_Area']) != 'nan' else -1.0
					cell_mask.AreaShape_Compactness = float(cell_mask_data['AreaShape_Compactness']) if str(cell_mask_data['AreaShape_Compactness']) != 'nan' else -1.0
					cell_mask.AreaShape_Eccentricity = float(cell_mask_data['AreaShape_Eccentricity']) if str(cell_mask_data['AreaShape_Eccentricity']) != 'nan' else -1.0
					cell_mask.AreaShape_EulerNumber = float(cell_mask_data['AreaShape_EulerNumber']) if str(cell_mask_data['AreaShape_EulerNumber']) != 'nan' else -1.0
					cell_mask.AreaShape_Extent = float(cell_mask_data['AreaShape_Extent']) if str(cell_mask_data['AreaShape_Extent']) != 'nan' else -1.0
					cell_mask.AreaShape_FormFactor = float(cell_mask_data['AreaShape_FormFactor']) if str(cell_mask_data['AreaShape_FormFactor']) != 'nan' else -1.0
					cell_mask.AreaShape_MajorAxisLength = float(cell_mask_data['AreaShape_MajorAxisLength']) if str(cell_mask_data['AreaShape_MajorAxisLength']) != 'nan' else -1.0
					cell_mask.AreaShape_MaximumRadius = float(cell_mask_data['AreaShape_MaximumRadius']) if str(cell_mask_data['AreaShape_MaximumRadius']) != 'nan' else -1.0
					cell_mask.AreaShape_MeanRadius = float(cell_mask_data['AreaShape_MeanRadius']) if str(cell_mask_data['AreaShape_MeanRadius']) != 'nan' else -1.0
					cell_mask.AreaShape_MedianRadius = float(cell_mask_data['AreaShape_MedianRadius']) if str(cell_mask_data['AreaShape_MedianRadius']) != 'nan' else -1.0
					cell_mask.AreaShape_MinorAxisLength = float(cell_mask_data['AreaShape_MinorAxisLength']) if str(cell_mask_data['AreaShape_MinorAxisLength']) != 'nan' else -1.0
					cell_mask.AreaShape_Orientation = float(cell_mask_data['AreaShape_Orientation']) if str(cell_mask_data['AreaShape_Orientation']) != 'nan' else -1.0
					cell_mask.AreaShape_Perimeter = float(cell_mask_data['AreaShape_Perimeter']) if str(cell_mask_data['AreaShape_Perimeter']) != 'nan' else -1.0
					cell_mask.AreaShape_Solidity = float(cell_mask_data['AreaShape_Solidity']) if str(cell_mask_data['AreaShape_Solidity']) != 'nan' else -1.0

					cell_mask.save()

					# for now
					cell_instance.set_from_masks(unique)

				else:
					# for now
					cell_instance.set_from_markers()

		# 6. calculate cell velocities
		print('calculating velocities...')
		for cell in self.composite.experiment.cells.all():
			cell.calculate_velocities()
			cell.calculate_confidences()

		return unique

	def segment_regions(self, region_marker_channel_name='-zbf', threshold_correction_factor=1.2, background=True):

		unique = random_string() # defines a single identifier for this run
		unique_key = '{}{}-{}'.format(region_marker_channel_name, self.name, unique)

		# setup
		region_marker_channel = self.composite.channels.get(name=region_marker_channel_name)

		# 1. create region primary
		print('running primary')
		region_marker_channel_primary_name = region_marker_channel.region_primary(unique=unique)

		# 2. create pipeline and run
		self.composite.experiment.save_region_pipeline(series_name=self.composite.series.name, primary_channel_name=region_marker_channel_primary_name, secondary_channel_name=self.name, threshold_correction_factor=threshold_correction_factor, background=background, unique=unique, unique_key=unique_key)
		self.composite.experiment.run_pipeline(series_ts=self.composite.series.ts, key='regions')

		# 3. import masks
		print('import masks')
		cp_out_file_list = [f for f in os.listdir(self.composite.experiment.cp_path) if (unique_key in f and '.tiff' in f)]
		# make new channel that gets put in mask path
		cp_template = self.composite.templates.get(name='cp')
		mask_template = self.composite.templates.get(name='mask')
		mask_channel = self.composite.mask_channels.create(name=unique_key)

		for cp_out_file in cp_out_file_list:
			array = imread(os.path.join(self.composite.experiment.cp_path, cp_out_file))
			metadata = cp_template.dict(cp_out_file)
			mask_channel.get_or_create_mask(array, int(metadata['t']))

		# 4. create regions and tracks
		print('create regions and tracks...')
		for t in range(self.composite.series.ts):
			mask_mask = mask_channel.masks.get(t=t)
			mask = mask_mask.load()

			region_markers = region_marker_channel.region_markers.filter(region_track_instance__t=t)
			for region_marker in region_markers:
				# 1. create cell
				region, region_created = self.composite.experiment.regions.get_or_create(series=self.composite.series, region_track=region_marker.region_track, name=region_marker.region_track.name)

				# 2. create cell instance
				region_instance, region_instance_created = region.instances.get_or_create(experiment=region.experiment,
																																									series=region.series,
																																									region_track_instance=region_marker.region_track_instance)

				# 3. create cell mask
				gray_value_id = mask[region_marker.r, region_marker.c]
				region_mask, region_mask_created = region_instance.masks.get_or_create(experiment=region.experiment,
																																							 series=region.series,
																																							 region=region,
																																							 mask=mask_mask)
				region_mask.gray_value_id = gray_value_id
				region_mask.save()

			for region_track_instance in region_marker_channel.region_track_instances.filter(t=t):
				gray_value_ids = [region_mask.gray_value_id for region_mask in region_track_instance.region_instance.masks.filter(mask=mask_mask)]
				region_track_instance.region_instance.mode_gray_value_id = int(mode(gray_value_ids)[0][0])
				region_track_instance.region_instance.save()

		self.composite.current_region_unique = unique
		self.composite.save()

		return unique

	# methods
	def region_labels(self):
		return np.unique([region_marker.region_track.name for region_marker in self.region_markers.all()])

	def get_or_create_gon(self, array, t, r=0, c=0, z=0, rs=None, cs=None, zs=1, path=None):
		# self.defaults
		rs = self.composite.series.rs if rs is None else rs
		cs = self.composite.series.cs if cs is None else cs
		path = self.composite.experiment.composite_path if path is None else path

		# build
		gon, gon_created = self.gons.get_or_create(experiment=self.composite.experiment, series=self.composite.series, composite=self.composite, t=t)
		gon.set_origin(r,c,z,t)
		gon.set_extent(rs,cs,zs)

		gon.array = array
		gon.save_array(path, self.composite.templates.get(name='source'))
		gon.save()

		return gon, gon_created

	def primary(self, unique=''):
		if self.markers.count()!=0:
			channel_name = ''

			# 1. loop through time series
			marker_channel, marker_channel_created = self.composite.channels.get_or_create(name='{}-primary-{}'.format(self.name, unique))

			for t in range(self.composite.series.ts):
				print('primary for composite {} {} {} channel {} | t{}/{}'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name, t+1, self.composite.series.ts), end='\n' if t==self.composite.series.ts-1 else '\r')

				# load all markers for this frame
				markers = self.markers.filter(track_instance__t=t)

				# blank image
				blank = np.zeros(self.composite.shape())

				for i, marker in enumerate(markers):

					blank[marker.r-3:marker.r+2, marker.c-3:marker.c+2] = 255

				blank_gon, blank_gon_created = marker_channel.get_or_create_gon(blank, t)

			return marker_channel.name

		else:
			print('primary for composite {} {} {} channel {} | no markers have been defined.'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name))

	def region_primary(self, unique=''):
		if self.region_markers.count()!=0:

			# 1. loop through time series
			marker_channel, marker_channel_created = self.composite.channels.get_or_create(name='{}-regionprimary-{}'.format(self.name, unique))

			for t in range(self.composite.series.ts):
				print('primary for composite {} {} {} channel {} | t{}/{}'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name, t+1, self.composite.series.ts), end='\n' if t==self.composite.series.ts-1 else '\r')
				# blank image
				blank = np.ones(self.composite.shape())

				for region_track_name in set([rm.region_track.name for rm in self.region_markers.all()]):

					region_markers = self.region_markers.filter(region_track_instance__t=t, region_track__name=region_track_name)

					previous_region_marker = None
					first_region_marker = None
					for i, region_marker in enumerate(list(sorted(region_markers, key=lambda rm: rm.region_track_index))):

						img = Image.fromarray(blank)
						draw = ImageDraw.Draw(img)

						if previous_region_marker is not None:
							draw.line([(previous_region_marker.c, previous_region_marker.r), (region_marker.c, region_marker.r)], fill=0, width=5)

						previous_region_marker = region_marker
						if first_region_marker is None:
							first_region_marker = region_marker if region_marker.region_track_index==1 else None

						if i==len(region_markers)-1:
							draw.line([(region_marker.c, region_marker.r), (first_region_marker.c, first_region_marker.r)], fill=0, width=5)

						blank = np.array(img)

				# fill in holes in blank
				blank, n = label(blank)
				blank[blank==blank[0,0]] = 0

				# create gon
				blank_gon, blank_gon_created = marker_channel.get_or_create_gon(blank, t)

			return marker_channel.name

		else:
			print('region primary for composite {} {} {} channel {} | no region markers have been defined.'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name))

	def outline(self, outline_channel=None):
		'''
		Use cells to overlay outlines on images. Take masks from outline_channel or same channel if None.
		'''

		pass

		# if outline_channel is None:
		#
		#
		# else:

	def tile_labels_and_outlines(self, label_channel=None):
		pass

class Gon(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='gons')
	series = models.ForeignKey(Series, related_name='gons')
	composite = models.ForeignKey(Composite, related_name='gons', null=True)
	template = models.ForeignKey(Template, related_name='gons', null=True)
	channel = models.ForeignKey(Channel, related_name='gons')
	gon = models.ForeignKey('self', related_name='gons', null=True)

	# properties
	id_token = models.CharField(max_length=8, default='')

	# 1. origin
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)
	t = models.IntegerField(default=-1)

	# 2. extent
	rs = models.IntegerField(default=-1)
	cs = models.IntegerField(default=-1)
	zs = models.IntegerField(default=1)

	# 3. data
	array = None

	# methods
	def set_origin(self, r, c, z, t):
		self.r = r
		self.c = c
		self.z = z
		self.t = t
		self.save()

	def set_extent(self, rs, cs, zs):
		self.rs = rs
		self.cs = cs
		self.zs = zs
		self.save()

	def shape(self):
		if self.zs==1:
			return (self.rs, self.cs)
		else:
			return (self.rs, self.cs, self.zs)

	def t_str(self):
		return str('0'*(len(str(self.series.ts)) - len(str(self.t))) + str(self.t))

	def z_str(self, z=None):
		return str('0'*(len(str(self.series.zs)) - len(str(self.z if z is None else z))) + str(self.z if z is None else z))

	def load(self):
		self.array = []
		for path in self.paths.order_by('z'):
			array = imread(path.url)
			self.array.append(array)
		self.array = np.dstack(self.array).squeeze() # remove unnecessary dimensions
		return self.array

	def save_array(self, root, template):
		# 1. iterate through planes in bulk
		# 2. for each plane, save plane based on root, template
		# 3. create path with url and add to gon

		if not os.path.exists(root):
			os.makedirs(root)

		file_name = template.rv.format(self.experiment.name, self.series.name, self.channel.name, str_value(self.t, self.series.ts), '{}')
		url = os.path.join(root, file_name)

		if len(self.array.shape)==2:
			imsave(url.format(str_value(self.z, self.series.zs)), self.array)
			self.paths.create(composite=self.composite if self.composite is not None else self.gon.composite, channel=self.channel, template=template, url=url.format(str_value(self.z, self.series.zs)), file_name=file_name.format(str_value(self.z, self.series.zs)), t=self.t, z=self.z)

		else:
			for z in range(self.array.shape[2]):
				plane = self.array[:,:,z].copy()

				imsave(url.format(str_value(z+self.z, self.series.zs)), plane) # z level is offset by that of original gon.
				self.paths.create(composite=self.composite, channel=self.channel, template=template, url=url.format(str_value(self.z, self.series.zs)), file_name=file_name.format(str_value(self.z, self.series.zs)), t=self.t, z=z+self.z)

				# create gons
				gon = self.gons.create(experiment=self.composite.experiment, series=self.composite.series, channel=self.channel, template=template)
				gon.set_origin(self.r, self.c, z, self.t)
				gon.set_extent(self.rs, self.cs, 1)

				gon.array = plane.copy().squeeze()

				gon.save_array(self.experiment.composite_path, template)
				gon.save()

### GON STRUCTURE AND MODIFICATION ###
class Path(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='paths')
	gon = models.ForeignKey(Gon, related_name='paths')
	channel = models.ForeignKey(Channel, related_name='paths')
	template = models.ForeignKey(Template, related_name='paths')

	# properties
	url = models.CharField(max_length=255)
	file_name = models.CharField(max_length=255)
	t = models.IntegerField(default=0)
	z = models.IntegerField(default=0)

	# methods
	def __str__(self):
		return '{}: {}'.format(self.composite.id_token, self.file_name)

	def load(self):
		return imread(self.url)

class Mod(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='mods')

	# properties
	id_token = models.CharField(max_length=8)
	algorithm = models.CharField(max_length=255)
	date_created = models.DateTimeField(auto_now_add=True)

	# methods
	def run(self, **kwargs):
		''' Runs associated algorithm to produce a new channel. '''
		algorithm = getattr(algorithms, self.algorithm)
		algorithm(self.composite, self.id_token, self.algorithm, **kwargs)

### MASKS
class MaskChannel(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='mask_channels')

	# properties
	name = models.CharField(max_length=255)

	# methods
	def __str__(self):
		return 'mask {} > {}'.format(self.composite.id_token, self.name)

	def get_or_create_mask(self, array, t, r=0, c=0, z=0, rs=None, cs=None, path=None):
		# self.defaults
		rs = self.composite.series.rs if rs is None else rs
		cs = self.composite.series.cs if cs is None else cs
		path = self.composite.experiment.composite_path if path is None else path

		# build
		mask, mask_created = self.masks.get_or_create(experiment=self.composite.experiment, series=self.composite.series, composite=self.composite, t=t)
		mask.set_origin(r,c,z,t)
		mask.set_extent(rs,cs)

		mask.array = array
		mask.save_array(path, self.composite.templates.get(name='mask'))
		mask.save()

		return mask, mask_created

class Mask(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='masks')
	series = models.ForeignKey(Series, related_name='masks')
	composite = models.ForeignKey(Composite, related_name='masks', null=True)
	channel = models.ForeignKey(MaskChannel, related_name='masks')
	template = models.ForeignKey(Template, related_name='masks', null=True)

	# properties
	id_token = models.CharField(max_length=8, default='')
	url = models.CharField(max_length=255)
	file_name = models.CharField(max_length=255)

	# 1. origin
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)
	t = models.IntegerField(default=-1)

	# 2. extent
	rs = models.IntegerField(default=-1)
	cs = models.IntegerField(default=-1)

	# 3. data
	array = None

	# methods
	def set_origin(self, r, c, z, t):
		self.r = r
		self.c = c
		self.z = z
		self.t = t
		self.save()

	def set_extent(self, rs, cs):
		self.rs = rs
		self.cs = cs
		self.save()

	def shape(self):
		return (self.rs, self.cs)

	def t_str(self):
		return str('0'*(len(str(self.series.ts)) - len(str(self.t))) + str(self.t))

	def load(self):
		array = imread(self.url)
		self.array = (exposure.rescale_intensity(array * 1.0) * (len(np.unique(array)) - 1)).astype(int) # rescale to contain integer grayscale id's.
		return self.array

	def save_array(self, root, template):
		# 1. iterate through planes in bulk
		# 2. for each plane, save plane based on root, template
		# 3. create path with url and add to gon

		if not os.path.exists(root):
			os.makedirs(root)

		self.file_name = template.rv.format(self.experiment.name, self.series.name, self.channel.name, str_value(self.t, self.series.ts), str_value(self.z, self.series.zs))
		self.url = os.path.join(root, self.file_name)

		imsave(self.url, self.array)

### DATA
class DataFile(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='data_files')
	series = models.ForeignKey(Series, related_name='data_files')
	composite = models.ForeignKey(Composite, related_name='data_files')
	template = models.ForeignKey(Template, related_name='data_files')

	# properties
	id_token = models.CharField(max_length=8)
	data_type = models.CharField(max_length=255)
	url = models.CharField(max_length=255)
	file_name = models.CharField(max_length=255)

	data = []

	# methods
	def load(self):
		self.data = []
		with open(self.url) as df:
			headers = []
			for n, line in enumerate(df.readlines()):
				if n==0: # title
					headers = line.rstrip().split(',')
				else:
					line_dict = {}
					for i, token in enumerate(line.rstrip().split(',')):
						line_dict[headers[i]] = token
					self.data.append(line_dict)
		return self.data

	def save_data(self, data_headers):
		with open(self.url, 'w+') as df:
			df.write('{}\n'.format(','.join(data_headers)))
			for line in self.data:
				df.write(line)

		# parse cell profiler results spreadsheet into array that can be used to make cell instances
		# 1. generate dictionary keys from title line
		# 2. return array of dictionaries
