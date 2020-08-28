from pathlib import Path
import logging
import logging.config
import sys

import yaml
from rich.logging import RichHandler
import bs4
import fire

ROOT_DIR = Path('.')
SRC_DIR = ROOT_DIR / 'src'
if str(SRC_DIR) not in sys.path:
  sys.path.append(str(SRC_DIR))

from draft import daou_draft, template


def main(mode='draft'):
  config_path = ROOT_DIR / 'logging.yaml'

  if config_path.exists():
    config = daou_draft.read_option(config_path)
    logging.config.dictConfig(config)

    root_logger = logging.getLogger()
    root_logger.addHandler(RichHandler(level=logging.INFO, show_time=False))
  else:
    raise FileNotFoundError(config_path)

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
