from config import images_dir, help_text
from credentials import token, group_id
from vk_facade import Api, Bot, Keyboard, Message
from game_management import Game, get_manager, get_dicts_list, get_random_words, Field
from log import get_logger
from random import shuffle
from PIL import Image
from json import loads
from cv2 import imread, imshow, waitKey, destroyAllWindows
from command_processor import process

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
			if pid > 2000000000:
				game = gm.find_by_pid(pid)

			com, grs = process(text)
			if com is None:
				continue
			match(com):
				case 'start':
					if pid < 2000000000:
						bot.send_message(pid, Message('Начать игру можно только находясь в беседе'))
						continue
					if game is not None and game.status != 'over':
						kb = Keyboard().from_list([
							[['Да', 'start', 'secondary'], ['Нет', 'cancel', 'secondary']]
						])
						bot.send_message(pid, Message('Начать игру заново?', kb))
					else:
						kb = Keyboard().from_list([
							[['Да', 'start', 'positive'], ['Нет', 'cancel', 'negative']]
						])
						bot.send_message(pid, Message('Начать игру в кодовые имена?', kb))
				case 'help':
					bot.send_message(pid, Message(help_text))
				case 'info':
					if pid < 2000000000:
						bot.send_message(pid, Message('Запросить информацию об игре можно только находясь в беседе'))
						continue
					bot.send_info(game)
				case 'hint':
					if pid < 2000000000:
						bot.send_message(pid, Message(
							'Чтобы дать подсказку отсюда, пишите:\n'
							'[id_беседы] [Слово] [кол-во]'))
						continue
					if game.status != 'progress':
						bot.send_message(pid, Message('Игра не идёт'))
						continue
					cap = game.red_cap if game.turn == 'red' else game.blue_cap
					if uid not in [game.red_cap, game.blue_cap]:
						bot.send_message(pid, Message('Только капитаны могут давать подсказки'))
						continue
					if uid == cap and game.hint_c > 0:
						bot.send_message(pid, Message('Вы не можете дать больше одной подсказки за ход'))
						continue
					if uid != cap:
						game.turn = 'blue' if game.turn == 'red' else 'red'
					info_msg = bot.msg_from_id(game.mid, pid)
					info_msg.set_text(
						'Ход: ' + ('синие' if (game.turn == 'blue') else 'красные') +
						'. Счёт: 🔴' + str(game.red_score) + ' : ' + str(game.blue_score) + '🔵\n' +
						''.join(info_msg.get_text().splitlines(True)[1:]) + '\n' +
						('🔴' if game.turn == 'red' else '🔵') + f'{grs[0]} {grs[1]}: '
					)
					game.hint_c = int(grs[1]) + 1
					bot.send_info(game)
					bot.commit_edits(info_msg)
				case 'word':
					if game.status != 'progress':
						continue
					r, c = game.pl_f.index_of(grs[0])
					if r >= 0 and c >= 0:
						if uid != game.red_cap and uid != game.blue_cap:
							if game.hint_c == 0:
								bot.send_message(pid, Message('Подсказка кончилась, ждём новую из центра!'))
								continue
							color = game.cap_f.get_color(r, c)
							if game.pl_f.get_color(r, c) == color:
								bot.send_message(pid, Message('Это слово уже нажимали'))
								continue
							game.hint_c -= 1
							if color == 'black':
								game.status = 'over'
								img = bot.upload_photo(images_dir + str(pid) + '.jpg')
								photo = f'photo{img["owner_id"]}_{img["id"]}'
								bot.send_message(pid, Message('Был нажат чёрный цвет, игра окончена, победили ' + ('красные' if color == 'blue' else 'синие'), atts=photo))

							if color != game.turn:
								game.hint_c = 0
								if color != 'black':
									bot.send_message(pid, Message('Неверно, смена хода'))

							if game.hint_c == 0:
								game.turn = 'red' if game.turn == 'blue' else 'blue'
								if game.status != 'over':
									bot.send_message(pid, Message(
										'Подсказка закончилась, теперь ход ' +
										('синих' if (game.turn == 'blue') else 'красных')
									))
								if game.turn == 'blue':
									bot.send_message(game.blue_cap, Message('Сейчас ваш ход'))
								else:
									bot.send_message(game.red_cap, Message('Сейчас ваш ход'))

							if color == 'red':
								s = '🔴'
								game.red_score -= 1
								if game.red_score == 0:
									game.status = 'over'
									img = bot.upload_photo(images_dir + str(pid) + '.jpg')
									photo = f'photo{img["owner_id"]}_{img["id"]}'
									bot.send_message(pid, Message('Конец игры, победа красных!', atts=photo))
							elif color == 'blue':
								s = '🔵'
								game.blue_score -= 1
								if game.blue_score == 0:
									game.status = 'over'
									img = bot.upload_photo(images_dir + str(pid) + '.jpg')
									photo = f'photo{img["owner_id"]}_{img["id"]}'
									bot.send_message(pid, Message('Конец игры, победа синих!', atts=photo))
							elif color == 'black':
								s = '⚫'
							elif color == 'white':
								s = '⚪'
							elif color == 'yellow':
								s = '🟡'
							game.pl_f.set_color(r, c, color)
							game.cap_f.set_color(r, c, 'white')

							photo = bot.upload_photo(game.pl_f.get_img(str(pid)+'_pl'))
							photo = f'photo{photo["owner_id"]}_{photo["id"]}'
							photo1 = bot.upload_photo(game.cap_f.get_img(str(pid) + '_cap'))
							photo1 = f'photo{photo1["owner_id"]}_{photo1["id"]}'

							info_msg = bot.msg_from_id(game.mid, pid)
							radm_msg = bot.msg_from_id(game.rmid, game.red_cap)
							badm_msg = bot.msg_from_id(game.bmid, game.blue_cap)
							info_msg.set_atts(photo)
							radm_msg.set_atts(photo1)
							badm_msg.set_atts(photo1)
							info_msg.set_text(
								'Ход: ' + ('синие' if (game.turn == 'blue') else 'красные') +
								'. Счёт: 🔴' + str(game.red_score) + ' : ' + str(game.blue_score) + '🔵\n' +
								''.join(info_msg.get_text().splitlines(True)[1:]) + ' ' + s + grs[0]
							)
							bot.commit_edits(info_msg)
							bot.commit_edits(radm_msg)
							bot.commit_edits(badm_msg)
				case 'im_hint':
					game = gm.find_by_gid(grs[0])
					if game is None:
						bot.send_message(pid, Message('Игра с таким айди не обнаружена'))
						continue
					if game.status != 'progress':
						bot.send_message(pid, Message('Игра с таким айди уже закончилась или ещё не началась'))
						continue
					pid = game.pid
					cap = game.red_cap if game.turn == 'red' else game.blue_cap
					if uid not in [game.red_cap, game.blue_cap]:
						bot.send_message(pid, Message('Только капитаны могут давать подсказки'))
						continue
					if uid == cap and game.hint_c > 0:
						bot.send_message(pid, Message('Вы не можете дать больше одной подсказки за ход'))
						continue
					if uid != cap:
						game.turn = 'blue' if game.turn == 'red' else 'red'
					info_msg = bot.msg_from_id(game.mid, pid)
					info_msg.set_text(
						'Ход: ' + ('синие' if (game.turn == 'blue') else 'красные') +
						'. Счёт: 🔴' + str(game.red_score) + ' : ' + str(game.blue_score) + '🔵\n' +
						''.join(info_msg.get_text().splitlines(True)[1:]) + '\n' +
						('🔴' if game.turn == 'red' else '🔵') + f'{grs[1]} {grs[2]}: '
					)
					game.hint_c = int(grs[2]) + 1
					bot.commit_edits(info_msg)

			if pid > 2000000000 and game is not None:
				gm.save_game(game)

		elif upd['type'] == 'message_event':
			msg = upd['object']
			pid = msg['peer_id']
			uid = msg['user_id']
			action = msg['payload']['button']
			eid = msg['event_id']
			if 'conversation_message_id' not in msg:
				continue
			answd_msg = bot.msg_from_id(msg['conversation_message_id'], pid)
			game = gm.find_by_pid(pid)
			if action == 'start':
				if not game:
					game = Game(pid)
				game.status = 'dict'
				game.blue_cap = 0
				game.red_cap = 0
				btns = []
				for dict_name in dicts:
					btns.append([[dict_name, dict_name, 'secondary']])
				kb = Keyboard().from_list(btns)
				bot.send_message(pid, Message('Выберите словарь для игры:', kb))
				answd_msg.kb.press_btn(0, 0)
				bot.commit_edits(answd_msg)
				bot.send_answer(pid, eid, uid, 'Начинаем новую игру')
			elif not game:
				continue
			elif action in dicts:
				if game.status != 'dict':
					bot.send_answer(pid, eid, uid, 'Сейчас нельзя выбрать словарь')
					continue
				bot.send_answer(pid, eid, uid, 'Вы выбрали ' + action)
				answd_msg.kb.press_btn(dicts.index(action), 0)
				bot.commit_edits(answd_msg)
				game.status = 'size'
				game.dict = action
				bot.send_message(
					pid,
					Message(
						'Выберите размер поля: ',
						Keyboard().from_list([
							[['Большое (5х6)', 'big', 'secondary']],
							[['Среднее (5х5)', 'medium', 'secondary']],
							[['Маленькое (5х4)', 'small', 'secondary']]
						])))
			elif action in ['big', 'medium', 'small']:
				if game.status != 'size':
					bot.send_answer(pid, eid, uid, 'Сейчас нельзя выбрать размер поля')
					continue
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
				colors = ['red'] * counts[0] + ['blue'] * counts[1] + ['yellow'] * gray + ['black']
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

				bot.send_answer(pid, eid, uid, 'Вы выбрали ' + s + ' поле')
				answd_msg.kb.press_btn(n, 0)
				bot.commit_edits(answd_msg)
				kb = Keyboard().from_list([
					[['Хочу быть красным капитаном', 'red_cap', 'negative'], ['Хочу быть синим капитаном', 'blue_cap', 'primary']]
				])
				bot.send_message(pid, Message(
					'Выбираем капитанов:\n'
					'⚠Внимание!⚠\n'
					'У капитанов должны быть открыта личка боту, '
					'чтобы её открыть, отправьте боту любое сообщение',
					kb
				))
				game.status = 'caps'
				gm.save_game(game)
			elif action in ['red_cap', 'blue_cap']:
				if game.status != 'caps':
					bot.send_answer(pid, eid, uid, 'Сейчас нельзя выбрать капитана')
					continue
				user = bot.api.method(
					'users.get',
					user_ids=uid
				)[0]
				if uid in [game.red_cap, game.blue_cap]:
					bot.send_answer(pid, eid, uid, 'Вы уже капитан')
					continue
				name = user['first_name'] + ' ' + user['last_name']
				if action == 'red_cap':
					game.red_cap = uid
					answd_msg.kb.set_btn(0, 0, [name, 'occupied', 'negative'])
				else:
					game.blue_cap = uid
					answd_msg.kb.set_btn(0, 1, [name, 'occupied', 'primary'])
				bot.commit_edits(answd_msg)
				gm.save_game(game)
				if game.red_cap and game.blue_cap:
					img1 = bot.upload_photo(game.cap_f.get_img(str(pid)))
					img2 = bot.upload_photo(game.pl_f.get_img(str(pid)+'_pl'))
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
					error = False
					if not bot.send_message(game.red_cap, message):
						bot.send_message(pid, Message('Ошибка, у красного капитана закрыты сообщения от бота'))
						error = True

					game.rmid = int(message.msg_id)
					if not bot.send_message(game.blue_cap, message):
						bot.send_message(pid, Message('Ошибка, у синего капитана закрыты сообщения от бота'))
						error = True

					if error:
						kb = Keyboard().from_list([
							[['Хочу быть красным капитаном', 'red_cap', 'negative'],
							 ['Хочу быть синим капитаном', 'blue_cap', 'primary']]
						])
						bot.send_message(pid, Message(
							'Выбираем капитанов:\n'
							'⚠Внимание!⚠\n'
							'У капитанов должны быть открыта личка боту, '
							'чтобы её открыть, отправьте боту любое сообщение',
							kb
						))
						game.blue_cap = 0
						game.red_cap = 0
						gm.save_game(game)
						continue

					game.bmid = int(message.msg_id)
					message = Message(f'Сейчас ваш ход')
					if game.turn == 'red':
						bot.send_message(game.red_cap, message)
					else:
						bot.send_message(game.blue_cap, message)
					bot.send_message(pid, Message(
						f'Игра: {game.gid}\n'
						f'Словарь: {game.dict}\n'
						f'[id{game.red_cap}|Капитан красных], [id{game.blue_cap}|Капитан синих]\n'
						f'Первый ход: команда ' + ('синих' if game.turn == 'blue' else 'красных')
					))
					info_msg = Message(
						'Ход: ' + ('синие' if (game.turn == 'blue') else 'красные') +
						'. Счёт: 🔴' + str(game.red_score) + ' : ' + str(game.blue_score) + '🔵\n' +
						'Журнал:', atts=photo2)
					bot.send_message(pid, info_msg)
					game.mid = info_msg.msg_id
					game.status = 'progress'
					gm.save_game(game)
			elif action == 'occupied':
				bot.send_answer(pid, eid, uid, 'У этой команды уже есть капитан')
			elif action == 'pressed':
				bot.send_answer(pid, eid, uid, 'Вы уже нажимали эту кнопку')
			if game != None:
				gm.save_game(game)
