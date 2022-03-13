from os.path import exists
from datetime import datetime


def check_file(func):
	def wrapper(*args):
		if not exists(args[0].path):
			with open(args[0].path, 'w') as f:
				f.write('')
		return func(*args)

	return wrapper


class Logger:
	path = 'logs\\log.txt'

	def __init__(self, path: str = 'logs\\log.txt'):
		self.path = path

	@check_file
	def log(self, text):
		with open(self.path, 'a') as f:
			f.write(datetime.now().strftime('%d.%m [%H:%M:%S] ') + text)


def get_logger() -> Logger:
	if 'logger' not in globals():
		globals()['logger'] = Logger()
	return globals()['logger']
