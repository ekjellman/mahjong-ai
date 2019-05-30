file_in = open("rating_scores.txt", "r")
lines = file_in.readlines()
lines = [line.strip() for line in lines]
import collections
ratings = collections.defaultdict(int)
positions = collections.defaultdict(list)
for i in range(0, len(lines), 2):
  r = lines[i]
  rs = r.split(",")
  if len(rs) < 4: continue
  rates = [int(float(x)) for x in rs]
  if min(rates) < 2000: continue
  s = lines[i+1]
  ss = s.split(",")
  if len(ss) != 4:
    continue
  for rate in rates:
    ratings[rate] += 1
  scores = [int(x) for x in ss]
  pairs = [(scores[i], i) for i in (0, 1, 2, 3)]
  pairs.sort()
  for i in (0, 1, 2, 3):
    rating = rates[pairs[i][1]]
    positions[rating].append(4 - i)

moving = []
for rating in sorted(ratings.keys()):
  if len(positions[rating]) < 1000: continue
  av = sum(positions[rating]) / float(len(positions[rating]))
  moving.append(av)
  if len(moving) > 10:
    moving.pop(0)
  mav = sum(moving) / len(moving)
  print "%.3f" % mav, rating, ratings[rating], av
  #print positions[rating]
