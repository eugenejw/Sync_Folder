# -*- coding: utf-8 -*-
# vim:set ts=4 sw=4 tw=79 expandtab:
'''
Copyright (C) 2013-2014 by Niara, Inc.
All Rights Reserved.

This software is an unpublished work and is protected by copyright and
trade secret law.  Unauthorized copying, redistribution or other use of
this work is prohibited.

The above notice of copyright on this source code product does not indicate
any actual or intended publication of such source code.
'''
# pylint: disable=W1202, C0330, E0611, F0401, W0640, E1101
# logging-format-interpolation, bad-continuation, no-name-in-module,
# import-error, cell-var-from-loop, no-member


import re
import enchant
from pyngram import calc_ngram
from wordsegment import WordSegment
ws_google = WordSegment(use_google_corpus=True)
ws = WordSegment()
#from wordsegment import segment
import cPickle as pickle
#from niara.common.util import whitelist


UNIGRAM_CORPUS_PATH =\
    '../dict_dga/unigrams.txt'
BIGRAM_CORPUS_PATH =\
    '../dict_dga/bigrams.txt'
CLASSIFIER_PATH =\
    '../dict_dga/dict_dga_dt_1.0.pkl'


PREPOSITIONS = ('aboard', 'about', 'above', 'across', 'after', 'against',
'along', 'amid', 'among', 'anti', 'around', 'as', 'at', 'before', 'behind',
'below', 'beneath', 'beside', 'besides', 'between', 'beyond', 'but', 'by',
'concerning', 'considering', 'despite', 'down', 'during', 'except', 'excepting',
'excluding', 'following', 'for', 'from', 'in', 'inside', 'into', 'like',
'minus', 'near', 'of', 'off', 'on', 'onto', 'opposite', 'outside', 'over',
'past', 'per', 'plus', 'regarding', 'round', 'save', 'since', 'than', 'through',
'to', 'toward', 'towards', 'under', 'underneath', 'unlike', 'until', 'up',
'upon', 'versus', 'via', 'with', 'within', 'without')

PRONOUNS = ('all', 'another', 'any', 'anybody', 'anyone', 'anything', 'both',
'each', 'each', 'other', 'either', 'everybody', 'everyone', 'everything',
'few', 'he', 'her', 'hers', 'herself', 'him', 'himself', 'his', 'i', 'it',
'its', 'itself', 'many', 'me', 'mine', 'more', 'most', 'much', 'myself',
'neither', 'no', 'one', 'nobody', 'none', 'nothing', 'one', 'one', 'another',
'other', 'others', 'ours', 'ourselves', 'several', 'she', 'some', 'somebody',
'someone', 'something', 'that', 'their', 'theirs', 'them', 'themselves',
'these', 'they', 'this', 'those', 'us', 'we', 'what', 'whatever', 'which',
'whichever', 'who', 'whoever', 'whom', 'whomever', 'whose', 'you', 'your',
'yours', 'yourself', 'yourselves')

CONJUNCTIONS = ('for', 'and', 'nor', 'but', 'or', 'yet', 'so', 'either',
'neither')

ARTICLES = ('a', 'an', 'the')

BES = ('be', 'were', 'being', 'is', 'am', 'are', 'was', 'been')

NOUNS = set()
with open(
    '/usr/local/share/niara/mr-units-py/data/dict_dga/nouns.txt', 'r') as f:
    for line in f:
        NOUNS.add(line.strip())

VERBS = set()
with open(
    '/usr/local/share/niara/mr-units-py/data/dict_dga/verbs.txt', 'r') as f:
    for line in f:
        VERBS.add(line.strip())

ADJS = set()
with open(
    '/usr/local/share/niara/mr-units-py/data/dict_dga/adjs.txt', 'r') as f:
    for line in f:
        ADJS.add(line.strip())

ADVS = set()
with open(
    '/usr/local/share/niara/mr-units-py/data/dict_dga/advs.txt', 'r') as f:
    for line in f:
        ADVS.add(line.strip())


def parse_file(filename):
    """Read `filename` and parse tab-separated file of (word, count) pairs
    """

    with open(filename) as fptr:
        lines = (line.split('\t') for line in fptr)
        return dict((word, float(number)) for word, number in lines)


class DictDGAClassifier(object):

    """ Main class for dictionary DGA classification
    """

    def __init__(self):
        self.dict_us = enchant.Dict("en_US")
        self.dict_gb = enchant.Dict("en_GB")
        self.bigram_corpus = parse_file(BIGRAM_CORPUS_PATH)
        self.unigram_corpus = parse_file(UNIGRAM_CORPUS_PATH)
        with open(CLASSIFIER_PATH, 'rb') as ifile:
            self.clf = pickle.load(ifile)

    @staticmethod
    def _count_bigram(pattern_str, bigram):
        """Function that counts how many times the given bigram appears
        """

        if len(pattern_str) == 1:
            return 0
        temp_list = calc_ngram(pattern_str, 2)
        temp_dic = {}
        for each in temp_list:
            temp_dic[each[0]] = each[1]
            if bigram in temp_dic:
                return temp_dic[bigram]
            else:
                return 0


    def pairwise_check(self, input_list):
        """Function that do a corpus look-up to check whether the bigram pair of
        the list appears in bi-gram corpus.
        if found, means the pair of words is meaningful
        """

        pair_list = []

        for i in xrange(len(input_list) - 1):
            pair_list.append(input_list[i:i+2])

        count_meaningful_pair = 0
        count_pair = len(input_list) - 1

        for pair in pair_list:
            if ' '.join(pair) in self.bigram_corpus:
                count_meaningful_pair += 1

        return (count_pair, count_meaningful_pair)


    def get_pattern(self, word):
        """Function that label a given word with word-type
        Lazily calling this function could improve performance
        """

        if word in ARTICLES:
            return 'a'
        elif word in PRONOUNS:
            return 'o'
        elif len(word) == 1:
            return 'S'
        elif word in NOUNS:
            return 'n'
        elif word in PREPOSITIONS:
            return 'p'
        elif word in BES:
            return 'b'
        elif word in CONJUNCTIONS:
            return 'c'
        elif word in VERBS:
            return 'v'
        elif word in ADJS:
            return 'j'
        elif word in ADVS:
            return 'r'
        elif word in self.unigram_corpus:
            return 'g'
        else:
            return 'X'

    def feature_extract(self, dname):
        """Function take domain name, and return a list of feature vectors.
        the feature vectors will be used to feed the classifier.

        The following three levels of features will be extracted from domain name.

            - url-level features
              for example, domain length
            - meaningfulness-level features
              for example, how many meaningful word this url contains
            - part-of-speech level features
              for example, how many nouns found in the domain

        :param dname: str, domain name
        :return a list of features
        """

        domain = re.sub('[-_\d]', '', dname)
        if len(domain) == 0:
            return None, None, None

        domain_length = float(len(domain))
        mea_word_count_enchant = 0
        mea_char_count_enchant = 0
        mea_word_count_google = 0
        mea_char_count_google = 0
        pattern_str = ''
        breakdowns = []

        # Doing word segmenting for domain
        # it yields optimal words from domain
#        '''
        if len(domain) > 12:
            breakdowns = ws.segment(domain)
        else:
            breakdowns = ws_google.segment(domain)
#        '''
#        breakdowns = ws_google.segment(domain)
#        breakdowns = segment(domain)

        #for each word that has been segmented
        #check its part-of-speech type and meaningfulness
        for word in breakdowns:
            #checking the part-of-speech type
            pattern_str += self.get_pattern(word)
            #checking its meaningfulness
            #note that single character will not be treated as meaningful
            if len(word) != 1:
                if word in self.unigram_corpus:
                    mea_word_count_google += 1
                    mea_char_count_google += len(word)
                if self.dict_us.check(word) or self.dict_us.check(word.capitalize())\
                    or self.dict_gb.check(word):
                    mea_word_count_enchant += 1
                    mea_char_count_enchant += len(word)

        total_word_count = len(breakdowns)
        mea_word_ratio_enchant = round(
            float(mea_word_count_enchant)/len(breakdowns), 3)
        mea_char_ratio_enchant = round(
            float(mea_char_count_enchant)/len(domain), 3)
        mea_word_ratio_google = round(
            float(mea_word_count_google)/len(breakdowns), 3)
        mea_char_ratio_google = round(
            float(mea_char_count_google)/len(domain), 3)

        #Getting pair-wise features
        total_pair_count, mea_pair_count = self.pairwise_check(breakdowns)
        if total_pair_count == 0:
            mean_pair_ratio = 0
        else:
            mean_pair_ratio = round(
                float(mea_pair_count)/float(total_pair_count), 3)

        #Getting word type features
        word_type_result = []
        for each in ('a', 'o', 'S', 'p', 'b', 'c', 'n', 'v', 'j', 'g', 'X'):
            word_type_result.append(
                pattern_str.count(each) / float(total_word_count))

        #top-10 pattern bigram
        bigram_list = ['nn', 'ng', 'gn', 'gg', 'Sn', 'SS', 'gS', 'Sg', 'nS',
            'on', 'pn', 'an', 'go', 'no', 'np', 'jn', 'og', 'ga', 'na', 'gp']

        non_top_bigram_count = 0
        for i in xrange(len(pattern_str) - 1):
            if pattern_str[i:i+2] not in bigram_list:
                non_top_bigram_count += 1
        if len(pattern_str) == 1:
            non_top_bigram_ratio = 0.0
        else:
            non_top_bigram_ratio =\
                float(non_top_bigram_count) / (len(pattern_str) - 1)

        feature_vector = [
            domain_length,
            total_word_count,
            mea_word_count_enchant,
            mea_word_ratio_enchant,
            mea_char_ratio_enchant,
            mea_word_count_google,
            mea_word_ratio_google,
            mea_char_ratio_google,
            total_pair_count,
            mea_pair_count,
            mean_pair_ratio,
            non_top_bigram_ratio
            ]

        feature_vector += word_type_result
        return feature_vector, pattern_str, '|'.join(breakdowns)


    def dict_dga_classifier(self, tld_domain):
        """Decision Tree Classifier

        :param tld_domain: Domain name in TLD extract format
        :return: probability of being a dict DGA
        """

        if tld_domain.domain and len(tld_domain.domain) > 1 and\
            tld_domain.suffix != 'in-addr.arpa' and\
            tld_domain.suffix != 'ip6.arpa':
            if True != True:
                #whitelist('.'.join([tld_domain.domain, tld_domain.suffix])):
                return (0.0, tld_domain.suffix, [])
            else:
                feature_vector = self.feature_extract(tld_domain.domain)[0]
                if feature_vector is not None:
                    classification = self.clf.predict_proba(feature_vector)
                    return (classification[0][1], tld_domain.suffix, feature_vector)
                else:
                    return (0.0, tld_domain.suffix, [])
        else:
            return (0.0, tld_domain.suffix, [])
