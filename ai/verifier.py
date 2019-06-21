from ai.verifier_ai import Action, VerifierAI
from gamestate.gamestate import Wall, Tile
from server.server import Server
import logging
import argparse
import xml.etree.cElementTree as ET
import collections

def start_wall(attribs):
  """
  Take the attributes of an INIT tag and begin forming a Wall object.

  For the verifier to work, we need the server to distribute the same tiles as
  were distributed in the game we're verifying and in the same order. To do this
  we build a Wall object with the tiles in the correct order. This starts that
  wall object with the tiles specified in the INIT tag of the mjlog file.

  Args:
    attrib: a dictionary of attributes from an INIT tag. Particularly, we care
            about hai0-hai3, and seed (which contains the dora indicator)
  Returns:
    an (incomplete) Wall object
  """
  wall = Wall()
  for hand in ("hai0", "hai1", "hai2", "hai3"):
    tiles = [Tile(int(x)) for x in attribs[hand].split(",")]
    wall.main_wall.extend(tiles)
  wall.dora_indicators.append(Tile(int(attribs["seed"].split(",")[-1])))
  return wall

def get_actions_and_walls(filename):
  """
  Creates four lists of Action objects for the verifier AI, representing the
  actions four players will take to verify the correctness of the mahjong
  server. Also returns a list of Wall objects for the server to use.
  None is returned in the case of an mjlog we don't want to use for
  verification

  Args:
    filename: the filename of an mjlog file.
  Returns:
    A tuple of (Action lists, Wall list).
      First, a list of four lists of Action objects. list[0] will have actions
      for player #0, list[1] for player #1, and so forth.
      Second, a list of Walls for the server to use to duplicate this game.
    If the file is invalid for some reason (wrong lobby type, incomplete,
    disconnection, etc) this will return None.
  """
  # TODO: Make copies of actions, in case verifier_ai wanted to modify?
  # TODO: Break this out into more functions.
  actions = [collections.deque() for _ in range(4)]
  walls = []
  xml_tree = ET.parse(filename)
  root = xml_tree.getroot()
  last_draw = None
  current_wall = None
  kan_draw_next = False
  last_meld_player = None
  for element in root:
    logging.debug("Element: %s" % element.tag)
    logging.debug("Attributes: %s" % element.attrib)
    if element.tag == "AGARI":
      action = Action("hand_finished", element.attrib, None)
      for player in xrange(4):
        actions[player].append(action)
      if "doraHaiUra" in element.attrib:
        uradora = [Tile(int(x)) for x in element.attrib["doraHaiUra"].split(",")]
        current_wall.uradora_indicators = uradora
      current_wall.fill()
      walls.append(current_wall)
      current_wall = None
    elif element.tag == "TAIKYOKU":
      pass # TODO
    elif element.tag == "UN":
      pass # TODO: return None for insufficient rating?
    elif element.tag[0] in "TUVW":  # Draw a tile
      player = ord(element.tag[0]) - 84   # ord("T") = 84
      tile = Tile(int(element.tag[1:]))
      actions[player].append(Action("draw_tile", {"tile": tile}, None))
      last_draw = player
      if kan_draw_next:
        current_wall.kan_draws.append(tile)
        kan_draw_next = False
      else:
        current_wall.main_wall.append(tile)
    elif element.tag == "DORA":
      current_wall.dora_indicators.append(Tile(int(element.attrib["hai"])))
      if last_draw == last_meld_player:
        # If the person who drew last called this kan, it's a self-kan, and the
        # next tile drawn will be a kan draw, so we need to put that in the wall
        # correctly. TODO: Do this from the meld object?
        kan_draw_next = True
    elif element.tag == "GO":
      pass # TODO: return None for bad lobby types.
    elif element.tag[0] in "DEFG":  # Discard a tile
      player = ord(element.tag[0]) - 68   # ord("D") = 68
      tile = int(element.tag[1:])
      actions[player].append(Action("discard_tile", {}, tile))
    elif element.tag == "REACH":
      # Riichi is in two steps, declaring, then discarding. We only want an
      # action for the first one.
      if element.attrib["step"] == "2": continue
      player = int(element.attrib["who"])
      actions[player].append(Action("should_call_riichi", None, True))
    elif element.tag == "N":
      player = int(element.attrib["who"])
      last_meld_player = player
      meld = int(element.attrib["m"])
      actions[player].append(Action("should_call_meld", {"meld": meld}, None))
    elif element.tag == "INIT":
      action = Action("start_hand", element.attrib, None)
      for player in xrange(4):
        actions[player].append(action)
      last_draw = None
      kan_draw_next = False
      current_wall = start_wall(element.attrib)
      last_meld_player = None
    elif element.tag == "RYUUKYOKU":
      if "type" in element.attrib and element.attrib["type"] == "yao9":
        actions[last_draw].append(Action("should_call_ryuukyoku", None, True))
    elif element.tag == "SHUFFLE":
      pass
    else:
      logging.warning("Unhandled element: %s %s" % (element.tag, element.attrib))
  return actions, walls

if __name__ == "__main__":
  parser = argparse.ArgumentParser("Verify server using mjlog files")
  parser.add_argument("filename", help="The mjlog file to verify with")
  parser.add_argument("-ll", "--loglevel",
                      help="Logging level to show (debug/info/warning/error)")
  args = parser.parse_args()
  if args.loglevel:
    level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(level, int):
      raise ValueError("Invalid log level: %s" % args.loglevel)
  else:
    level = logging.WARNING
  logging.basicConfig(format='%(asctime)s.%(msecs)d [%(filename)s:%(lineno)d] %(levelname).1s: %(message)s',
    datefmt='%y%m%d:%H%M%S',
    level=level)
  logging.basicConfig(level=level)

  logging.info("Verifying %s" % args.filename)

  action_lists, walls = get_actions_and_walls(args.filename)
  players = [VerifierAI(i, action_lists[i]) for i in xrange(4)]
  # TODO: try/catch so we can do multiple files
  s = Server(players, walls)
  s.start_play()
  #logging.warning("%s could not be verified" % args.filename)

  """
  for x in action_lists[0]:
    print x
  for x in walls:
    print x
  """
