from os.path import join, dirname, realpath
import logging
import itertools, enchant
import collections
from multiprocessing import Pool
import csv
from pyngram import calc_ngram
import logging
import time
import re
import sys
import tldextract
#from wordsegment import WordSegment
#ws = WordSegment(use_google_corpus=True)
#ws = WordSegment()
#from wordsegment import segment
from pattern.en import pluralize, singularize
from pattern.en import conjugate, lemma, lexeme
from itertools import permutations

from dict_dga_classifier import DictDGAClassifier
d = DictDGAClassifier()


#decorator for recording  performance statistics
def timeit(f):
    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        with open('performance_result_snall.txt', 'a') as file:
            file.write('%d:\t%2.4f\n'%(int(dga_flag), (te-ts)))

        return (result,(te-ts))

    return timed




#split the string in all possible combinations
def break_down(text):
    words = text.split()
    ns = range(1, len(words))
    for n in ns:
        for idxs in itertools.combinations(ns, n):
            yield [' '.join(words[i:j]) for i, j in zip((0,) + idxs, idxs + (None,))]

#compute the maximum meaningful characters ratio
@timeit
def get_features(domain, dgaflag):#meaningful_characters(domain):
#    domain = domain.encode('ascii', errors='ignore')
#    features = collections.namedtuple('Featrues', ['breakdowns_str', 'pattern_str','domain_length','mea_word_ratio_enchant','mea_char_ratio_enchant','mea_word_ratio_google','mea_char_ratio_google','total_pair_count','mea_pair_count','mean_pair_ratio', 'total_word_count','total_mea_word_count_enchant','total_mea_word_count_google', 'a', 'o', 'S', 'p', 'b', 'c', 'n', 'v', 'j', 'g', 'X', 'nn', 'gg', 'gn', 'ng', 'gs', 'Sg'])

    domain_length = float(len(domain))
    mea_word_count_enchant = 0
    mea_char_count_enchant = 0
    mea_word_count_google = 0
    mea_char_count_google = 0
    pattern_str = ''
    ratio = 0.0
    pairwise_score = -100.0
#    bigram_counts = bigram_counts
#    breakdowns = break_down(" ".join(domain))
    breakdowns = []
    breakdowns = ws.segment(domain)
#    breakdowns = segment(domain)
    if len(breakdowns) == 0:
        logging.error('{0} becomes empty. This should not occur to log'.format(domain))
#    print "breakdowns list is: {0}".format(breakdowns) 
    breakdowns_str = '/'.join(breakdowns)
#    print "breakdowns_str: {0}".format(breakdowns_str)


    for word in breakdowns:
        if word in unigram_corpus and len(word) != 1: 
            mea_word_count_google += 1
            mea_char_count_google += len(word)
        if len(word) != 1:
            if dic_us.check(word) or dic_us.check(word.capitalize()) or dic_gb.check(word):
                mea_word_count_enchant += 1
                mea_char_count_enchant += len(word)

        pattern_str += get_pattern(word)

    total_word_count = len(breakdowns)
    domain_length = domain_length
    breakdowns_str = breakdowns_str
    mea_word_ratio_enchant = round(float(mea_word_count_enchant)/len(breakdowns),3)
    mea_char_ratio_enchant = round(float(mea_char_count_enchant)/len(domain),3)
    mea_word_ratio_google = round(float(mea_word_count_google)/len(breakdowns),3)
    mea_char_ratio_google = round(float(mea_char_count_google)/len(domain),3)

    total_pair_count, mea_pair_count = _pairwise_check(breakdowns)
    if total_pair_count == 0:
        mean_pair_ratio = 0
    else:
        mean_pair_ratio = round(float(mea_pair_count)/float(total_pair_count), 3)
        
    
    a = pattern_str.count('a')
    o = pattern_str.count('o')
    S = pattern_str.count('S')
    p = pattern_str.count('p')
    b = pattern_str.count('b')
    c = pattern_str.count('c')
    n = pattern_str.count('n')
    v = pattern_str.count('v')
    j = pattern_str.count('j')
    g = pattern_str.count('g')
    X = pattern_str.count('X')
    
    bigram_result = []
    bigram_list = [ 'gn', 'gv', 'nv', 'gS', 'vn', 'ng', 'Sv', 'Sg', 'nS', 'vg']
    for each in bigram_list:
        bigram_result.append(_pattern_bigram(pattern_str, each))

#    perms = ['ao', 'aS', 'ap', 'ab', 'ac', 'an', 'av', 'aj', 'ag', 'aX', 'oa', 'oS', 'op', 'ob', 'oc', 'on', 'ov', 'oj', 'og', 'oX', 'Sa', 'So', 'Sp', 'Sb', 'Sc', 'Sn', 'Sv', 'Sj', 'Sg', 'SX', 'pa', 'po', 'pS', 'pb', 'pc', 'pn', 'pv', 'pj', 'pg', 'pX', 'ba', 'bo', 'bS', 'bp', 'bc', 'bn', 'bv', 'bj', 'bg', 'bX', 'ca', 'co', 'cS', 'cp', 'cb', 'cn', 'cv', 'cj', 'cg', 'cX', 'na', 'no', 'nS', 'np', 'nb', 'nc', 'nv', 'nj', 'ng', 'nX', 'va', 'vo', 'vS', 'vp', 'vb', 'vc', 'vn', 'vj', 'vg', 'vX', 'ja', 'jo', 'jS', 'jp', 'jb', 'jc', 'jn', 'jv', 'jg', 'jX', 'ga', 'go', 'gS', 'gp', 'gb', 'gc', 'gn', 'gv', 'gj', 'gX', 'Xa', 'Xo', 'XS', 'Xp', 'Xb', 'Xc', 'Xn', 'Xv', 'Xj', 'Xg']
    
#    bigram_count = []
#    for each in perms:
#       bigram_count.append(_pattern_bigram(pattern_str, each))

    f = [breakdowns_str, pattern_str,domain_length,mea_word_ratio_enchant,mea_char_ratio_enchant,mea_word_ratio_google, mea_char_ratio_google,total_pair_count, mea_pair_count, mean_pair_ratio,total_word_count, mea_word_count_enchant, mea_word_count_google, a, o, S, p, b, c, n, v, j, g, X]
    #f = [breakdowns_str, pattern_str,domain_length,mea_word_ratio_enchant,mea_char_ratio_enchant,mea_word_ratio_google, mea_char_ratio_google,total_pair_count, mea_pair_count, mean_pair_ratio,total_word_count, mea_word_count_enchant, mea_word_count_google, a, o, S, p, b, c, n, v, j, g, X]

#    print '[info]:domain %s has been broken into %s words. The meaningful score is %s. The pairwise meaningful score is %s\n' %(domain,str(len(breakdowns)), str(ratio), str(pairwise_score))

    return f + bigram_result


def _pattern_bigram(pattern_str,bigram):
    if len(pattern_str) == 1:
        return 0
    temp_list =  calc_ngram(pattern_str,2)
    temp_dic = {}
    for each in temp_list:
        temp_dic[each[0]] = each[1]
        if bigram in temp_dic:
            return temp_dic[bigram]
        else:
            return 0

def get_pattern(word):
    if word in articles:
        return 'a'
    elif word in pronouns:
        return 'o'
    elif len(word) == 1:
        return 'S'
    elif word in prepositions:
        return 'p'
    elif word in bes:
        return 'b'
    elif word in conjunctions:
        return 'c'
    elif word in verbs:
        return 'v'
    elif word in nouns:
        return 'n'

    elif word in adjs:
        return 'j'
    elif word in advs:
        return 'r'
    elif word in unigram_corpus:
        return 'g'
    else:
        return 'X'
        


def _ngrams(input, n):
  input = input.split(' ')
  output = []
  for i in range(len(input)-n+1):
    output.append(input[i:i+n])
  return output

#compute the emaningful pairwise score
def _pairwise_check(input_list):
    pair_string = ' '.join(input_list)#need change 
    pair_list = []
    pair_list = _ngrams(pair_string,2)
    count_meaningful_pair = 0
    count_pair = len(input_list) - 1

    for each in pair_list:
        prev = each[0]
        word = each[1]
        bigram = '{0} {1}'.format(prev, word)
        if bigram in bigram_corpus:
            count_meaningful_pair = count_meaningful_pair + 1

    return (count_pair, count_meaningful_pair)



#tld sessions
def get_domain(raw_url, dga_flag):
    try:
        tld = tldextract.extract(raw_url)
    except Exception  as e:
        with open('runtime_log.log','a') as f:
            f.write('tld module raised error: {0} for url {1}\n'.format(e, raw_url.encode('utf-8')))
        return ''
    
    domain = tld.domain
    subdomain = tld.subdomain
    if len(subdomain) > len(domain) and int(dga_flag) == 2:
        domain = subdomain
    

    #remove duplicated domain
#    if domain in domain_seen:
#        print "duplicated domain: {0} found \n".format(domain)
#        logging.debug('get_domain func raised info: {0} found in domain_seen {1} --> duplicated domain '.format(raw_url, domain))
#        return ''
#    else:
#        domain_seen.add(domain)

    #remove number(s) and hyphen(s) in domain
    domain = re.sub('[\d-]','',domain)
    domain = re.sub('[_.]','',domain)


    if len(domain) == 0:
        return ''
#        logging.warning('tld module raised warning: {0} --> empty domain '.format(raw_url))
        
    return domain



#pre-load the data
def parse_file(filename):
    """Read `filename` and parse tab-separated file of (word, count) pairs."""
    with open(filename) as fptr:
        lines = (line.split('\t') for line in fptr)

        return dict((word, float(number)) for word, number in lines)

def pattern_recognizing(x):
    return {
        'a': 1,
        'b': 2,
    }[x]

def create_lexicon():
    
    with open('../nltk/nouns.txt', 'r') as f:
        for line in f:
#            word = singularize(line.strip())
#            nouns.add(pluralize(word))
            nouns.add(line.strip())

    with open('../nltk/verbs.txt', 'r') as f:
        for line in f:
#            word = lemma(line.strip())
#            possible_forms = lexeme(word)
#            for each in possible_forms:
#                verbs.add(each)
            verbs.add(line.strip())
    with open('../nltk/adjs.txt', 'r') as f:
        for line in f:
            adjs.add(line.strip())
    with open('../nltk/advs.txt', 'r') as f:
        for line in f:
            advs.add(line.strip())
    return (nouns, verbs, adjs, advs)
            
def destributed_row_processing(line):
    url = re.match('(.*)[\t].*', line).group(1)
#    print "url is {0}\n".format(url)
    dga_flag = re.match('.*[\t](\d).*', line).group(1)
#    print "dga_flag is {0}\n".format(dga_flag)
    url = url.encode('ascii', errors='ignore')
    counter = 1
    try:
        domain = get_domain(url, dga_flag)
        if len(domain.strip()) == 0:
            return ''
    except Exception  as e:
        with open('runtime_log.log','a') as f:
            f.write('get_domain func raised error: {0} for url {1}\n'.format(e, url.encode('utf-8')))
#        logging.error('get_domain func raised error on {1}: {0}'.format(e, url.encode('utf-8')))
        return ''
    row = []
    
    try:
        f = d.feature_extract(domain)
#        f = get_features(domain, dga_flag)
    except Exception  as e:
        with open('runtime_log.log','a') as f:
            f.write('get_feature func raised error: {0} for domain {1}\n'.format(e, domain.encode('utf-8')))
#        logging.error('get_feature func raised error on {1}: {0}'.format(e, url.encode('utf-8').strip()))
        return ''


    time_cost = f[1]
#    if counter%5000 == 0:
#    print 'done! Sampled Cost: {0}s!\n'.format(f[1])
    if counter == 0:
            row.append('url')
            row.append('dga_flag')
            header = ['domain','family','breakdowns_str', 'pattern_str','domain_length','total_word_count', 'mea_word_count_enchant',
            'mea_word_ratio_enchant',
            'mea_char_ratio_enchant',
            'mea_word_count_google',
            'mea_word_ratio_google',
            'mea_char_ratio_google',
            'total_pair_count',
            'mea_pair_count',
            'mean_pair_ratio',
            'non_top_bigram_ratio','a', 'o', 'S', 'p', 'b', 'c', 'n', 'v', 'j', 'g', 'X']
            for i in xrange(len(header)):
                row.append(header[i])

    else:
#            if counter > 1000002 and counter <= 2000002 :
#                dga_flag = 1
#            elif counter > 2000002:
#                dga_flag = 2
#            else:
#        dga_flag = 0

        row.append(domain)
        row.append(dga_flag)
        row.append(f[2])
        row.append(f[1])
        for i in xrange(len(f[0])):
            row.append(f[0][i])
            
#    all.append(row)

    return row


#global_counter = 0

if __name__ == '__main__':
    #setting up logging

    open('runtime_log.log', 'a').close()
    open('performance_result.txt', 'w').close
    logging.basicConfig(filename='runtime_log.log',level=logging.ERROR)
    logging.debug('logging test: This debug message should go to the log file')
    logging.info('logging test: this info message should go to the log file')
    logging.warning('logging test: this warning message should go to the log file')
    logging.error('logging test: this error message should go to the log file')
    logging.debug('\n')
    logging.debug('\n')
    #preload the lexicons
    unigram_corpus = parse_file(join(dirname(realpath(__file__)), 'wordsegment_data', 'unigrams.txt'))
    bigram_corpus = parse_file(join(dirname(realpath(__file__)), 'wordsegment_data', 'bigrams.txt'))
    dic_us = enchant.Dict("en_US") #initial dictionary
    dic_gb = enchant.Dict("en_GB") #initial dictionary
    domain_seen = set() #to de-duplicate the same domain
    nouns = set()
    verbs = set()
    adjs = set()
    advs = set()
    nouns, verbs, adjs, advs = create_lexicon()
    print "creating lexicon...\n"
#    create_lexicon()
    print "lexicon created!\n"
    prepositions = ('aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'anti', 'around', 'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between', 'beyond', 'but', 'by', 'concerning', 'considering', 'despite', 'down', 'during', 'except', 'excepting', 'excluding', 'following', 'for', 'from', 'in', 'inside', 'into', 'like', 'minus', 'near', 'of', 'off', 'on', 'onto', 'opposite', 'outside', 'over', 'past', 'per', 'plus', 'regarding', 'round', 'save', 'since', 'than', 'through', 'to', 'toward', 'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within', 'without')
    pronouns = ('all', 'another', 'any', 'anybody', 'anyone', 'anything', 'both', 'each', 'each', 'other', 'either', 'everybody', 'everyone', 'everything', 'few', 'he', 'her', 'hers', 'herself', 'him', 'himself', 'his', 'i', 'it', 'its', 'itself', 'many', 'me', 'mine', 'more', 'most', 'much', 'myself', 'neither', 'no', 'one', 'nobody', 'none', 'nothing', 'one', 'one', 'another', 'other', 'others', 'ours', 'ourselves', 'several', 'she', 'some', 'somebody', 'someone', 'something', 'that', 'their', 'theirs', 'them', 'themselves', 'these', 'they', 'this', 'those', 'us', 'we', 'what', 'whatever', 'which', 'whichever', 'who', 'whoever', 'whom', 'whomever', 'whose', 'you', 'your', 'yours', 'yourself', 'yourselves')
    conjunctions = ('for', 'and', 'nor','but', 'or', 'yet', 'so', 'either','neither')
    articles = ('a', 'an', 'the')
    bes = ('be','were','being','is','am','are','was','been')


    pool = Pool(processes=7)
    all = []
#    global all
    ts = time.time()
    with open('dataset_4_families.txt','rb') as input_file:
      with open('dataset_4_families_google_off.csv', 'w') as csvoutput:
        counter = 0

        writer = csv.writer(csvoutput, lineterminator='\n')
#        rows = pool.map(destributed_row_processing,input_file)
        count = 0
        for each in input_file:
            count += 1
            if count > 0 and count < 10000:
                print destributed_row_processing(each)

#            if count > 2200000 and count  < 2200100:
#                print destributed_row_processing(each)
                
#            if count > 2400000 and count < 2400100:
#                print destributed_row_processing(each)
        '''
        header = ['domain','family','breakdowns_str', 'pattern_str','domain_length','total_word_count', 'mea_word_count_enchant',
            'mea_word_ratio_enchant',
            'mea_char_ratio_enchant',
            'mea_word_count_google',
            'mea_word_ratio_google',
            'mea_char_ratio_google',
            'total_pair_count',
            'mea_pair_count',
            'mean_pair_ratio',
            'non_top_bigram_ratio','a', 'o', 'S', 'p', 'b', 'c', 'n', 'v', 'j', 'g', 'X']
        '''

#        all.append(header)
#        for each in rows:
#            if len(each) == 0:
#                continue
#            else:
#                all.append(each)
        
        
#        writer.writerows(all)
    te = time.time()

    logging.error('Time_Record: {0} mins\n'.format((te-ts)/60))

