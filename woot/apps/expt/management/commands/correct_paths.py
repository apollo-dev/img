
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

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		expt = Experiment.objects.get(name__contains='zhao')
		series = expt.series.get(name='1')

		# 1. shift the t value of each image in the composite by 1, starting from the top
		#

		# 2. shift the t value of every
