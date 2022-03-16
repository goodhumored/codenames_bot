from config import images_dir
from credentials import token, group_id
from vk_facade import Api, Bot, Keyboard, Message
from game_management import Game, get_manager, get_dicts_list, get_random_words, Field
from log import get_logger
from random import shuffle
from PIL import Image
from json import loads
from cv2 import imread, imshow, waitKey, destroyAllWindows

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
				game.status = 'dict'
				btns = []
				for dict_name in dicts:
					btns.append([[dict_name, dict_name, 'secondary']])
				kb = Keyboard().from_list(btns)
				bot.send_message(pid, Message('Выберите словарь для игры:', kb))
				answd_msg.kb.press_btn(0, 0)
				bot.commit_edits(answd_msg)
				bot.send_answer(pid, msg['event_id'], uid, 'Начинаем новую игру')
				gm.save_game(game)
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

				shuffle(counts)
				colors = ['red'] * counts[0] + ['blue'] * counts[1] + ['white'] * gray + ['black']
				game.red_score = counts[0]
				game.blue_score = counts[1]
				game.turn = 'red' if counts[0] > counts[1] else 'blue'
				shuffle(colors)
				words = get_random_words(game.dict, 5 * rows)
				btns1 = []
				btns2 = []
				for y in range(rows):
					row1 = list()
					row2 = list()
					for x in range(5):
						i = x + y * 5
						row1.append([words[i], colors[i]])
						row2.append([words[i], 'white'])
					btns1.append([*row1])
					btns2.append([*row2])
				game.cap_f = Field().from_list(btns1)
				game.pl_f = Field().from_list(btns2)

				bot.send_answer(pid, msg['event_id'], uid, 'Вы выбрали ' + s + ' поле')
				answd_msg.kb.press_btn(n, 0)
				bot.commit_edits(answd_msg)
				kb = Keyboard().from_list([
					[['Хочу быть красным капитаном', 'red_cap', 'negative'], ['Хочу быть синим капитаном', 'blue_cap' 'primary']]
				])
				bot.send_message(pid, Message('Выбираем капитанов:', kb))
				game.status = 'caps'
				gm.save_game(game)
			elif action in ['red_cap', 'blue_cap'] and game.status == 'caps':
				user = bot.api.method(
					'users.get',
					user_ids=uid
				)[0]
				name = user['first_name'] + ' ' + user['last_name']
				if action == 'red_cap':
					game.red_cap = uid
					answd_msg.kb.set_btn(0, 0, [name, 'occupied', 'negative'])
				else:
					game.blue_cap = uid
					answd_msg.kb.set_btn(0, 0, [name, 'occupied', 'primary'])

				if game.red_cap and game.blue_cap:
					img1 = bot.upload_photo(images_dir + game.cap_f.get_img(str(pid) + '_cap'))
					img2 = bot.upload_photo(images_dir + game.pl_f.get_img(str(pid)))
					photo1 = f'photo{img1["owner_id"]}_{img1["id"]}'
					photo2 = f'photo{img2["owner_id"]}_{img2["id"]}'

					message = Message(
						f'Поле от игры {game.gid}\n'
						f'Чтобы отправить подсказку команде пишите\n'
						f'{game.gid} [Слово] [кол-во]\n'
						f'сюда, или \n'
						f'[Слово] [кол-во]\n'
						f'в беседу с игрой',
						atts=photo1)
					bot.send_message(game.red_cap, message)
					bot.send_message(game.blue_cap, message)
					message = Message(f'Сейчас ваш ход')
					if game.turn == 'red':
						bot.send_message(game.red_cap, message)
					else:
						bot.send_message(game.blue_cap, message)
					bot.send_message(pid, Message(
						f'Игра: {game.gid}\n'
						f'Словарь: {game.dict}\n'
						f'[id{game.red_cap}|Капитан красных], [id{game.red_cap}|Капитан синих]\n'
						f'Первый ход: команда ' + 'синих' if game.turn == 'blue' else 'красных',
						atts=photo2
					))
					game.mid = bot.send_message(pid, Message('Ход: ' + 'синие' if game.turn == 'blue' else 'красные'
															'Журнал:'))[0]['conversation_message_id']
					gm.save_game(game)
			elif action == 'occupied':
				bot.send_answer(pid, msg['event_id'], uid, 'У этой команды уже есть капитан')
			elif action == 'pressed':
				bot.send_answer(pid, msg['event_id'], uid, 'Вы уже нажимали эту кнопку')

