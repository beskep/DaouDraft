import logging
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).parents[2]


def read_option(fname):
  path = ROOT_DIR / fname

  try:
    with open(path, 'r', encoding='utf-8') as f:
      option = yaml.load(f, Loader=yaml.FullLoader)
  except FileNotFoundError as e:
    logger = logging.getLogger(__name__)
    logger.error('Option 파일이 없습니다: {}'.format(path))
    raise e

  return option
