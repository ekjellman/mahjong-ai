import logging
import random
import collections

# TODO: Once this works for one file, start a test suite.
# TODO: Make sure each function has some debug logging.

class GameInfo(object):
  """
  An object representing information to be passed to a player.
  TODO: more detail

  Attributes:
    info_type: A string representing the kind of information this represents
    player: An int, 0-3, if the info is for one player, None if for all.
    data: Any necessary data for this GameInfo
  """

  def __init__(self, info_type, player, data):
    self.info_type = info_type
    self.player = player
    self.data = data

  def __str__(self):
    return "Info: info_type: %s  player: %s  data: %s" % (self.info_type, self.player, self.data)

class Wall(object):
  def __init__(self):
    self.main_wall = collections.deque()
    self.kan_draws = []
    self.dora_indicators = []
    self.uradora_indicators = []

  # NOTE: Making an assumption that player 0 draws all tiles first, then 1, etc.
  #       This shouldn't matter (since it's randomized anyway) but if it does,
  #       we will fix this later.

  @staticmethod
  def next_wall():
    tiles = range(136)
    random.shuffle(tiles)
    wall = Wall()
    wall.main_wall = collections.deque(tiles[:122])
    wall.kan_draws = tiles[122:126]
    wall.dora_indicators = tiles[126:131]
    wall.uradora_indicators = tiles[131:136]
    return wall

  def draw_tile(self):
    if len(self.main_wall) == 0:
      raise ValueError("Cannot draw from empty wall")
    return self.main_wall.popleft()

  def fill(self):
    all_tiles = set(range(136))
    used_tiles = set(self.main_wall)
    used_tiles.update(self.kan_draws)
    used_tiles.update(self.dora_indicators)
    used_tiles.update(self.uradora_indicators)
    remaining_tiles = all_tiles - used_tiles
    while len(self.main_wall) < 122:
      self.main_wall.append(remaining_tiles.pop())
    while len(self.kan_draws) < 4:
      self.kan_draws.append(remaining_tiles.pop())
    while len(self.dora_indicators) < 5:
      self.dora_indicators.append(remaining_tiles.pop())
    while len(self.uradora_indicators) < 5:
      self.uradora_indicators.append(remaining_tiles.pop())
    assert len(set(list(self.main_wall) + self.kan_draws + self.dora_indicators +
                   self.uradora_indicators)) == 136

  def __str__(self):
    mw_str = "Main Wall: %s" % self.main_wall
    kd_str = "Kan Draws: %s" % self.kan_draws
    di_str = "Dora Indicators: %s" % self.dora_indicators
    udi_str = "Uradora Indicators: %s" % self.uradora_indicators
    return "\n".join((mw_str, kd_str, di_str, udi_str))

class GameState(object):
  def __init__(self, walls=None):
    self.wind = 0 # E, S, W, N
    self.kyoku = 0  # Zero-indexed, E starts
    self.scores = [25000, 25000, 25000, 25000]
    self.wall = None
    if walls is not None:
      self.wall_iter = iter(walls)
      self.wall_generator = self.wall_iter.next
    else:
      self.wall_generator = Wall.next_wall
    self.discards = [[] for _ in xrange(4)]
    self.hands = None
    self.terminal = False
    self.current_action = None
    self.current_player = None

  def get_round_name(self):
    wind = ("East", "South", "West", "North")[self.wind]
    return "%s %d" % (wind, self.kyoku + 1)

  def game_over(self):
    return self.terminal

  def draw_hand(self):
    hand = []
    for tile in xrange(13):
      hand.append(self.wall.draw_tile())
    return hand

  def set_action(self, action):
    self.current_action = action
    return action

  def play(self):
    try:
      self.wall = self.wall_generator()
    except StopIteration:
      logging.critical("No hands left in generator.")
      raise ValueError("Wall Generator ran out of hands")
    while not self.game_over():
      logging.info("Starting %s" % self.get_round_name())
      logging.debug(self.wall)
      for info in self.play_hand():
        yield info
        # TODO: Check for hand terminal conditions
    yield self.set_action(GameInfo("start_hand", None, None))

  def play_hand(self):
    # Give initial hands
    self.hands = [[] for _ in xrange(4)]
    for player in xrange(4):
      self.hands[player] = self.draw_hand()
      logging.debug("Player %d hand: %s" % (player, self.hands[player]))
    yield self.set_action(GameInfo("start_hand", None, None))
    # In turn, players draw a tile. If possible, they may tsumo.
    self.current_player = self.kyoku
    while len(self.wall.main_wall) > 0:
      next_tile = self.wall.draw_tile()
      # Draw and tsumo check
      yield self.set_action(GameInfo("draw_tile", self.current_player, next_tile))
      self.hands[self.current_player].append(next_tile)
      if self.hand_complete(self.current_player, None):
        yield self.set_action(GameInfo("can_tsumo", self.current_player, None))
      # Discard and ron/naki check
      yield self.set_action(GameInfo("discard_tile", self.current_player, None))
      discard = self.discards[self.current_player][-1]
      # TODO: Consider caching these?
      for check in ("can_ron", "can_kan", "can_pon", "can_chi"):
        for player in xrange(4):
          if player == self.current_player: continue
          func = getattr(self, check)
          if func(player, self.discards[self.current_player][-1]):
            yield self.set_action(GameInfo(check, player, discard))

      self.current_player = (self.current_player + 1) % 4
    self.terminal = True

  def can_chi(self, player, tile):
    # Return False if player is wrong
    # START HERE: naki checks
    return False

  def can_pon(self, player, tile):
    return False

  def can_kan(self, player, tile):
    return False

  def can_ron(self, player, tile):
    return False

  def discard_tile(self, player, tile):
    """
    Discards a tile from the given player's hand
    """
    logging.debug("Discard tile: player: %d  tile: %d" % (player, tile))
    assert tile in self.hands[player]
    assert player == self.current_player
    self.hands[player].remove(tile)
    self.discards[player].append(tile)

  def hand_complete(self, player, discarded_tile):
    # TODO: Remember to consider furiten. If tsumo, the last tile in the hand is
    #       the new one.
    """
      Determine if the given player's hand is complete.
      Args:
        player: int, a player number 0-3
        discarded_tile: Either None if checking for a ron, or an int 0-135
                        representing a tile if checking for a tsumo.
      Returns:
        A boolean, True if this hand can be completed.
    """
    return False

