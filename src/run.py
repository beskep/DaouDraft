from pathlib import Path
import json
import logging
import logging.config

from rich.logging import RichHandler

from draft import daou_draft

ROOT_DIR = Path(__file__).parents[1]

if __name__ == "__main__":
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

  runner = daou_draft.Runner()
  runner.run()

  logger.debug('Finished')

  # os.system('pause')
