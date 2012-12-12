import os
import time

import pygame
import pinproc
import procgame.game

import midi
import net

class LampTestMode(procgame.game.Mode):
    def __init__(self, game):
        super(LampTestMode, self).__init__(game, 1)

        self.lamps = sorted(list(game.lamps), lambda a, b: cmp(a.name, b.name))

    def mode_started(self):
        self.game.enable_flippers(False)

        print("%d lamps:" % len(self.lamps))

        for i in range(len(self.lamps)):
            print("%3d: %s" % (i, self.lamps[i].name))

        self.index = 0
        self.update()

    def update(self):
        for i in range(len(self.lamps)):
            lamp = self.lamps[i]

            if i == self.index:
                lamp.schedule(0xf0f0f0f0)
                print(lamp.name)
            else:
                lamp.enable()

    def sw_flipperL_active(self, sw):
        self.index = (self.index - 1) % len(self.lamps)
        self.update()

    def sw_flipperR_active(self, sw):
        self.index = (self.index + 1) % len(self.lamps)
        self.update()

    def sw_test_active_for_1s(self, sw):
        self.game.enter_switch_test_mode()

class SwitchTestMode(procgame.game.Mode):
    def __init__(self, game):
        super(SwitchTestMode, self).__init__(game, 1)

    def mode_started(self):
        for lamp in self.game.lamps:
            lamp.enable()

    def switch_active(self, sw):
        self.game.sound.switchTest.play()
        print(sw.name)

    sw_drain_active = switch_active
    sw_flipperL_active = switch_active
    sw_flipperR_active = switch_active
    sw_outlaneL_active = switch_active
    sw_outlaneR_active = switch_active
    sw_popB_active = switch_active
    sw_popL_active = switch_active
    sw_popR_active = switch_active
    sw_returnlane_active = switch_active
    sw_rollover0_active = switch_active
    sw_rollover1_active = switch_active
    sw_rollover2_active = switch_active
    sw_rollover3_active = switch_active
    sw_slingL_active = switch_active
    sw_slingR_active = switch_active
    sw_spinner_active = switch_active
    sw_standupLwL_active = switch_active
    sw_standupLwR_active = switch_active
    sw_standupUpL_active = switch_active
    sw_standupUpR_active = switch_active
    sw_watergate_active = switch_active
    sw_start_active = switch_active
    sw_test_active = switch_active
    sw_tilt_active = switch_active
    sw_shooterlane_active = switch_active

    def sw_test_active_for_1s(self, sw):
        self.game.enter_attract_mode()

class AttractMode(procgame.game.Mode):
    def __init__(self, game):
        super(AttractMode, self).__init__(game, 1)

        def update(line):
            for i in range(len(self.lamps)):
                lamp = self.lamps[i]

                if line[i]:
                    lamp.enable()
                else:
                    lamp.disable()

        self.lamps = sorted(list(game.lamps), lambda a, b: cmp(a.name, b.name))
        self.sequencer = midi.Sequencer(update)

        self.game.send_highscores()

    def mode_started(self):
        self.game.enable_flippers(False)
        self.playing = True
        self.playing_intro = False
        self.index = 0
        self.boe = 1
        self.ticks = 0
        self.music_countup = 7

        self.game.display("intro")

    def mode_tick(self):
        if not self.playing:
            return

        self.sequencer.tick()

        self.ticks += 1

        if self.ticks % 1000 == 0:
            if self.music_countup >= 7:
                pygame.mixer.stop()

                self.game.sound.attractMusic.play()
                self.music_countup = 0

            if self.ticks < 5000:
                self.game.display("intro")
            elif 5000 < self.ticks < 8000:
                self.game.display("highscore")
            elif 8000 < self.ticks < 10000:
                self.game.display("credits")
            elif 10000 < self.ticks:
                self.ticks = 0
                self.music_countup += 1

    def all_off(self):
        for lamp in self.game.lamps:
            lamp.disable()

    def sw_flipperL_active_for_1s(self, sw):
        if self.playing_intro:
            if self.game.switches.flipperR.is_active():
                self.start_game()

    def sw_flipperR_active_for_1s(self, sw):
        if self.playing_intro:
            if self.game.switches.flipperL.is_active():
                self.start_game()

    def start_game(self):
        if not self.playing_intro:
            return

        self.playing_intro = False

        pygame.mixer.stop()
        self.all_off()

        self.game.display("game")

        self.game.start_game()

    def sw_start_active(self, sw):
        if self.playing_intro:
            return

        pygame.mixer.stop()
        self.game.sound.velkommen.play()

        self.game.display("B%d" % (self.game.balls_per_game))
        self.game.display("C1000")
        self.game.display("title")

        self.playing = False
        self.playing_intro = True

        self.all_off()
        self.delay(delay=15.2, handler=self.sunshine)
        self.delay(delay=7.5, handler=self.fade_in)

    sw_flipperL_active = sw_start_active
    sw_flipperR_active = sw_start_active

    def fade_in(self):
        if not self.playing_intro:
            return

        self.game.display("game")

    def sunshine(self):
        if not self.playing_intro:
            return

        self.game.display("sunshine")

        self.game.lamps.popL.schedule(0b11111111111001100000011001000010)
        self.game.lamps.popR.schedule(0b11111111111001100001100001000100)
        self.game.lamps.popB.schedule(0b11111111111001100110000001001000)

        self.delay(delay=1.5, handler=self.water)

    def water(self):
        if not self.playing_intro:
            return

        self.game.display("water")

        self.all_off()

        self.game.lamps.trunk0.schedule(0b11111111111111111111111111000000)
        self.game.lamps.trunk1.schedule(0b11111111111111111111111100000000)
        self.game.lamps.trunk2.schedule(0b11111111111111111111110000000000)
        self.game.lamps.trunk3.schedule(0b11111111111111111111000000000000)
        self.game.lamps.trunk4.schedule(0b11111111111111111100000000000000)
        self.game.lamps.star.schedule(  0b11111010101010000000000000000000)

        self.delay(delay=2, handler=self.co2)

    def co2(self):
        if not self.playing_intro:
            return

        self.game.display("co2")

        self.all_off()

        self.game.lamps.GIspinner1.schedule(0xf000000f)
        self.game.lamps.GIspinner0.schedule(0x000000ff)
        self.game.lamps.GIstandupUpL.schedule(0x00000ff0)
        self.game.lamps.GIUpL0.schedule(0x0000ff00)
        self.game.lamps.GIUpL1.schedule(0x000ff000)
        self.game.lamps.GIrollover0.schedule(0xff500000)
        self.game.lamps.GIrollover1.schedule(0xff500000)
        self.game.lamps.GIrollover2.schedule(0xff500000)
        self.game.lamps.GIrollover3.schedule(0xff500000)
        self.game.lamps.GIrollover4.schedule(0xff500000)

        self.delay(delay=2, handler=self.tree)

    def tree(self):
        if not self.playing_intro:
            return

        self.all_off()

        self.game.lamps.tree00.schedule(0x0ff00ff0)
        self.game.lamps.tree10.schedule(0x0ff00ff0)
        self.game.lamps.tree20.schedule(0x0ff00ff0)
        self.game.lamps.tree21.schedule(0x0ff00ff0)
        self.game.lamps.tree30.schedule(0x0ff00ff0)
        self.game.lamps.tree31.schedule(0x0ff00ff0)
        self.game.lamps.tree32.schedule(0x0ff00ff0)
        self.game.lamps.tree40.schedule(0x0ff00ff0)
        self.game.lamps.tree41.schedule(0x0ff00ff0)
        self.game.lamps.tree42.schedule(0x0ff00ff0)
        self.game.lamps.tree43.schedule(0x0ff00ff0)
        self.game.lamps.tree50.schedule(0x0ff00ff0)
        self.game.lamps.tree51.schedule(0x0ff00ff0)
        self.game.lamps.tree52.schedule(0x0ff00ff0)
        self.game.lamps.tree53.schedule(0x0ff00ff0)
        self.game.lamps.tree54.schedule(0x0ff00ff0)

        self.delay(delay=3, handler=self.start_game)

    def sw_test_active_for_1s(self, sw):
        self.game.enter_lamp_test_mode()

class BaseGameMode(procgame.game.Mode):
    def __init__(self, game):
        super(BaseGameMode, self).__init__(game, 1)

    def mode_started(self):
        self.game.enable_flippers(True)

        self.ticks = 0
        self.spinner = 0
        self.warnings = 0
        self.mute = False
        self.mute_outlaneL = False

        self.nonagtime = 30
        self.co2_nag = self.nonagtime;
        self.sunshine_nag = self.nonagtime;
        self.water_nag = self.nonagtime;

        self.update_lamps()

    def mode_tick(self):
        self.ticks += 1

        if self.ticks % 256:
            return

        co2 = self.game.current_player().co2
        level = self.game.current_player().level
        sunshine = self.game.current_player().sunshine
        water = self.game.current_player().water

        self.co2_nag -= 1;
        self.sunshine_nag -= 1;
        self.water_nag -= 1;

        if not self.game.collected_co2 or self.mute:
            return

        if self.co2_nag < 0:
            self.co2_nag = 2 * self.nonagtime

            if co2 < min(level, 4):
                self.game.sound.moreCo2.play()
                self.sunshine_nag = self.nonagtime
                self.water_nag = self.nonagtime

        if self.sunshine_nag < 0:
            self.sunshine_nag = 2 * self.nonagtime

            if sunshine < level:
                self.game.sound.moreSunshine.play()
                self.co2_nag = self.nonagtime
                self.water_nag = self.nonagtime

        if self.water_nag < 0:
            self.water_nag = 2 * self.nonagtime

            if water < level:
                self.game.sound.moreWater.play()
                self.co2_nag = self.nonagtime
                self.sunshine_nag = self.nonagtime

    def update_lamps(self):
        if self.mute:
            return

        co2 = self.game.current_player().co2
        level = self.game.current_player().level
        sunshine = self.game.current_player().sunshine
        water = self.game.current_player().water
        kickback_enabled = self.game.current_player().kickback_enabled

        self.game.display("C%d%d%d%d" % (level, min(co2, level), min(sunshine, level), min(water, level)))

        if level >= 6:
            for lamp in self.game.lamps:
                lamp.disable()

            self.game.display("black")
            self.game.enable_flippers(False)
            self.mute = True

            return

        lamps = {}

        if co2 >= level:
            lamps["rollover0"] = True
            lamps["rollover1"] = True
            lamps["rollover2"] = True
            lamps["rollover3"] = True
            lamps["rollover4"] = True

            self.game.lamps.GIspinner1.enable()
            self.game.lamps.GIspinner0.enable()
            self.game.lamps.GIstandupUpL.enable()
            self.game.lamps.GIUpL0.enable()
            self.game.lamps.GIUpL1.enable()
            self.game.lamps.GIrollover0.enable()
            self.game.lamps.GIrollover1.enable()
            self.game.lamps.GIrollover2.enable()
            self.game.lamps.GIrollover3.enable()
            self.game.lamps.GIrollover4.enable()
        else:
            lamps["rollover0"] = co2 > 0
            lamps["rollover1"] = co2 > 1
            lamps["rollover2"] = co2 > 2
            lamps["rollover3"] = co2 > 3
            lamps["rollover4"] = co2 > 4

            self.game.lamps.GIspinner1.schedule(0xf000000f)
            self.game.lamps.GIspinner0.schedule(0x000000ff)
            self.game.lamps.GIstandupUpL.schedule(0x00000ff0)
            self.game.lamps.GIUpL0.schedule(0x0000ff00)
            self.game.lamps.GIUpL1.schedule(0x000ff000)
            self.game.lamps.GIrollover0.schedule(0xff500000)
            self.game.lamps.GIrollover1.schedule(0xff500000)
            self.game.lamps.GIrollover2.schedule(0xff500000)
            self.game.lamps.GIrollover3.schedule(0xff500000)
            self.game.lamps.GIrollover4.schedule(0xff500000)

        if water >= level:
            lamps["trunk0"] = True
            lamps["trunk1"] = True
            lamps["trunk2"] = True
            lamps["trunk3"] = True
            lamps["trunk4"] = True
            lamps["star"] = True
        else:
            if water > 0:
                lamps["trunk0"] = True
            else:
                self.game.lamps.trunk0.schedule(0b11111111111111111111111111000000)

            if water > 1:
                lamps["trunk1"] = True
            else:
                self.game.lamps.trunk1.schedule(0b11111111111111111111111100000000)

            if water > 2:
                lamps["trunk2"] = True
            else:
                self.game.lamps.trunk2.schedule(0b11111111111111111111110000000000)

            if water > 3:
                lamps["trunk3"] = True
            else:
                self.game.lamps.trunk3.schedule(0b11111111111111111111000000000000)

            if water > 4:
                lamps["trunk4"] = True
            else:
                self.game.lamps.trunk4.schedule(0b11111111111111111100000000000000)

            self.game.lamps.star.schedule(0b11111010101010000000000000000000)

        if sunshine >= level:
            self.game.lamps.popL.enable()
            self.game.lamps.popR.enable()
            self.game.lamps.popB.enable()
        else:
            self.game.lamps.popL.schedule(0b11111111111001100000011001000010)
            self.game.lamps.popR.schedule(0b11111111111001100001100001000100)
            self.game.lamps.popB.schedule(0b11111111111001100110000001001000)

        lamps["tree00"] = level > 0
        lamps["tree10"] = level > 1
        lamps["tree20"] = level > 2
        lamps["tree21"] = level > 2
        lamps["tree30"] = level > 3
        lamps["tree31"] = level > 3
        lamps["tree32"] = level > 3
        lamps["tree40"] = level > 4
        lamps["tree41"] = level > 4
        lamps["tree42"] = level > 4
        lamps["tree43"] = level > 4
        lamps["tree50"] = level > 5
        lamps["tree51"] = level > 5
        lamps["tree52"] = level > 5
        lamps["tree53"] = level > 5
        lamps["tree54"] = level > 5

        lamps["outlaneL"] = kickback_enabled

        noton = (
                "GIspinner1",
                "GIspinner0",
                "GIstandupUpL",
                "GIUpL0",
                "GIUpL1",
                "GIrollover0",
                "GIrollover1",
                "GIrollover2",
                "GIrollover3",
                "GIrollover4",
                "GIslingL0",
                "GIslingL1",
                "GIslingR0",
                "GIslingR1",
                )

        for lamp in self.game.lamps:
            if lamp.name.startswith("GI") and not lamp.name in noton:
                lamp.enable()
            elif lamp.name in lamps:
                if lamps[lamp.name]:
                    lamp.enable()
                else:
                    lamp.disable()

        self.slings()

    def start_music(self):
        if self.mute:
            return

        self.game.sound.music.play(loops=-1)

    def sw_shooterlane_active(self, sw):
        if self.mute:
            return

        if self.game.ball_shot:
            return

        self.mute = False
        self.game.sound.roll.play()
        self.game.sound.shooterGroove.stop()
        self.delay(delay=3, handler=self.start_music)

        self.game.ball_shot = True

    def rollover(self, sw):
        if self.mute:
            return

        self.game.collected_co2 = True
        self.co2_nag = 2 * self.nonagtime

        self.game.sound.rollover.play()
        self.game.current_player().add_co2()
        self.update_lamps()

    sw_rollover0_active = rollover
    sw_rollover1_active = rollover
    sw_rollover2_active = rollover
    sw_rollover3_active = rollover

    def unmute_outlaneL(self):
        self.mute_outlaneL = False

    def sw_outlaneL_active(self, sw):
        if self.mute:
            return

        if self.mute_outlaneL:
            return

        self.mute_outlaneL = True
        self.delay(delay=1, handler=self.unmute_outlaneL)

        if not self.game.current_player().kickback_enabled:
            self.game.sound.suspense.play()
            return

        self.game.sound.cheerKickback.play()
        self.game.coils.kickback.pulse()
        self.game.current_player().kickback_enabled = False
        self.update_lamps()

    def sw_returnlane_active(self, sw):
        if self.mute:
            return

        self.game.sound.cheerKickback.play()

    def sw_outlaneR_active(self, sw):
        if self.mute:
            return

        self.game.sound.suspense.play()

    def sw_standupUpL_active(self, sw):
        if sw.time_since_change() > 2:
            self.game.sound.thunder.play()

    def sw_standupUpR_active(self, sw):
        if self.mute:
            return

        if sw.time_since_change() > 2:
            self.game.sound.festivalpass.play()

        self.game.current_player().kickback_enabled = True
        self.update_lamps()

    def sw_standupLwL_active(self, sw):
        if self.mute:
            return

        self.game.sound.standupL.play()

    def sw_standupLwR_active(self, sw):
        if self.mute:
            return

        self.game.sound.standupR.play()

    def pop(self, sw):
        self.sunshine_nag = 2 * self.nonagtime

        if self.mute:
            return

        self.game.current_player().add_sunshine()
        self.update_lamps()

    sw_popL_active = pop
    sw_popR_active = pop
    sw_popB_active = pop

    def sw_watergate_active(self, sw):
        self.water_nag = 2 * self.nonagtime

        if self.mute:
            return

        self.game.sound.water.play()
        self.game.current_player().add_water()
        self.update_lamps()

    def sw_spinner_active(self, sw):
        if self.mute:
            return

        self.spinner = (self.spinner + 1) % 2

        if self.spinner == 0:
            self.game.sound.bil1.play()
        elif self.spinner == 1:
            self.game.sound.bil2.play()

    def slings(self):
        #if self.game.current_player().level < 4:
        self.game.lamps.GIslingL0.enable()
        self.game.lamps.GIslingL1.enable()
        self.game.lamps.GIslingR0.enable()
        self.game.lamps.GIslingR1.enable()
        return

        self.game.lamps.GIslingL0.schedule(0b11111111111001111111111001111110, cycle_seconds=0)
        self.game.lamps.GIslingL1.schedule(0b11111111111111111110001111111111, cycle_seconds=0)
        self.game.lamps.GIslingR0.schedule(0b11111111111001100111111111001111, cycle_seconds=0)
        self.game.lamps.GIslingR1.schedule(0b11111111111011111111011111111001, cycle_seconds=0)

    def sw_slingL_active(self, sw):
        if self.mute:
            return

        if self.game.current_player().level < 4:
            return

        self.game.coils.slingL.pulse()
        self.game.sound.slingL.play()
        self.game.lamps.GIslingL0.schedule(0b11111111111001100000011001000010, cycle_seconds=1)
        self.game.lamps.GIslingL1.schedule(0b11111111111000110000001100100001, cycle_seconds=1)
        self.delay(delay=1, handler=self.slings)

    def sw_slingR_active(self, sw):
        if self.mute:
            return

        if self.game.current_player().level < 4:
            return

        self.game.coils.slingR.pulse()
        self.game.sound.slingR.play()
        self.game.lamps.GIslingR0.schedule(0b11111111111001100000011001000010, cycle_seconds=1)
        self.game.lamps.GIslingR1.schedule(0b11111111111000110000001100100001, cycle_seconds=1)
        self.delay(delay=1, handler=self.slings)

    def sw_tilt_active(self, sw):
        if sw.time_since_change() < 0.5 or self.mute:
            return

        self.game.sound.tiltWarning.play()

        self.warnings += 1

        if self.warnings >= 3:
            pygame.mixer.stop()

            self.game.sound.tilt.play()

            for lamp in self.game.lamps:
                lamp.disable()

            self.game.display("black")
            self.game.enable_flippers(False)
            self.mute = True

    def sw_drain_active(self, sw):
        self.mute = True

        pygame.mixer.stop()

        self.game.display("B%d" % (self.game.balls_per_game - self.game.ball))

        if not self.game.ball_in_play:
            return

        self.game.ball_in_play = False

        if self.game.current_player().level >= 6:
            self.delay(delay=1.0, handler=self.game.sound.gratulerer.play)
            self.delay(delay=9.0, handler=self.lights)
            return

        if self.game.ball < self.game.balls_per_game:
            self.game.sound.boo.play()
            self.delay(delay=3.0, handler=self.game.end_ball)
            return

        for lamp in self.game.lamps:
            lamp.disable()

        self.game.enable_flippers(False)

        self.game.display("black")

        self.delay(delay=1.0, handler=self.game.sound.braJobba.play)
        self.delay(delay=5.0, handler=self.game.enter_video_mode)

    def lights(self):
        self.game.lamps.popL.schedule(0b00001000001000000100001000000100)
        self.game.lamps.popR.schedule(0b10000010010000100000100000100000)
        self.game.lamps.popB.schedule(0b00010000100000001000000001001000)
        self.game.lamps.GIslingL0.schedule(0b01010000101000101000001010000000)
        self.game.lamps.GIslingL1.schedule(0b10100001010001010000010100000000)
        self.game.lamps.GIslingR0.schedule(0b00000101000010100010100000101000)
        self.game.lamps.GIslingR1.schedule(0b00001010000101000101000001010000)
        self.game.lamps.GIspinner1.schedule(  0b00000011000000110000001100000011)
        self.game.lamps.GIspinner0.schedule(  0b00000110000001100000011000000110)
        self.game.lamps.GIstandupUpL.schedule(0b00001100000011000000110000001100)
        self.game.lamps.GIUpL0.schedule(      0b00011000000110000001100000011000)
        self.game.lamps.GIUpL1.schedule(      0b00110000001100000011000000110000)
        self.game.lamps.GIrollover0.schedule( 0b01100000011000000110000001100000)
        self.game.lamps.GIrollover1.schedule( 0b01100000011000000110000001100000)
        self.game.lamps.GIrollover2.schedule( 0b01100000011000000110000001100000)
        self.game.lamps.GIrollover3.schedule( 0b01100000011000000110000001100000)
        self.game.lamps.GIrollover4.schedule( 0b01100000011000000110000001100000)
        self.game.lamps.trunk0.schedule(0b00100010001000100010001000100010)
        self.game.lamps.trunk1.schedule(0b01000100010001000100010001000100)
        self.game.lamps.trunk2.schedule(0b10001000100010001000100010001000)
        self.game.lamps.trunk3.schedule(0b00010001000100010001000100010001)
        self.game.lamps.trunk4.schedule(0b00100010001000100010001000100010)
        self.game.lamps.star.schedule(0b01010101010101010101010101010101)
        self.game.lamps.tree00.schedule(0b10101010101010101010101010101010)
        self.game.lamps.tree10.schedule(0b00010001000100010001000100010001)
        self.game.lamps.tree20.schedule(0b00010001000100010001000100010001)
        self.game.lamps.tree30.schedule(0b00010001000100010001000100010001)
        self.game.lamps.tree40.schedule(0b00010001000100010001000100010001)
        self.game.lamps.tree50.schedule(0b00010001000100010001000100010001)
        self.game.lamps.tree21.schedule(0b00100010001000100010001000100010)
        self.game.lamps.tree31.schedule(0b00100010001000100010001000100010)
        self.game.lamps.tree41.schedule(0b00100010001000100010001000100010)
        self.game.lamps.tree51.schedule(0b00100010001000100010001000100010)
        self.game.lamps.tree32.schedule(0b01000100010001000100010001000100)
        self.game.lamps.tree42.schedule(0b01000100010001000100010001000100)
        self.game.lamps.tree52.schedule(0b01000100010001000100010001000100)
        self.game.lamps.tree43.schedule(0b10001000100010001000100010001000)
        self.game.lamps.tree53.schedule(0b10001000100010001000100010001000)
        self.game.lamps.tree54.schedule(0b00010001000100010001000100010001)

        self.delay(delay=8.0, handler=self.action)

    def action(self):
        self.game.coils.popL.schedule(0b00001000001000000100001000000100)
        self.game.coils.popR.schedule(0b10000010010000100000100000100000)
        self.game.coils.popB.schedule(0b00010000100000001000000001001000)
        self.game.coils.slingL.schedule(0b00010000001000001000000010000000)
        self.game.coils.slingR.schedule(0b00000001000000100000100000001000)
        self.game.coils.kickback.schedule(0b00010000000000100000000010000000)
        self.game.coils.flipperLMain.schedule(0b00000000010000010000010010000000)
        self.game.coils.flipperRMain.schedule(0b01000010000000100000000100000100)

        self.delay(delay=6.0, handler=self.cut)

    def cut(self):
        for lamp in self.game.lamps:
            lamp.disable()

        for coil in self.game.coils:
            coil.disable()

        self.delay(delay=4.0, handler=self.game.enter_video_mode)

class VideoMode(procgame.game.Mode):
    def __init__(self, game):
        super(VideoMode, self).__init__(game, 1)

    def mode_started(self):
        self.select = False

        self.game.display("wood")
        self.game.sound.chainsaw.play()

        self.delay(delay=5.0, handler=self.game.sound.biomassen.play)
        self.delay(delay=9.0, handler=self.do_select)

    def do_select(self):
        self.game.display("select")
        self.select = True

    def sw_flipperL_active(self, sw):
        if not self.select:
            return

        self.game.sound.house.play()
        self.game.display("house")
        self.delay(delay=8.0, handler=self.game.enter_highscore_mode)
        self.select = False

    def sw_flipperR_active(self, sw):
        if not self.select:
            return

        self.game.sound.fire.play()
        self.game.display("fire")
        self.delay(delay=8.0, handler=self.game.enter_highscore_mode)
        self.select = False

class HighscoreMode(procgame.game.Mode):
    def __init__(self, game):
        super(HighscoreMode, self).__init__(game, 1)
        self.lower = "abcdefghijklmnopqrstuvwxyz{|}"
        self.upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]"

    def mode_started(self):
        self.mute = True
        self.c = 0
        self.i = 0
        self.name = ["a", " ", " "]

        if self.game.current_player().level < 6:
            self.game.end_game()
            return

        self.update()
        self.game.display("entry")
        self.mute = False

    def update(self):
        if self.mute:
            return

        if self.i < 3:
            self.name[self.i] = self.lower[self.c]

        self.game.display("E%s" % "".join(self.name))

    def select(self):
        if self.mute:
            return

        if self.i >= 3:
            return

        self.game.sound.freeHat.play()

        self.name[self.i] = self.upper[self.c]
        self.c = 0
        self.i += 1

        self.update()

        if self.i >= 3:
            self.mute = True
            self.game.highscores = ["".join(self.name)] + self.game.highscores[:-1]
            self.game.save_highscores()
            self.game.send_highscores()
            self.delay(delay=4.0, handler=self.game.end_game)

    def sw_flipperL_inactive(self, sw):
        if self.mute:
            return

        self.game.sound.switchTest.play()
        self.c = (self.c - 1) % len(self.lower)
        self.update()

    def sw_flipperR_inactive(self, sw):
        if self.mute:
            return

        self.game.sound.switchTest.play()
        self.c = (self.c + 1) % len(self.lower)
        self.update()

    def sw_flipperL_active(self, sw):
        if self.mute:
            return

        if self.game.switches.flipperR.is_active():
            self.select()

    def sw_flipperR_active(self, sw):
        if self.mute:
            return

        if self.game.switches.flipperL.is_active():
            self.select()

class DrainStatsMode(procgame.game.Mode):
    def __init__(self, game):
        super(DrainStatsMode, self).__init__(game, 1)

    def mode_started(self):
        self.drain_type = "Straight down the middle"

    def sw_outlaneL_active(self, sw):
        self.drain_type = "Left outlane"

    def sw_outlaneR_active(self, sw):
        self.drain_type = "Right outlane"

    def sdm(self, sw):
        self.drain_type = "Straight down the middle"

    sw_popB_active = sdm
    sw_popL_active = sdm
    sw_popR_active = sdm
    sw_returnlane_active = sdm
    sw_rollover0_active = sdm
    sw_rollover1_active = sdm
    sw_rollover2_active = sdm
    sw_rollover3_active = sdm
    sw_shooterlane_active = sdm
    sw_slingL_active = sdm
    sw_slingR_active = sdm
    sw_spinner_active = sdm
    sw_standupLwL_active = sdm
    sw_standupLwR_active = sdm
    sw_standupUpLactive = sdm
    sw_standupUpR_active = sdm
    sw_tilt_active = sdm
    sw_watergate_active = sdm

class Player(procgame.game.Player):
    def __init__(self, name):
        super(Player, self).__init__(name)

        self.level = 1
        self.co2 = 0
        self.sunshine = 0
        self.water = 0
        self.kickback_enabled = False

        return
        self.level = 5
        self.co2 = 4
        self.sunshine = 5
        self.water = 5

    def update_level(self):
        if self.co2 < self.level:
            return

        if self.sunshine < self.level:
            return

        if self.water < self.level:
            return

        self.level += 1
        self.co2 = 0
        self.sunshine = 0
        self.water = 0

        pygame.mixer.stop()

        self.game.display("co2 off")
        self.game.display("sunshine off")
        self.game.display("water off")

        if self.level == 2:
            self.game.sound.level1.play()
        elif self.level == 3:
            self.game.sound.level2.play()
        elif self.level == 4:
            self.game.sound.level3.play()
        elif self.level == 5:
            self.game.sound.level4.play()

        if self.level != 6:
            self.game.sound.music.play(loops=-1)

    def add_co2(self):
        self.game.display("co2")
        self.co2 += 1

        if self.co2 >= self.level:
            self.game.display("co2 on")

        self.update_level()

    def add_sunshine(self):
        self.game.display("sunshine")
        self.sunshine += 1

        if self.sunshine >= self.level:
            self.game.display("sunshine on")

        self.update_level()

    def add_water(self):
        self.game.display("water")
        self.water += 1

        if self.water >= self.level:
            self.game.display("water on")

        self.update_level()

    def __str__(self):
        return "%g, CO2=%d, sunshine=%d, water=%d" % (self.game_time, self.co2, self.sunshine, self.water)

class Game(procgame.game.GameController):
    def __init__(self):
        super(Game, self).__init__(pinproc.MachineTypePDB)

        self.hspath = "highscores.txt"

    def setup(self):
        self.load_config("fotosyntesefestival.yaml")
        self.load_highscores()

        self.balls_per_game = 5
        #self.balls_per_game = 1

        class Sounds:
            pass

        pygame.mixer.init(buffer=768)
        Sound = pygame.mixer.Sound
        self.sound = Sounds()

        self.sound.attractMusic = Sound("sound/Attract Music_PN.wav")
        self.sound.bil1 = Sound("sound/Bil 1.wav")
        self.sound.bil2 = Sound("sound/Bil 2.wav")
        self.sound.biomassen = Sound("sound/Biomassen.wav")
        self.sound.boe = Sound("sound/Boe.wav")
        self.sound.boe1 = Sound("sound/Boe1.wav")
        self.sound.boe2 = Sound("sound/Boe2.wav")
        self.sound.boo = Sound("sound/Boo.wav")
        self.sound.braJobba = Sound("sound/Bra Jobba.wav")
        self.sound.chainsaw = Sound("sound/Chainsaw.wav")
        self.sound.cheerKickback = Sound("sound/Cheer Kickback.wav")
        self.sound.cheerLevel = Sound("sound/Cheer Level.wav")
        self.sound.festivalpass = Sound("sound/Festivalpass.wav")
        self.sound.fire = Sound("sound/Fire.wav")
        self.sound.freeHat = Sound("sound/Free Hat.wav")
        self.sound.gratulerer = Sound("sound/Gratulerer.wav")
        self.sound.hereAndHere = Sound("sound/Here and here_PN.wav")
        self.sound.house = Sound("sound/House.wav")
        self.sound.level1 = Sound("sound/Nivaa 1.wav")
        self.sound.level2 = Sound("sound/Nivaa 2.wav")
        self.sound.level3 = Sound("sound/Nivaa 3.wav")
        self.sound.level4 = Sound("sound/Nivaa 4.wav")
        self.sound.level5 = Sound("sound/Nivaa 5.wav")
        self.sound.moreCo2 = Sound("sound/Mere Karbondioksid.wav")
        self.sound.moreSunshine = Sound("sound/Mere Sollys.wav")
        self.sound.moreWater = Sound("sound/Mere Vann.wav")
        self.sound.music = Sound("sound/Music_PN.wav")
        self.sound.roll = Sound("sound/Roll.wav")
        self.sound.rollover = Sound("sound/Rollover.wav")
        self.sound.shooterGroove = Sound("sound/Shooter Groove_PN.wav")
        self.sound.slingL = Sound("sound/Left Sling.wav")
        self.sound.slingR = Sound("sound/Right Sling.wav")
        self.sound.standupL = Sound("sound/Left Standup.wav")
        self.sound.standupR = Sound("sound/Right Standup.wav")
        self.sound.sun = Sound("sound/Sun.wav")
        self.sound.suspense = Sound("sound/Suspense.wav")
        self.sound.switchTest = Sound("sound/Switch Test.wav")
        self.sound.thunder = Sound("sound/Thunder.wav")
        self.sound.tilt = Sound("sound/Tilt.wav")
        self.sound.tiltWarning = Sound("sound/Tilt Warning.wav")
        self.sound.velkommen = Sound("sound/Velkommen_PN.wav")
        self.sound.water = Sound("sound/Water.wav")

        self.display = net.Display()

        self.attract_mode = AttractMode(self)
        self.base_game_mode = BaseGameMode(self)
        self.drain_stats_mode = DrainStatsMode(self)
        self.video_mode = VideoMode(self)
        self.highscore_mode = HighscoreMode(self)
        self.lamp_test_mode = LampTestMode(self)
        self.switch_test_mode = SwitchTestMode(self)

        self.reset()

    def reset(self):
        super(Game, self).reset()

        self.ball_in_play = False

        self.proc.switch_update_rule(self.switches.flipperL.number, 'closed_debounced', {'notifyHost':True, 'reloadActive':False}, [], False)
        self.proc.switch_update_rule(self.switches.flipperR.number, 'closed_debounced', {'notifyHost':True, 'reloadActive':False}, [], False)

        self.modes.add(self.attract_mode)
        #self.modes.add(self.drain_stats_mode)

    def load_highscores(self):
        self.highscores = eval(open(self.hspath).read())

    def save_highscores(self):
        f = open(self.hspath, "w")
        f.write(repr(self.highscores))
        f.close()

    def send_highscores(self):
        self.display("H%s " % " ".join(self.highscores))

    def enter_video_mode(self):
        self.modes.remove(self.base_game_mode)
        self.modes.add(self.video_mode)

    def enter_highscore_mode(self):
        self.modes.remove(self.video_mode)
        self.modes.add(self.highscore_mode)

    def enter_lamp_test_mode(self):
        self.modes.remove(self.attract_mode)
        self.modes.add(self.lamp_test_mode)

    def enter_switch_test_mode(self):
        self.modes.remove(self.lamp_test_mode)
        self.modes.add(self.switch_test_mode)

    def enter_attract_mode(self):
        self.modes.remove(self.switch_test_mode)
        self.modes.add(self.attract_mode)

    def create_player(self, name):
        return Player(name)

    def game_started(self):
        super(Game, self).game_started()

        self.first_ball = True

        self.add_player()
        self.current_player().game = self
        self.start_ball()

        self.modes.remove(self.attract_mode)
        self.modes.add(self.base_game_mode)

    def ball_starting(self):
        super(Game, self).ball_starting()

        self.display("B%d" % (self.balls_per_game - self.ball))
        self.display("game")

        self.coils.ballserve.pulse()
        self.ball_in_play = True
        self.ball_shot = False
        self.collected_co2 = False

        self.base_game_mode.mute = False
        self.base_game_mode.mute_outlaneL = False
        self.base_game_mode.nonagtime = 30
        self.base_game_mode.warnings = 0

        self.base_game_mode.update_lamps()

        self.enable_flippers(True)

        self.sound.shooterGroove.play(loops=-1)

    def ball_ended(self):
        super(Game, self).ball_ended()

        self.ball_in_play = False
        self.first_ball = False

        pygame.mixer.stop()

        if False:
            try:
                f = open("drains.txt", "a")
                f.write("%s\n" % self.drain_stats_mode.drain_type)
                f.close()
            except:
                print("Error while writing to drain log")
        
    def game_ended(self):
        self.modes.remove(self.highscore_mode)
        self.modes.add(self.attract_mode)

        super(Game, self).game_ended()

def main():
    game = Game()
    game.setup()
    game.run_loop()

if __name__ == "__main__":
    main()
