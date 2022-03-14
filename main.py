from config import token, group_id
from vk_facade import Api, Bot, Keyboard, Message
from game_management import Game, get_manager, get_dicts_list, get_random_words
from log import get_logger
from random import shuffle
from json import loads

api = Api(token)
bot = Bot(api, group_id)
gm = get_manager()
log = get_logger()
dicts = get_dicts_list()

while True:
	upds = bot.get_updates()
	for upd in upds:
		if upd['type'] == 'message_new':
			msg = upd['object']['message']
			pid = msg['peer_id']
			uid = msg['from_id']
			text = msg['text'].lower()
			if text == 'codenames start':
				game = gm.find_by_pid(pid)
				if game is not None and game.status != 'over':
					kb = Keyboard().from_list([
						[['Да', 'start', 'primary'], ['Нет', 'cancel', 'secondary']]
					])
					bot.send_message(pid, Message('Начать игру заново?', kb))
				else:
					kb = Keyboard().from_list([
						[['Да', 'start', 'positive'], ['Нет', 'cancel', 'negative']]
					])
					bot.send_message(pid, Message('Начать игру в кодовые имена?', kb))
		elif upd['type'] == 'message_event':
			msg = upd['object']
			pid = msg['peer_id']
			uid = msg['user_id']
			action = msg['payload']['button']
			answd_msg = bot.msg_from_id(msg['conversation_message_id'], pid)
			game = gm.find_by_pid(pid)
			if action == 'start':
				if not game:
					game = Game(pid)
					gm.save_game(game)
				game.status = 'dict'
				btns = []
				for dict_name in dicts:
					btns.append([[dict_name, dict_name, 'secondary']])
				kb = Keyboard().from_list(btns)
				bot.send_message(pid, Message('Выберите словарь для игры:', kb))
				answd_msg.kb.press_btn(0, 0)
				bot.commit_edits(answd_msg)
				bot.send_answer(pid, msg['event_id'], uid, 'Начинаем новую игру')
			elif not game:
				continue
			elif action in dicts and game.status == 'dict':
				bot.send_answer(pid, msg['event_id'], uid, 'Вы выбрали ' + action)
				answd_msg.kb.press_btn(dicts.index(action), 0)
				bot.commit_edits(answd_msg)
				game.status = 'size'
				game.dict = action
				gm.save_game(game)
				bot.send_message(
					pid,
					Message(
						'Выберите размер поля: ',
						Keyboard().from_list([
							[['Большое (5х6)', 'big', 'secondary']],
							[['Среднее (5х5)', 'medium', 'secondary']],
							[['Маленькое (5х4)', 'small', 'secondary']]
						])))
			elif action in ['big', 'medium', 'small'] and game.status == 'size':
				if action == 'big':
					n = 0
					counts = [10, 9]
					gray = 10
					rows = 6
					s = 'большое'
				elif action == 'medium':
					n = 1
					counts = [8, 9]
					gray = 7
					rows = 5
					s = 'среднее'
				else:
					n = 2
					counts = [8, 7]
					gray = 4
					rows = 4
					s = 'маленькое'
				bot.send_answer(pid, msg['event_id'], uid, 'Вы выбрали ' + s + ' поле')
				answd_msg.kb.press_btn(n, 0)
				bot.commit_edits(answd_msg)
				shuffle(counts)
				colors = ['negative']*counts[0] + ['primary']*counts[1] + ['secondary']*gray + ['positive']
				game.red_score = counts[0]
				game.blue_score = counts[1]
				shuffle(colors)
				words = get_random_words(game.dict, 5*rows)
				btns1 = []
				btns2 = []
				for y in range(rows):
					row1 = list()
					row2 = list()
					for x in range(5):
						i = x+y*5
						row1.append([words[i], words[i], colors[i]])
						row2.append([words[i], words[i], 'secondary'])
					btns1.append([*row1])
					btns2.append([*row2])
				game.cap_kb = Keyboard(False).from_list(btns1)
				game.kb = Keyboard(False).from_list(btns2)
				bot.send_message(pid, Message('Поле', game.cap_kb))
			elif action == 'pressed':
				bot.send_answer(pid, msg['event_id'], uid, 'Вы уже нажимали эту кнопку')

