import re
import logging

logging.basicConfig(filename='find_ave.log',level=logging.DEBUG)
with open('find_ave.log', 'w') as f:
    pass


with open("samples.txt", "r") as f1:
    count = 0
    total_len = 0
    for line in f1:
        count += 1
        try:
            url, flag = re.search(r'(.*)[.].*\t(\d)', line).group(1), re.search(r'(.*)[.].*\t(\d)', line).group(2)
            print "url: {0}  <-- {1}".format(url, flag)
            total_len += len(url)
        except Exception as e:
            logging.error(e)
        if int(flag) != 0:
            print "ave_len: {}".format(float(total_len/count))
            break


