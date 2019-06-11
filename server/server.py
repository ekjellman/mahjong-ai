import logging
from gamestate.gamestate import GameState

class Server(object):
  def __init__(self, players, walls=None):
    self.players = players
    self.gamestate = GameState(walls)

  def start_play(self):
    while not self.gamestate.game_over():
      self.gamestate.start_hand()

