'''
Socks
=============
'''


import re
import kivy

from kivy.factory import Factory as F
from kivy.properties import *
from kivy.app import App
from functools import partial
from glob import glob
from itertools import combinations
from os.path import join, dirname
from random import randint, random, shuffle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
# FIXME this shouldn't be necessary
from kivy.logger import Logger

# ALL THESE UIX ONES SHOULD BE REPLACEABLE BY JUST "F"ing them.  See F.Image below
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter

class Card(F.Image):
    selected=BooleanProperty(False)
    show_card=BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        super(Card,self).__init__(**kwargs)

    def on_touch_down(self,touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_press')
            return True

    def on_press(self,*args):
        self.selected = not self.selected

    def on_selected(self,obj,value):
        if value:
            Animation(color=[0,1,1,0.5],d=.2).start(self)
        else:
            Animation(color=[1,1,1,1],d=.2).start(self)

    def on_show_card(self,obj,value):
        if value:
            Animation(color=[1,1,0,0.5],d=.2).start(self)
        else:
            Animation(color=[1,1,1,1],d=.2).start(self)

    def get_binary(self):
        match=re.match(r'images/([01]+)\.gif',self.source)
        if match:
            binary_string=match.group(1)
            binary_rep=int(binary_string,2)
            return binary_rep
        else:
            return 0

class Gameboard(GridLayout):
    no_sets_disabled = BooleanProperty(True)
    deck = ListProperty([])
    three_is_maximum = BooleanProperty(True)
    empties = ListProperty([])
    target_number_cards = NumericProperty(12)
    app = ObjectProperty(None)

    def setup(self):
        shuffle(self.deck)

    def count_cards(self):
        return len(self.children)-len(self.empties)

    def deal(self):
        self.app.game_on=True
        self.app.set_up=False

        while (len(self.children) < self.target_number_cards) and (len(self.deck)>0):
            card=Card()
            self.add_widget(card)
            card.source=self.deck.pop()
            self.no_sets_disabled = False

        while self.empties and len(self.deck)>0:
            card=self.empties.pop()
            if len(self.children) > self.target_number_cards:
                self.remove_widget(card)
            else:
                card.source=self.deck.pop()
                self.no_sets_disabled = False
        if 0<len(self.deck)<=5:
            self.app.deck_image.source = str(len(self.deck))+'_socks_back.png'
        if len(self.deck)==0:
            self.app.deck_image.source = 'blank_card.png'


    def find_set(self):
        actual_cards=list(set(self.children)-set(self.empties))
        size_of_set=3
        if self.three_is_maximum:
            maximum_set_size = 3
        else:
            maximum_set_size = len(actual_cards)
        while size_of_set <= maximum_set_size:
            for sock_set in combinations(actual_cards, size_of_set):
                set_checker = 0
                for card in sock_set:
                    set_checker ^= card.get_binary()
                if 0 == set_checker:
                    return sock_set
            size_of_set+=1
        return []

class PlayerPad(Scatter):
    score = NumericProperty(0)
    app = ObjectProperty(None)
    pad_color = ListProperty(None)
    no_set_button = ObjectProperty(None)
    def __init__(self,**kwargs):
        super(PlayerPad,self).__init__(**kwargs)
        self.bind(size=self.resize_rec)
        self.pad_color=[.2+.8*random(),.2+.8*random(),.2+.8*random()]
        with self.canvas.before:
            Color(*self.pad_color)
            self.rec = Rectangle(size=(self.width, self.height))
        self.app.gameboard.bind(no_sets_disabled=self.no_sets_trigger)
        self.no_sets_trigger(self.app.gameboard, self.app.gameboard.no_sets_disabled)

    def resize_rec(self,*args):
        self.rec.size=self.size

    def on_touch_down(self,touch):
        if self.collide_point(*touch.pos):
            return super(PlayerPad,self).on_touch_down(touch)

    def no_sets_trigger(self,gameboard,no_sets_disabled):
        if no_sets_disabled:
            Animation(background_color=[1,0,0,1],d=.2).start(self.no_set_button)
        else:
            Animation(background_color=[1,1,1,1],d=.2).start(self.no_set_button)


F.register('Gameboard',Gameboard)

class SocksApp(App):

    gameboard = ObjectProperty(None)
    set_up=BooleanProperty(True)
    game_on = BooleanProperty(False)
    show_set_button = ObjectProperty(None)
    show_set_button_toggle=BooleanProperty(True)
    deck_image = ObjectProperty(None)

    def build(self):
        self.gameboard = self.root.gameboard
        self.root.app = self
        self.gameboard.app=self
        self.new_game()
        self.show_set_button = self.root.show_set_button
        self.deck_image = self.root.deck_image

    def new_game(self):
        self.gameboard.deck = []
        curdir = dirname(__file__)
        for filename in glob(join(curdir, 'images', '*')):
            try:
                self.gameboard.deck.append(filename)
            except Exception as e:
                Logger.exception('Card: Unable to load <%s>' % filename)
        self.gameboard.setup()

    def add_player(self):
        new_player=PlayerPad(app=self)
        new_player.center=self.root.center
        self.root.add_widget(new_player)

    def show_set(self):
        if not self.set_up:
            if self.show_set_button_toggle:
                self.game_on=False
                sock_set=self.gameboard.find_set()
                if not self.gameboard.find_set():
                    Popup(title='',separator_color=[0,0,0,1],content=Label(text='There are no sets.'),
                          size_hint=(.5,.5)).open()
                    if self.gameboard.count_cards() >= 12:
                        self.gameboard.target_number_cards +=3
                    self.gameboard.no_sets_disabled = True
                    return []
                else:
                    for card in sock_set:
                        card.show_card=True
                    self.show_set_button.text='Remove Set'
                    Animation(background_color=[1,1,0,1],d=.2,).start(self.show_set_button)
                    self.show_set_button_toggle=False
            else:
                selected_cards = []
                self.game_on=True
                self.show_set_button.text='Show a Set'
                Animation(background_color=[1,1,1,1],d=.2,).start(self.show_set_button)
                self.show_set_button_toggle=True
                for card in self.gameboard.children:
                    if card.show_card:
                        selected_cards.append(card)
                        show_card=False
                self.animate_capture(self.show_set_button,selected_cards)
                if self.gameboard.target_number_cards > 12:
                    self.gameboard.target_number_cards -=3


    def claim(self,player):
        if self.game_on:
            set_checker = 0
            selected_cards = []
            for card in self.gameboard.children:
                if card.selected:
                    set_checker ^= card.get_binary()
                    selected_cards.append(card)
            if self.gameboard.three_is_maximum and len(selected_cards) != 3:
                Popup(title='',separator_color=[0,0,0,1],
                      content=Label(text='Three cards must be selected to claim a set.'),
                      size_hint=(.5,.5)).open()
                return False
            if not self.gameboard.three_is_maximum and len(selected_cards) < 3:
                Popup(title='',separator_color=[0,0,0,1],
                      content=Label(text='At least three cards must be selected to claim a set.'),
                      size_hint=(.5,.5)).open()
                return False
            if set_checker != 0:
                Popup(title='',separator_color=[0,0,0,1],
                      content=Label(text='These cards do not form a set.'),
                      size_hint=(.5,.5)).open()
                player.score -=1
            if set_checker == 0:
                self.animate_capture(player,selected_cards)
                player.score +=1
                if self.gameboard.target_number_cards > 12:
                    self.gameboard.target_number_cards -=3

    def claim_no_sets(self,player):
        if self.game_on:
            if not self.gameboard.no_sets_disabled:
                if self.gameboard.find_set():
                    Popup(title='',separator_color=[0,0,0,1],
                          content=Label(text='There is a set.'),
                          size_hint=(.5,.5)).open()
                    player.score -=1
                else:
                    Popup(title='',separator_color=[0,0,0,1],
                          content=Label(text='Correct! There are no sets.'),
                          size_hint=(.5,.5)).open()
                    player.score +=1
                    if self.gameboard.count_cards() >= 12:
                        self.gameboard.target_number_cards +=3
                    self.gameboard.no_sets_disabled = True

    def animate_capture(self,player,selected_cards):
        duration=.5
        anim=Animation(pos=player.center,size=[.5*x for x in selected_cards[0].size],d=duration)

        for card in selected_cards:
            new_card=Card(source=card.source,pos=card.pos,size=card.size,size_hint=(None,None))
            self.root.add_widget(new_card)
            card.source="blank_card.png"
            card.selected=False
            card.show_card=False
            anim.start(new_card)
            self.timed_delete(new_card,duration)
        self.gameboard.empties.extend(selected_cards)
#        self.gameboard.no_sets_disabled=True

    def timed_delete(self,card,duration):
        Clock.schedule_once(lambda dt: self.root.remove_widget(card),duration)



if __name__ in ('__main__', '__android__'):
    SocksApp().run()

