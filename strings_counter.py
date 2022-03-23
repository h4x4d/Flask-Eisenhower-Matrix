import glob

f = []
f += glob.glob("*.py")
f += glob.glob("*/*.py")

strings = 0
for i in f:
    if 'testing' not in i and 'strings_counter' not in i:
        strings += len(open(i, encoding='UTF-8').readlines())

print(strings)
# 517