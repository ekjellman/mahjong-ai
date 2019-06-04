# -*- coding: utf-8 -*-
from base_ai import BaseAI
import logging

class Action(object):
  """
    A generic representation of an action the verifier AI is expected to take.

    The verifier that create this object (and passes it to the VerifierAI) will
    be looking at XML from an mjlog file and populating the necessary info. For
    example, given a tag to start a hand like this:

    <INIT seed="1,0,0,0,4,52" ten="210,230,330,230" oya="1"
          hai0="9,87,65,98,39,73,93,82,38,20,60,24,115"
          hai1="11,8,1,102,88,97,62,58,76,6,59,113,3,5"
          hai2="4,132,54,130,128,126,57,94,112,103,123,66,131"
          hai3="48,12,25,11,106,119,49,7,55,116,105,15,84"/>

    the verifier might create a dictionary with seed, ten, oya, and one of the
    hais as the inputs for the Action. The VerifierAI would check that the state
    of the game is consistent with the data passed in the action.

    function_name: string, the name of the function expected to be called
    inputs: a dictionary where the values are names for the pieces of input
            data, and the keys are the input data. See above for a description.
    output: The expected return from the function.
  """

  def __init__(self, function_name, inputs, output):
    self.function_name = function_name
    self.inputs = inputs
    self.output = output

  def __str__(self):
    return "Action: %s %s %s" % (self.function_name, self.inputs, self.output)

class VerifierAI(BaseAI):
  """
  AI used to verify the correctness of the game server.

  This "AI" will take in a mjlog file, and play the part of one of the players
  in the file, taking all the actions that player took. At the same time, the
  server will be seeded with the initial gamestate from the file (i.e. the
  order of the tiles, etc). If the server is correct, we should be able to
  duplicate the results from the game.
  """
  def __init__(self, player, gamestate, actions):
    """
    Initialize the AI for the current match. This is only called once per
    hanchan.
    Args:
      player: an int (0-3) indicating which player this is.
      gamestate: a GameState object.
      actions: a list of Action objects. Not all function calls will be in this
               list; for example there might be calls to should_call_meld not in
               the list. In those cases, it is assumed we do nothing / return
               False.
    """
    self.player = player
    self.gamestate = gamestate
    self.actions = actions

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
    Args:
      tile: an int from 0-135 of the drawn tile
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
    # TODO: The action may say should_call_meld, just verify and go on
    raise NotImplemented()

  def should_call_meld(self, tile, enemy_player):
    """
    Called when it is possible to chi or pon.
    Args:
      tile: an integer, 0-135, representing a tile.
      enemy_player: an integer, 0-3, representing which player discarded.
    Returns:
      None for no meld, or two tiles (0-135 integers) to meld with.
    """
    # TODO: The action will have the meld, but we'll have to verify and
    #       figure out the correct return here.
    raise NotImplemented()

  def should_call_ryuukyoku(self):
    """
    Called when it is possible to call a ryuukyoku due to 9 terminals.
    Returns:
      True if we should call ryuukyoku, False otherwise.
    """
    raise NotImplemented()
