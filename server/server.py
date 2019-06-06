import random
import logging

class Wall(object):
  def __init__(self):
    self.main_wall = []
    self.kan_draws = []
    self.dora_indicators = []
    self.uradora_indicators = []

  @staticmethod
  def random_wall():
    tiles = range(136)
    random.shuffle(tiles)
    wall = Wall()
    wall.main_wall = tiles[:122]
    wall.kan_draws = tiles[122:126]
    wall.dora_indicators = tiles[126:131]
    wall.uradora_indicators = tiles[131:136]

  def fill(self):
    all_tiles = set(range(136))
    used_tiles = set(self.main_wall)
    used_tiles.update(self.kan_draws)
    used_tiles.update(self.dora_indicators)
    used_tiles.update(self.uradora_indicators)
    remaining_tiles = all_tiles - used_tiles
    print self
    while len(self.main_wall) < 122:
      self.main_wall.append(remaining_tiles.pop())
    while len(self.kan_draws) < 4:
      self.kan_draws.append(remaining_tiles.pop())
    while len(self.dora_indicators) < 5:
      self.dora_indicators.append(remaining_tiles.pop())
    while len(self.uradora_indicators) < 5:
      self.uradora_indicators.append(remaining_tiles.pop())
    print self
    assert len(set(self.main_wall + self.kan_draws + self.dora_indicators +
                   self.uradora_indicators)) == 136

  def __str__(self):
    mw_str = "Main Wall: %s" % self.main_wall
    kd_str = "Kan Draws: %s" % self.kan_draws
    di_str = "Dora Indicators: %s" % self.dora_indicators
    udi_str = "Uradora Indicators: %s" % self.uradora_indicators
    return "\n".join((mw_str, kd_str, di_str, udi_str))

# NOTE: Making an assumption that player 0 draws all tiles first, then 1, etc.
#       This shouldn't matter (since it's randomized anyway) but if it does,
#       we will fix this later.
