import logging
import sys
from logging.handlers import RotatingFileHandler

import config

FORMATTER = logging.Formatter("%(levelname)s - %(message)s") 
#%(levelname)s - %(message)s")
LOG_FILE = config.LOG_FILENAME

def get_console_handler():
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(FORMATTER)
	return console_handler

def get_file_handler():
	file_handler = RotatingFileHandler(LOG_FILE,  maxBytes=10000000, backupCount=10) # when='midnight')
	file_handler.setFormatter(FORMATTER)
	return file_handler

def get_logger(logger_name):
	logger = logging.getLogger(logger_name)

	logger.setLevel(logging.DEBUG) # better to have too much log than not enough
	logging.root.handlers = [get_file_handler()] # overriding root handler so that werkzeug logs also would appear here.

	logger.addHandler(get_console_handler())
	logger.addHandler(get_file_handler())

	# log messages emitted by Werkzeug in your log file
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(get_file_handler())
	# with this pattern, it's rarely necessary to propagate the error up to parent
	# logger.propagate = False

	return logger