# -*- coding: utf-8 -*-

"""
English Word Heuristical Segmentation tool in Python

Heuristical Word Finding is the process of find meaningful word(s), which
contains at least N characters(len(word)>=N), from a string.

It provides one public interface -- "segment".
The interface takes a string as input,
returns a list of "words" as output.

>>> from wordsegment import WordSegment
>>> ws = WordSegment()
#or enbale the google corpus   >>> ws = WordSegment(use_google_corpus=True)
>>> ws.segment('facebookingirl')
['facebook', 'in', 'girl']

##################
Segmentation Logic

The algorithm takes the following step to do the segmentation.
Let's use this example input,
>>> ws.segment('facebook72847helloworld')
['facebook', '72847', 'hello', 'world']

1.the first step is to find all meaningful words(len>=2) from the input string.
  in the example, the meaningful words are
  "face, facebook, ace, boo, book, ok, hell, hello, low, world"

2.then it creates a graph for the input string, and add all possible meaningful
  words as nodes into the graph. each node is with the position of the word,
  for example, a node is in form of struct like this ((0,4), 'face')

3.for each node, the algorithm will find whether node intersects other, in terms of position.
  If intersects, add edge between the two nodes.
  for example, node ((0,4), 'face') intersects ((1,4), 'ace'), so they are linked.

4.now the graph contains many components. in the example,
  the components are "face, ace, facebook, ace, boo, book, ok", "hell, hello, low, world"

5.segmentation algorithem will make decision on component-level.
  for example, for component "face, ace, facebook, ace, boo, book, ok",
  should we segment it as ['face', 'book'], or ['facebook'], or even
  ['ace', 'book']? word-level unigram corpus from Google trillion corpus is used to do the scoring.

6.after each component-level segmentation is made, we glue the component-level output with
  non-meaningful characters in original string.
  in our example, the non-meaningful characters are "72847"

7.finally, the interace returns a list of segmentation. in our example, it is
  ['facebook', '72847', 'hello', 'world']

################
Pros and Cons,
comparing with open-source segment tool https://pypi.python.org/pypi/wordsegment/0.6.1
I would refer this segmentation tool to as "old algorithm".

1. more accurate when handling long urls.
As shown below, the upper result what the old algorithm produces,
it missed some very obvious words because of algorithm defects.

>>> segment('sdfjqueueuhfgqerfhwqasfhelloworldsjdiofjqrjfoqerkf')
['sdfjqueueuhfgqerfhwqasf', 'helloworld', 'sjdiofjqrjfoqerkf']

>>> ws.segment('sdfjqueueuhfgqerfhwqasfhelloworldsjdiofjqrjfoqerkf')
['sdfj', 'queue', 'uhf', 'gqerfhwq', 'as', 'f', 'hello', 'worlds', 'jdi', 'of', 'jqrjfoqerkf']


another example could be

The upper  algorithm fails to deal with string like above,
while our algorithm could handle it properly.

>>> segment('xkkopahelloworld43576983456')
['x', 'kk', 'opahelloworld43576983456']

>>> ws.segment('xkkopahelloworld43576983456')
['xkkopa', 'hello', 'world', '43576983456']


2. new algorithm will not prefer small fractions.

As shown below, the old algorithm produces some meaningfulless fractions,

the new algorithm does not.

>>> segment('fjfgjsddevelopers')
['fj', 'fg', 'jsd', 'developers']

>>> ws.segment('fjfgjsddevelopers')
['fjfgjsd', 'developers']


##################################
Performance for the new algorithm.
Performance test showed that the new algorithm is slightly slower than
the old one, but remains in the same level

****below are perf test result for new algorithm****.
Alexa Mean(out of top 1 million): 0.00344653956482 s
Alexa Median: 0.0026 s
Alexa Standard Deviation: 0.00414564042867

F1(Family 1, 1 million) Mean: 0.012299464851 s
F1 Median: 0.0089 s
F1 Standard Deviation: 0.026318170557

F2 Mean(out of 200k): 0.00800411521876 s
F2 Median: 0.0059 s
F2 Standard Deviation: 0.0159249383211

****below are perf test result for old algorithm****.
Alexa Mean: 0.00156934240115 s
Alexa Median: 0.0009 s
Alexa Standard Deviation: 0.00379112385851

F1 Mean: 0.0086756611575 s
F1 Median: 0.0067 s
F1 Standard Deviation: 0.0192146079067

F2 Mean: 0.00403571021107 s
F2 Median: 0.003 s
F2 Standard Deviation: 0.0130515844687

##################################
In the code, a modified version of  corpus containing 1024908267229 total
number of words is used.
I've truncated the corpus by removing all non-dictionary words.
The dictionary I used to truncate it is Python Enchant Dictionary.
So any word found in the truncated corpus will be deemed as meaningful.
The probability of words in the corpus is used to achieve the "heuristic"
The search will start from the most popular words to make it
terminate earlier.

The original version of the corpus  may be found at
http://norvig.com/ngrams/ under the name count_1w.txt.

# Copyright (c) 2015 by Niara

Original corpus is from the chapter "Natural Language Corpus Data"
from the book "Beautiful Data" (Segaran and Hammerbacher, 2009)
http://oreilly.com/catalog/9780596157111/

Original Copyright (c) 2008-2009 by Peter Norvig
"""

import sys
from os.path import join, dirname, realpath
from itertools import groupby
import networkx as nx
from itertools import groupby, count
from math import log10
from functools import wraps
import inspect

if sys.hexversion < 0x03000000:
    range = xrange

def parse_file(filename):
    '''
    Global function that parses file and form a dictionary.
    '''
    with open(filename) as fptr:
        lines = (line.split('\t') for line in fptr)
        return dict((word, float(number)) for word, number in lines)

UNIGRAM_COUNTS = parse_file(join(dirname(realpath(__file__)), 'corpus', 'unigrams.txt'))

def as_range(group):
    '''
    Global function returns range
    '''
    tmp_lst = list(group)
    return tmp_lst[0], tmp_lst[-1]

class Data(object):
    '''
    Read corpus from path, and provide the following functionalities,
    1. data as "property", it is a dictionary where key is word,
       while the value is the frequency count of this word.
    2. generator that yield word and its frequency
    '''
    def __init__(self, use_google_corpus):
        self._unigram_counts = dict()
        self._use_google_corpus = use_google_corpus
        if self._use_google_corpus:
            #use pure google corpus
            self._unigram_counts = parse_file(
                join(dirname(realpath(__file__)), 'corpus', 'filtered_1_2_letter_only.txt')
            )
        else:
            #use dictionary-filtered google corpus
            self._unigram_counts = parse_file(
                join(dirname(realpath(__file__)), 'corpus', 'unigrams.txt')
            )

    @property
    def data(self):
        '''
        return the whole dictionary out to user as a property.
        '''
        return self._unigram_counts

    def __iter__(self):
        for each in self._unigram_counts.keys():
            yield each

class ConstructCorpus(object):
    '''
    according to the minimal character limit,
    construct a corpus at initial time.
    it provides the following two properties,
    1. ngram_distribution -- a dictionary where key is the ngram,
       value is an int of summation of frequency of each English
       word starts with that specific ngram.
    2. ngram_tree -- a dictionary where key is the ngram,
       value is a list containing all possile English word
       starts with that specific ngram.
    '''
    def __init__(self, min_length, use_google_corpus):
        self._minlen = min_length
        self._use_google_corpus = use_google_corpus

    @property
    def ngram_distribution(self):
        '''
        return a dictionary containing the following pairs,
        key: ngram string, for example, when minlen=5,
             the ngram string for word "university" is "unive".
        value: added-up frequency(from google corpus) of all
               words starting with "unive".
        '''
        ngram_distribution = dict()
        instance_d = Data(self._use_google_corpus)
        data = instance_d.data
        for entry in instance_d:
            if len(entry) >= self._minlen:
                cut = entry[:self._minlen]
                if cut in ngram_distribution:
                    ngram_distribution[cut] += data[entry]
                else:
                    ngram_distribution[cut] = data[entry]

        return ngram_distribution

    @property
    def ngram_tree(self):
        '''
        return a dictionary containing the following pairs,
        key: ngram string, for example, when minlen=5,
             the ngram string for word "university" is "unive".
        value: all words starting with the ngram,
               in the example, it is "unive".
        '''
        ngram_tree = dict()
        instance_d = Data(self._use_google_corpus)
        for entry in instance_d:
            if len(entry) >= self._minlen:
                cut = entry[:self._minlen]
                if cut in ngram_tree:
                    ngram_tree[cut].append(entry)
                else:
                    ngram_tree[cut] = [entry]

        return ngram_tree

class key_memoized(object):
    def __init__(self, func):
       self.func = func
       self.cache = {}


    def __call__(self, *args, **kwargs):
#        print "CHECK: kwargs.items(): {}".format(kwargs.items())
#        print "CHECK: args: {}".format(args)
        key = self.key(args, kwargs)
#        print "key is: {}".format(key)
        for each in kwargs.items():
            if isinstance(each[1], list):
                if len(each[1]) > 1:
#                    print "QUIT*******************"
                    return self.func(*args, **kwargs)
        if key not in self.cache:
#            print "key not in self.cache***********"
            self.cache[key] = self.func(*args, **kwargs)
#            print "self.cache: {}".format(self.cache)
            return self.cache[key]
        else:
#            print "Result from Momery*********"
#            print "self.cache: {}".format(self.cache)
            return self.cache[key]

    def normalize_args(self, args, kwargs):
        spec = inspect.getargs(self.func.__code__).args
#        print "kwargs.items(): {}".format(kwargs.items())
        new_kwargs = []
        for each in kwargs.items():
            tmp_lst = []
#            print "working on each {0}, of type {1}".format(each, type(each))
            for e in each:
                if isinstance(e, list):
                    new_e = tuple(e)
                    tmp_lst.append(new_e)
#                    print "appended {}".format(new_e)
                    continue
                tmp_lst.append(e)
#                print "appended {}".format(e)
            new_kwargs.append(tuple(tmp_lst))
        
#        print "After tupling, kwargs.items(): {}".format(new_kwargs)
#        print "dict(new_kwargs + zip(spec, args)): {}".format(dict(new_kwargs + zip(spec, args)))
        return dict(new_kwargs + zip(spec, args))

    def key(self, args, kwargs):
        
        a = self.normalize_args(args, kwargs)
        return tuple(sorted(a.items()))


class WordSegment(object):
    '''
    class that provides the following two fuctions,
    1. Finds whether a string contains any meaningful word,
       that is more than <minimal length> characters.
       If found, return True.
    2. Finds all meaningful words in a string.
    '''

    def __init__(self, min_length=2, casesensitive=False, use_google_corpus=False):
        self._minlen = min_length
        self._string = ''
        self._use_google_corpus = use_google_corpus
        self._casesensitive = casesensitive
        corpus = ConstructCorpus(self._minlen, self._use_google_corpus)
        self.ngram_distribution = corpus.ngram_distribution
        self.ngram_tree = corpus.ngram_tree

    def _divide(self):
        """
        Iterator finds ngrams(with its position in string) and their suffix.
        An example input of string "helloworld" yields the following tuples,
        (('hello',(0,5)), 'world')
        (('ellow',(1,6)), 'orld')
        (('llowo',(2,7)), 'rld')
        (('lowor',(3,8)), 'ld')
        (('oworl',(4,9)), 'd')
        (('world',(5,10)), '')
        """
        counter = 0
        for cut_point in range(self._minlen, len(self._string)+1):
            yield (
                (self._string[counter:cut_point], (counter, counter+self._minlen)),
                self._string[cut_point:]
                )
            counter += 1

    def _intersect(self, tuple_0, tuple_1):
        '''
        finds intersection of two words
        '''
        word1 = range(tuple_0[0], tuple_0[1])
        word2 = range(tuple_1[0], tuple_1[1])
        tmp_xs = set(word1)
        return tmp_xs.intersection(word2)

    def _connected_components(self, neighbors):
        '''
        finds connected components
        '''
        seen = set()
        def component(node):
            nodes = set([node])
            while nodes:
                node = nodes.pop()
                seen.add(node)
                nodes |= neighbors[node] - seen
            yield node
        for node in neighbors:
            if node not in seen:
                yield component(node)

    def _init_graph(self, meaningful_words):
        '''
        Create graph for each requesting string
        #An example input is a list like this:
        [((0, 3),"face"), ((0, 7),"facebook"),((1, 3),"ace"), ((4, 6),"boo"),
        ((4, 7),"book"), ((6, 7), "ok"), ((8, 19),"anotherword")]
        '''
        G = nx.Graph()
        G.add_nodes_from(meaningful_words)
        for each in meaningful_words:
            for each_2 in meaningful_words:
                if each == each_2:
                    continue
                elif self._intersect(each[0], each_2[0]):
                    if (each[0], each_2[0]) in G.edges():
                        continue
                    else:
                        G.add_edge(each, each_2)
        return G

    def _score_by_len(self, lst):
        """
        Score a nodes by how 'full' they occupy the whole string.
        Input is a list
        Output is a float score
        """
        words = []
        score = 0
        if isinstance(lst, tuple):
            words = [lst[1]]
        else:
            for each in lst:
                words.append(each[1])

        for word in words:
            if word in UNIGRAM_COUNTS:
                score = score + len(word)
            else:
                score = score + len(word)

        return score


    def score(self, lst):
        """
        Score a nodes by how 'frequently' they appears in Google trillion corpus
        Input is a list
        Output is a float score
        """
        words = []
        score = 0
        for each in lst:
            words.append(each[1])

        for word in words:
            if word in UNIGRAM_COUNTS:
                score = score + log10((UNIGRAM_COUNTS[word] / 1024908267229.0))
            else:
                score = score +  log10((10.0 / (1024908267229.0 * 10 ** len(word))))

        return score


    def _max(self, lst):
        '''
        Finding max without penalizing the non-meaningful words
        '''
        tmp_lst = []
        for each in lst:
            tmp_lst.append(each[0])

        max_score = max(tmp_lst)

        winners = []
        for each in lst:
            if each[0] == max_score:
                winners.append((self.score(each[1]), each[0], each[1]))
        return (max(winners)[1], max(winners)[2])

    def _max_2(self, lst, start_pos, end_pos):
        '''
        Finding max  with penalizing the non-meaningful words
        '''
        tmp_lst = []
        for each in lst:
            tmp_lst.append(each[0])

        winners = []
        for each in lst:
            winners.append(
                (
                    self.score(each[1]) + self._penalize(each[1], start_pos, end_pos),
                    each[0],
                    each[1]
                    )
                )

        return (max(winners)[1], max(winners)[2])



    def _find_components(self, meaningful_words):
        '''
        function that finds the components in the graph.
        each component represents overlaping words
        for example, in the example below, except the word "anotherword",
        all rest words have at least one character contained in other words.
        They will become one component in the who string-level graph

        Example input is a list like this: [((0, 3),"face"), ((0, 7),"facebook"), ((1, 3),"ace"),
        ((4, 6),"boo"), ((4, 7),"book"), ((6, 7), "ok"), ((8, 19),"anotherword")]
        '''
        G = nx.Graph()
        G = self._init_graph(meaningful_words)
        components = []
        components = list(nx.connected_component_subgraphs(G))
        return components

    def _penalize(self, lst, start_pos, end_pos):
        '''
        function that penalizes the non-meaningful intervals
        '''
        #(0.00011509110207386408, [((1, 3), 'ac'), ((7, 11), 'king')])
        #(-8.483260969067402, [((1, 3), 'ac'), ((7, 11), 'king'), ((11, 13), 'ir')])
        if not lst[0][0][0] - start_pos == 0:
            starting_pos_penalty = log10(
                10.0 / (1024908267229.0 * 10 ** (lst[0][0][0] - start_pos))
                )
        else:
            starting_pos_penalty = 0

        if not end_pos - lst[-1][0][1] == 0:
            ending_pos_penalty = log10(10.0 / (1024908267229.0 * 10 ** (end_pos - lst[-1][0][1])))
        else:
            ending_pos_penalty = 0

        interval_penalty = [0]
        node_count = len(lst)
        for i in xrange(node_count-1):
            if not lst[i+1][0][0] - lst[i][0][1] == 0:
                interval_penalty.append(
                    log10(10.0 / (1024908267229.0 * 10 ** (lst[i+1][0][0] - lst[i][0][1])))
                    )
        return sum(interval_penalty) + starting_pos_penalty + ending_pos_penalty

    def _component_optimizing(self, component):
        '''
        function that makes decision which words combination is the optimal one.
        for example, the component in the example below, what is the optimal word combination?
        "facebook"?
        or "face" + "book"?
        or even, "ace" + "book"
        This function will give an answer.
        example input is like: [((0, 3),"face"), ((0, 7),"facebook"), ((1, 3),"ace"),
        ((4, 6),"boo"), ((4, 7),"book"), ((6, 7), "ok")]
        '''

        start_pos_lst = []
        end_pos_lst = []
        segment_word_lst = []
        for each in component:
            start_pos_lst.append(each[0][0])
            end_pos_lst.append(each[0][1])
        start_pos = min(start_pos_lst)
        end_pos = max(end_pos_lst)
        #if the component contains only one word
        if len(component) == 1:
            return ((start_pos, end_pos), [component.nodes()[0][1]])

        candidate_list = []
        candidate_list = self._optimizing(component)
        
        
#        for each in candidate_list:
#            print "candidate_list has: {}".format(each)
#            print "candidate_list's first element is : {}".format(each[0])

        scored_candidate_list = []
        for each in candidate_list:
            scored_candidate_list.append(self._segment(each))

        scored_candidate_list.sort(reverse=True)
        max_3_list = scored_candidate_list[:3]
        max_result = []
        max_result = self._max_2(max_3_list, start_pos, end_pos)
        for each in max_result[1]:
            segment_word_lst.append(each[1])
        start_pos = max_result[1][0][0][0]
        end_pos = max_result[1][-1][0][1]
        return ((start_pos, end_pos), segment_word_lst)


    def _segment(self, lst):
        """return a list of words that is the best segmentation of 'text'"""
        def search(lst):
            '''
            recursive call
            '''
            flag = "ALL_NON_LIST"
            if len(lst) == 1 and not isinstance(lst[0], list):
                return (self._score_by_len(lst), lst)
            for each in lst:
                if isinstance(each, list):
                    flag = "LIST_FOUND"
            if flag == "ALL_NON_LIST":
                return (self._score_by_len(lst), lst)

            def candidates():
                leading_word = lst[0]
                suffix_words = lst[1:][0]
                dedup_suffix_words = []
                for i in suffix_words:
                    if i not in dedup_suffix_words:
                        dedup_suffix_words.append(i)

                leading_score = self._score_by_len(leading_word)
                for each in dedup_suffix_words:
                    suffix_score, suffix_list = search(each)
                    yield (leading_score + suffix_score, [leading_word] + suffix_list)

            return self._max(list(candidates()))

        return search(lst)


    def _optimizing(self, component):
        if True:
            nodes = component.nodes() #initially nodes = all nodes in component
#            print "nodes are: {}".format(nodes)
            starting_words = []
            min_node = min(nodes)
            min_pos = min_node[0][0]
            starting_words = []
            for each in nodes:
                if each[0][0] == min_pos:
                    starting_words.append(each)

            tmp_lst = []
            for each in starting_words:
                tmp_lst.append(each[0][1])
            max_pos = max(tmp_lst)
            starting_words = []
            for each in nodes:
                if each[0][0] <= max_pos:
                    starting_words.append(each)
#            print "starting words are: {}".format(starting_words)
            nodes = starting_words
            nodes.sort()



            @key_memoized
            def search(component, nodes=nodes, node=nodes[0], flag='init'):
                if not nx.non_neighbors(component, node) and flag != 'init':
#                    print "no neighbor found for node: {}".format([node])
                    return node

                elif nx.non_neighbors(component, node) and flag != 'init':
                    #only look at word forwad
                    flag = "HASNOT"
                    for each in nx.non_neighbors(component, node):

                        if each[0][0] > node[0][0]:
                            #if non_neighbor has forward neighbors
                            #keep the flag
                            flag = "HAS"
                            break
                        else:
                            #all non_neighbors are in front of the node
                            pass

                    if flag == "HASNOT":
#                        print "no forward neighbor folloing node: {}".format([node])
                        #means no forward neighbor found
                        return node
                    else:
                        #means it has non_neighbor following it
                        pass

                def candidates():
                    for node in nodes:
#                        print "working on node: {}".format(node)
                        if list(nx.non_neighbors(component, node)) != []:
                            for each_non_neighbor in nx.non_neighbors(component, node):
                                candidate_nodes = [node]
#                                print "candidate_nodes are {}".format(candidate_nodes)
#                                print "and the each_non_neighbor is {}".format(each_non_neighbor)
                                if each_non_neighbor[0][0] == node[0][1]:
#                                    print "position adhered each_non_neighbor found: {0} of node {1}\n".format(each_non_neighbor,node)
                                    candidate_nodes.append(
                                        search(
                                            component, nodes=[each_non_neighbor],    #DP remembers this list
                                            node=each_non_neighbor, flag=''
                                            )
                                        )

                                yield candidate_nodes

                        else:
                            #NO NEIGHBOR WORD
                            candidate_nodes = [node]
                            yield candidate_nodes

                tmp_lst = list(candidates())
                
                s = []
                for i in tmp_lst:
                    if i not in s:
                        s.append(i)

                return s

            optimized_words = search(component) 
            
#            print "optimized_words is {}\n".format(optimized_words)
            #dedup
            s = []
            for i in optimized_words:
                if i not in s:
                    s.append(i)
#        print "s is {}".format(s)
#        for each in s:
#            print '\n' 
#            print each

        return s


    #public interface
    def segment(self, text):
        '''
        Public interface for user to find all meaningful words in a string.
        Input: string
        Return: a set of meaningful English words found
        '''
        if self._casesensitive == False:
            self._string = text.lower()
            self._string = self._string.strip("'")
        else:
            #for current version, only supports lowercase version
            pass

        candidate_list = []
        pair_dic = dict()
        for prefix, suffix in self._divide():
            pair_dic[prefix] = suffix
            if prefix[0] in self.ngram_distribution:
                candidate_list.append(
                    (self.ngram_distribution[prefix[0]], prefix)
                )
            else:
                #means this prefix was not likely
                #to be a part of meaningful word
                pass

        candidate_list.sort(reverse=True)
        #now candidate list is [(2345234, ("hello",(0,5)))]
        meaningful_words = []
        #meaningful_words is [((0, 10),"helloworld"),...]
        for each in candidate_list:
            #(17507324569.0, ('in', (8, 10)))
            for word in self.ngram_tree[each[1][0]]:
                if word in each[1][0] + pair_dic[each[1]]:
                    if self._string[each[1][1][0]:each[1][1][0]+len(word)] == word:
                        meaningful_words.append(((each[1][1][0], each[1][1][0]+len(word)), word))
        #sort the list in order of position in original text
        meaningful_words.sort()
        #the sorted list is [((0,5), "hello"),((0,10), "helloword"),...]
        components = []
        components = self._find_components(meaningful_words)

        for each in components:
            temp_lst = each.nodes()
            temp_lst.sort()

        post_components = []
        for each in components:
            post_components.append(self._component_optimizing(each))

        meaningful_pos_lst = []
        for each in post_components:
            meaningful_pos_lst += range(each[0][0], each[0][1])

        non_meaning_pos_lst = []
        for pos in xrange(len(self._string)):
            if pos in meaningful_pos_lst:
                continue
            else:
                non_meaning_pos_lst.append(pos)

        non_meaningful_range = []
        non_meaningful_range = [
            as_range(g) for _, g in groupby(non_meaning_pos_lst, key=lambda n, c=count(): n-next(c))
            ]

        meaningful_dic = dict()

        overall_pos_lst = []
        for each in non_meaningful_range:
            overall_pos_lst.append(each)
        for component in post_components:
            overall_pos_lst.append(component[0])
            meaningful_dic[component[0]] = component[1]

        overall_pos_lst.sort()
        return_lst = []
        for each in overall_pos_lst:
            if each in meaningful_dic:
                return_lst.extend(meaningful_dic[each])
            else:
                return_lst.append(self._string[each[0]:each[1]+1])

        #print "RESULT: {}\n".format(return_lst)
        return return_lst


__title__ = 'English Word Segmentation Tool'
__version__ = '0.1'
__build__ = 0x0003
__author__ = 'Weihan Jiang'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright (c) 2015 Niara Inc'
