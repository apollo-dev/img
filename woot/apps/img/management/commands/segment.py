
# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.img.models import Channel

# util
import os
from os.path import join, exists
from optparse import make_option
from subprocess import call
import shutil as sh

spacer = ' ' *	20

### Command
class Command(BaseCommand):

	args = ''
	help = ''

	def handle(self, *args, **options):

		# vars
		c = Channel.objects.get(name='-zmax', composite__series__name='54')
		c.segment()