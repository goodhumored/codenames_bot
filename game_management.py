from __future__ import annotations
from os.path import exists
from json import loads, load, dump
from vk_facade import Keyboard
from typing import Union
from log import get_logger
from random import shuffle

dicts_dir = 'resources\\dictionaries\\'


class Game:
	pid = 0
	red_team = []
	blue_team = []
	cap_kb = Keyboard()
	kb = Keyboard()
	status = 'dict'

	def __init__(self, pid: int = 0):
		self.pid = pid

	def load_from_dict(self, game: dict) -> Game:
		self.pid = game['pid']
		self.red_team = game['red_team']
		self.blue_team = game['blue_team']
		self.cap_kb = Keyboard().from_json(game['cap_kb'])
		self.kb = Keyboard().from_json(game['kb'])
		self.status = game['status']
		return self

	def load_from_json(self, json: str) -> Game:
		return self.load_from_dict(loads(json))

	def to_dict(self) -> dict:
		return {
			'pid': self.pid,
			'red_team': self.red_team,
			'blue_team': self.blue_team,
			'cap_kb': self.cap_kb,
			'kb': self.kb,
			'status': self.status
		}


def check_file(func):
	def wrapper(*args):
		if not exists(args[0].path):
			with open(args[0].path, 'w') as f:
				f.write('{}')
		return func(*args)

	return wrapper


class GameManager:
	path = 'games\\games.json'

	def __init__(self, path: str = 'games\\games.json'):
		self.path = path

	@check_file
	def find_by_pid(self, pid: int) -> Union[Game, None]:
		with open(self.path, 'r') as f:
			games = load(f)
			if pid in games:
				return Game().load_from_dict(games[pid])
			else:
				return None

	@check_file
	def save_game(self, game: Game) -> bool:
		try:
			with open(self.path, 'r+') as f:
				games = load(f)
				games[game.pid] = game.to_dict()
				dump(games, f)
				return True
		except Exception as e:
			print(e)
			get_logger().log(str(e))
			return False


def get_manager(path: str = '') -> GameManager:
	if 'manager' not in globals():
		globals()['manager'] = GameManager(path)
	return globals()['manager']


def get_dicts_list() -> list:
	res = []
	with open(dicts_dir + 'dicts.json') as f:
		dicts = load(f)
		for name, fn in dicts:
			res.append(name)
	return res


def get_random_words(name: str, count: int) -> list:
	with open(dicts_dir + 'dicts.json') as f:
		with open(dicts_dir + load(f)[name]) as f1:
			words = list(load(f1))
			return shuffle(words)[:count]
