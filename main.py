# -*- coding: utf-8 -*-

from __future__ import division, print_function

import random
from itertools import product

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.graphics import Ellipse, Rectangle, Color
from kivy.animation import Animation
Config.set('graphics','width','360')
Config.set('graphics','height','640')
#Config.set('graphics','resizable',0)


class MainScreen(Screen):
    pass

class StatsScreen(Screen):
    pass

class OptionsScreen(Screen):
    pass

class ConfirmPopup(Popup):
    pass


class FairerDie():
    def __init__(self, sides):
        self.sides = sides
        self.n_sides = len(self.sides)
        self.reset_counts()
        return

    def reset_counts(self):
        self.n_rolls = 0  # will be incremented
        self.history = {side: 0 for side in self.sides}
        self.update_counts()
        return

    def update_counts(self):
        self.sollwert = self.n_rolls / self.n_sides
        self.helper_cnt = {}
        for side in self.sides:
            roll_count = self.history[side]
            offset = roll_count - self.sollwert
            x = roll_count - (2 * offset)
            if x <= 0.5:
                self.helper_cnt[side] = 0.5
            else:
                self.helper_cnt[side] = x
        helper_cnt_sum = sum(self.helper_cnt.values())
        self.roll_chances = \
            {s: self.helper_cnt[s] / helper_cnt_sum for s in self.sides}
        return

    def fair_roll(self):
        rand = random.random()
        lower_bound = 0
        upper_bound = 0
        for side, roll_chance in self.roll_chances.items():
            upper_bound += roll_chance
            if lower_bound < rand < upper_bound:
                return side
            lower_bound += roll_chance
        return

    def roll(self):
        #n = random.choice(self.sides)
        n = self.fair_roll()
        print("rolled", n)
        self.history[n] += 1
        self.n_rolls += 1
        self.update_counts()
        return n


EVENTS = ('eventa', 'eventb', 'mill', 'club', 'joust', 'goodyear')
CFG_DEFAULTS = {
    'numbers': {str(x): '0' for x in range(1,7)},
    'events': {x: '0' for x in EVENTS},
    'stats': {'n_rolls': '0'},
}
TRANSLATE = {
    'eventa': 'Ereignis',
    'eventb': 'Ereignis',
    'mill': 'Mühle',
    'joust': 'Turnier',
    'club': 'Räuber',
    'goodyear': 'Ertragreiches Jahr',
}


class DiceApp(App):
    def build(self):
        self.manager = ScreenManager(transition=SlideTransition())
        self.main = MainScreen(name='main')
        self.stats = StatsScreen(name='stats')
        self.options = OptionsScreen(name='options')
        self.manager.add_widget(self.main)
        self.manager.add_widget(self.stats)
        self.manager.add_widget(self.options)
        self.stats.ids.club_label.text = 'Räuber'  # fix unicode bugs...
        self.stats.ids.mill_label.text = 'Mühle'  # fix unicode bugs...
        self.event_die = FairerDie(sides=EVENTS)
        self.number_die = FairerDie(('1', '2', '3', '4', '5', '6'))
        self.load_cfg()
        return self.manager

    def build_config(self, config):
        for section, value_dict in CFG_DEFAULTS.items():
            config.setdefaults(section, value_dict)
        return

    def load_cfg(self):
        # load dice counts from config file
        cfg = self.config
        for key, val in self.event_die.history.items():
            self.event_die.history[key] = cfg.getdefaultint('events', key, 0)
        for key, val in self.number_die.history.items():
            self.number_die.history[key] = cfg.getdefaultint('numbers', key, 0)
        self.number_die.n_rolls = cfg.getdefaultint('stats', 'n_rolls', 0)
        self.event_die.n_rolls = cfg.getdefaultint('stats', 'n_rolls', 0)
        self.number_die.update_counts()
        self.event_die.update_counts()
        self.update_stats_screen()
        return

    def on_stop(self):
        # save dice counts to config file
        self.config.setall('numbers', self.number_die.history)
        self.config.setall('events', self.event_die.history)
        self.config.set('stats', 'n_rolls', self.number_die.n_rolls)
        self.config.write()
        return

    def on_pause(self):
        self.on_stop()
        return True

    def show_reset_popup(self):
        self.popup = ConfirmPopup()
        self.popup.open()
        return

    def reset_counts(self):
        print("resetting")
        for section, value_dict in CFG_DEFAULTS.items():
            self.config.setall(section, value_dict)
        self.event_die.reset_counts()
        self.number_die.reset_counts()
        self.update_stats_screen()
        self.popup.dismiss()
        return

    def roll_dice(self):
        eyes = self.number_die.roll()
        event = self.event_die.roll()
        anim = Animation(color=[1,1,1,1])
        self.main.ids.eyes.color=[1,1,1,0]
        self.main.ids.eyes.text = str(eyes)
        self.main.ids.event.color=[1,1,1,0]
        self.main.ids.event.text = TRANSLATE[event]
        anim.start(self.main.ids.eyes)
        anim.start(self.main.ids.event)
        self.update_stats_screen()
        return

    def update_stats_screen(self):
        for side, chance in self.number_die.roll_chances.items():
            rect = getattr(self.stats.ids, str(side))
            rect.size_hint_x = chance
            rect.children[0].text = '{:.1%}'.format(chance)

        max_freq = max(self.number_die.history.values())
        for side, freq in self.number_die.history.items():
            stats_rect = getattr(self.stats.ids, str(side) + '_freq')
            if max_freq == 0:
                stats_rect.size_hint_y = 0.01
            else:
                stats_rect.size_hint_y = freq / max_freq
            stats_rect.children[0].text = str(freq)

        for side, chance in self.event_die.roll_chances.items():
            if side == 'eventa':
                continue
            elif side == 'eventb':
                chance = self.event_die.roll_chances['eventa'] + \
                    self.event_die.roll_chances['eventb']
            prob_rect = getattr(self.stats.ids, side)
            prob_rect.size_hint_x = chance
            prob_rect.children[0].text = '{:.1%}'.format(chance)

        max_freq = max(self.event_die.history.values())
        for side, freq in self.event_die.history.items():
            if side == 'eventa':
                continue
            elif side == 'eventb':
                freq = self.event_die.history['eventa'] + \
                    self.event_die.history['eventb']
                height = freq / 2
            else:
                height = freq
            stats_rect = getattr(self.stats.ids, side + '_freq')
            if max_freq == 0:
                stats_rect.size_hint_y = 0.01
            else:
                stats_rect.size_hint_y = height / max_freq
            stats_rect.children[0].text = str(freq)
        return


if __name__ == '__main__':
    app = DiceApp()
    app.run()
