import time, os, pandas

from threading import Thread, RLock
from datetime import datetime
from colorama import init
from termcolor import colored
from PIL import Image as IMG

from survePy_functions import *
from survePy_config import *

# initializing the script
survey_lock, count_lock = RLock(), RLock()
overall_blacklist, target_no_survey, overall_results = [], [], {}
count, scan_progress, stopped_threads = 0, 0, 0
n_threads = 1 # threading appeared to be useless (not improving speed). If you want to give it life back, you should edit the way results are retrieved from the get_results function.

class solving_instance(Thread):

	def __init__(self):
		Thread.__init__(self)

	def run(self):

		global count
		global scan_progress
		global stopped_threads

		while 1:

			with survey_lock:
				survey, no_survey, found, blacklist = get_survey(path, overall_blacklist)
				if found is False:
					break
				else:
					overall_blacklist.append(blacklist)


			try:
				final_list = get_points_list(survey, colors, color_choice, count, survey_amount)
			except:
				step = "get_points_list"
				print(colored("An error occured - \"get_points_list\" step","red"))
				overall_results[no_survey] = []
				error_logging(no_survey, step)
				continue


			try:
				pixels_areas_tuple = get_pixels_areas(final_list)
			except:
				step = "get_pixels_areas"
				print(colored("An error occured - \"get_pixels_areas\" step","red"))
				overall_results[no_survey] = []
				error_logging(no_survey, step)
				continue


			try:
				results, scan_progress = get_results(survey, pixels_areas_tuple, colors, no_survey, excel, scan_progress, target_no_survey)
			except:
				step = "get_results"
				print(colored("An error occured - \"get_results\" step","red"))
				overall_results[no_survey] = []
				error_logging(no_survey, step)
				continue

				
			overall_results[no_survey] = results[no_survey]
			with count_lock:
				count += 1
				print(colored("A survey has been solved ({}/{})".format(str(count),str(survey_amount)),"green"))


		stopped_threads += 1
		if stopped_threads == n_threads:
			cleaned_results(overall_results, scans_per_subject_n, columns_n, excel)
			os.system("pause")
			quit()


# Start of the script
init()
print(colored("Surve","cyan")+colored("P","yellow")+colored("y","cyan")+"\n")

survey_amount = len(os.listdir("{}/surveys".format(path)))
if survey_amount == 0:
	print(colored("You have to fill the \"surveys\" folder with surveys\n","yellow"))
	os.system("pause")
	quit()
elif survey_amount == 1:
	print("1 survey found\n")
else:
	print("{} surveys found\n".format(survey_amount))

excel = pandas.read_excel("{}/settings.xlsx".format(path))

scans_per_subject_n = excel["Item 1"][2]
columns_n = excel["Item 1"][3]
color_choice = str(excel["Item 1"][4]).lower()

while scan_progress < survey_amount:
	target_no_survey.append(scan_progress)
	scan_progress += scans_per_subject_n
scan_progress = 0

for i in range(0, n_threads):
	solving_instance().start()