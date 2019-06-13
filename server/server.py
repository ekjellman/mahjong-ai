import logging
from gamestate.gamestate import GameState

class Server(object):
  def __init__(self, players, walls=None):
    self.players = players
    self.gamestate = GameState(walls)

  def start_play(self):
    gamestate_gen = self.gamestate.play()
    for player in self.players:
      player.start_hanchan(self.gamestate)   # TODO? Should this be?
    while not self.gamestate.game_over():
      info = gamestate_gen.next()
      logging.debug("Received Info: %s" % info)
      if info.info_type == "start_hand":
        for player in self.players:
          player.start_hand()
      # Start here: Handle the draw_tile action, pass it to the verifier AI
      #             Then on to discard


    # Make the gamestate save the action it returns, then verify/assert in its
    # submethods (discard, pon, etc) that the action/player are correct.

