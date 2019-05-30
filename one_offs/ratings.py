import xml.etree.cElementTree as ET
import sys

def get_elements(filename):
  tree = ET.parse(filename)
  root = tree.getroot()
  elements = [c for c in root]
  return elements

def get_ratings(elements):
  for element in elements:
    if element.tag == "UN":
      return element.attrib["rate"]
  return None

elements = get_elements(sys.argv[1])
ratings = get_ratings(elements)
assert ratings
assert elements[-1].tag == "AGARI" or elements[-1].tag == "RYUUKYOKU"
scores = elements[-1].attrib["sc"].split(",")[::2]
print ratings
print ",".join(scores)
