from __future__ import annotations
from requests import session
from json import dumps, loads
from random import randint
from log import get_logger


class Keyboard:
	one_time = False
	inline = False

	def __init__(self, inline: bool = True, one_time: bool = False):
		self.__kb = {}
		self.one_time = one_time
		self.inline = inline

	def from_json(self, json: str):
		self.__kb = loads(json)
		self.__kb['one_time'] = self.one_time
		self.__kb['inline'] = self.inline
		return self

	def from_dict(self, kb: dict):
		self.__kb = kb
		self.__kb['one_time'] = self.one_time
		self.__kb['inline'] = self.inline
		return self

	def from_list(self, btns: list):
		kb = []
		for row in btns:
			row1 = list()
			for btn in row:
				row1.append({
					'action': {
						'type': 'callback',
						'label': btn[0],
						'payload': '{"button": "'+btn[1]+'"}'
					},
					'color': btn[2]
				})
			kb.append(row1)

		self.__kb = {
			'one_time': self.one_time,
			'inline': self.inline,
			'buttons': kb
		}
		return self

	def get_dict(self):
		return self.__kb

	def get_json(self):
		return dumps(self.__kb)


class Message:
	msg_id = 0

	def __init__(self, text: str, keyboard: Keyboard = None, atts=None):
		if atts is None:
			atts = []
		self.__text = text
		self.__atts = atts
		self.kb = keyboard
		self.rand = randint(-1000000, 1000000)

	def get_text(self):
		return self.__text

	def set_text(self, val: str):
		self.__text = val
		return self

	def get_atts(self):
		return self.__atts

	def set_atts(self, val: dict):
		self.__atts = val
		return self


class Api:
	token = ''
	v = 5.103
	session = None

	def __init__(self, token: str, v: int):
		self.token = token
		self.v = v
		self.session = session()

	def method(self, method: str, **args) -> dict:
		"""Send request to vk api method with given args and return answer or None if error"""
		try:
			resp = loads(self.session.get(
				'https://api.vk.com/method/' + method,
				params={
					'V': self.v,
					'access_token': self.token,
					**args}
			).text)
			if 'error' in resp:
				raise Exception(dumps(resp['error']))
		except Exception as e:
			print('Ошибка:\n' + str(e))
			get_logger().log(str(e))
			return {}
		else:
			return resp


class Bot:
	api = None
	gid = 0
	server = ''
	ts = ''
	key = ''

	def __init__(self, api: Api, gid: int):
		self.api = api
		self.gid = gid
		self.get_longpoll()

	def get_longpoll(self):
		ans = self.api.method(
			'groups.getLongPollServer',
			group_id=self.gid
		)
		self.server = ans['server']
		self.ts = ans['ts']
		self.key = ans['key']

	def send_message(self, peer_id: int, msg: Message):
		"""send message object from this bot to pid"""
		self.api.method(
							'messages.send',
							peer_id=peer_id,
							message=msg.get_text(),
							attachment=msg.get_atts(),
							keyboard=msg.kb.get_dict()
							)

	def get_updates(self) -> list:
		response = loads(self.api.session.get(
			f'{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25'
		).text)
		if 'failed' in response:
			if response['failed'] == '1':
				self.ts = response['ts']
			else:
				self.get_longpoll()
			return self.get_updates()
		self.ts = response['ts']
		return response['updates']

# def msg_from_id(self, msg_id: int, group_id: int = 0) -> Message:
# 	ans = self.method('messages.getById',
# 			message_ids = [self.msg_id],
# 			group_id = group_id)
# 	if ans:
# 		msg = ans['items'][0];
# 		return Message(msg['text'], Keyboard())

# def commit_edits(self, msg: Message):
# 	self.api.method('messages.edit',
# 			peer_id = peer_id,
# 			message_id = self.msg_id,
# 			message = msg.get_text(),
# 			attachment = msg.get_atts()
# 		)
