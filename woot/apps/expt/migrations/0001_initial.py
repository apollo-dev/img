# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

		dependencies = [
		]

		operations = [
				migrations.CreateModel(
						name='Experiment',
						fields=[
								('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
								('name', models.CharField(max_length=255)),
								('base_path', models.CharField(max_length=255)),
								('storage_path', models.CharField(max_length=255)),
								('composite_path', models.CharField(max_length=255)),
								('cp_path', models.CharField(max_length=255)),
								('ij_path', models.CharField(max_length=255)),
								('regions_path', models.CharField(max_length=255)),
								('plot_path', models.CharField(max_length=255)),
								('track_path', models.CharField(max_length=255)),
								('data_path', models.CharField(max_length=255)),
								('pipeline_path', models.CharField(max_length=255)),
								('video_path', models.CharField(max_length=255)),
								('inf_path', models.CharField(max_length=255)),
						],
				),
				migrations.CreateModel(
						name='Path',
						fields=[
								('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
								('url', models.CharField(max_length=255)),
								('file_name', models.CharField(max_length=255)),
								('t', models.IntegerField(default=0)),
								('z', models.IntegerField(default=0)),
						],
				),
				migrations.CreateModel(
						name='PathChannel',
						fields=[
								('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
								('name', models.CharField(max_length=255)),
								('experiment', models.ForeignKey(related_name='channels', to='expt.Experiment')),
						],
				),
				migrations.CreateModel(
						name='Series',
						fields=[
								('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
								('name', models.CharField(max_length=255)),
								('rs', models.IntegerField(default=-1)),
								('cs', models.IntegerField(default=-1)),
								('zs', models.IntegerField(default=-1)),
								('ts', models.IntegerField(default=-1)),
								('rmop', models.FloatField(default=0.0)),
								('cmop', models.FloatField(default=0.0)),
								('zmop', models.FloatField(default=0.0)),
								('tpf', models.FloatField(default=0.0)),
								('experiment', models.ForeignKey(related_name='series', to='expt.Experiment')),
						],
				),
				migrations.CreateModel(
						name='Template',
						fields=[
								('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
								('name', models.CharField(max_length=255)),
								('rx', models.CharField(max_length=255)),
								('rv', models.CharField(max_length=255)),
								('experiment', models.ForeignKey(related_name='templates', to='expt.Experiment')),
						],
				),
				migrations.AddField(
						model_name='path',
						name='channel',
						field=models.ForeignKey(related_name='paths', to='expt.PathChannel'),
				),
				migrations.AddField(
						model_name='path',
						name='experiment',
						field=models.ForeignKey(related_name='paths', to='expt.Experiment'),
				),
				migrations.AddField(
						model_name='path',
						name='series',
						field=models.ForeignKey(related_name='paths', to='expt.Series'),
				),
				migrations.AddField(
						model_name='path',
						name='template',
						field=models.ForeignKey(related_name='paths', to='expt.Template'),
				),
		]
