# coding: utf-8

import logging
import random
import collections

# TODO: Once this works for one file, start a test suite.
# TODO: Make sure each function has some debug logging.
# TODO: Make sure that all of the functions the server calls to affect
#       gamestate (discard, melding, etc) check that self.current_action are
#       correct

class Meld(object):
  # TODO: Credit this function, fix style issues
  @classmethod
  def decode(cls, data):
    data = int(data)
    meld = Meld()
    meld.data = data
    meld.fromPlayer = data & 0x3
    if data & 0x4:
      meld.decodeChi()
    elif data & 0x18:
      meld.decodePon()
    elif data & 0x20:
      meld.decodeNuki()
    else:
      meld.decodeKan()
    return meld

  def __eq__(self, other):
    return isinstance(other, Meld) and self.data == other.data

  def __ne__(self, other):
    return not self.__eq__(other)

  def __str__(self):
    return ("%s, %s, %s" % (self.meld_type,
                            " ".join(str(t.num) for t in self.tiles),
                            self.called))

  def contains_tile(self, tile):
    tile_num = tile.num / 4
    for t in self.tiles:
      if t.num / 4 == tile_num: return True
    return False

  def decodeChi(self):
    self.meld_type = "chi"
    t0, t1, t2 = (self.data >> 3) & 0x3, (self.data >> 5) & 0x3, (self.data >> 7) & 0x3
    baseAndCalled = self.data >> 10
    self.called = baseAndCalled % 3
    base = baseAndCalled // 3
    base = (base // 7) * 9 + base % 7
    self.tiles = Tile(t0 + 4 * (base + 0)), Tile(t1 + 4 * (base + 1)), Tile(t2 + 4 * (base + 2))

  def decodePon(self):
    t4 = (self.data >> 5) & 0x3
    t0, t1, t2 = ((1,2,3),(0,2,3),(0,1,3),(0,1,2))[t4]
    baseAndCalled = self.data >> 9
    self.called = baseAndCalled % 3
    base = baseAndCalled // 3
    if self.data & 0x8:
      self.meld_type = "pon"
      self.tiles = Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base)
    else:
      self.meld_type = "chakan"
      self.tiles = Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base), Tile(t4 + 4 * base)

  def decodeKan(self):
    baseAndCalled = self.data >> 8
    if self.fromPlayer:
      self.called = baseAndCalled % 4
    else:
      self.called = None
      # del self.fromPlayer
    base = baseAndCalled // 4
    self.meld_type = "kan"
    self.tiles = Tile(4 * base), Tile(1 + 4 * base), Tile(2 + 4 * base), Tile(3 + 4 * base)

  def decodeNuki(self):
    self.called = None
    # del self.fromPlayer
    self.meld_type = "nuki"
    self.tiles = Tile(self.data >> 8)

class Tile(object):
  def __init__(self, num):
    self.num = num
    self.index = num / 4
    self.string = Tile.tile_str(num)
    self.suit = self.string[1]
    self.value = self.string[0]
    if num >= 108:
      self.number = None
      self.honor = True
    else:
      self.number = int(self.value)
      self.honor = False

  def __str__(self):
    return self.string

  def __int__(self):
    return self.num

  def __repr__(self):
    return "Tile(%d)" % self.num

  def __hash__(self):
    return self.num

  def __eq__(self, other):
    return isinstance(other, Tile) and self.num == other.num

  def __ne__(self, other):
    return not self.__eq__(other)

  @staticmethod
  def tile_str(tile_num):
    return Tile.TILES[tile_num / 4]

  UNICODE_TILES = """
    🀐 🀑 🀒 🀓 🀔 🀕 🀖 🀗 🀘
    🀙 🀚 🀛 🀜 🀝 🀞 🀟 🀠 🀡
    🀇 🀈 🀉 🀊 🀋 🀌 🀍 🀎 🀏
    🀀 🀁 🀂 🀃
    🀆 🀅 🀄
  """.split()

  TILES = """
    1s 2s 3s 4s 5s 6s 7s 8s 9s
    1p 2p 3p 4p 5p 6p 7p 8p 9p
    1m 2m 3m 4m 5m 6m 7m 8m 9m
    ew sw ww nw
    wd gd rd
  """.split()

  TERMINALS = {0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33}

class GameInfo(object):
  """
  An object representing information to be passed to a player.
  TODO: more detail

  Attributes:
    info_type: A string representing the kind of information this represents
    player: An int, 0-3, if the info is for one player, None if for all.
    data: Any necessary data for this GameInfo
  """
  action_count = 0

  def __init__(self, info_type, player, data):
    self.info_type = info_type
    self.player = player
    self.data = data
    self.action_id = GameInfo.action_count
    GameInfo.action_count += 1

  def __str__(self):
    return "Info (%d): info_type: %s  player: %s  data: %r" % (self.action_id, self.info_type, self.player, self.data)

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
    tiles = [Tile(x) for x in xrange(136)]
    random.shuffle(tiles)
    wall = Wall()
    wall.main_wall = collections.deque(tiles[:122])
    wall.kan_draws = tiles[122:126]
    wall.dora_indicators = tiles[126:131]
    wall.uradora_indicators = tiles[131:136]
    return wall

  def kan_draw_tile(self):
    logging.debug("Kan wall draw")
    if len(self.kan_draws) == 0:
      raise ValueError("Cannot draw from empty kan wall")
    return self.kan_draws.pop(0)

  def draw_tile(self):
    if len(self.main_wall) == 0:
      raise ValueError("Cannot draw from empty wall")
    return self.main_wall.popleft()

  def fill(self):
    all_tiles = set(Tile(x) for x in xrange(136))
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
    self.melds = None
    self.terminal = False
    self.current_action = None
    self.current_player = None
    self.melded = False  # A meld was just called
    self.kan = False  # A kan was just called
    self.action_id = 0

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
    # TODO: Try to simplify this. Probably turn some stuff into functions.
    # Give initial hands
    self.hands = [[] for _ in xrange(4)]
    self.melds = [[] for _ in xrange(4)]
    for player in xrange(4):
      self.hands[player] = self.draw_hand()
      logging.debug("Player %d hand: %s" % (player, self.hands[player]))
    yield self.set_action(GameInfo("start_hand", None, None))
    # In turn, players draw a tile. If possible, they may tsumo.
    self.current_player = self.kyoku
    while len(self.wall.main_wall) > 0:
      if (not self.melded) or self.kan:  # Need to draw a tile
        if self.kan:
          next_tile = self.wall.kan_draw_tile()
        else:
          next_tile = self.wall.draw_tile()
        # Draw and tsumo check
        yield self.set_action(GameInfo("draw_tile", self.current_player, next_tile))
        self.hands[self.current_player].append(next_tile)
        if self.hand_complete(self.current_player, None):
          yield self.set_action(GameInfo("can_tsumo", self.current_player, None))
      self.melded, self.kan = False, False
      # Discard and ron/naki check
      yield self.set_action(GameInfo("discard_tile", self.current_player, None))
      discard = self.discards[self.current_player][-1]
      # TODO: Consider caching these?
      for check in ("can_ron", "can_kan", "can_pon", "can_chi"):
        for player in xrange(4):
          if self.melded or player == self.current_player: continue
          func = getattr(self, check)
          if func(player, discard):
            data = {"from": self.current_player, "tile": discard}
            yield self.set_action(GameInfo(check, player, data))
      if not self.melded:
        self.current_player = (self.current_player + 1) % 4
    self.terminal = True

  # TODO: Convert everything to using tile objects
  def can_chi(self, player, tile):
    # Only next player can chi
    if (self.current_player + 1) % 4 != player: return False
    if tile.honor: return False  # Can't chi winds or dragons
    suit = tile.suit
    number = tile.number
    hand_numbers = set(x.number for x in self.hands[player] if x.suit == suit)
    if number + 1 in hand_numbers and number + 2 in hand_numbers: return True
    if number - 1 in hand_numbers and number + 1 in hand_numbers: return True
    if number - 2 in hand_numbers and number - 1 in hand_numbers: return True
    return False

  def can_pon(self, player, tile):
    count = sum(1 for x in self.hands[player] if x.index == tile.index)
    if count >= 2: return True
    return False

  def can_kan(self, player, tile):
    count = sum(1 for x in self.hands[player] if x.index == tile.index)
    if count >= 3: return True
    return False

  def can_ron(self, player, tile):
    return False

  def discard_tile(self, player, tile):
    """
    Discards a tile from the given player's hand
    """
    logging.debug("Discard tile: player: %d  tile: %d" % (player, tile))
    t = Tile(tile)
    assert t in self.hands[player]
    assert player == self.current_player
    self.hands[player].remove(t)
    self.discards[player].append(t)

  def meld(self, player, meld_object):
    logging.debug("Meld: player: %d  meld: %s" % (player, meld_object))
    for tile in meld_object.tiles:
      if tile in self.hands[player]:
        self.hands[player].remove(tile)
      else:
        discard = self.discards[self.current_player][-1]
        if tile != discard:
          raise ValueError("Meld is incorrect")
    self.melds[player].append(meld_object)
    self.current_player = player
    self.melded = True
    if meld_object.meld_type == "kan":
      self.kan = True
    # START HERE: Need to handle dead wall draw after kan


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

