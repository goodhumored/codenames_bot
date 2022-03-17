from __future__ import annotations
from requests import session
from json import dumps, loads
from random import randint

from credentials import group_id
from log import get_logger
from config import *


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
		if 'buttons' in kb:
			self.__kb['buttons'] = kb['buttons']
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

	def get_dict(self) -> dict:
		return self.__kb

	def get_json(self) -> str:
		return dumps(self.__kb, ensure_ascii=False)

	def set_btn(self, row: int, n: int, btn: list):
		b = self.__kb['buttons'][row][n]
		b['action']['label'] = btn[0]
		b['action']['payload'] = '{"button": "'+btn[1]+'"}'
		b['color'] = btn[2]

	def press_btn(self, row: int, n: int):
		btn = self.__kb['buttons'][row][n]
		btn['action']['label'] += ' ✅'
		btn['action']['payload'] = '{"button": "pressed"}'
		btn['color'] = 'primary'


class Message:
	msg_id = 0
	pid = 0

	def __init__(self, text: str, keyboard: Keyboard = None, atts=None):
		if atts is None:
			atts = ''
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
	v = 5.131
	session = None

	def __init__(self, token: str, v: int = 5.131):
		self.token = token
		self.v = v
		self.session = session()

	def method(self, method: str, **args) -> dict:
		"""Send request to vk api method with given args and return answer or None if error"""
		try:
			resp = self.session.get(
				'https://api.vk.com/method/' + method,
				params={
					'v': self.v,
					'access_token': self.token,
					**args}
			).text
			if log_answers:
				get_logger().log(resp)
			resp = loads(resp)
			if 'error' in resp:
				raise Exception(dumps(resp['error']))
		except Exception as e:
			print('Ошибка:\n' + str(e))
			get_logger().log(str(e))
			return {}
		return resp['response']


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

	def send_message(self, peer_id: int, msg: Message) -> bool:
		"""send message object from this bot to pid"""
		resp = self.api.method(
			'messages.send',
			peer_ids=peer_id,
			message=msg.get_text(),
			attachment=msg.get_atts(),
			keyboard=msg.kb.get_json() if msg.kb else None,
			random_id=msg.rand
		)
		if 'error' in resp[0]:
			return False
		msg.msg_id = resp[0]['conversation_message_id']
		msg.pid = peer_id
		return True

	def get_updates(self) -> list:
		resp = self.api.session.get(
			f'{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25'
		).text
		response = loads(resp)
		if log_answers:
			get_logger().log(resp)
		if 'failed' in response:
			if response['failed'] == '1':
				self.ts = response['ts']
			else:
				self.get_longpoll()
			return self.get_updates()
		self.ts = response['ts']
		return response['updates']

	def send_answer(self, pid: int, eid: str, uid: int, text: str):
		self.api.method(
			'messages.sendMessageEventAnswer',
			event_id=eid,
			user_id=uid,
			peer_id=pid,
			event_data='{"type":"show_snackbar","text":"'+text+'"}'
		)

	def msg_from_id(self, msg_id: int, pid: int) -> Message:
		ans = self.api.method(
			'messages.getByConversationMessageId',
			conversation_message_ids=[msg_id],
			peer_id=pid
		)
		if ans:
			msg = ans['items'][0]
			if 'keyboard' in msg:
				kb = Keyboard().from_dict(msg['keyboard'])
			else:
				kb = None
			if 'attachments' in msg:
				atts = []
				for att in msg['attachments']:
					atts.append(f"{att['type']}{att[att['type']]['owner_id']}_{att[att['type']]['id']}_{att[att['type']]['access_key']}")
				atts = ','.join(atts)
			else:
				atts = ''
			res = Message(msg['text'], kb)
			res.pid = pid
			res.msg_id = msg_id
			res.set_atts(atts)
			return res

	def commit_edits(self, msg: Message):
		kb = msg.kb.get_json() if msg.kb else None
		self.api.method(
			'messages.edit',
			peer_id=msg.pid,
			conversation_message_id=msg.msg_id,
			message=msg.get_text(),
			attachment=msg.get_atts(),
			keyboard=kb
		)

	def send_info(self, game):
		info_msg = self.msg_from_id(game.mid, game.pid)
		self.send_message(game.pid, info_msg)
		game.mid = info_msg.msg_id

	def upload_photo(self, path):
		upload_url = self.api.method(
			'photos.getMessagesUploadServer',
			group_id=self.gid
		)['upload_url']

		files = {'photo': open(path, 'rb')}

		response_data = self.api.session.post(upload_url, files=files).json()
		try:
			photo_info = self.api.method(
				'photos.saveMessagesPhoto',
				server=response_data['server'],
				photo=response_data['photo'],
				hash=response_data['hash']
			)[0]
			return photo_info
		except Exception as e:
			print(e)
			get_logger().log(str(e))
			return None
