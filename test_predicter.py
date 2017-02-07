import csv, sys, bisect
from datetime import datetime
import json
import urllib
from bs4 import BeautifulSoup
import requests
from splinter import Browser
import time

# first step: take in a birth date and return the nearest date from the birth date data
input_date = sys.argv[1]
datetime_object = datetime.strptime(input_date, '%m/%d/%Y')
input_birthday = datetime_object.day
input_birthmonth = datetime_object.month
input_birthyear = datetime_object.year

# next, load up the death data csv
with open('death_data_sorted_tester.csv', 'rb') as death_data_object:
    death_data_reader = csv.reader(death_data_object)
    next(death_data_reader)
    death_data_list = list(death_data_reader)

# create the better death list, with only dates in it (sorted)
better_death_list = []
for n in death_data_list:
    date_string = n[2] + '/' + n[3] + '/' + n[1]
    current_date_object = datetime.strptime(date_string, '%m/%d/%Y')
    better_death_list.append(current_date_object)

# if the data contains 1 or more rows with the same date as the one requested,
# then we want the nearest previous date, all rows with the same date, plus the closest one after that
exact_date_found = 'no'
lst = []
length_death_list = len(better_death_list)
for i, n in enumerate(better_death_list):
    if (n == datetime_object):
        exact_date_found = 'yes'
        prev_index = i - 1
        lst.append(prev_index)
        cur_index = i
        lst.append(cur_index)
        break

# if the exact date has been found in the data, we need to do some special stuff:
if (exact_date_found == 'yes'):
    # we now have the prev index and the cur index in a list. we need the index after
    after_index = bisect.bisect_right(better_death_list, datetime_object, lo=lst[1], hi=len(better_death_list))
    # get the indices between cur and after
    between = range(lst[1]+1, after_index)
    for item in between:
        lst.append(item)
    lst.append(after_index)
    # for item in lst:
    #     print "date is", better_death_list[item]
    #     print "SSN is", death_data_list[item][0]
    prev_index = lst[0]
    after_index = lst[-1]
# otherwise, we just want the before and after dates:
else:
    prev_index = bisect.bisect(better_death_list, datetime_object)-1
    after_index = bisect.bisect_right(better_death_list, datetime_object)
    # print "prior date is", better_death_list[prev_index]
    # print "and its SSN is", death_data_list[prev_index][0]
    # print "after date is", better_death_list[after_index]
    # print "and its SSN is", death_data_list[after_index][0]

# create a sequential list of the group numbers (as strings), in order that they are supposed to be used
group_numbers = ['01', '03', '05', '07', '09']
for n in range(10, 99, 2):
    group_numbers.append(str(n))
even_smalls = ['02', '04', '06', '08']
for n in even_smalls:
    group_numbers.append(n)
for n in range(11, 100, 2):
    group_numbers.append(str(n))

used_lower_bound_type = ''
used_upper_bound_type = ''

# If the DOB is after 4th Jan 1999, we need to find the ranges given by the group number
if (datetime_object >= datetime.strptime('01/04/1999', '%m/%d/%Y')):
    # open up the high order data as a list of lists
    with open('high_order_data_sorted.csv', 'rb') as high_order_object:
        high_order_reader = csv.reader(high_order_object)
        next(high_order_reader)
        high_order_list = list(high_order_reader)

    # create a list of these dates, in datetime object format
    high_order_dates_only = []
    for a in high_order_list:
        cur_date = a[3] + '/' + a[4] + '/' + a[2]
        high_order_date_object = datetime.strptime(cur_date, '%m/%d/%Y')
        high_order_dates_only.append(high_order_date_object)

    # get the nearest dates that are in the High Order dataset
    # Question: is the High Order number for each date mean the highest order number reached up until that day (including that day)?
    # I'm gonna interpret the data to mean, eg the number 27 was the highest group number reached up to but not including 4th Jan 1999
    group_lower_index = bisect.bisect(high_order_dates_only, datetime_object) - 1
    group_higher_index = bisect.bisect_right(high_order_dates_only, datetime_object)

    # next step is to get lower and upper bounds, depending on whether death data or group data gives
    # the smaller range here
    if (high_order_dates_only[group_lower_index] <= better_death_list[prev_index]):
        lower_bound_date = better_death_list[prev_index]
        # want to go to the next SSN in this case, so that later the dead person's SSN is not considered a possibility
        lower_bound_SSN = death_data_list[prev_index][0]
        if (lower_bound_SSN[-4:] == "9999"):
            # get current group number so we can increment it
            cur_group_number = lower_bound_SSN[3:5]
            new_group_number = group_numbers[group_numbers.index(cur_group_number) + 1]
            lower_bound_SSN = "574" + new_group_number + "0001"
        else:
            thing = (int(lower_bound_SSN[-4:])) + 1
            lower_bound_SSN = lower_bound_SSN[0:5] + str(thing)
    else:
        lower_bound_date = high_order_dates_only[group_lower_index]
        lower_bound_SSN = "574" + high_order_list[group_lower_index][0] + "0001"

    if (high_order_dates_only[group_higher_index] >= better_death_list[after_index]):
        higher_bound_date = better_death_list[after_index]
        higher_bound_SSN = death_data_list[after_index][0]
        if (higher_bound_SSN[-4:] == "0001"):
            # get current group number so we can decrement it
            cur_group_number = higher_bound_SSN[3:5]
            new_group_number = group_numbers[group_numbers.index(cur_group_number) - 1]
            higher_bound_SSN = "574" + new_group_number + "9999"
    else:
        higher_bound_date = high_order_dates_only[group_higher_index]
        higher_bound_SSN = "574" + high_order_list[group_higher_index][0] + "9999"
# if it is between 1990 and 4th Jan 1999, then just go ahead with ranges given by birth death data
else:
    lower_bound_date = better_death_list[prev_index]
    lower_bound_SSN = death_data_list[prev_index][0]
    higher_bound_date = better_death_list[after_index]
    higher_bound_SSN = death_data_list[after_index][0]
print lower_bound_date, lower_bound_SSN
print higher_bound_date, higher_bound_SSN

# We asssume that we are not being given DOB for dead people in our excerpt! Is this reasonable?

# Using the lower and upper bounds, either from group numbers or from DOBs, create a list of possible
# SSNs in order of possible issuance

# step 2: function to produce a list of possible SSNs given upper and lower bound SSNs, which are inclusive
def possible_SSNs(lower, upper):
    # get me from lower SSN to the start of a new group
    output_list = [lower]
    cur_group_num = lower[3:5]
    g_upper = upper[3:5]
    # if (cur_group_num == g_upper):
    #     lower_seq = int(lower[-4:])
    #     upper_seq = int(upper[-4:]) + 1
    #     for n in range(lower_seq, upper_seq):
    #         n = str(n).zfill(4)
    #         possi
    if (lower[-4:] != "9999"):
        last_four = int(lower[-4:])
        group_num = lower[3:5]
        # then we want to go from 0865 to 9999
        for n in range((last_four + 1), 10000):
            # turn n in into a string with leading zeroes
            n = str(n).zfill(4)
            possible_SSN = "574" + group_num + n
            output_list.append(possible_SSN)
    # then I calculate all the SSNs through to the upper bound SSN
    # find current group num in group_num ordered list, then get next one
    group_lower_bound = group_numbers[(group_numbers.index(cur_group_num) + 1)]
    # set up the upper bound
    # get the group number just before this one, so we can go to the end of that
    group_upper_bound = group_numbers[(group_numbers.index(g_upper) - 1)]
    # cycle through the group numbers, inclusive of both group bounds, using their indices
    g_lower_index = group_numbers.index(cur_group_num) + 1
    g_upper_index = group_numbers.index(g_upper)
    for e in range(g_lower_index, g_upper_index):
        current_group_num = group_numbers[e]
        for n in range(1, 10000):
            n = str(n).zfill(4)
            output_list.append("574" + current_group_num + n)
    return output_list

possibles = possible_SSNs(lower_bound_SSN, higher_bound_SSN)
print len(possibles)

# Validate these, and if you have several that are valid then those are your number of guesses needed
def validate_list(lst):
    valid_list = []
    for item in lst:
        url = 'http://www.ssnvalidator.com/'
        browser = Browser('phantomjs')
        browser.visit(url)
        time.sleep(1)
        area_code = "574"
        group = item[3:5]
        seq = item[-4:]
        # now execute the given SSN
        browser.fill('ctl00$ContentPlaceHolder1$SsnFirstPartTextBox', "574")
        browser.fill('ctl00$ContentPlaceHolder1$SsnSecondPartTextBox', group)
        browser.fill('ctl00$ContentPlaceHolder1$SsnThirdPartTextBox', seq)
        browser.choose('ctl00$ContentPlaceHolder1$accept_terms', 'YesRadioButton')
        browser.find_by_name('ctl00$ContentPlaceHolder1$SubmitButton').first.click()
        # now wait a second or 3
        time.sleep(1)

        # now pull the results and sift for what we need
        text = browser.evaluate_script('document.getElementById("ContentPlaceHolder1_ResultsPanel").outerHTML')
        soup = BeautifulSoup(text, "html.parser")
        # looking for anything with the class "ssn_valid"
        results = soup.find_all("span", class_="ssn_valid")
        if (len(results) == 1):
            valid_list.append(item)
            print valid_list
        else:
            print "not valid - not added"
        # now go back to the search page to start again
        # browser.find_by_name('ctl00$ContentPlaceHolder1$SearchAgainButton').first.click()
        # time.sleep(1)
        browser.quit()
        print "got to end of loop: restarting loop"
    return valid_list

# print len(validate_list(possibles))

# Take the first (births_per_day * days_between bounds) SSNs (this is when things get uncertain)
# for 1990-1994, we have no data
# for 1995-2002, we have only yearly data, not monthly
# for 2002-2014, we have monthly data
# let the default be set below for 1990-1994, and it will be overridden if the DOB requested is 1995 onwards
births_per_day = 28

if (datetime_object >= datetime.strptime('01/01/1995', '%m/%d/%Y')):
    dob_year = datetime_object.year
    dob_month = datetime_object.month
    # then test if in 2003 onwards
    if (datetime_object >= datetime.strptime('01/01/2003', '%m/%d/%Y')):
        # find monthly data
        with open('alaska_natality_2003_2014.csv', 'rb') as birth_data_object:
            birth_data_reader = csv.reader(birth_data_object)
            next(birth_data_reader)
            birth_data_list = list(birth_data_reader)
        for n in birth_data_list:
            if ((n[0] == dob_year) and (n[2] == dob_month)):
                births_per_day = (int(n[3]) / 30)
    else:
        # then we use the yearly data, divide by 12
        with open('alaska_natality_1995_2002.csv', 'rb') as birth_data_object:
            birth_data_reader = csv.reader(birth_data_object)
            next(birth_data_reader)
            birth_data_list = list(birth_data_reader)
        for n in birth_data_list:
            if (n[0] == dob_year):
                births_per_day = (int(n[1]) / 12) / 30

# now we have our births_per_day in the month of our requested DOB
length_of_SSN_possibles = len(possibles)
five_percent = int(0.025 * length_of_SSN_possibles)
target_index = int(births_per_day * datetime_object.day)
before_target_index = target_index - five_percent
after_target_index = target_index + five_percent

prediction_list = possibles[before_target_index:after_target_index]
print len(prediction_list)


# Testing the data set using a subset of the death data
with open('tester_birthdays.csv', 'rb') as tester_object:
    tester_reader = csv.reader(tester_object)
    tester_list = list(tester_reader)

# tell me if the input DOB's SSN is in testers:
for f in tester_list:
    if (input_date in f):
        print "yes, input DOB is in prediction_list"
        print input_date, f[1]