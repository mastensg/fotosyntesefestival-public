import sys

from midi import Track

def load(path):
    f = open(path)
    state = eval(f.read())
    f.close()

    return state["tracks"]

tracks = load("lightshow")

for t in tracks:
    sys.stdout.write("%s\n" % (64 * "-"))

    for line in t.pattern:
        for i in line:
            if i:
                sys.stdout.write(".")
            else:
                sys.stdout.write(" ")

        sys.stdout.write("\n")
