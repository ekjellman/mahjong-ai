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
    meld.fromPlayer = data & 0x3
    if data & 0x4:
      meld.decodeChi(data)
    elif data & 0x18:
      meld.decodePon(data)
    elif data & 0x20:
      meld.decodeNuki(data)
    else:
      meld.decodeKan(data)
    return meld

  def __str__(self):
    return "Meld type: %s   Tiles: %s" % (self.meld_type, " ".join(str(t) for t in self.tiles))

  def decodeChi(self, data):
    self.meld_type = "chi"
    t0, t1, t2 = (data >> 3) & 0x3, (data >> 5) & 0x3, (data >> 7) & 0x3
    baseAndCalled = data >> 10
    self.called = baseAndCalled % 3
    base = baseAndCalled // 3
    base = (base // 7) * 9 + base % 7
    self.tiles = Tile(t0 + 4 * (base + 0)), Tile(t1 + 4 * (base + 1)), Tile(t2 + 4 * (base + 2))

  def decodePon(self, data):
    t4 = (data >> 5) & 0x3
    t0, t1, t2 = ((1,2,3),(0,2,3),(0,1,3),(0,1,2))[t4]
    baseAndCalled = data >> 9
    self.called = baseAndCalled % 3
    base = baseAndCalled // 3
    if data & 0x8:
      self.meld_type = "pon"
      self.tiles = Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base)
    else:
      self.meld_type = "chakan"
      self.tiles = Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base), Tile(t4 + 4 * base)

  def decodeKan(self, data):
    baseAndCalled = data >> 8
    if self.fromPlayer:
      self.called = baseAndCalled % 4
    else:
      del self.fromPlayer
    base = baseAndCalled // 4
    self.meld_type = "kan"
    self.tiles = Tile(4 * base), Tile(1 + 4 * base), Tile(2 + 4 * base), Tile(3 + 4 * base)

  def decodeNuki(self, data):
    del self.fromPlayer
    self.meld_type = "nuki"
    self.tiles = Tile(data >> 8)

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

  def initialize_hand(self, tile_string):
    self.hand = set(int(t) for t in tile_string.split(","))
    assert len(self.hand) == 13

  def __str__(self):
    hand_string = " ".join(Tile.tile_str(t) for t in sorted(self.hand))
    discard_string = " ".join(Tile.tile_str(t) for t in self.discards)
    meld_string = " | ".join(str(m) for m in self.melds)
    return "Hand: %s\nDiscards: %s\nMelds: %s\n" % (hand_string, discard_string, meld_string)

class GameState(object):
  def __init__(self):
    self.hands = [Hand() for i in xrange(4)]
    pass

  #START HERE: Go through handle_elements, replacing every print with an update
  #            of the game state, noting ones we're skipping.
  #            Make a __str__ method for GameState

def handle_elements(elements):
  for element in elements:
    if element.tag == "INIT":
      print "Start of hand"
      print "Points: ", element.attrib["ten"]
      print "Hand 0: ", element.attrib["hai0"]
      print "Hand 1: ", element.attrib["hai1"]
      print "Hand 2: ", element.attrib["hai2"]
      print "Hand 3: ", element.attrib["hai3"]
      print "Dealer: ", element.attrib["oya"]
      print "Seed  : ", element.attrib["seed"]
      seed_info = element.attrib["seed"].split(",")
      round_num = int(seed_info[0])
      assert round_num % 4 == int(element.attrib["oya"])
    elif 84 <= ord(element.tag[0]) <= 87:  # T-W
      if element.tag == "TAIKYOKU":
        print "Start of match"
        print "Dealer: ", element.attrib["oya"]
        assert element.attrib["oya"] == "0"
      elif element.tag == "UN":
        if "dan" in element.attrib:
          print "Player data:"
          print "Name 0: ", element.attrib["n0"]
          print "Name 1: ", element.attrib["n1"]
          print "Name 2: ", element.attrib["n2"]
          print "Name 3: ", element.attrib["n3"]
          print "Dan   : ", element.attrib["dan"]
          print "Rating: ", element.attrib["rate"]
          print "Sexes : ", element.attrib["sx"]
        else:
          print "User connected: " % element.attrib
      else:
        player = ord(element.tag[0]) - 84
        tile = int(element.tag[1:])
        print "Player %d drew tile %d" % (player, tile)
    elif 68 <= ord(element.tag[0]) <= 71:  # D-G
      if element.tag == "DORA":
        print "New dora: ", element.attrib["hai"]
      elif element.tag == "GO":
        print "Room info"
        print "Lobby type: ", element.attrib["type"]
        print "Lobby number: ", element.attrib["lobby"] if "lobby" in element.attrib else "None"
      else:
        player = ord(element.tag[0]) - 68
        tile = int(element.tag[1:])
        print "Player %d discarded tile %d" % (player, tile)
    elif element.tag == "SHUFFLE":
      continue   # Shuffle has no useful info for us
    elif element.tag == "N":
      print "Player %d makes a meld" % int(element.attrib["who"])
      print "Meld: %s %s" % (element.attrib["m"], bin(int(element.attrib["m"]) & 0xFFFF))
      print "Decode: %s" % Meld.decode(element.attrib["m"])
    elif element.tag == "AGARI":
      print "Player %s wins" % element.attrib["who"]
      if element.attrib["who"] == element.attrib["fromWho"]:
        print "Tsumo"
      else:
        print "Ron from player %s" % element.attrib["fromWho"]
        print "Tiles: ", element.attrib["hai"]
        print "Waits: ", element.attrib["machi"]
        print "Melds: ",
        if "m" in element.attrib:
          for m in element.attrib["m"].split(","):
            print m, bin(int(m) & 0xFFFF)
        # skipping ba, ten, yaku, doraHai, sc
    elif element.tag == "REACH":
      if element.attrib["step"] == "1":
        print "Player %s declared riichi" % element.attrib["who"]
      elif element.attrib["step"] == "2":
        print "Player paid 1000 points"
      else:
        raise
    # START HERE (Ryuukyoku: Can also tell who is tenpai here)
    elif element.tag == "RYUUKYOKU":
      print "Scores and changes: ", element.attrib["sc"]
      print "Player 0 tiles: ", show_hand(element.attrib["hai0"]) if "hai0" in element.attrib else "noten"
      print "Player 1 tiles: ", show_hand(element.attrib["hai1"]) if "hai1" in element.attrib else "noten"
      print "Player 2 tiles: ", show_hand(element.attrib["hai2"]) if "hai2" in element.attrib else "noten"
      print "Player 3 tiles: ", show_hand(element.attrib["hai3"]) if "hai3" in element.attrib else "noten"
      # skipping ba
    elif element.tag == "BYE":
      print "Player %s left" % element.attrib["who"]
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



