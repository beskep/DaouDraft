import json
import logging
import logging.config
import os
import sys
from pathlib import Path

import fire
import bs4
from rich.logging import RichHandler

ROOT_DIR = Path('.')
SRC_DIR = ROOT_DIR / 'src'
if str(SRC_DIR) not in sys.path:
  sys.path.append(str(SRC_DIR))

from draft import daou_draft, template


def main(mode='draft'):
  log_setting_path = ROOT_DIR / 'logging.json'

  if log_setting_path.exists():
    with open(log_setting_path, 'r') as f:
      config = json.load(f)
    logging.config.dictConfig(config)

    root_logger = logging.getLogger()
    root_logger.addHandler(RichHandler(level=logging.INFO, show_time=False))
  else:
    raise FileNotFoundError(log_setting_path)

  logger = logging.getLogger(__name__)
  logger.debug('Started')

  if mode not in ('draft', 'template'):
    logger.error('mode는 "draft" 또는 "template"이어야 함')
    logger.error('입력된 mode: {}'.format(mode))
    raise ValueError(mode)

  if mode == 'draft':
    runner = daou_draft.Runner()
    runner.run()
  elif mode == 'template':
    template.run()

  logger.debug('Finished')


if __name__ == "__main__":
  fire.Fire(main)

  # os.system('pause')
