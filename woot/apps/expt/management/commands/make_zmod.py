
# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *

# util
import os
from os.path import join, exists
from optparse import make_option

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

		make_option('--expt', # option that will appear in cmd
			action='store', # no idea
			dest='expt', # refer to this in options variable
			default='', # some default
			help='Name of the experiment to import' # who cares
		),

		make_option('--series', # option that will appear in cmd
			action='store', # no idea
			dest='series', # refer to this in options variable
			default='', # some default
			help='Name of the series' # who cares
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):

		# vars
		experiment_name = options['expt']
		series_name = options['series']
		data_root = settings.DATA_ROOT

		# 1. create experiment and series
		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# 6. make zmod channels
			composite = series.composites.get()

			if composite.channels.filter(name='-zmod'):
				composite.channels.get(name='-zmod').delete()

			mod = composite.mods.create(id_token=generate_id_token('img', 'Mod'), algorithm='mod_zmod')

			# Run mod
			print('step01 | processing mod_zmod...', end='\r')
			mod.run()
			print('step01 | processing mod_zmod... done.{}'.format(spacer))

		else:
			print('Please enter an experiment')
