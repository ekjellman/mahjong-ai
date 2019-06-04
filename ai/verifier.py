from verifier_ai import Action
import logging
import argparse

def get_actions(filename):
  """
  Creates four lists of Action objects for the verifier AI, representing the
  actions four players will take to verify the correctness of the mahjong
  server.

  Args:
    filename: the filename of an mjlog file.
  Returns:
    A list of four lists of Action objects. list[0] will have actions for player
    #0, list[1] for player #1, and so forth.
  """
  # START HERE


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

  action_lists = get_actions(args.filename)
