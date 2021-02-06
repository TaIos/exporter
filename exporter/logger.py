import logging
import pathlib
import time


class ExporterLogger:

    def __init__(self, debug=False, log_dir=None, log_file=None):
        self.log_dir = pathlib.Path(log_dir or 'logs') / time.strftime("%d%m%Y_%H%M%S")
        self.log_file = log_file or 'main'
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            filename=(self.log_dir / self.log_file).with_suffix(".log"),
            filemode='w',
            level=self.level,
            format='%(asctime)s: %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S %Z %z'
        )

    def info(self, msg):
        logging.info(msg)
