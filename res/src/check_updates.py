import requests
import json
from datetime import datetime, timedelta
import time
import os
import zipfile
import shutil


def check_local():
	if os.getcwd() == "/storage/emulated/0/Download/mgit/test/res/src": # check for local testing
		os.chdir("../../")


def decide_update(vpath, vapi, vchangelog):
	print('  checking the online changelog/data folder')
	# check for folder
	if not os.path.isdir('tmp/'):
		os.mkdir('tmp/')
	if not os.path.isdir(vpath):
		os.mkdir(vpath)
	# get last modified changelog
	request = requests.get(vapi, allow_redirects=True, timeout=30)
	data = request.json()
	lastmodifiedO = datetime.strptime(data[0]['commit']['committer']['date'],'%Y-%m-%dT%H:%M:%SZ')
	if vpath == 'tmp/continuous/': # request last modified data folder instead
		newrequest = requests.get('https://api.github.com/repos/endless-sky/endless-sky/commits?path=data&page=1&per_page=1', allow_redirects=True, timeout=30) 
		data = newrequest.json()
		lastmodifiedO = datetime.strptime(data[0]['commit']['committer']['date'],'%Y-%m-%dT%H:%M:%SZ')
	# get version number
	request = requests.get(vchangelog)
	with open(vpath + 'changelog.txt', 'wb') as changelog:
		changelog.write(request.content) # downloading the changelog
	with open(vpath + 'changelog.txt', 'r') as sourcefile:
		onlineversion = sourcefile.readline().replace('Version ', '').replace('\n', '').replace(':', '') # result example: 0.10.10
	# check for local data
	if not os.path.isfile(vpath + 'check.txt'):
		# create a new check.txt
		print('  no local data found, creating it now')
		with open(vpath + 'check.txt', 'w') as target:
			target.writelines('version=' + onlineversion + '\n')
			target.writelines('lastUpdate=' + str(lastmodifiedO)+ '\n')
		return True, onlineversion, lastmodifiedO
	# local data is there
	else:
		print('  found local data, comparing now')
		with open(vpath + 'check.txt', 'r') as source:
			localversion = source.readline().replace('version=', '').replace('\n', '')
			uDate = datetime.strptime(source.readline().replace('lastUpdate=', '').replace('\n', ''),'%Y-%m-%d %H:%M:%S')
		if uDate != lastmodifiedO:
			print('  online and local data is different')
			with open(vpath + 'check.txt', 'w') as target:
				target.writelines('version=' + onlineversion + '\n')
				target.writelines('lastUpdate=' + str(lastmodifiedO)+ '\n')
			return True, onlineversion, lastmodifiedO
		else:
			print('  online and local data is the same')
			return False, onlineversion, lastmodifiedO
	

def download(version, vpath, vzip):
	# downloading zip
	if vpath == 'tmp/release/':
		vzip = vzip.replace('0.10.10', version)
	print('  downloading now')
	request = requests.get(vzip, allow_redirects=True, timeout=30)
	with open(vpath + version + '.zip', 'wb') as zipped: # creating zip file
		zipped.write(request.content)
	print('    download complete')


def unpack(version, vpath, lastmodifiedO):
	# modifying index.html
	print('  unpacking zip')
	archive = zipfile.ZipFile(vpath + version + '.zip')
	# if release
	if vpath == 'tmp/release/':
		with open('page/index.html', 'r') as source: # writing version to page/index.html
			lines = source.readlines()
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('release/index') > 0:
					line = '<td style="width:200px"><a href="release/index.html" style="color: #80808;">release (' + version + ')</a></td>\n'
				elif line.find('release update') > 0:
					line = '<td style="font-size:11px;">release update: <br>[' + str(lastmodifiedO).split(' ')[0] + ']</td>\n'
				target.write(line)
	# if android
	if vpath == 'tmp/android/':
		with open('page/index.html', 'r') as source: # writing version to page/index.html
			lines = source.readlines()
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('android/index') > 0:
					line = '<td style="width:200px"><a href="android/index.html" style="color: #80808;">android (' + version + ')</a></td>\n'
				elif line.find('android update') > 0:
					line = '<td style="font-size:11px;">android update: <br>[' + str(lastmodifiedO).split(' ')[0] + ']</td>\n'
				target.write(line)
	# if continuous
	if vpath == 'tmp/continuous/':
		with open('page/index.html', 'r') as source: # writing version to page/index.html
			lines = source.readlines()
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('continuous/index') > 0:
					line = '<td style="width:200px"><a href="continuous/index.html" style="color: #808080;">continuous (' + version + ' +)</a></td>\n'
				elif line.find('continuous update') > 0:
					line = '<td style="font-size:11px;">continuous update: <br>[' + str(lastmodifiedO).split(' ')[0] + ']</td>\n'
				target.write(line)		
	# unpacking
	for file in archive.namelist():
		# if release
		if vpath == 'tmp/release/':
			if file.startswith('data/') or file.startswith('images/'):
				archive.extract(file, vpath)
		# if android				
		elif vpath == 'tmp/android/':
			if file.startswith('endless-mobile-android/data/') or file.startswith('endless-mobile-android/images/'):
				archive.extract(file, vpath)
				shutil.copytree('tmp/android/endless-mobile-android/', 'tmp/android/', dirs_exist_ok=True)
				shutil.rmtree('tmp/android/endless-mobile-android/')
		# if continuous
		elif vpath == 'tmp/continuous/':
			if file.startswith('endless-sky-master/data/') or file.startswith('endless-sky-master/images/'):
				archive.extract(file, vpath)
				shutil.copytree('tmp/continuous/endless-sky-master/', 'tmp/continuous/', dirs_exist_ok=True)
				shutil.rmtree('tmp/continuous/endless-sky-master/')
	os.remove(vpath + version + '.zip')
	print('    unpacking done')


def run():
	check_local()	
	# checking for Release update
	print('[release version]')
	vRpath = 'tmp/release/'
	vRapi = 'https://api.github.com/repos/endless-sky/endless-sky/commits?path=changelog&page=1&per_page=1'
	vRchangelog = 'https://github.com/endless-sky/endless-sky/raw/refs/heads/master/changelog'
	vRzip = 'https://github.com/endless-sky/endless-sky/releases/download/v0.10.10/EndlessSky-win64-v0.10.10.zip' # 0.10.10 will be replaced with current version	
	update, version, lastmodifiedO = decide_update(vRpath, vRapi, vRchangelog)
	if update == True:
		download(version, vRpath, vRzip)
		unpack(version, vRpath, lastmodifiedO)
		print('  DONE')
	else:
		print('  ABORTING')
	print('')
	# checking for Android update
	print('[android version]')
	vApath = 'tmp/android/'
	vAapi = 'https://api.github.com/repos/thewierdnut/endless-mobile/commits?path=changelog&page=1&per_page=1'
	vAchangelog = 'https://github.com/thewierdnut/endless-mobile/raw/refs/heads/android/changelog'
	vAzip = 'https://github.com/thewierdnut/endless-mobile/archive/refs/heads/android.zip'	
	update, version, lastmodifiedO = decide_update(vApath, vAapi, vAchangelog)
	if update == True:
		download(version, vApath, vAzip)
		unpack(version, vApath, lastmodifiedO)
		print('  DONE')
	else:
		print('  ABORTING')
	print('')
	# checking for Continous update
	print('[continuous version]')
	vCpath = 'tmp/continuous/'
	vCapi = 'https://api.github.com/repos/endless-sky/endless-sky/commits?path=changelog&page=1&per_page=1'
	vCchangelog = 'https://github.com/endless-sky/endless-sky/raw/refs/heads/master/changelog'
	vCzip = 'https://github.com/endless-sky/endless-sky/archive/refs/heads/master.zip'
	update, version, lastmodifiedO = decide_update(vCpath, vCapi, vCchangelog)
	if update == True:
		download(version, vCpath, vCzip)
		unpack(version, vCpath, lastmodifiedO)
		print('  DONE')
	else:
		print('  ABORTING')
	print('')


if __name__ == "__main__":
	run()
