with open("dataset_4_families.csv", "w") as fo:
    with open('samples.txt', 'r') as f1:
        for line in f1:
            fo.write("{}".format(line))
    with open('linux_dga.txt', 'r') as f2:
        for line in f2:
            fo.write("{}".format(line))
