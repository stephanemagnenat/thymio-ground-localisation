#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cython: profile=False
# kate: replace-tabs off; indent-width 4; indent-mode normal; remove-trailing-spaces all;
# vim: ts=4:sw=4:noexpandtab

import os
import numpy as np
import matplotlib
matplotlib.use("PDF") # do this before pylab so you don't get the default back end.
import matplotlib.pyplot as plt
import prettyplotlib as ppl
#plt.style.use('ggplot')
import os.path
import argparse


result_base_dir = '../result'
data_base_dir = '../data'
dest_base_dir = '../article/figures'

plot_params = {'font.size' : 8,
		  'legend.fontsize': 8,
		  'font.family' : 'lmodern',
		  'text.latex.preamble' : [r"\usepackage{lmodern}"],
		  'text.usetex' : True,
		  'legend.frameon': True }



#colors = ['#2c7bb6', '#abd9e9', '#fdae61', '#d7191c']
colors = ['#2cb67b', '#2c7bb6', '#fdae61', '#d7191c']

default_width_in = 3.6
aspect_ratio = 4./2.
default_height_in = default_width_in / aspect_ratio

def plot_cpu_load(name):

	# setup parameters
	plt.rcParams.update(plot_params)

	# data to use
	runs = ['random_1', 'random_2']
	algos = ['ml', 'mcl']
	algo_params = { 'ml': [18, 36, 54, 72], 'mcl': ['50k', '100k', '200k', '400k'] }

	# create plot
	fig, ax = plt.subplots(figsize=(3.4, 1.8))
	ax.set_ylim(0,12)

	# one bar for each algo,param couple
	all_durations = []
	all_labels = []
	all_colors = []
	for algo in algos:
		params = algo_params[algo]
		for i, param in enumerate(params):
			# average on runs
			durations = np.array([])
			for run in runs:
				result_file = '{}_{}_{}'.format(run, algo, param)
				data = np.loadtxt(os.path.join(result_base_dir, result_file))
				durations = np.append(durations, np.average(data[:,1]))
			average_durations = np.average(durations)
			all_durations.append(average_durations)
			all_labels.append(str(param))
			all_colors.append(colors[i])
			print algo, param, average_durations
	ppl.bar(ax, np.arange(len(all_durations)), all_durations, color=all_colors)
	plt.ylabel('step duration [s]')
	ax.set_xticks(np.arange(len(all_durations))+0.4)
	ax.set_xticklabels(all_labels)
	ax.text(2-0.1, -2.3, 'Markov Localization', horizontalalignment='center')
	ax.text(6-0.1, -2.3, 'Monte Carlo Localization', horizontalalignment='center')

	# save figure
	fig.tight_layout(pad=0.02, rect=(0,0.08,1,1))
	fig.savefig(os.path.join(dest_base_dir, name), pad_inches=0.02)


def plot_trajectories():

	# setup parameters
	plt.rcParams.update(plot_params)

	# parameters
	runs = ['random_1', 'random_2']
	algos = ['ml', 'mcl']
	algo_params = {'ml': 72, 'mcl': '400k'}

	# process all runs
	for run in runs:
		for algo in algos:
			param = algo_params[algo]
			result_file = '{}_{}_{}'.format(run, algo, param)

			data = np.loadtxt(os.path.join(result_base_dir, result_file))
			xy = data[:,5:7]

			# create plot
			fig, ax = plt.subplots(figsize=(3, 3))
			ax.set_xlim(0, 150)
			ax.set_ylim(0, 150)

			# draw
			x = xy[20:,0]
			y = xy[20:,1]
			ppl.plot(ax, x, y)

			# save
			name = '{}-{}-{}-trajectory.svg'.format(algo, param, run)
			fig.tight_layout(pad=0.02, rect=(0,0,1,1))
			fig.savefig(os.path.join(dest_base_dir, name), pad_inches=0.02)


def plot_grayscale_images(run, show_dist_not_angle, name):

	# setup parameters
	plt.rcParams.update(plot_params)

	# create figure
	path_length = 180
	fig, ax = plt.subplots(figsize=(3.6, 1.8))
	ax.set_xlim(0, path_length)

	# show dist or angle diff?
	if show_dist_not_angle:
		dataCol = 8
		ylabel = 'position error [cm]'
		ylim = 50
	else:
		dataCol = 9
		ylabel = 'angular error [degrees]'
		ylim = 90
	ax.set_ylim(0, ylim)

	# for different map
	algo = 'ml'
	param = 36
	map_names =  ['breugel_babel', 'van-gogh_starry-night', 'kandinsky_comp-8', 'vermeer_girl-pearl', 'babar', 'childs-drawing_tooth-fairy']
	map_labels = ['Breugel',  'Van Gogh', 'Kandinsky', 'Vermeer', 'Babar', 'Child']
	colors = ['#2cb67b', '#2c7bb6', '#fdae61', '#2cb67b', '#2c7bb6', '#fdae61']
	linestyles = ['-', '-', '-', ':', ':', ':']
	x_ticks = np.arange(0., path_length)
	for i, map_name in enumerate(map_names):

		result_file = 'grayscale_images/{}_{}_{}_{}'.format(run, map_name, algo, param)
		data = np.loadtxt(os.path.join(result_base_dir, result_file))
		gt = np.loadtxt(os.path.join(data_base_dir, run, 'gt.txt'))

		# get the indices in gt for every line in data
		indices = data[:,0].astype(int)

		# compute the local change of the sensors position between every line in data
		# we consider the center between the two centers, which is in (12,0) cm local frame
		thetas = gt[indices,2]
		sensor_local_poses = np.vstack((np.cos(thetas) * .12, np.sin(thetas) * .12))
		deltas_sensor_poses = np.diff(sensor_local_poses, axis=1).transpose()

		# compute the change of the position of the robot's center between every line in data
		xys = gt[indices,0:2]
		deltas_xy = np.diff(xys, axis=0)

		# compute the global distances traveled by the sensors between every line in data
		deltas_dists = np.linalg.norm(deltas_xy + deltas_sensor_poses, axis=1)

		# sum these distances to get the x axis
		cum_dists = np.cumsum(deltas_dists)
		if cum_dists[-1] * 100. < path_length:
			print 'WARNING: In', result_file, 'last path point', cum_dists[-1] * 100., 'is before requested distance travelled', path_length
		x_values = np.insert(cum_dists, 0, [0.]) * 100.
		# get the y values directly from data
		y_values = np.minimum(np.abs(data[:,dataCol]), ylim)

		# plot
		ppl.plot(ax, x_values, y_values, label=map_labels[i], color=colors[i], ls=linestyles[i])

	# add label, legend and show plot
	plt.xlabel('distance travelled [cm]')
	plt.ylabel(ylabel)
	ppl.legend(ax)
	fig.savefig(os.path.join(dest_base_dir, name), bbox_inches='tight', pad_inches=0.02)


def plot_small_maps(show_dist_not_angle, name):

	# setup parameters
	plt.rcParams.update(plot_params)

	# create figure
	path_length = 35
	fig, ax = plt.subplots(figsize=(3.6, 1.5))
	ax.set_xlim(0, path_length)

	# show dist or angle diff?
	if show_dist_not_angle:
		dataCol = 8
		ylabel = 'position error [cm]'
		ylim = 50
	else:
		dataCol = 9
		ylabel = 'angular error [degrees]'
		ylim = 90
	ax.set_ylim(0, ylim)

	# for different map
	algo = 'ml'
	param = 36
	run = 'forward_x_minus_slow_1'
	map_names =  ['map', 'map-xhalf', 'map-xhalf-yhalf']
	map_labels = ['full map', '1/2 map', '1/4 map']
	x_ticks = np.arange(0., path_length)
	for i, map_name in enumerate(map_names):
		start_positions = [80, 85, 90]
		y_median_values = []
		for start_pos in start_positions:

			result_file = 'small_maps/{}_{}_{}_{}_{}'.format(run, map_name, start_pos, algo, param)
			data = np.loadtxt(os.path.join(result_base_dir, result_file))
			gt = np.loadtxt(os.path.join(data_base_dir, run, 'gt.txt'))

			# get the indices in gt for every line in data
			indices = data[:,0].astype(int)

			# compute the local change of the sensors position between every line in data
			# we consider the center between the two centers, which is in (12,0) cm local frame
			thetas = gt[indices,2]
			sensor_local_poses = np.vstack((np.cos(thetas) * .12, np.sin(thetas) * .12))
			deltas_sensor_poses = np.diff(sensor_local_poses, axis=1).transpose()

			# compute the change of the position of the robot's center between every line in data
			xys = gt[indices,0:2]
			deltas_xy = np.diff(xys, axis=0)

			# compute the global distances traveled by the sensors between every line in data
			deltas_dists = np.linalg.norm(deltas_xy + deltas_sensor_poses, axis=1)

			# sum these distances to get the x axis
			cum_dists = np.cumsum(deltas_dists)
			if cum_dists[-1] * 100. < path_length:
				print 'WARNING: In', result_file, 'last path point', cum_dists[-1] * 100., 'is before requested distance travelled', path_length
			x_values = np.insert(cum_dists, 0, [0.]) * 100.
			# get the y values directly from data
			y_values = np.minimum(np.abs(data[:,dataCol]), ylim)
			y_median_values.append(np.interp(x_ticks, x_values, y_values))

			# plot dots
			ppl.plot(ax, x_values, y_values, color=colors[i], alpha=0.4, marker=',', ls='')

		# plot
		y_median_values = np.median(y_median_values, axis=0)
		ppl.plot(ax, x_ticks, y_median_values, label=map_labels[i], color=colors[i])

	# add label, legend and show plot
	plt.xlabel('distance travelled [cm]')
	plt.ylabel(ylabel)
	ppl.legend(ax, loc=3)
	fig.savefig(os.path.join(dest_base_dir, name), bbox_inches='tight', pad_inches=0.02)



def draw_plot(algo, runs, params, show_dist_not_angle, name, path_length, **kwargs):

	# setup parameters
	plt.rcParams.update(plot_params)

	# create figure
	if 'width_in' in kwargs:
		width_in = kwargs['width_in']
	else:
		width_in = default_width_in
	if 'height_in' in kwargs:
		height_in = kwargs['height_in']
	else:
		height_in = default_height_in
	fig, ax = plt.subplots(figsize=(width_in, height_in))
	ax.set_xlim(0, path_length)

	# show dist or angle diff?
	if show_dist_not_angle:
		dataCol = 8
		ylabel = 'position error [cm]'
		ylim = 50
	else:
		dataCol = 9
		ylabel = 'angular error [degrees]'
		ylim = 90
	ax.set_ylim(0, ylim)

	# for every parameter
	x_ticks = np.arange(0., path_length)
	for i, param in enumerate(params):
		y_average_values = np.zeros(shape=x_ticks.shape, dtype=float)
		y_median_values = []
		y_average_counter = 0

		# iterate on all runs
		for run in runs:

			# check if there are specific result runs
			if 'custom_results' in kwargs:
				results = kwargs['custom_results'][run]
			else:
				results = [run]

			# iterate on different results run, if any
			for result in results:
				result_file = '{}_{}_{}'.format(result, algo, param)
				data = np.loadtxt(os.path.join(result_base_dir, result_file))
				gt = np.loadtxt(os.path.join(data_base_dir, run, 'gt.txt'))

				# get the indices in gt for every line in data
				indices = data[:,0].astype(int)

				# compute the local change of the sensors position between every line in data
				# we consider the center between the two centers, which is in (12,0) cm local frame
				thetas = gt[indices,2]
				sensor_local_poses = np.vstack((np.cos(thetas) * .12, np.sin(thetas) * .12))
				deltas_sensor_poses = np.diff(sensor_local_poses, axis=1).transpose()

				# compute the change of the position of the robot's center between every line in data
				xys = gt[indices,0:2]
				deltas_xy = np.diff(xys, axis=0)

				# compute the global distances traveled by the sensors between every line in data
				deltas_dists = np.linalg.norm(deltas_xy + deltas_sensor_poses, axis=1)

				# sum these distances to get the x axis
				cum_dists = np.cumsum(deltas_dists)
				if cum_dists[-1] * 100. < path_length:
					print 'WARNING: In', result_file, 'last path point', cum_dists[-1] * 100., 'is before requested distance travelled', path_length
				x_values = np.insert(cum_dists, 0, [0.]) * 100.
				# get the y values directly from data
				y_values = np.minimum(np.abs(data[:,dataCol]), ylim)
				# interpolate to put them in relation with other runs
				y_average_values += np.interp(x_ticks, x_values, y_values)
				y_median_values.append(np.interp(x_ticks, x_values, y_values))
				y_average_counter += 1

				if len(results) > 1:
					ppl.plot(ax, x_values, y_values, color=colors[i], alpha=0.4, marker=',', ls='')

				#print run, result, param, show_dist_not_angle
				#print x_values, y_values, cum_dists[-1] * 100.
				#for i, d in zip(indices, x_values):
				#	print i, d

		# plot
		y_average_values /= y_average_counter
		y_median_values = np.median(y_median_values, axis=0)
		ppl.plot(ax, x_ticks, y_median_values, label=str(param), color=colors[i])

	# add label, legend and show plot
	plt.xlabel('distance travelled [cm]')
	plt.ylabel(ylabel)
	ppl.legend(ax)
	fig.savefig(os.path.join(dest_base_dir, name), bbox_inches='tight', pad_inches=0.02)


if __name__ == '__main__':
	# draw plots

	parser = argparse.ArgumentParser(description='Generate plots for Thymio localization')
	parser.add_argument('--whole_range_random12', help='whole range on random_1 and random_2 for ML and MCL', action='store_true')
	parser.add_argument('--whole_range_random_long', help='whole range on random_long for ML and MCL', action='store_true')
	parser.add_argument('--small_runs', help='small runs on random_1 and random_2 for ML and MCL', action='store_true')
	parser.add_argument('--small_maps', help='multiple map sizes using forward_x_minus_slow_1, ML and 36 angle steps', action='store_true')
	parser.add_argument('--cpu_load', help='plot CPU load for different methods and paramters on random_1 and random_2', action='store_true')
	parser.add_argument('--grayscale_images', help='various grayscale images using random_1 and random_2', action='store_true')
	parser.add_argument('--trajectories', help='trajectories for random_1 and random_2', action='store_true')

	args = parser.parse_args()

	if args.whole_range_random12:
		# random1 and random2, whole range
		whole_range_length = 180

		# ML
		draw_plot('ml', ['random_1'], [18, 36, 54, 72], True, 'ml-whole_random_1-xy.pdf', whole_range_length)
		draw_plot('ml', ['random_1'], [18, 36, 54, 72], False, 'ml-whole_random_1-theta.pdf', whole_range_length)
		draw_plot('ml', ['random_2'], [18, 36, 54, 72], True, 'ml-whole_random_2-xy.pdf', whole_range_length)
		draw_plot('ml', ['random_2'], [18, 36, 54, 72], False, 'ml-whole_random_2-theta.pdf', whole_range_length)

		# MCL
		mcl_results = {'random_1': [ 'multiple_mcl/random_1_0', 'multiple_mcl/random_1_1', 'multiple_mcl/random_1_2', 'multiple_mcl/random_1_3', 'multiple_mcl/random_1_4', 'multiple_mcl/random_1_5', 'multiple_mcl/random_1_6', 'multiple_mcl/random_1_7', 'multiple_mcl/random_1_8', 'multiple_mcl/random_1_9'], 'random_2': [ 'multiple_mcl/random_2_0', 'multiple_mcl/random_2_1', 'multiple_mcl/random_2_2', 'multiple_mcl/random_2_3', 'multiple_mcl/random_2_4', 'multiple_mcl/random_2_5', 'multiple_mcl/random_2_6', 'multiple_mcl/random_2_7', 'multiple_mcl/random_2_8', 'multiple_mcl/random_2_9']}
		draw_plot('mcl', ['random_1'], ['50k', '100k', '200k', '400k'], True, 'mcl-whole_random_1-xy.pdf', whole_range_length, custom_results = mcl_results)
		draw_plot('mcl', ['random_1'], ['50k', '100k', '200k', '400k'], False, 'mcl-whole_random_1-theta.pdf', whole_range_length, custom_results = mcl_results)
		draw_plot('mcl', ['random_2'], ['50k', '100k', '200k', '400k'], True, 'mcl-whole_random_2-xy.pdf', whole_range_length, custom_results = mcl_results)
		draw_plot('mcl', ['random_2'], ['50k', '100k', '200k', '400k'], False, 'mcl-whole_random_2-theta.pdf', whole_range_length, custom_results = mcl_results)

	elif args.whole_range_random_long:
		# random_long, ML and MCL whole range
		draw_plot('ml', ['random_long'], [18, 36, 54, 72], True, 'ml-whole_random_long-xy.pdf', 1400.)
		draw_plot('ml', ['random_long'], [18, 36, 54, 72], False, 'ml-whole_random_long-theta.pdf', 1400.)
		mcl_results = {'random_long': ['multiple_mcl/random_long_0', 'multiple_mcl/random_long_1', 'multiple_mcl/random_long_2', 'multiple_mcl/random_long_3', 'multiple_mcl/random_long_4', 'multiple_mcl/random_long_5', 'multiple_mcl/random_long_6', 'multiple_mcl/random_long_7', 'multiple_mcl/random_long_8', 'multiple_mcl/random_long_9' ]}
		draw_plot('mcl', ['random_long'], ['50k', '100k', '200k', '400k'], True, 'mcl-whole_random_long-xy.pdf', 1400., custom_results = mcl_results)
		draw_plot('mcl', ['random_long'], ['50k', '100k', '200k', '400k'], False, 'mcl-whole_random_long-theta.pdf', 1400., custom_results = mcl_results)

	elif args.small_runs:
		# small runs
		small_runs_results = {'random_1': ['small_runs/random_1_0', 'small_runs/random_1_20', 'small_runs/random_1_40', 'small_runs/random_1_60', 'small_runs/random_1_80'], 'random_2': ['small_runs/random_2_0', 'small_runs/random_2_20', 'small_runs/random_2_40', 'small_runs/random_2_60', 'small_runs/random_2_80']}
		draw_plot('ml', ['random_1', 'random_2'], [18, 36, 54, 72], True, 'ml-small_runs_random_12-xy.pdf', 77, custom_results = small_runs_results)
		draw_plot('ml', ['random_1', 'random_2'], [18, 36, 54, 72], False, 'ml-small_runs_random_12-theta.pdf', 77, custom_results = small_runs_results)
		draw_plot('mcl', ['random_1', 'random_2'], ['50k', '100k', '200k', '400k'], True, 'mcl-small_runs_random_12-xy.pdf', 77, custom_results = small_runs_results)
		draw_plot('mcl', ['random_1', 'random_2'], ['50k', '100k', '200k', '400k'], False, 'mcl-small_runs_random_12-theta.pdf', 77, custom_results = small_runs_results)

	elif args.small_maps:
		# small maps, same run
		plot_small_maps(True, 'ml-small_maps-xy.pdf')
		plot_small_maps(False, 'ml-small_maps-theta.pdf')

	elif args.grayscale_images:
		# various grayscale images
		plot_grayscale_images('random_1', True, 'ml-grayscale_images-random_1-xy.pdf')
		plot_grayscale_images('random_1', False, 'ml-grayscale_images-random_1-theta.pdf')
		plot_grayscale_images('random_2', True, 'ml-grayscale_images-random_2-xy.pdf')
		plot_grayscale_images('random_2', False, 'ml-grayscale_images-random_2-theta.pdf')

	elif args.cpu_load:
		plot_cpu_load('cpu_load.pdf')

	elif args.trajectories:
		plot_trajectories()

	else:
		parser.print_help()
