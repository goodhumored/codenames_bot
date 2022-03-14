from __future__ import annotations
from os.path import exists
from json import loads, load, dump, dumps
from vk_facade import Keyboard
from typing import Union
from log import get_logger
from random import shuffle

dicts_dir = 'resources\\dictionaries\\'
games_json = 'games\\games.json'


class Game:
	pid = 0
	red_team = []
	blue_team = []
	cap_kb = Keyboard()
	kb = Keyboard()
	status = 'dict'
	dict = ''

	def __init__(self, pid: int = 0):
		self.pid = pid

	def load_from_dict(self, game: dict) -> Game:
		self.pid = game['pid']
		self.red_team = game['red_team']
		self.blue_team = game['blue_team']
		self.cap_kb = Keyboard().from_dict(game['cap_kb'])
		self.kb = Keyboard().from_dict(game['kb'])
		self.status = game['status']
		self.dict = game['dict']
		return self

	def load_from_json(self, json: str) -> Game:
		return self.load_from_dict(loads(json))

	def to_dict(self) -> dict:
		return {
			'pid': self.pid,
			'red_team': self.red_team,
			'blue_team': self.blue_team,
			'cap_kb': self.cap_kb.get_dict(),
			'kb': self.kb.get_dict(),
			'status': self.status,
			'dict': self.dict
		}


def check_file(func):
	def wrapper(*args):
		if not exists(args[0].path):
			with open(args[0].path, 'w', encoding="utf-8") as f:
				f.write('{}')
		return func(*args)

	return wrapper


class GameManager:
	path = ''

	def __init__(self, path: str = games_json):
		self.path = path

	@check_file
	def find_by_pid(self, pid: int) -> Union[Game, None]:
		with open(self.path, 'r', encoding="utf-8") as f:
			games = loads(f.read())
			pid = str(pid)
			if pid in games:
				return Game().load_from_dict(games[pid])
			else:
				return None

	@check_file
	def save_game(self, game: Game) -> bool:
		try:
			f = open(self.path, 'r', encoding="utf-8")
			games = loads(f.read())
			f.close()

			f1 = open(self.path, 'w', encoding="utf-8")
			games[game.pid] = game.to_dict()
			f1.write(dumps(games))
			f1.close()
			return True
		except Exception as e:
			print(e)
			get_logger().log(str(e))
			return False


def get_manager(path: str = games_json) -> GameManager:
	if 'manager' not in globals():
		globals()['manager'] = GameManager(path)
	return globals()['manager']


def get_dicts_list() -> list:
	res = []
	with open(dicts_dir + 'dicts.json', encoding='utf8') as f:
		dicts = loads(f.read())
		for name, fn in dicts.items():
			res.append(name)
	return res


def get_random_words(name: str, count: int) -> list:
	with open(dicts_dir + 'dicts.json', encoding='utf8') as f:
		with open(dicts_dir + load(f)[name], 'r', encoding='utf8') as f1:
			words = loads(f1.read())['words']
			shuffle(words)
			return words[:count]
