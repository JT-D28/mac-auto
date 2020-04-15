#import easycython
import os, subprocess, shutil, traceback, stat, datetime, random, sys, time, multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

class EncryptCode(object):
	EASYCYTHON_PREFIX = 'cpython-37m-x86_64-linux-gnu'
	WORKERER_COUNT = 1
	KZ = (lambda: 'pyd' if sys.platform.startswith('win') else 'so')()
	CYCLE_SKIP = ['_pycache', 'tools', 'logs', '.git', 'migrations', 'Function','storage','django']
	ENCRYPT_SKIP = ['__init__.py', 'builtin.py', 'manage.py', 'configs.py', 'models.py', 'invoker.py']
	ERROR_MAP = {
		'Mixed use of tabs and spaces': 'Mixed use of tabs and spaces',
		'undeclared name not builtin': 'undeclared name not builtin',
		'Unrecognized character': 'Unrecognized character'
	}
	ERROR_MSG = {}
	_TOTAL = 0
	_ALL_TASK = []
	_e = ThreadPoolExecutor(max_workers=WORKERER_COUNT)
	@classmethod
	def main(cls, encrypt_taget):
		start_time = time.time()
		suc = err = 0
		project_name = os.path.basename(encrypt_taget)
		parent_name = os.path.dirname(encrypt_taget)
		wait_encrypt_file = os.path.join(parent_name, '%s_encypt' % project_name)
		
		try:
			import easycython
		except:
			print('[-]install easycython')
			return
		
		if os.path.isfile(encrypt_taget):
			print('[-]put one dir')
			return
		
		if os.path.exists(wait_encrypt_file):
			shutil.rmtree(wait_encrypt_file, onerror=cls._rm_read_only)
		
		shutil.copytree(encrypt_taget, wait_encrypt_file)
		
		cls.ENCRYPT_PROJECT = wait_encrypt_file
		print('[+]create=>%s' % wait_encrypt_file)
		print('[+]start')
		
		cls._cycle(wait_encrypt_file)
		
		for future in as_completed(cls._ALL_TASK):
			status, tag = future.result()
			if status is not 'success':
				continue
			
			error = cls.ERROR_MSG.get(tag)
			errortag = ''
			
			filename = tag.replace('|', os.sep)
			if error:
				err += 1
				errtag = ''
				for key in cls.ERROR_MAP:
					if error.__contains__(key):
						errortag = cls.ERROR_MAP.get(key)
				
				print('[-]done\t<%s>\nError[%s]:\n%s' % (filename, errortag, error))
				continue
			else:
				suc += 1
				print('[-]success\t<%s> ' % filename)
			
			parent_name = os.path.dirname(filename)
			base_name = os.path.basename(filename)
			simple_name = base_name.split('.')[0]
			ext_name = base_name.split('.')[1]
			files = os.listdir('.')
			src = ''
			for f in files:
				if simple_name in f and f.endswith(cls.KZ):
					src = '.'.join([simple_name, f.split('.')[1], cls.KZ])
			dist = os.path.join(parent_name, '%s.%s' % (simple_name, cls.KZ))
			pyfile = os.path.join(parent_name, '%s.py' % simple_name)
			
			try:
				print('hhh',src,dist)
				shutil.move(src, dist)
				print('[-]create file %s' % dist)
				
				os.remove(pyfile)
				print('[-]remove  %s' % pyfile)
			
			
			except:
				print('[-]error ,reduce worker %s' % dist)
				print(traceback.format_exc())
		
		print('\n====================has done==================')
		print('spend:%.1fs\t\ttotal=%s\t\tsuccess=%s\t\terror=%s' % ((time.time() - start_time), (suc + err), suc, err))
	
	@classmethod
	def _cycle(cls, full_path):
		for _ in cls.CYCLE_SKIP:
			if full_path.__contains__(_):
				return;
		
		files = os.listdir(full_path)
		for file in files:
			cur_path = os.path.join(full_path, file)
			if os.path.isfile(cur_path):
				if cur_path.endswith('.py'):
					# cls._gen_pyd_so(cur_path)
					
					cls._ALL_TASK.append(cls._e.submit(cls._gen_pyd_so, (cur_path)))
			else:
				cls._cycle(cur_path)
	
	@classmethod
	def _gen_pyd_so(cls, file):
		# print('file=>',__file__)
		# print('1',os.path.dirname(__file__))
		os.chdir(os.path.dirname(__file__))
		tag = '|'.join(file.split(os.sep))
		# timefile_dist=''
		# stime=str(random.random()).replace('\s+','.')
		try:
			# tag=str(datetime.datetime.now())+str(random.random())
			cls._TOTAL = cls._TOTAL + 1
			filename = os.path.basename(file)
			
			if filename in cls.ENCRYPT_SKIP:
				return ('skip', '')
			
			##
			# command = os.path.join(cls.EASYCYTHON_PREFIX, 'easycython') + ' %s' % file
			command = 'python3 easycython.py %s'%file
			print('commandYYYYYYYYYYYYYYYYyyyy=>',command)
			# os.system(command)
			p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
			                     stderr=subprocess.PIPE)
			p.wait()
			msg, error = p.communicate()
			
			if error.decode().__contains__('Error compiling Cython file:'):
				errmsg = str(error.decode())
			
				cls.ERROR_MSG[tag] = errmsg
	
	##
	
		except:
			print('[-]encypt[%s]except=>', traceback.format_exc())


		return ('success', tag)


	@classmethod
	def _easycython_install(cls):
		pass
	
	
	@classmethod
	def _rm_read_only(cls, fn, tmp, info):
		if os.path.isfile(tmp):
			os.chmod(tmp, stat.S_IWRITE)
			os.remove(tmp)
		elif os.path.isdir(tmp):
			os.chmod(tmp, stat.S_IWRITE)
			shutil.rmtree(tmp)


if __name__ == '__main__':
	project = r'%s'%sys.argv[1]
	try:
		ec = EncryptCode()
		ec.main(project)
	except:
		print(traceback.format_exc())
