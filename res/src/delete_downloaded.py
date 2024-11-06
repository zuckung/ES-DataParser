import os
import shutil


def run():
	if os.path.isdir('tmp/release/data/'):
		print('deleting [release] data')
		shutil.rmtree('tmp/release/data/')
		shutil.rmtree('tmp/release/images/')
		print('DONE')
		print('')
	if os.path.isfile('tmp/release/changelog.txt'):
		print('deleting [release] changelog')
		os.remove('tmp/release/changelog.txt')
		print('DONE')
		print('\n')
	if os.path.isdir('tmp/android/data/'):
		print('deleting [android] data')
		shutil.rmtree('tmp/android/data/')
		shutil.rmtree('tmp/android/images/')
		print('DONE')
		print('')
	if os.path.isfile('tmp/android/changelog.txt'):
		print('deleting [android] changelog')
		os.remove('tmp/android/changelog.txt')
		print('DONE')
		print('\n')
	if os.path.isdir('tmp/continuous/data/'):
		print('deleting [continuous] data')
		shutil.rmtree('tmp/continuous/data/')
		shutil.rmtree('tmp/continuous/images/')
		print('DONE')
		print('')
	if os.path.isfile('tmp/continuous/changelog.txt'):
		print('deleting [continuous] changelog')
		os.remove('tmp/continuous/changelog.txt')
		print('DONE')
		print('')


if __name__ == "__main__":
	run()