from __future__ import division

import time

class Track:
    def __init__(self, scroll_x=0, scroll_y=0, pattern=[], speed=64, start=0, stop=8*8*8*5):
        self.scroll_x = scroll_x
        self.scroll_y = scroll_y
        self.pattern = pattern[:]
        self.speed = speed
        self.start = start
        self.stop = stop

    def __repr__(self):
        return "Track(%s, %s, %s, %s, %s, %s)" % (self.scroll_x, self.scroll_y, self.pattern, self.speed, self.start, self.stop)

class Sequencer:
    def __init__(self, callback, path="lightshow", editing=False):
        self.callback = callback
        self.path = path
        self.editing = editing

        self.last_t = 0
        self.ticks = 0
        self.holding = 64 * [False]
        self.playing = True
        self.position = 0
        self.shift = False

        self.tracks = [Track() for i in range(8)]
        self.select_track(0)

        if editing:
            import pygame
            import pygame.locals as pgl
            import pygame.midi 

            pygame.midi.init()

            self.midi_in = pygame.midi.Input(3)
            self.midi_out = pygame.midi.Output(2)

        try:
            self.load()
        except IOError:
            self.save()

        self.update_pinball()
        self.update_apc()

    def load(self):
        f = open(self.path)
        state = eval(f.read())
        f.close()

        self.tracks = state["tracks"]
        self.select_track(state["track_index"])

    def save(self):
        state = {
                "tracks": self.tracks,
                "track_index": self.track_index,
                }

        f = open(self.path, "w")
        f.write(repr(state))
        f.close()

    def select_track(self, i):
        self.track_index = i
        self.track = self.tracks[i]
        self.position = self.track.start

    def toggle(self, x, y):
        if y >= len(self.track.pattern):
            for i in range(y - len(self.track.pattern) + 1):
                self.track.pattern.append(64 * [False])

        self.track.pattern[y][x] = not self.track.pattern[y][x]
        self.save()

    def update_apc(self):
        if not self.editing:
            return

        for y in range(5):
            if y + self.track.scroll_y >= len(self.track.pattern):
                for x in range(8):
                    self.midi_out.write_short(144 + x, 53 + y, 3)
            else:
                for x in range(8):
                    c = 0

                    if self.track.pattern[y + self.track.scroll_y][x + self.track.scroll_x]:
                        if y == self.position - self.track.scroll_y:
                            c = 5
                        else:
                            c = 1

                    self.midi_out.write_short(144 + x, 53 + y, c)

            self.midi_out.write_short(144, 82 + y, 4 if self.track.start - self.track.scroll_y <= y <= self.track.stop - self.track.scroll_y else 0)

        for i in range(8):
            self.midi_out.write_short(144 + i, 52, self.track.scroll_x in range(-7 + i * 8, 8 + i * 8))
            self.midi_out.write_short(144 + i, 51, i == self.track_index)
            self.midi_out.write_short(144 + i, 50, i == (self.track.scroll_y // (5 * 8 * 8)) % 8)
            self.midi_out.write_short(144 + i, 49, i == (self.track.scroll_y // (5 * 8)) % 8)
            self.midi_out.write_short(144 + i, 48, self.track.scroll_y % (5 * 8) in range(-4 + i * 5, 5 + i * 5))

        self.midi_out.write_short(176, 48, self.track.speed)

    def update_pinball(self):
        if len(self.track.pattern) and not True in self.holding:
            self.callback(self.track.pattern[self.position % len(self.track.pattern)])
        else:
            self.callback(self.holding)

    def advance(self):
        if not self.playing or len(self.track.pattern) < 1 or True in self.holding:
            return

        self.position += 1

        if self.position >= len(self.track.pattern) or self.position > self.track.stop:
            self.position = self.track.start

        self.update_pinball()
        self.update_apc()

    def tick(self):
        self.ticks += 1
        threshold = 4000 / (self.track.speed + 1) 

        if self.ticks > threshold:
            self.ticks -= threshold
            self.advance()

        if not self.editing:
            return

        if not self.midi_in.poll():
            return

        midi_events = self.midi_in.read(10)

        for e in pygame.midi.midis2events(midi_events, self.midi_in.device_id):
            if e.status & ~0b10000 in range(128, 136) and e.data1 in range(53, 58):
                x = (e.status & ~0b10000 - 128) + self.track.scroll_x
                y = (e.data1 - 53) + self.track.scroll_y

                if e.status & 0b10000:
                    self.holding[x] = True
                else:
                    self.holding[x] = False

                    self.toggle(x, y)
                    self.update_apc()

                self.update_pinball()

            elif e.status & ~0b10000 == 128 and e.data1 in range(82, 87):
                y = (e.data1 - 82) + self.track.scroll_y

                if not e.status & 0b10000:
                    return

                if self.shift:
                    self.track.stop = y
                else:
                    self.track.start = y

                self.update_apc()

            elif e.status == 176 and e.data1 == 15:
                self.track.scroll_x = min(e.data2 // 2, 64 - 8)
                self.update_apc()
                self.save()

            elif e.status == 176 and e.data1 == 47:
                dy = e.data2

                if dy & 0b1000000:
                    dy -= 128

                self.track.scroll_y = min(max(self.track.scroll_y + dy, 0), len(self.track.pattern))
                self.update_apc()
                self.save()

            elif e.status in range(176, 184) and e.data1 in range(16, 24):
                if e.data1 != 16:
                    return

                self.select_track(e.status - 176)
                self.update_apc()
                self.update_pinball()
                self.save()

            elif e.status & ~0b10000 in range(128, 136) and e.data1 == 52:
                self.track.scroll_x = (e.status & ~0b10000 - 128) * 8
                self.update_apc()
                self.save()

            elif e.status & ~0b10000 in range(128, 136) and e.data1 == 50:
                self.track.scroll_y = (e.status & ~0b10000 - 128) * 5 * 8 * 8
                self.update_apc()
                self.save()

            elif e.status & ~0b10000 in range(128, 136) and e.data1 == 49:
                self.track.scroll_y = (self.track.scroll_y // (5 * 8 * 8)) * (5 * 8 * 8) + (e.status & ~0b10000 - 128) * 5 * 8
                self.update_apc()
                self.save()

            elif e.status & ~0b10000 in range(128, 136) and e.data1 == 48:
                self.track.scroll_y = (self.track.scroll_y // (5 * 8)) * (5 * 8) + (e.status & ~0b10000 - 128) * 5
                self.update_apc()
                self.save()

            elif e.status & ~0b10000 == 128 and e.data1 == 91:
                self.playing = True

            elif e.status & ~0b10000 == 128 and e.data1 == 92:
                self.playing = False
                self.position = 0
                self.update_pinball()
                self.update_apc()

            elif e.status == 176 and e.data1 == 48:
                self.track.speed = max(e.data2, 1)
                self.save()

            elif e.status == 144 and e.data1 == 94:
                self.track.scroll_y = min(max(self.track.scroll_y - 1, 0), len(self.track.pattern))
                self.update_apc()
                self.save()

            elif e.status == 144 and e.data1 == 95:
                self.track.scroll_y = min(max(self.track.scroll_y + 1, 0), len(self.track.pattern))
                self.update_apc()
                self.save()

            elif e.status == 144 and e.data1 == 96:
                self.track.scroll_x = min(max(self.track.scroll_x + 1, 0), 64 - 8)
                self.update_apc()
                self.save()

            elif e.status == 144 and e.data1 == 97:
                self.track.scroll_x = min(max(self.track.scroll_x - 1, 0), 64 - 8)
                self.update_apc()
                self.save()

            elif e.status == 144 and e.data1 == 98:
                self.shift = True

            elif e.status == 128 and e.data1 == 98:
                self.shift = False

            else:
                pass
                #print("%3d %3d %3d %3d" % (e.status, e.data1, e.data2, e.data3))

def main():
    def p(s):
        print(s)

    s = Sequencer(p)

    t = 0

    while True:
        s.tick(t)
        time.sleep(0.001)
        t += 1

if __name__ == "__main__":
    main()
