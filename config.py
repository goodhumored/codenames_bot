log_answers = True
colors = {
	'black': (68, 68, 68),
	'black_text': (170, 170, 170),
	'red': (255, 100, 80),
	'red_text': (138, 16, 0),
	'blue': (80, 187, 255),
	'blue_text': (0, 84, 138),
	'white': (250, 250, 250),
	'white_text': (68, 68, 68),
	'yellow': (255, 224, 178),
	'yellow_text': (54, 38, 32)
}

commands = {
	r'\s*(начать|новая игра|(codenames )?start)\s*': 'start',
	r'\s*(\w+)\s*(\d)\s*': 'hint',
	r'\s*(\d+)\s*(\w+)\s*(\d)\s*': 'im_hint',
	r'\s*(правила|help|hilfe)\s*': 'help',
	r'\s*(info|game|игра|инф(о|а))\s*': 'info',
	r'\s*(\w+\s?\w*)\s*': 'word',
}


help_text = '''
Краткие правила:
  Капитаны двух команд знают кодовые имена своих тайных агентов. А их товарищи по команде не догадываются, кто 
скрываетсяза тем или иным именем. Команды соревнуются, стараясь первыми установить контакт со всеми своими агентами.
 
  В свой ход капитан даёт подсказку, состоящую из одного слова, которое объединяет несколько карточек на поле.
Игрокаи пытаются отгадать слова своей команды, при этом остерегаясь тех карточек, которые принадлежат соперникам.

И все хотят избежать встречи с убийцей.
Полные правила: https://vk.cc/cbVXIc 
'''

block_width = 355
block_height = 70
block_margin = 12
field_padding = 24

dicts_dir = 'resources\\dictionaries\\'
images_dir = 'resources\\images\\'
fonts_dir = 'resources\\fonts\\'
games_json = 'games\\games.json'

font_name = 'Roboto-Regular.ttf'
font_size = 29


