import sys

from midi import Track

def load(path):
    f = open(path)
    state = eval(f.read())
    f.close()

    return state

def save(path, tracks, track_index):
    state = {
            "tracks": tracks,
            "track_index": track_index,
            }

    f = open(path, "w")
    f.write(repr(state))
    f.close()

state = load("lightshow")

tracks = state["tracks"]
track_index = state["track_index"]

j = -1
for l in sys.stdin.readlines():
    if "-" in l:
        j += 1
        tracks[j].pattern = []
        continue

    line = [True if c == "." else False for c in l]

    finalline = 64 * [False]
    for i in range(len(line)):
        if i >= 64:
            break

        finalline[i] = line[i]

    tracks[j].pattern.append(finalline)

save("lightshow", tracks, track_index)
