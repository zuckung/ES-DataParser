import os


def check_local():
	if os.getcwd() == "/storage/emulated/0/Download/mgit/ES-DataParser/res/src": # check for local testing
		os.chdir("../../")


def rewrite_check():
	with open('tmp/release/check.txt', 'w') as target:
		target.writelines('version=0.10.9\n')
		target.writelines('lastUpdate=2024-01-01 00:00:00\n')
	with open('tmp/continuous/check.txt', 'w') as target:
		target.writelines('version=0.10.9\n')
		target.writelines('lastUpdate=2024-01-01 00:00:00\n')
	with open('tmp/android/check.txt', 'w') as target:
		target.writelines('version=0.10.9\n')
		target.writelines('lastUpdate=2024-01-01 00:00:00\n')


def run():
	check_local()
	rewrite_check()
	

if __name__ == "__main__":
	run()	