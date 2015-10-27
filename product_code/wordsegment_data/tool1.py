import enchant
import re
d_us = enchant.Dict('en_US')
d_gb = enchant.Dict('en_GB')

with open('unigrams.txt','r') as inf:
    with open('filtered_unigrams.txt', 'a') as ouf:
        for line in inf:
            try:
                word = re.search('(.*)[\t].*',line).group(1)
                word = word.strip()
            except:
                print "Re pattern error, please check line {0}\n".format(line)
            if d_us.check(word) or d_gb.check(word) or d_us.check(word.capitalize()):
                ouf.write('{0}\n'.format(line.strip()))
                
