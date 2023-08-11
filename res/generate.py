import os
import time

def check_local():
	if os.getcwd() == "/storage/emulated/0/Download/mgit/ES-Dataarser/res": # check for local testing
		os.chdir("../")

def read_template():
	with open('res/template.txt', 'r') as file1:
		templates_all = file1.read()
		templates = templates_all.split('%cut template here%')
	index_temp = templates[0]
	menu_temp = templates[1]
	category_temp = templates[2].split('%tmpl%')
	upper_category_temp = category_temp[0]
	lower_category_temp = category_temp[1]
	object_temp = templates[3]
	return index_temp, menu_temp, object_temp, upper_category_temp, lower_category_temp

def read_everything():
	started = False
	obj, obj_path, obj_name = [], [], []
	folders = os.listdir(data_folder)
	folders.append('')
	folders.sort()
	for folder in  folders:
		if os.path.isdir(data_folder + folder):
			text_files = os.listdir(data_folder + folder)
			text_files.sort()
			for text_file in text_files:
				if os.path.isfile(data_folder + folder + '/' + text_file) == False:
					continue
				if len(folder + text_file)  < 80: # just for displaying / max len = 44(currently)
					count = 80 - len(folder + text_file)
					spaces = ''
					for i in range(0, count):
						spaces += ' '
				print('reading: ' + folder + '/' + text_file + spaces, end = '\r', flush= True)
				#time.sleep(.01)
				with open(data_folder + folder + '/' + text_file, 'r') as source_file:
					lines = source_file.readlines()
				for line in lines:
					if line[:1] == '#':
						continue
					elif line == '\n':
						continue
					elif line == '\t\n':
						continue
					elif line == '\t\t\n':
						continue
					elif line[:1] != '\t':
							if started == True:
								obj.append(txt)
								obj_path.append(txt2)
								obj_name.append(txt3)
								started = False
							txt = line
							if folder != '':
								folder_fix = folder + '/'
							else:
								folder_fix = folder
							txt2 = 'data/' + folder_fix + text_file
							txt3 = line[:len(line)-1]
							started = True
					else:
						if started == True:
							txt += line
	return obj, obj_path, obj_name

def write_frameset():
	if os.path.isdir('page/') == False:
		os.mkdir('page/')
	with open('page/index.html', 'w') as readme_write:
		readme_write.writelines(index_template)
	with open('page/menu.html', 'w') as readme_write:
		readme_write.writelines(menu_template)

def replace_template(ob, ob_path, ob_name):
	template = object_template
	template = template.replace('%filename%', ob_path).replace('%objectname%', ob_name).replace('%object%', ob)
	return template

def store_category(category):
	with open('page/' + category.strip() + '.html', 'w') as file1:
		file1.writelines(upper_category_template)
		for each in objects:
			if each[:len(category)] == category:
				o_index = objects.index(each)
				obj_path = object_paths[o_index]
				obj_name = object_names[o_index]
				txt = replace_template(each, obj_path, obj_name)
				#print(each)		
				file1.writelines(txt + '\n')
		file1.writelines(lower_category_template)

def write_html():
	#categories = ['system '] # for testing
	categories = ['category ', 'conversation ', 'effect ', 'event ', 'fleet ', 'galaxy ', 'government ', 'hazard ', 'minable ', 'mission ', 'news ', 'outfit ', 'outfitter ', 'person ', 'phrase ', 'planet ', 'ship ', 'shipyard ', 'star ', 'start ', 'system ']
	print('\n\n')
	for each in categories:
		print('creating ' + each[:len(each)-1] + '.html')
		store_category(each)

		
data_folder = 'data/'

check_local()
objects, object_paths, object_names = read_everything() # creates list of objects, a list of each path and each name
index_template, menu_template, object_template, upper_category_template, lower_category_template = read_template() # read the templates
write_frameset() # write indec.html and menu.html
write_html() # write all category html files

