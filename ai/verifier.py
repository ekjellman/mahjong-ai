from verifier_ai import Action
import logging
import argparse
import xml.etree.cElementTree as ET

def get_actions(filename):
  """
  Creates four lists of Action objects for the verifier AI, representing the
  actions four players will take to verify the correctness of the mahjong
  server. None is returned in the case of an mjlog we don't want to use for
  verification

  Args:
    filename: the filename of an mjlog file.
  Returns:
    A list of four lists of Action objects. list[0] will have actions for player
    #0, list[1] for player #1, and so forth.
    If the file is invalid for some reason (wrong lobby type, incomplete,
    disconnection, etc) this will return None.
  """
  # TODO: Make copies of actions, in case verifier_ai wanted to modify?
  # TODO: Break this out into more functions.
  actions = [[] for _ in range(4)]
  xml_tree = ET.parse(filename)
  root = xml_tree.getroot()
  last_draw = None
  for element in root:
    logging.debug("Element: %s" % element.tag)
    logging.debug("Attributes: %s" % element.attrib)
    if element.tag == "AGARI":
      action = Action("hand_finished", element.attrib, None)
      for player in xrange(4):
        actions[player].append(action)
    elif element.tag == "TAIKYOKU":
      pass # TODO
    elif element.tag == "UN":
      pass # TODO: return None for insufficient rating?
    elif element.tag[0] in "TUVW":  # Draw a tile
      player = ord(element.tag[0]) - 84   # ord("T") = 84
      tile = int(element.tag[1])
      actions[player].append(Action("draw_tile", {"tile": tile}, None))
      last_draw = player
    elif element.tag == "DORA":
      pass # No action involved
    elif element.tag == "GO":
      pass # TODO: return None for bad lobby types.
    elif element.tag[0] in "DEFG":
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
      meld = int(element.attrib["m"])
      actions[player].append(Action("should_call_meld", {"meld": meld}, None))
    elif element.tag == "INIT":
      action = Action("start_hand", element.attrib, None)
      for player in xrange(4):
        actions[player].append(action)
      last_draw = None
    elif element.tag == "RYUUKYOKU":
      if "type" in element.attrib and element.attrib["type"] == "yao9":
        actions[last_draw].append(Action("should_call_ryuukyoku", None, True))
    elif element.tag == "SHUFFLE":
      pass
    else:
      logging.warning("Unhandled element: %s %s" % (element.tag, element.attrib))

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
  logging.basicConfig(level=level)

  action_lists = get_actions(args.filename)
