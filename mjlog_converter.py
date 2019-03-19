# coding: utf-8
# Module to convert mjlogs into a data format to feed to a NN for training

# My first goal is to try to train a NN to determine if an opponent is in tenpai
# or not. To create the data for this NN, we'll read logs from tenhou to get
# a bunch of game states we can feed into a NN.

# TODO:
# Check tenpai using ryuukyoku
# Check tenpai using reach
# Get rid of all logs of three-player games
# Get rid of games with players under a certain level
# Get rid of games with disconnections?

# Items needed for state:
# Players discards
# Players melds
# dora? dealer? Don't know.

import xml.etree.cElementTree as ET
import sys

# Taken from
# https://github.com/NegativeMjark/tenhou-log/blob/master/TenhouDecoder.py

###

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
    self.melds = []
    self.riichi = False

  def initialize_hand(self, tile_string):
    self.hand = set(int(t) for t in tile_string.split(","))
    assert len(self.hand) == 13

  def draw(self, tile):
    self.hand.add(tile)
    assert len(self.hand) + len(self.melds) * 3 == 14

  def discard(self, tile):
    self.hand.remove(tile)
    self.discards.append(tile)
    print self
    print "Tenpai: ", self.is_tenpai()
    assert len(self.hand) + len(self.melds) * 3 == 13
    if self.riichi:
      assert self.is_tenpai()

  def declare_riichi(self):
    # TODO: Assert tenpai
    self.riichi = True

  def meld(self, meld_object):
    for i, tile in enumerate(meld_object.tiles):
      tile_num = tile.num
      if meld_object.called == i:
        continue
      self.hand.remove(tile.num)
    self.melds.append(meld_object)

  def is_tenpai(self):
    # TODO: Kokushi, 7 pairs
    # START HERE
    counts = [0] * 34
    for tile in self.hand:
      counts[tile / 4] += 1
    return self.tenpai_inner(counts, len(self.melds), 0)

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
    return "Hand: %s\nDiscards: %s\nMelds: %s" % (hand_string, discard_string, meld_string)

class GameState(object):
  def __init__(self):
    self.hands = [Hand() for i in xrange(4)]
    self.dealer = None
    self.dora = []
    self.abort = False
    self.finished = False

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
      self.hands[player].draw(self.hands[from_player].discards[-1])
      finished_hand = set(int(t) for t in winning_hand.split(","))
      assert finished_hand == self.hands[player].hand
      melds = [Meld.decode(s) for s in winning_melds.split(",")] if winning_melds else []
      for meld in melds:
        assert meld in self.hands[player].melds
    self.complete = True

  def ryuukyoku(self, hands):
    self.complete = True
    # TODO: Assert tenpai
    for player, hand in enumerate(hands):
      if hand:
        finished_hand = set(int(t) for t in hand.split(","))
        assert finished_hand == self.hands[player].hand
      else:
        assert not self.hands[player].riichi

  #START HERE: Go through handle_elements, replacing every print with an update
  #            of the game state, noting ones we're skipping.
  #            Make a __str__ method for GameState

def handle_elements(elements):
  game_state = None
  for element in elements:
    if element.tag == "INIT":
      if game_state:
        assert game_state.complete or game_state.abort
      game_state = GameState()
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
              print "Missing name %s, Aborting.", name
              game_state.abort = True
              return
          ratings = [float(r) for r in element.attrib["rate"].split(",")]
          if min(ratings) < 2000.0:
            game_state.abort = True
            return
        else:
          game_state.abort = True
          return
      else:
        player = ord(element.tag[0]) - 84
        tile = int(element.tag[1:])
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
    # START HERE (Ryuukyoku: Can also tell who is tenpai here)
    elif element.tag == "RYUUKYOKU":
      # Skipping sc, ba
      hai0 = element.attrib["hai0"] if "hai0" in element.attrib else None
      hai1 = element.attrib["hai1"] if "hai1" in element.attrib else None
      hai2 = element.attrib["hai2"] if "hai2" in element.attrib else None
      hai3 = element.attrib["hai3"] if "hai3" in element.attrib else None
      game_state.ryuukyoku([hai0, hai1, hai2, hai3])
    elif element.tag == "BYE":
      game_state.abort = True
      return
    else:
      print "UNHANDLED: ", element.tag, element.attrib
      raise ValueError("Could not parse file")



if len(sys.argv) > 1:
  filename = sys.argv[1]
else:
  filename = "2018010100gm-00a9-0000-0d318262.mjlog"
try:
  elements = get_elements(filename)
  handle_elements(elements)
except ValueError as e:
  print "COULD NOT HANDLE %s" % filename
  print e



