import os
import shutil



def main():
	if os.path.isdir('tmp/release/data/'):
		shutil.rmtree('tmp/release/data/')
		shutil.rmtree('tmp/release/images/')
		print('\n')
	if os.path.isdir('tmp/android/data/'):
		shutil.rmtree('tmp/android/data/')
		shutil.rmtree('tmp/android/images/')
		print('\n')
	if os.path.isdir('tmp/continuous/data/'):
		shutil.rmtree('tmp/continuous/data/')
		shutil.rmtree('tmp/continuous/images/')



# run
main()