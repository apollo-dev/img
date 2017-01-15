
# django
from django.core.management.base import BaseCommand, CommandError

# util
import json
from optparse import make_option

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

		# vars
		if 'path' in options:
			path = options['path']

			with open('./setup.json', 'r+') as setup_file:
				data = json.loads(setup_file.read())
				data['data_path'] = path
				setup_file.seek(0)
				setup_file.write(json.dumps(data))
				setup_file.truncate()

		if 'bf_ratio' in options:
			bf_ratio = options['bf_ratio']

		if 'gfp_sigma' in options:
			gfp_sigma = options['gfp_sigma']
