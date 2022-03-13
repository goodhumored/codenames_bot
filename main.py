from config import token, group_id
from vk_facade import Api, Bot, Keyboard, Message
from game_management import Game, get_manager, get_dicts_list, get_random_words
from log import get_logger
from json import loads

api = Api(token)
bot = Bot(api, group_id)
gm = get_manager()
log = get_logger()

while True:
	upds = bot.get_updates()
	for upd in upds:
		msg = upd['object']
		pid = msg['peer_id']
		if upd['type'] == 'message_new':
			uid = msg['from_id']
			text = msg['text'].lower()
			if text == 'codenames start':
				game = gm.find_by_pid(pid)
				if game is not None and game.status == 'over':
					kb = Keyboard().from_list([
						[['Да', 'start', 'secondary'], ['Нет', 'cancel', 'primary']]
					])
					bot.send_message(pid, Message('Начать игру заново?', kb))
				else:
					kb = Keyboard().from_list([
						[['Да', 'start', 'secondary'], ['Нет', 'cancel', 'primary']]
					])
					bot.send_message(pid, Message('Начать игру в кодовые имена?', kb))
		elif upd['type'] == 'message_event':
			uid = msg['user_id']
			action = loads(msg['payload'])['button']
			match action:
				case 'start':
					game = gm.find_by_pid(pid)
					if not game:
						game = Game(pid)
					dicts = get_dicts_list()
					btns = []
					for dict_name in dicts:
						btns.append([[dict_name, dict_name, 'secondary']])
					kb = Keyboard().from_list(btns)
					bot.send_message(pid, Message('Выберите словарь для игры:',kb))

