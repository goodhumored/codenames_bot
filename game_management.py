from __future__ import annotations
from os.path import exists
from json import loads, load, dumps
from typing import Callable

from config import *
from typing import Union
from log import get_logger
from random import shuffle


class Cell:
	text = ''
	color = ''

	def __init__(self, text: str, color: str):
		self.text = text
		self.color = color

	def __str__(self):
		return f'["{self.text}", "{self.color}"]'


class Field:
	path = ''

	def __init__(self):
		self.cells = []

	def from_list(self, words: list) -> Field:
		for row in words:
			r = []
			for word in row:
				r.append(Cell(word[0], word[1]))
			self.cells.append([*r])
		return self

	def from_json(self, json: str) -> Field:
		return self.from_list(loads(json))

	def get_dict(self) -> list:
		res = []
		for row in self.cells:
			r = []
			for cell in row:
				r.append([cell.text, cell.color])
			res.append([*r])
		return res

	def get_json(self) -> str:
		return dumps(self.cells)

	def get_color(self, row: int, n: int) -> str:
		return self.cells[row][n].color

	def set_color(self, row: int, n: int, color: str):
		self.cells[row][n].color = color

	def map(self, func: Callable):
		for row in self.cells:
			for cell in row:
				func(cell)

	def get_img(self, name) -> str:
		import cv2
		from PIL import ImageFont, ImageDraw, Image
		img = cv2.imread(images_dir + 'default.jpg')

		# Filling cells
		y = field_padding
		for row in self.cells:
			x = field_padding
			for word in row:
				cv2.floodFill(img, None, (int(x+block_width/2), int(y+block_height/2)), colors[word.color], loDiff=20, upDiff=20)
				x += block_width + block_margin * 2
			y += block_height + block_margin * 2

		im = Image.fromarray(img)
		draw = ImageDraw.Draw(im)
		font = ImageFont.truetype(fonts_dir + font_name, font_size)

		# Putting text
		y = field_padding
		for row in self.cells:
			x = field_padding
			for word in row:
				w, h = draw.textsize(word.text, font)
				draw.text(
					(int(x + (block_width-w)/2), int(y + (block_height - h)/2)),
					word.text,
					colors[word.color+'_text'],
					font
				)
				x += block_width + block_margin * 2
			y += block_height + block_margin * 2
		im = im.crop((0, 0, x, y))

		name = images_dir + name + ".jpg"
		im.save(name, "JPEG")
		return name

	def index_of(self, item):
		r, n = 0, 0
		for row in self.cells:
			n = 0
			for cell in row:
				if cell.text == item:
					return r, n
				n += 1
			r += 1
		return -1, -1


class Game:
	def __init__(self, pid: int = 0):
		self.gid = get_manager().get_id()
		self.pid = pid
		self.red_cap = 0
		self.blue_cap = 0
		self.red_score = 0
		self.blue_score = 0
		self.status = 'dict'
		self.turn = 'blue'
		self.dict = ''
		self.mid = 0
		self.rmid = 0
		self.bmid = 0
		self.hint_c = 0
		self.cap_f = Field()
		self.pl_f = Field()

	def load_from_dict(self, game: dict) -> Game:
		self.gid = game['gid']
		self.pid = game['pid']
		self.red_cap = game['red_cap']
		self.blue_cap = game['blue_cap']
		self.cap_f = Field().from_list(game['cap_f'])
		self.pl_f = Field().from_list(game['pl_f'])
		self.red_score = game['red_score']
		self.blue_score = game['blue_score']
		self.status = game['status']
		self.turn = game['turn']
		self.dict = game['dict']
		self.mid = game['mid']
		self.rmid = game['rmid']
		self.bmid = game['bmid']
		self.hint_c = game['hint_c']
		return self

	def load_from_json(self, json: str) -> Game:
		return self.load_from_dict(loads(json))

	def to_dict(self) -> dict:
		return {
			'gid': self.gid,
			'pid': self.pid,
			'red_cap': self.red_cap,
			'blue_cap': self.blue_cap,
			'red_score': self.red_score,
			'blue_score': self.blue_score,
			'status': self.status,
			'turn': self.turn,
			'dict': self.dict,
			'mid': self.mid,
			'rmid': self.rmid,
			'bmid': self.bmid,
			'hint_c': self.hint_c,
			'cap_f': self.cap_f.get_dict(),
			'pl_f': self.pl_f.get_dict(),
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
	def find_by_gid(self, gid: int) -> Union[Game, None]:
		with open(self.path, 'r', encoding="utf-8") as f:
			games = loads(f.read())
			for pid in games:
				if int(games[pid]['gid']) == int(gid):
					return Game().load_from_dict(games[pid])

	@check_file
	def save_game(self, game: Game) -> bool:
		try:
			f = open(self.path, 'r', encoding="utf-8")
			games = loads(f.read())
			f.close()

			f1 = open(self.path, 'w', encoding="utf-8")
			games[str(game.pid)] = game.to_dict()
			f1.write(dumps(games))
			f1.close()
			return True
		except Exception as e:
			print(e)
			get_logger().log(str(e))
			return False

	@check_file
	def get_id(self):
		with open(self.path, 'r', encoding="utf-8") as f:
			games = loads(f.read())
			if games != {}:
				return int(max(games.values(), key=lambda x: int(x['gid']))['gid']) + 1
			else:
				return 1


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
