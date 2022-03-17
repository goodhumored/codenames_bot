from config import commands
from re import fullmatch


class CommandProcessor:
	def __init__(self):
		pass


def process(text: str):
	for command in commands:
		r = fullmatch(command, text)
		if r:
			return commands[command], r.groups()
	return None, None


def get_processor() -> CommandProcessor:
	if 'com_proc' not in globals():
		globals()['com_proc'] = CommandProcessor()
	return globals()['com_proc']
