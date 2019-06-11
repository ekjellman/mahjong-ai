import logging
import random

class Wall(object):
  def __init__(self):
    self.main_wall = []
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
    wall.main_wall = tiles[:122]
    wall.kan_draws = tiles[122:126]
    wall.dora_indicators = tiles[126:131]
    wall.uradora_indicators = tiles[131:136]
    return wall

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
    assert len(set(self.main_wall + self.kan_draws + self.dora_indicators +
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

  def get_round_name(self):
    wind = ("East", "South", "West", "North")[self.wind]
    return "%s %d" % (wind, self.kyoku + 1)

  def game_over(self):
    return False # TODO

  def start_hand(self):
    self.wall = self.wall_generator()
    logging.info("Starting %s" % self.get_round_name())
    logging.debug(self.wall)

