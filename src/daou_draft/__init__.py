from os import path
import sys

SRC_DIR = path.abspath(path.join(__file__, '../../'))
if SRC_DIR not in sys.path:
  sys.path.append(SRC_DIR)