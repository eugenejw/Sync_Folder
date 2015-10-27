from nltk.corpus import wordnet as wn
import re
from pattern.en import pluralize, singularize
from pattern.en import conjugate, lemma, lexeme


counter = 0
word_seen = set()
with open('verbs.txt','w') as f:

    for synset in list(wn.all_synsets('v')):
        counter += 1
#        if counter > 20000:
#            break
        try:
#            print 'working on synset {0}\n'.format(synset)
            word = synset.name().split('.')[0]
#            for each in (synset.lemmas()):

            new_word=re.sub(r'[_\\\\/\'-.]','',word)
#                new_word = singularize(new_word.strip())
#                plural_word = pluralize(new_word)
            if new_word in word_seen:
                continue#pass
            else:
                word_seen.add(new_word)
                f.write('{0}\n'.format(new_word.strip().lower()))

#                if plural_word in word_seen:
#                    pass
#/                else:
 #                   word_seen.add(plural_word)
 #                   f.write('{0}\n'.format(plural_word.strip().lower()))
                
        except:
            print "failure happened on synset {0}\n".format(synset)





