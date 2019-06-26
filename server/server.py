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
      elif info.info_type == "draw_tile":
        self.players[info.player].draw_tile(info.data)
      elif info.info_type == "discard_tile":
        tile = self.players[info.player].discard_tile()
        self.gamestate.discard_tile(info.player, tile)
      elif info.info_type in ("can_chi", "can_pon", "can_kan"):
        from_player = info.data["from"]
        tile = info.data["tile"]
        kind = info.info_type[-3:]
        meld = self.players[info.player].should_call_meld(tile, from_player, kind)
        logging.debug("Received Meld: %s" % meld)
        if meld is not None:
          self.gamestate.meld(info.player, meld)
        # START HERE: Call chi/pon/kan on the gamestate object, and continue


    # Make the gamestate save the action it returns, then verify/assert in its
    # submethods (discard, pon, etc) that the action/player are correct.

