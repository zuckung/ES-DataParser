import os
import time



def read_template():
	print('creating html')
	print('  reading templates')
	with open('res/template.txt', 'r') as file1:
		templates_all = file1.read()
		templates = templates_all.split('%cut template here%')
	menu_template = templates[0]
	category_template = templates[1]
	object_template = templates[2]
	return menu_template, category_template, object_template
	
def read_everything(data_folder):
	print('  reading data folder')
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
				#print('    reading: ' + folder + '/' + text_file + spaces, end = '\r', flush= True)
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
								obj.append(txt.replace('<', '&#60;').replace('>', '&#62;'))
								obj_path.append(txt2)
								obj_name.append(txt3.replace('\t', ' '))
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


def get_object_categories(object_names):
	print('  getting categories')
	categories = []
	for obj in object_names:
		if obj[:1] == '"':
			pos = obj.find('"', 1) + 1
			category = obj[:pos]
		else:
			category = obj.split(' ')[0]
		if category in categories:
			continue
		else:
			categories.append(category)
	categories.sort()
	return categories


def write_html(categories, category_template, object_names, object_paths, objects, object_template, version):
	print('  writing html files')
	counting = []
	globalcount = 0
	for category in categories:
		catcount = 0
		catfile = category.replace('"', '').replace(' ', '_')
		#print('    creating ' + catfile.strip() + '.html')
		with open('page/' + version + '/' + catfile.strip() + '.html', 'w') as file1:
			splitted = category_template.split('%tmpl%')
			file1.writelines(splitted[0])
			for obj_name in object_names:
				if obj_name.startswith(category + ' ') or obj_name.startswith(category + '\t') or obj_name == (category):
					catcount += 1
					globalcount +=1
					o_index = object_names.index(obj_name)
					obj_path = object_paths[o_index]
					obj = objects[o_index]
					txt = object_template.replace('%filename%', obj_path).replace('%objectname%', obj_name).replace('%object%', obj)
					#print(each)		
					file1.writelines(txt + '\n')
			file1.writelines(splitted[1])
			counting.append(catcount)
	return counting, globalcount


def write_menu(menu_template, categories, counting, version):
	print('  writing html menu')
	splitted = menu_template.split('%categories%')
	with open('page/' + version + '/menu.html', 'w') as file1:
		file1.writelines(splitted[0])
		catpos = 0
		for each in categories:
			each = each.replace('"', '').replace(' ', '_')
			file1.writelines('<a href="' + each + '.html" target="main">' + each + '</a>  (' + str(counting[catpos]) + ')<br>\n')
			catpos += 1
		file1.writelines(splitted[1])


def save_global_count(globalcount, vpath):
	with open('page/index.html', 'r') as source:
		lines = source.readlines()
	if vpath == 'tmp/release/':
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('release objects') > 0:
					line ='<td style="font-size:11px;">release objects: <br>[' + str(globalcount) + ']</td>\n'
				target.write(line)
	if vpath == 'tmp/continuous/':
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('continuous objects') > 0:
					line ='<td style="font-size:11px;">continuous objects: <br>[' + str(globalcount) + ']</td>\n'
				target.write(line)
	if vpath == 'tmp/android/':
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('android objects') > 0:
					line ='<td style="font-size:11px;">android objects: <br>[' + str(globalcount) + ']</td>\n'
				target.write(line)


def main():
	if os.path.isdir('tmp/release/data/'):
		data_folder = 'tmp/release/data/'
		vpath  = 'tmp/release/'
		print('[release]')
		menu_template, category_template, object_template = read_template()
		objects, object_paths, object_names = read_everything(data_folder) # creates list of objects, a list of each path and each name
		categories = get_object_categories(object_names)
		counting, globalcount = write_html(categories, category_template, object_names, object_paths, objects, object_template, 'release')
		save_global_count(globalcount,vpath)
		write_menu(menu_template, categories, counting, 'release')
		print('\n')
	if os.path.isdir('tmp/android/data/'):
		data_folder = 'tmp/android/data/'
		vpath  = 'tmp/android/'
		print('[android]')
		menu_template, category_template, object_template = read_template()
		objects, object_paths, object_names = read_everything(data_folder) # creates list of objects, a list of each path and each name
		categories = get_object_categories(object_names)
		counting, globalcount = write_html(categories, category_template, object_names, object_paths, objects, object_template, 'android')
		save_global_count(globalcount,vpath)
		write_menu(menu_template, categories, counting, 'android')
		print('\n')
	if os.path.isdir('tmp/continuous/data/'):
		data_folder = 'tmp/continuous/data/'
		vpath  = 'tmp/continuous/'
		print('[continuous]')
		menu_template, category_template, object_template = read_template()
		objects, object_paths, object_names = read_everything(data_folder) # creates list of objects, a list of each path and each name
		categories = get_object_categories(object_names)
		counting, globalcount = write_html(categories, category_template, object_names, object_paths, objects, object_template, 'continuous')
		save_global_count(globalcount,vpath)
		write_menu(menu_template, categories, counting, 'continuous')



# run
main()