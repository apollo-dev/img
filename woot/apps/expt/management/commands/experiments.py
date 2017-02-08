
# django
from django.core.management.base import BaseCommand, CommandError

# util
import json
from optparse import make_option

# local
from apps.expt.models import Experiment

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('--path', # option that will appear in cmd
			action='store', # no idea
			dest='path', # refer to this in options variable
			default='', # some default
			help='Location of data' # who cares
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):

		for experiment in Experiment.objects.all():
			print(experiment.name)
			print(experiment.composites.all())
