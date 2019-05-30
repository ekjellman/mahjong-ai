# coding: utf-8
# Module to convert mjlogs into a data format to feed to a NN for training

# My first goal is to try to train a NN to determine if an opponent is in tenpai
# or not. To create the data for this NN, we'll read logs from tenhou to get
# a bunch of game states we can feed into a NN.

# Items needed for state:
# Players discards
# Players melds
# dora? dealer? Don't know.

import collections
import copy
import itertools
import os
import random
import sys
import xml.etree.cElementTree as ET

# Tile/Meld modified from
# https://github.com/NegativeMjark/tenhou-log/blob/master/TenhouDecoder.py
###

DEBUG = False

class Tile(object):
  def __init__(self, num):
    self.num = num

  def index(self):
    return self.num / 4

  def __str__(self):
    return Tile.TILES[self.num / 4]

  @staticmethod
  def tile_str(num):
    return Tile.TILES[num / 4]

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

class Meld(object):
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

  def __str__(self):
    return ("%s, %s, %s" % (self.meld_type,
                            " ".join(str(t) for t in self.tiles),
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

###

def show_hand(hai):
  tiles = [Tile.TILES[int(t) / 4] for t in hai.split(",")]
  unicode_tiles = [Tile.UNICODE_TILES[int(t) / 4] for t in hai.split(",")]
  return "\n%s\n%s" % (" ".join(tiles), " ".join(unicode_tiles))

def get_elements(filename):
  tree = ET.parse(filename)
  root = tree.getroot()
  elements = [c for c in root]
  return elements

class Hand(object):
  def __init__(self):
    self.hand = None
    self.discards = []
    self.tsumogiri = []
    self.melds = []
    self.riichi = -1
    self.last_play = None
    self.last_draw = None

  def initialize_hand(self, tile_string):
    self.hand = set(int(t) for t in tile_string.split(","))
    assert len(self.hand) == 13

  def draw(self, tile):
    self.hand.add(tile)
    self.last_draw = tile
    assert len(self.hand) + len(self.melds) * 3 == 14

  def discard(self, tile):
    self.hand.remove(tile)
    self.discards.append(tile)
    if self.last_draw is not None:
      self.tsumogiri.append(tile == self.last_draw)
    else:
      self.tsumogiri.append(False)   # Called Chi/Pon/Kan/etc
    assert len(self.discards) == len(self.tsumogiri)
    self.last_play = tile
    self.last_draw = None
    #print self
    #print "Tenpai: ", self.is_tenpai()
    assert len(self.hand) + len(self.melds) * 3 == 13
    if self.riichi != -1:
      assert self.is_tenpai()

  def declare_riichi(self):
    # TODO: Assert tenpai
    self.riichi = len(self.discards)

  def meld(self, meld_object):
    if meld_object.meld_type == "chakan":
      # Find the pon we're upgrading
      meld_index = None
      for i, mo in enumerate(self.melds):
        if mo.contains_tile(meld_object.tiles[0]):
          meld_index = i
          break
      assert meld_index is not None
      # Replace it with the new chakan
      self.melds.pop(i)
      self.melds.append(meld_object)
      self.hand.remove(meld_object.tiles[3].num)  # Last tile in chakan is new
      self.last_play = meld_object.tiles[3].num   # Can rob a chankan
    else:
      for i, tile in enumerate(meld_object.tiles):
        tile_num = tile.num
        if meld_object.called == i:
          continue
        self.hand.remove(tile.num)
      self.melds.append(meld_object)

  def kokushi_tenpai(self):
    if len(self.hand) < 13: return False  # Must be closed
    tiles = set()
    for tile in self.hand:
      if (tile / 4) in Tile.TERMINALS:
        tiles.add(tile / 4)
      else:
        return False
    return len(tiles) >= 12  # Have at least 12 unique terminals out of 13

  def seven_pairs_tenpai(self, counts):
    if len(self.hand) < 13: return False
    pairs = 0
    for count in counts:
      if count == 2:
        pairs += 1
    return pairs == 6

  def is_tenpai(self):
    if self.kokushi_tenpai(): return True
    counts = [0] * 34
    for tile in self.hand:
      counts[tile / 4] += 1
    if len(self.hand) + len(self.melds) * 3 == 13:
      if self.tenpai_inner(counts, len(self.melds), 0): return True
      #if self.tenpai_inner(counts, 0, 0): return True
    else:
      return None  # TODO
    if self.seven_pairs_tenpai(counts): return True
    return False

  @staticmethod
  def tenpai_inner(counts, melds, pairs, start_index=0):
    # Base cases
    if melds == 4:  # Single wait on a pairing tile
      assert sum(counts) == 1
      return True
    if melds == 3 and pairs == 1:
      assert sum(counts) == 2
      if any(count == 2 for count in counts):   # Incomplete triplet
        return True
      return Hand.incomplete_run(counts)
    # Recursive cases
    for meld_start in xrange(start_index, len(Tile.TILES)):
      if counts[meld_start] >= 3:
        # Try triplet
        counts[meld_start] -= 3
        if Hand.tenpai_inner(counts, melds + 1, pairs, meld_start): return True
        counts[meld_start] += 3
      if counts[meld_start] >= 2 and pairs == 0:
        # Try pair
        counts[meld_start] -= 2
        if Hand.tenpai_inner(counts, melds, pairs + 1, meld_start): return True
        counts[meld_start] += 2
      if meld_start < 27 and meld_start % 9 <= 6:  # Suit, and value 0-6
        # Try run
        if counts[meld_start] >= 1 and counts[meld_start+1] >= 1 and counts[meld_start+2] >= 1:
          counts[meld_start] -= 1
          counts[meld_start+1] -= 1
          counts[meld_start+2] -= 1
          if Hand.tenpai_inner(counts, melds + 1, pairs, meld_start): return True
          counts[meld_start] += 1
          counts[meld_start+1] += 1
          counts[meld_start+2] += 1
    return False

  @staticmethod
  def incomplete_run(counts):
    for i in xrange(len(counts)):
      if counts[i] == 1:
        if i >= 27: return False  # Honors can't be part of a run
        value = (i % 9) + 1
        if value > 8: return False  # Incomplete runs can't start with a 9
        if counts[i + 1] == 1: return True
        if value <= 7 and counts[i + 2] == 1: return True
        return False
    assert False  # Should only be run if sum(counts) is 2, and no element of
                  # counts is 2

  def __str__(self):
    hand_string = " ".join(Tile.tile_str(t) for t in sorted(self.hand))
    discard_string = " ".join(Tile.tile_str(t) for t in self.discards)
    meld_string = " | ".join(str(m) for m in self.melds)
    tenpai_string = "Tenpai: %r   Riichi: %r" % (self.is_tenpai(), self.riichi)
    return "Hand: %s\nDiscards: %s\nMelds: %s\n%s" % (hand_string, discard_string, meld_string, tenpai_string)

  def nn_output(self):
    discards = [str(t / 4) for t in self.discards]
    meld_tiles = []
    for meld in self.melds:
      meld_tiles.extend(t.num/4 for t in meld.tiles)
      while len(meld_tiles) % 4 != 0:
        meld_tiles.append(-1)
    discard_string = ",".join(discards)
    meld_string = ",".join(str(x) for x in meld_tiles)
    tsumogiri_string = ",".join("T" if x else "F" for x in self.tsumogiri)
    return "%s|%d|%s|%s" % (",".join(discards), self.riichi, meld_string,
                         tsumogiri_string)

class GameState(object):
  def __init__(self):
    self.hands = [Hand() for i in xrange(4)]
    self.dealer = None
    self.dora = []
    self.finished = False

  def nn_output(self):
    lines = []
    for h in self.hands:
      lines.append(h.nn_output())
    lines.append(",".join(str(h.is_tenpai())[0] for h in self.hands))
    return "\n".join(lines)

  def __str__(self):
    pieces = []
    pieces.append("Dealer: %d" % self.dealer)
    for i, hand in enumerate(self.hands):
      pieces.append("Player %d:" % i)
      pieces.append(str(hand))
    return "\n".join(pieces)

  def draw(self, player, tile):
    self.hands[player].draw(tile)

  def discard(self, player, tile):
    self.hands[player].discard(tile)

  def meld(self, player, meld_object):
    self.hands[player].meld(meld_object)

  def initialize_hand(self, player, hai):
    self.hands[player].initialize_hand(hai)

  def set_dealer(self, player):
    self.dealer = player

  def add_dora(self, tile):
    self.dora.append(tile)

  def declare_riichi(self, player):
    self.hands[player].declare_riichi()

  def agari(self, player, from_player, winning_hand, winning_melds):
    # TODO: assert tenpai
    if player != from_player:
      self.hands[player].draw(self.hands[from_player].last_play)
      finished_hand = set(int(t) for t in winning_hand.split(","))
      assert finished_hand == self.hands[player].hand
      melds = [Meld.decode(s) for s in winning_melds.split(",")] if winning_melds else []
      for meld in melds:
        assert meld in self.hands[player].melds
    self.finished = True

  def ryuukyoku(self, hands, kind=None):
    self.finished = True
    # TODO: Assert tenpai
    for player, hand in enumerate(hands):
      if hand:
        finished_hand = set(int(t) for t in hand.split(","))
        assert finished_hand == self.hands[player].hand
      else:
        # There are some cases where the tiles in the ryuukyoku tag are not
        # a tenpai hand, and they're so rare I'm just not going to fix this
        # assertion for them. (i.e.: double riichi into kyuushuu kyuuhai)
        assert kind or self.hands[player].riichi == -1

def reservoir(held, current, count):
  if held is None:
    result = copy.deepcopy(current)
  else:
    if random.random() < (1.0 / count):
      result = copy.deepcopy(current)
    else:
      result = held
  return result

def update_stats(game_state, player, stats):
  draws = len(game_state.hands[player].discards)
  melds = len(game_state.hands[player].melds)
  opponent_riichi = sum(game_state.hands[x].riichi != -1 for x in (0, 1, 2, 3) if x != player)
  noten, tenpai = stats.get((draws, melds, opponent_riichi), (0, 0))
  in_tenpai = game_state.hands[player].is_tenpai()
  if in_tenpai:
    tenpai += 1
  else:
    noten += 1
  stats[draws, melds, opponent_riichi] = (noten, tenpai)

def handle_elements(elements):
  game_state = None
  random_state = None
  draw_count = 0
  stats = {}   # Dictionary from (draws, melds, opponent riichi) -> (noten count, tenpai count)
  collected_states = []
  for element in elements:
    # TODO: Make debug flag
    if DEBUG: print element.tag, element.attrib
    if element.tag == "INIT":
      game_state = GameState()
      if random_state:
        collected_states.append(random_state)
      random_state = None
      draw_count = 0
      # Skipping ten
      game_state.initialize_hand(0, element.attrib["hai0"])
      game_state.initialize_hand(1, element.attrib["hai1"])
      game_state.initialize_hand(2, element.attrib["hai2"])
      game_state.initialize_hand(3, element.attrib["hai3"])
      game_state.set_dealer(int(element.attrib["oya"]))
      seed_info = element.attrib["seed"].split(",")
      round_num = int(seed_info[0])
      assert round_num % 4 == int(element.attrib["oya"])
    elif 84 <= ord(element.tag[0]) <= 87:  # T-W
      if element.tag == "TAIKYOKU":
        assert element.attrib["oya"] == "0"
      elif element.tag == "UN":
        if "dan" in element.attrib:
          # skipping dan, sx
          for name in ("n0", "n1", "n2", "n3"):
            if name not in element.attrib or not element.attrib[name]:
              return "Aborted, missing name %s" % name, None, None
          ratings = [float(r) for r in element.attrib["rate"].split(",")]
          if min(ratings) < 2000.0:
            return "Aborted, minimum rating too low", None, None
        else:
          return "Aborted, no dan?", None, None
      else:
        player = ord(element.tag[0]) - 84
        tile = int(element.tag[1:])
        draw_count += 1
        random_state = reservoir(random_state, game_state, draw_count)
        update_stats(game_state, player, stats)
        game_state.draw(player, tile)
    elif 68 <= ord(element.tag[0]) <= 71:  # D-G
      if element.tag == "DORA":
        game_state.add_dora(int(element.attrib["hai"]))
      elif element.tag == "GO":
        pass
        #print "Room info"
        #print "Lobby type: ", element.attrib["type"]
        #print "Lobby number: ", element.attrib["lobby"] if "lobby" in element.attrib else "None"
      else:
        player = ord(element.tag[0]) - 68
        tile = int(element.tag[1:])
        game_state.discard(player, tile)
    elif element.tag == "SHUFFLE":
      continue   # Shuffle has no useful info for us
    elif element.tag == "N":
      player = int(element.attrib["who"])
      meld_object = Meld.decode(element.attrib["m"])
      game_state.meld(player, meld_object)
    elif element.tag == "AGARI":
      # Skipping machi, ba, ten, yaku, doraHai, sc
      winner = int(element.attrib["who"])
      from_player = int(element.attrib["fromWho"])
      winning_hand = element.attrib["hai"]
      winning_melds = element.attrib["m"] if "m" in element.attrib else None
      game_state.agari(winner, from_player, winning_hand, winning_melds)
    elif element.tag == "REACH":
      if element.attrib["step"] == "1":
        game_state.declare_riichi(int(element.attrib["who"]))
      elif element.attrib["step"] == "2":
        # print "Player paid 1000 points"
        pass
      else:
        raise
    elif element.tag == "RYUUKYOKU":
      # Skipping sc, ba
      hai0 = element.attrib["hai0"] if "hai0" in element.attrib else None
      hai1 = element.attrib["hai1"] if "hai1" in element.attrib else None
      hai2 = element.attrib["hai2"] if "hai2" in element.attrib else None
      hai3 = element.attrib["hai3"] if "hai3" in element.attrib else None
      kind = element.attrib["type"] if "type" in element.attrib else None
      game_state.ryuukyoku([hai0, hai1, hai2, hai3], kind)
    elif element.tag == "BYE":
      return "Aborted, player disconnected", None, None
    else:
      print "UNHANDLED: ", element.tag, element.attrib
      return "Aborted, could not parse file", None, None
  if random_state:
    collected_states.append(random_state)
  return "OK", collected_states, stats

def handle_file(filename):
  try:
    elements = get_elements(filename)
    result = handle_elements(elements)
    return result
  except ValueError as e:
    print "COULD NOT HANDLE %s" % filename
    print e

def output_gamestates(file_handle, states):
  for state in states:
    output = state.nn_output()
    file_handle.write(output)
    file_handle.write("\n")

def combine_stats(total, new_stats):
  for key in new_stats:
    noten, tenpai = new_stats[key]
    total_noten, total_tenpai = total.get(key, (0, 0))
    total_noten += noten
    total_tenpai += tenpai
    total[key] = (total_noten, total_tenpai)

def output_stats(stats_output, total_stats):
  for key in total_stats:
    draws, melds, riichi = key
    noten, tenpai = total_stats[key]
    stats_output.write("%d,%d,%d,%d,%d" % (draws, melds, riichi, noten, tenpai))
    stats_output.write("\n")

"""
tenpai_counts = Hand.generate_tenpai_counts()
print len(tenpai_counts)
sys.exit(1)
"""

if len(sys.argv) > 1:
  arg = sys.argv[1]
else:
  arg = "2018010100gm-00a9-0000-0d318262.mjlog"
if len(sys.argv) > 3:
  stats_output = open(sys.argv[2], "w")
  gamestate_output = open(sys.argv[3], "w")
else:
  stats_output, gamestate_output = None, None
count = 0
total_stats = {}
if os.path.isdir(arg):
  filenames = [f for f in os.listdir(arg) if os.path.isfile(os.path.join(arg, f))]
  for i, f in enumerate(filenames):
    if f.endswith("mjlog"):
      filename = os.path.join(arg, f)
      print "(%7d) Parsing %s" % (i, filename)
      try:
        message, collected_states, stats = handle_file(filename)
        if message == "OK":
          count += 1
          if gamestate_output:
            output_gamestates(gamestate_output, collected_states)
          combine_stats(total_stats, stats)
        else:
          print message
      except AssertionError:
        print "ASSERTION FAILED"
      except ET.ParseError:
        print "XML PARSE FAILED"
    else:
      print "Skipping %s" % f
  if stats_output:
    output_stats(stats_output, total_stats)
elif os.path.isfile(arg):
  message, collected_states, stats = handle_file(arg)
  count += 1
print "%d files parsed" % count
if stats_output: stats_output.close()
if gamestate_output: gamestate_output.close()

"""
hand = Hand.tenhou_string_to_hand(sys.argv[1])
print hand
"""
"""
  def shanten(self):
    counts = [0] * 34
    for tile in self.hand:
      counts[tile / 4] += 1
    if len(self.hand) < 13:
      best = len(self.hand)
    else:
      best = kokushi_shanten(self)
      best = min(best, seven_pairs_shanten(counts))
    return best

  def kokushi_shanten(self):
    assert len(self.hand) >= 13
    tiles = []
    for tile in self.hand:
      if (tile / 4) in Tile.TERMINALS:
        tiles.append(tile / 4)
    tile_set = set(tiles)
    return 13 - min(len(tile_set) + 1, len(tiles))

  @staticmethod
  def seven_pairs_shanten(counts):
    pairs = 0
    for count in counts:
      if count >= 2: pairs += 1
    return 6 - pairs

  @staticmethod
  def tenhou_string_to_hand(s):
    # TODO: Handle reds
    hand_tiles = []
    current = []
    for c in s:
      if c in "smp":
        for number in current:
          tile_str = number + c
          tile_index = Tile.TILES.index(tile_str)
          assert tile_index != -1
          hand_tiles.append(tile_index)
        current = []
      elif c == "z":
        for number in current:
          hand_tiles.append(int(number) + 27 - 1)
        current = []
      else:
        current.append(c)
    assert not current
    counts = collections.Counter(hand_tiles)
    result = Hand()
    result.hand = set()
    for tile in counts:
      assert counts[tile] <= 4
      for i in xrange(counts[tile]):
        result.hand.add(tile * 4 + i)
    print result.hand
    return result
"""

