# -*- coding: utf-8 -*-

class BaseAI(object):
  """
  Base interface for Mahjong AIs.

  Adapted with modifications from
  https://github.com/MahjongRepository/tenhou-python-bot/blob/master/project/game/ai/base/main.py
  """
  def __init__(self, player, gamestate):
    """
    Initialize the AI for the current match. This is only called once per
    hanchan.
    Args:
      player: an int (0-3) indicating which player this is.
      gamestate: a GameState object.
    """
    self.player = player
    self.gamestate = gamestate

  def discard_tile(self):
    """
    Ask the AI which tile should be discarded from its hand.
    Returns:
      an int, from 0-135, of which tile to discard from its hand.
      This int should be in the player's hand.
    """
    raise NotImplemented()

  def start_hanchan(self):
    """
    Called at the start of a match.
    """
    raise NotImplemented()

  def start_hand(self):
    """
    Called at the start of an individual hand.
    """
    raise NotImplemented()

  def hand_finished(self):
    """
    Called at the end of a hand, either by agari or ryuukyoku.
    """
    raise NotImplemented()

  def draw_tile(self, tile):
    """
    Called when a tile is drawn.
    """
    raise NotImplemented()

  def should_call_win(self, tile, enemy_seat):
    """
    Called when a tile is discarded that we can declare a win off of.
    This include chankan.
    If enemy_seat is our seat, it is a Tsumo.
    Returns:
      a boolean, True if we should declare a win, False otherwise.
    """
    raise NotImplemented()

  def should_call_riichi(self):
    """
    Called when it is possible to call a riichi.
    Returns:
      a boolean, True if we should declare riichi, False otherwise
    """
    raise NotImplemented()

  def should_call_kan(self, tile, open_kan, from_riichi=False):
    """
    Called when it is possible to call a kan.
    Args:
      tile: an integer, 0-135, representing a tile.
      open_kan: boolean, Whether this will be an open kan or not.
      from_riichi: boolean, if the AI player is in riichi and can call this
             kan (if it doesn't affect the waits)
    Returns:
      a boolean, True if we should call this kan, False otherwise.
    """
    # TODO: Not sure these parameters are what we should do.
    raise NotImplemented()

  def should_call_meld(self, tile, enemy_player):
    """
    Called when it is possible to chi or pon.
    Args:
      tile: an integer, 0-135, representing a tile.
      enemy_player: an integer, 0-3, representing which player discarded.
    Returns:
      None, None for no meld, or two tiles (0-135 integers) to meld with.
    """
    raise NotImplemented()

  def should_call_ryuukyoku(self):
    """
    Called when it is possible to call a ryuukyoku due to 9 terminals.
    Returns:
      True if we should call ryuukyoku, False otherwise.
    """
    raise NotImplemented()
