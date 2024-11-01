import requests
import json
from datetime import datetime
import time
import os
import zipfile
import shutil



def get_changelog(vpath, vapi, vchangelog):
	# getting the changelog online
	print('checking for update and downloading if needed')
	if vpath == 'tmp/release/':
		print('  [release version]')
	elif vpath == 'tmp/android/':
		print('  [android version]')
	elif vpath == 'tmp/continuous/':
		print('  [continuous version]')
	print('  checking the changelog')
	# decide if changelog gets downloaded
	request = requests.get(vapi, allow_redirects=True, timeout=30)
	data = request.json()
	lastmodified1 = datetime.strptime(data[0]['commit']['committer']['date'],'%Y-%m-%dT%H:%M:%SZ')
	if os.path.isfile(vpath + 'changelog.txt'):
		lastmodified2 = datetime.strptime(time.ctime(os.path.getmtime(vpath + 'changelog.txt')), '%a %b %d %H:%M:%S %Y')
	else:
		lastmodified2 = lastmodified1
	difference = lastmodified2 - lastmodified1
	print('    online changelog: ' + str(lastmodified1) + ' | local changelog: ' + str(lastmodified2) + ' | difference: ' + str(difference))
	if difference.seconds < 1: # if local version is older
		print('    online changelog is newer, downloading it now')
		request = requests.get(vchangelog)
		with open(vpath + 'changelog.txt', 'wb') as changelog:
			changelog.write(request.content) # downloading new changelog
		return True
	else:
		print('    local changelog is newer, not downloading')
		return False


def get_version(vpath):
	# extracting current and downloaded version
	print('  getting current version')
	with open(vpath + 'changelog.txt', 'r') as sourcefile:
		onlineversion = sourcefile.readline().replace('Version ', '').replace('\n', '') # result example: 0.10.10
	with open(vpath + 'currentversion.txt', 'r') as sourcefile:
		localversion = sourcefile.readline().replace('Version ', '').replace('\n', '') # result example: 0.10.10
	print('    online version: ' + onlineversion + ' | local version: ' + localversion)
	if onlineversion != localversion:
		print('    different versions, continuing')
		return True, onlineversion
	else:
		print('    same versions, stopping')
		return False, onlineversion
	

def download(version, vpath, vzip):
	# downloading zip
	if vpath == 'tmp/release/':
		vzip = vzip.replace('0.10.10', version)
	print('  downloading now')
	request = requests.get(vzip, allow_redirects=True, timeout=30)
	with open(vpath + version + '.zip', 'wb') as zipped: # creating zip file
		zipped.write(request.content)
	if vpath != 'tmp/continous/':
		with open(vpath +'currentversion.txt', 'w') as versionfile: # updating version file
			versionfile.write(version)
	print('    download complete')


def unpack(version, vpath):
	# modifying index.html
	print('  unpacking zip')
	
	archive = zipfile.ZipFile(vpath + version + '.zip')
	if vpath == 'tmp/release/':
		with open('page/index.html', 'r') as source: # writing version to page/index.html
			lines = source.readlines()
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('release/index') > 0:
					line = '<td style="width:200px"><a href="release/index.html" style="color: #80808;">release (' + version + ')</a></td>\n'
				elif line.find('release update') > 0:
					line = '<td style="font-size:11px;">release update: <br>[' + datetime.today().strftime('%Y-%m-%d') + ']</td>\n'
				target.write(line)
				
	if vpath == 'tmp/android/':
		with open('page/index.html', 'r') as source: # writing version to page/index.html
			lines = source.readlines()
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('android/index') > 0:
					line = '<td style="width:200px"><a href="android/index.html" style="color: #80808;">android (' + version + ')</a></td>\n'
				elif line.find('android update') > 0:
					line = '<td style="font-size:11px;">android update: <br>[' + datetime.today().strftime('%Y-%m-%d') + ']</td>\n'
				target.write(line)
				
	if vpath == 'tmp/continuous/':
		with open('page/index.html', 'r') as source: # writing version to page/index.html
			lines = source.readlines()
		with open('page/index.html', 'w') as target:
			for line in lines:
				if line.find('continuous/index') > 0:
					line = '<td style="width:200px"><a href="continuous/index.html" style="color: #808080;">continuous (' + version + ')</a></td>\n'
				elif line.find('continuous update') > 0:
					line = '<td style="font-size:11px;">continuous update: <br>[' + datetime.today().strftime('%Y-%m-%d') + ']</td>\n'
				target.write(line)
				
	# unpacking
	for file in archive.namelist():
		if vpath == 'tmp/release/':
			if file.startswith('data/') or file.startswith('images/'):
				archive.extract(file, vpath)
						
		elif vpath == 'tmp/android/':
			if file.startswith('endless-mobile-android/data/') or file.startswith('endless-mobile-android/images/'):
				archive.extract(file, vpath)
				shutil.copytree('tmp/android/endless-mobile-android/', 'tmp/android/', dirs_exist_ok=True)
				shutil.rmtree('tmp/android/endless-mobile-android/')
				
		elif vpath == 'tmp/continuous/':
			if file.startswith('endless-sky-master/data/') or file.startswith('endless-sky-master/images/'):
				archive.extract(file, vpath)
				shutil.copytree('tmp/continuous/endless-sky-master/', 'tmp/continuous/', dirs_exist_ok=True)
				shutil.rmtree('tmp/continuous/endless-sky-master/')
			
	os.remove(vpath + version + '.zip')
	print('    unpacking done')
	print('\n')


def main():
	vRpath = 'tmp/release/'
	vRapi = 'https://api.github.com/repos/endless-sky/endless-sky/commits?path=changelog&page=1&per_page=1'
	vRchangelog = 'https://github.com/endless-sky/endless-sky/raw/refs/heads/master/changelog'
	vRzip = 'https://github.com/endless-sky/endless-sky/releases/download/v0.10.10/EndlessSky-win64-v0.10.10.zip' # 0.10.10 will be replaced with current version
	
	vApath = 'tmp/android/'
	vAapi = 'https://api.github.com/repos/thewierdnut/endless-mobile/commits?path=changelog&page=1&per_page=1'
	vAchangelog = 'https://github.com/thewierdnut/endless-mobile/raw/refs/heads/android/changelog'
	vAzip = 'https://github.com/thewierdnut/endless-mobile/archive/refs/heads/android.zip'
	
	vCpath = 'tmp/continuous/'
	vCapi = 'https://api.github.com/repos/endless-sky/endless-sky/commits?path=changelog&page=1&per_page=1'
	vCchangelog = 'https://github.com/endless-sky/endless-sky/raw/refs/heads/master/changelog'
	vCzip = 'https://github.com/endless-sky/endless-sky/archive/refs/heads/master.zip'
	
	# checking for Release update
	update = False
	newchangelog = get_changelog(vRpath, vRapi, vRchangelog)
	if newchangelog == True:
		update, version = get_version(vRpath)
	else: # just to get baseversion for continuous
		update, version = get_version(vRpath)
		update = False
	if update == True:
		download(version, vRpath, vRzip)
		unpack(version, vRpath)
	# checking for Android update
	update = False
	newchangelog = get_changelog(vApath, vAapi, vAchangelog)
	if newchangelog == True:
		update, version = get_version(vApath)
	if update == True:
		download(version, vApath, vAzip)
		unpack(version, vApath)
	# checking for Continous update
	update = False
	update = get_changelog(vCpath, vCapi, vCchangelog) # prints are wrong, due to different actions
	stub, version = get_version(vCpath)
	if update == True:
		download(version, vCpath, vCzip)
		unpack(version, vCpath)



# run
main()
