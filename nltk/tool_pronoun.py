raw = 'all another any anybody anyone anything both each each other either everybody everyone everything few he her hers herself him himself his I it its itself many me mine more most much myself neither no one nobody none nothing one one another other others ours ourselves several she some somebody someone something that their theirs them themselves these they this those us we what whatever which whichever who whoever whom whomever whose you your yours yourself yourselves'

lst = raw.split(' ')
#print lst


lst1 = []
with open('prepositions.txt', 'r') as f:
    for each in f:
        if len(each.strip()) == 0:
            continue
        lst1.append(each.strip())

print lst1
