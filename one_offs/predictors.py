from abc import ABCMeta, abstractmethod
import sys

class Predictor(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def predict_gamestate(discards, tenpai_turns, melds):
    pass

class StupidPredictor(Predictor):
  def predict_gamestate(self, discards, tenpai_turns, melds):
    predictions = []
    for i in xrange(4):
      if tenpai_turns[i] != -1:
        predictions.append(1.0)
      else:
        predictions.append(0.0)
    return predictions

class StatsPredictor(Predictor):
  def __init__(self, filename):
    self.stats = {}
    with open(filename, "r") as file_in:
      for line in file_in:
        tokens = [int(x) for x in line.split(",")]
        discards, melds, riichi, noten, tenpai = tokens
        self.stats[discards, melds, riichi] = noten, tenpai

  def predict_gamestate(self, discards, tenpai_turns, melds):
    predictions = []
    for i in xrange(4):  # or len(discards)
      if tenpai_turns[i] != -1:
        predictions.append(1.0)
      else:
        draws = len(discards[i])
        opp_riichi = sum(tt != -1 for tt in tenpai_turns)  # we are not riichi
        meld_count = len(melds[i]) / 4
        while (draws, meld_count, opp_riichi) not in self.stats:
          print "TABLE MISSING VALUE", draws, meld_count, opp_riichi
          draws -= 1
        noten, tenpai = self.stats[draws, meld_count, opp_riichi]
        predictions.append(float(tenpai) / float(tenpai + noten))
    return predictions

def read_gamestates(filename):
  with open(filename, "r") as file_in:
    discards = []
    tenpai_turns = []
    melds = []
    while True:
      line = file_in.readline()
      if len(line) == 0:
        raise StopIteration
      if len(discards) == 4:
        tokens = line.split(",")
        labels = [x == "T" for x in tokens]
        yield discards, tenpai_turns, melds, labels
        discards = []
        tenpai_turns = []
        melds = []
      else:
        ds, ts, ms = line.split("|")
        ms = ms.strip()
        d = [int(x) for x in ds.split(",")] if ds else []
        t = int(ts)
        m = [int(x) for x in ms.split(",")] if ms else []
        discards.append(d)
        tenpai_turns.append(t)
        melds.append(m)

class NNPredictor(object):
  def __init__(self):
    pass

  def train(self, gamestates):
    # START HERE:
    # Convert the gamestate into input for the neural network
    # 4 * 1360 bits:
    #   0-33 24 times for discards  (24?)
    #   0-23 for tenpai turn
    #   0-33 16 times for melds
    pass

  def predict_gamestate(self, discards, tenpai_turns, melds):
    pass


if len(sys.argv) > 2:
  stats = sys.argv[1]
  gamestates = sys.argv[2]
else:
  #stats = "/Users/nor/nn_input/2009_stats"
  #gamestates = "/Users/nor/nn_input/2009_gamestates"
  stats = "/Users/nor/dev/mahjong-ai/test_stats"
  gamestates = "/Users/nor/dev/mahjong-ai/test_gamestates"

states = []
for discards, tenpai_turns, melds, labels in read_gamestates(gamestates):
  states.append((discards, tenpai_turns, melds, labels))

nnp = NNPredictor()
nnp.train(states)
"""
sp = StatsPredictor(stats)
dp = StupidPredictor()
correct = 0
incorrect = 0
score = 0
count = 0
tenpais = 0
notens = 0
stupid_correct, stupid_incorrect = 0, 0
for discards, tenpai_turns, melds, labels in read_gamestates(gamestates):
  t = sum(labels)
  f = 4 - t
  tenpais += t
  notens += f
  if count % 10000 == 0:
    print "Handled", count
  predicted = sp.predict_gamestate(discards, tenpai_turns, melds)
  stupid_predicted = dp.predict_gamestate(discards, tenpai_turns, melds)
  #print "Values: ", predicted
  #print "Stupid Values: ", stupid_predicted
  results = [x > .5 for x in predicted]
  stupid_results = [x > .5 for x in stupid_predicted]
  #print "Predictions: ", results
  #print "Labels: ", labels
  count += 1
  error = 0
  for result, label, value in zip(results, labels, predicted):
    if result == label:
      correct += 1
    else:
      incorrect += 1
    value_label = 1.0 if label else 0.0
    error += abs(value_label - value)
  for result, label, value in zip(stupid_results, labels, stupid_predicted):
    if result == label:
      stupid_correct += 1
    else:
      stupid_incorrect += 1
  score += (error * error)
print "Average score: ", score / count
print "Correct: ", correct
print "Incorrect: ", incorrect
print "Stupid: %d %d" % (stupid_correct, stupid_incorrect)
print tenpais, notens
"""




