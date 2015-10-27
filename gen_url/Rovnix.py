import re
import random


def getWords(text):
    return re.compile('\w+').findall(text)

def get_dic():
    list_a = []
    with open('base.txt') as logfile:
        for line in logfile:
            list_a = list_a + getWords(line)        

#    list_b = set(list_a)
#    print list_b
    return list_a

def tld_generator():
    list_tld = []
    list_tld = ['com', 'net', 'biz', 'cn', 'eu']    
    return random.choice(list_tld)

def selection_based_generator(list_input):
    temp_list = []
    list_input = list_input
    temp_list.append(random.choice(list_input))
    while True:
        domain_length = 0
        word_count = len(temp_list)
        for i in range(0, len(temp_list)):
            domain_length = domain_length + len(temp_list[i])
        if domain_length > 25 or word_count > 6:
            break
        else:
            temp_list.append(random.choice(list_input))

    str1 = ''.join(temp_list)    
    return str1.lower()
    
def tld_generator():
    list_tld = []
    list_tld = ['com', 'net', 'biz', 'cn', 'eu']
    return random.choice(list_tld)
    
def transposition_based_generator(list_input):
    #english_vowels = ['a', 'e', 'i', 'o', 'u']
    input_domain = selection_based_generator(get_dic())
    tld = tld_generator()
    return input_domain+'.'+tld


def rovnix():
    print selection_based_generator(get_dic())

def transposition_based_domain():
    print transposition_based_generator(get_dic())
    return transposition_based_generator(get_dic())
    
    
fp = open("linux_dga.txt", "w")
for i in range (0, 500000):
#    rovnix()
    domain = transposition_based_domain()
    line = "%s\t3\n"%domain
    fp.write(line)
fp.close()



