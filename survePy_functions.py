import time, os, pandas

from threading import Thread, RLock
from datetime import datetime
from colorama import init
from termcolor import colored
from PIL import Image as IMG

from survePy_config import path


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'): # returns progress bar for completion of each survey (thanks https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console)
    
    
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()


def get_survey(path, overall_blacklist): # returns the survey handled with PIL


        found = False
        blacklist = 0

        files_list = os.listdir("{}/surveys".format(path))

        for file in files_list:
                if found is True:
                        break
                if ".jpg" in file or ".png" in file:
                        survey = IMG.open("{}/surveys/{}".format(path,file))

                        no_survey = int(file.split("(")[1].split(")")[0]) # required scanned surveys' name format is 'xxxxxx (0)" ; "xxxxx (1)" ; "xxxxxx (2)"  (which is the common way scanned documents are named on my computer)
                        if no_survey not in overall_blacklist:
                                blacklist += no_survey
                                found = True
                        else:
                                found = False

        return survey, no_survey, found, blacklist


def get_points_list(survey, colors, color_choice, count, survey_amount): # returns a list containing all colored points with all coordinates (x,y) of each pixel for each points


        pixels_list = []
        survey_pixels = survey.load()

        xmin = 0
        xmax = survey.size[0]
        ymin = 0
        ymax = survey.size[1]

        printProgressBar(ymin, ymax, prefix = 'Survey {}/{} - first step'.format(str(count+1),str(survey_amount)), suffix = 'Complete', length = 50)

        for y in range(ymin, ymax):

                printProgressBar(y + 1, ymax, prefix = 'Survey {}/{} - first step'.format(str(count+1),str(survey_amount)), suffix = 'Complete', length = 50)
                
                for x in range(xmin, xmax):

                    if colors[color_choice][0][0] <= survey_pixels[x,y][0] <= colors[color_choice][1][0] and \
                    colors[color_choice][0][1] <= survey_pixels[x,y][1] <= colors[color_choice][1][1] and \
                    colors[color_choice][0][2] <= survey_pixels[x,y][2] <= colors[color_choice][1][2]:

                        pixels_list.append((x,y))


        n, upbar, lenbar = 0, 0, len(pixels_list)
        points_list = []

        printProgressBar(upbar, lenbar, prefix = 'Survey {}/{} - last step '.format(str(count+1),str(survey_amount)), suffix = 'Complete', length = 50)

        while len(pixels_list) != 0: # red pixels are put together to form points

                added_value = False
                points_list.append([pixels_list[0]])
                del pixels_list[0]
                upbar += 1
                printProgressBar(upbar, lenbar, prefix = 'Survey {}/{} - last step '.format(str(count+1),str(survey_amount)), suffix = 'Complete', length = 50)

                for pixel in pixels_list:
                        if pixel[0]-2 <= points_list[n][0][0] <= pixel[0]+2:
                                if pixel[1]-2 <= points_list[n][0][1] <= pixel[1]+2:
                                        points_list[n].append(pixel)
                                        pixels_list.remove(pixel)
                                        added_value = True
                                        upbar += 1
                                        printProgressBar(upbar, lenbar, prefix = 'Survey {}/{} - last step '.format(str(count+1),str(survey_amount)), suffix = 'Complete', length = 50)

                add = 0
                if added_value == True:
                        while add < len(points_list[n]):
                                for pixel in pixels_list:
                                        if pixel[0]-2 <= points_list[n][add][0] <= pixel[0]+2:
                                                if pixel[1]-2 <= points_list[n][add][1] <= pixel[1]+2:
                                                        points_list[n].append(pixel)
                                                        pixels_list.remove(pixel)
                                                        upbar += 1
                                                        printProgressBar(upbar, lenbar, prefix = 'Survey {}/{} - last step '.format(str(count+1),str(survey_amount)), suffix = 'Complete', length = 50)
                                add += 1

                n += 1

        erase = True
        while erase is True:
                erase = False
                for point in points_list:
                        # print(len(point))
                        if len(point) < 50: # we hypothesize that all points which don't have at least 50 pixels are odd
                                points_list.remove(point)
                                erase = True

        x_total = 0
        y_total = 0
        final_list = []

        for point in points_list: # x/y coordinates (means) for each point are calculated
                for pixel in point:
                        x_total += pixel[0]
                        y_total += pixel[1]
                final_list.append((x_total/len(point),y_total/len(point)))
                x_total = 0
                y_total = 0

        return final_list


def get_pixels_areas(final_list): # returns a list containing areas to parse for each question


        n_points = len(final_list) #  building the list of pixels areas to parse
        y_mean = []

        n = 0
        while n < n_points / 2:
                y_mean.append(0)
                n += 1


        o = 0
        for n in range(0, n_points, 2):
                y_mean[o] += final_list[n][1]
                y_mean[o] += final_list[n+1][1]
                y_mean[o] = int(y_mean[o]/2)
                o += 1

        pixels_areas = []
        for n in range(0, n_points):
                pixels_areas.append([])

        o = 0
        for n in range(0, len(pixels_areas), 2):
                pixels_areas[n].append(int(final_list[n][0]))
                pixels_areas[n+1].append(int(final_list[n+1][0]))
                pixels_areas[n].append(y_mean[o])
                pixels_areas[n+1].append(y_mean[o])
                o += 1

        n = 0
        for point in pixels_areas: # adjusting areas to parse so a decent amount of pixels is treated (probably something to work around in the future for a better accuracy)
                if n % 2 == 0:
                        point[1] -= 10
                else:
                        point[1] += 20
                n += 1

        pixels_areas_tuple = []
        for n in range(0, len(pixels_areas), 2):
                pixels_areas_tuple.append((pixels_areas[n],pixels_areas[n+1]))
        
        return pixels_areas_tuple


def get_results(survey, pixels_areas_tuple, colors, no_survey, excel, scan_progress, target_no_survey): # returns the crossed case for each question
        
        if no_survey in target_no_survey:
                scan_progress = 0

        results = {no_survey : []}
        survey_pixels = survey.load()

        for i, area in enumerate(pixels_areas_tuple): # trick to switch the position of pixels areas in the tuple when required
                if area[0][0] > area[1][0]:
                        area = ([area[1][0],area[0][1]],[area[0][0],area[1][1]])
                pixels_areas_tuple[i] = area

        for area in pixels_areas_tuple: # parsing of the pixels areas to determine which case is crossed : at the moment, the case with the less amount of white pixels 

                pixels_in_answers_areas = []

                scan_progress += 1
                answers_n = int(excel["Item {}".format(str(scan_progress))][1])
                for n in range(0, answers_n):
                        pixels_in_answers_areas.append([0,n+1])

                ymin = area[0][1]
                ymax = area[1][1]
                xmin = area[0][0]
                xmax = area[1][0]

                borders = int(( xmax - xmin ) / answers_n)
                answers_areas_x = []
                answers_areas_x.append([xmin, xmin + borders])

                for n in range(1, answers_n):
                        answers_areas_x.append([answers_areas_x[n-1][1], answers_areas_x[n-1][1] + borders])

                for y in range(ymin,ymax):

                        for x in range(xmin,xmax):

                                if colors["white"][0][0] <= survey_pixels[x,y][0] <= colors["white"][1][0] and \
                                colors["white"][0][1] <= survey_pixels[x,y][1] <= colors["white"][1][1] and \
                                colors["white"][0][2] <= survey_pixels[x,y][2] <= colors["white"][1][2]:

                                        n = 0
                                        for area in answers_areas_x:
                                                if area[0] <= x < area[1]:
                                                        pixels_in_answers_areas[n][0] += 1
                                                        break
                                                n += 1


                pixels_in_answers_areas = sorted(pixels_in_answers_areas)

                if (pixels_in_answers_areas[1][0] - pixels_in_answers_areas[0][0]) / pixels_in_answers_areas[0][0] < 0.02: # when the supposed crossed case has an amount of white pixels close to another case, we set the result as "?" (unsure)
                        pixels_in_answers_areas[0][1] = "?"


                results[no_survey].append(pixels_in_answers_areas[0][1])

        return results, scan_progress


def cleaned_results(overall_results, scans_per_subject_n, columns_n, excel): # returns a cleaned csv file of the overall results

        csv_results = "" # till the call of columns_n, the following code is preparing the content the results file
        n = 0
        for i in range(0, len(overall_results)): # if an error occured in a previous step, values of the related survey are turned to "?"
                if len(overall_results[i]) == 0:
                        try:
                                for k in range(i-scans_per_subject_n, len(overall_results), scans_per_subject_n):
                                        if len(overall_results[i]) == 0:
                                                if len(overall_results[k]) != 0:
                                                        for m in range(0, len(overall_results[k])):
                                                                overall_results[i].append("?")
                        except:
                                for k in range(i+scans_per_subject_n, len(overall_results), scans_per_subject_n):
                                        if len(overall_results[i]) == 0:
                                                if len(overall_results[k]) != 0:
                                                        for m in range(0, len(overall_results[k])):
                                                                overall_results[i].append("?")                         
        

        no_items = 0
        for i in range(0, scans_per_subject_n):
                no_items += len(overall_results[i])

        
        for i in range(0, no_items):
                csv_results += ",item {}".format(str(i+1))
        csv_results += ",\n"


        if columns_n == 1: # no column: no need to reorganize the answers
                s = 0
                for i in range(0, len(overall_results), scans_per_subject_n):
                        csv_results += "subject {},".format(str(s+1))
                        for z in range(0,scans_per_subject_n):
                                for k in range(0, len(overall_results[z+i])):
                                        overall_results[z+i][k] = str(overall_results[z+i][k])
                                csv_results += ",".join(overall_results[z+i])
                                csv_results += ","
                        csv_results += "\n"
                        s += 1


        elif columns_n == 2: # column: this code will reorganize the answers in a more intuitive way (column 1 then column 2)
                overall_results2 = {}
                for i in range(0,len(overall_results)):
                        overall_results2[i] = []
                s = 0
                for i in range(0, len(overall_results), scans_per_subject_n):
                        csv_results += "subject {},".format(str(s+1))
                        for z in range(0,scans_per_subject_n):
                                for k in range(0, len(overall_results[z+i])):
                                        if k % 2 == 0: # or != in several cases
                                                overall_results2[z+i].append(str(overall_results[z+i][k]))

                                for k in range(0, len(overall_results[z+i])):
                                        if k % 2 != 0: # or == in several cases
                                                overall_results2[z+i].append(str(overall_results[z+i][k]))
                                                
                                csv_results += ",".join(overall_results2[z+i])
                                csv_results += ","
                        csv_results += "\n"
                        s += 1


             
        n = 1 # this code will correct / adjust the answers provided by the subject, based on the nature of each item (straight, reversed, or has a correct answer)
        correction = []
        while n < len(excel.columns):
                correction.append(excel["Item {}".format(str(n))][0])
                n+=1

        init_len = len(csv_results.split("subject")[0]) # in order to not misreplace things

        scan_progress = 0
        for i, subject in enumerate(csv_results.split("subject")):
                if i != 0:
                        csv_results = csv_results.split("subject")
                        contenu = csv_results[i][3:-2]
                        csv_results2 = list(csv_results[i][3:-2].replace(",",""))
                        for k, answer in enumerate(csv_results2):
                                if scan_progress == len(correction):
                                        scan_progress = 0
                                if str(answer) != str(correction[scan_progress]).split(".")[0]:
                                        if answer != "?": # values assigned to "straight" in "correction.csv" won't be corrected.
                                                if str(correction[scan_progress]).lower() == "reversed":
                                                        csv_results2[k] = str(int(excel["Item {}".format(str(scan_progress+1))][1]) - int(answer) + 1)
                                                elif str(correction[scan_progress]).lower() == "straight":
                                                        csv_results2[k] = str(answer)
                                                elif str(correction[scan_progress]).lower() != "straight":
                                                        csv_results2[k] = "wrong"
                                elif str(answer) == str(correction[scan_progress]).split(".")[0]:
                                        if answer != ",":
                                                csv_results2[k] = "right"
                                scan_progress += 1
                        csv_results2 = ",".join(csv_results2)
                        csv_results = "subject".join(csv_results)
                        csv_results = csv_results[:init_len] + csv_results[init_len:].replace(","+contenu,","+csv_results2,1)
                        init_len += len(csv_results.split("subject")[i]) +7
                        
                        
        with open("{}/results.csv".format(path),"w") as opening: # saves the results in a csv file
                opening.write(csv_results)
                print(colored("\nResults saved","yellow"))
                print("\n")


def error_logging(no_survey,step): # saves in a txt file the number of the scan and the nature of the problem that occured

        with open("{}/error_logs.txt".format(path),"a") as opening:
                opening.write("{} ---- survey no.{} ---- {}\n".format(str(datetime.now())[:-7], str(no_survey),step))
