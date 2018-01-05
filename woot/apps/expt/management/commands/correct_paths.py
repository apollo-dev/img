
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
from subprocess import call
import shutil as sh

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

		make_option('--lif', # option that will appear in cmd
			action='store', # no idea
			dest='lif', # refer to this in options variable
			default='', # some default
			help='Name of the .lif archive' # who cares
		),

		make_option('--gfp', # option that will appear in cmd
			action='store', # no idea
			dest='gfp_channel', # refer to this in options variable
			default='0', # some default
		),

		make_option('--bf', # option that will appear in cmd
			action='store', # no idea
			dest='bf_channel', # refer to this in options variable
			default='1', # some default
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		expt = Experiment.objects.get(name__contains='zhao')
		for path in expt.paths.all():
			print(path.url, path.file_name, path.t)
