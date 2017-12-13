import csv
from os import listdir
import sys

file_list = [1,2,3]
csv_file = ''
if sys.argv[1] == '0':
    csv_file = 'res.csv'
else:
    csv_file = 'iterative.csv'
with open(csv_file, 'wb') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)

    for f_num in file_list:
        dir_name = 'p0' + str(f_num)
        if sys.argv[1] == '0':
            for file in listdir( dir_name):
                if file.find('.vero') + 1:
                    #got the file.
                    #check the last word.
                    with open(dir_name + '/' + file) as res:
                        eq = res.read()[-4:-1] == 'yes'
                        csv_line = file.split('.')[0].split(',') + [eq] + [f_num]
                        csvwriter.writerow(csv_line)
        elif sys.argv[1] == '1':
            dir_name = dir_name + '/res'

            for i, file in enumerate(listdir( dir_name)):
                if file.find('.iter') + 1:
                    #got the file.
                    #check the last word.
                    with open(dir_name + '/' + file) as res:
                        eq = res.read()[-4:-1] == 'yes'
                        csv_line = file.split('.')[0].split(',') + [eq] + [f_num] + [file[-1:]]
                        csvwriter.writerow(csv_line)
