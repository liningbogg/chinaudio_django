# coding = utf-8
import json
import pickle
import smtplib
import time
import wave
from datetime import datetime
from datetime import timedelta
from email.mime.application import MIMEApplication
from io import BytesIO
import threading
import librosa.display
import numpy as np
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import loader
from django.utils.decorators import method_decorator
from django.views.generic import View
from pydub import AudioSegment
from django.db.models import Q
import os, shutil
from target.models import Clip
from target.models import MarkedPhrase
from target.models import Tone
from target.models import Wave
from target.models import Labeling
from .forms import RegisterForm
from .forms import UserForm
from .forms import UserFormWithoutCaptcha
from .targetTools import RWLock
from abc import abstractmethod
import scipy
from target.targetTools import targetTools
from baseFrqComb import BaseFrqDetector

# 归一化函数
def MaxMinNormalization(x, minv, maxv):
	Min = np.min(x)
	Max = np.max(x)
	y = (x - Min) / (Max - Min + 0.0000000001) * (maxv - minv) + minv
	return y

# filter by basefrq
def filterByBasefrq(src, basefrq, width, nfft, fs):
	width = width*nfft/fs
	basefrq = basefrq*nfft/fs
	tar = np.copy(src)
	num = min(int(len(src) / basefrq), 30)
	for i in np.arange(num):
		frq = i * basefrq
		tar[int(frq - width):int(frq + width)] = min(src[int(frq - width)], src[int(frq + width)])
	return tar

class MemItem:
	"""
	曲目条目定义类
	"""
	obsolete = timedelta(minutes=120)
	val_list = []  # 成员变量名称列表
	rwLock = RWLock()

	def __init__(self, **kw):
		"""
		初始化参数
		:param kw:
		"""
		self.timestamp = datetime.now()
		try:
			for key in kw:
				if key in self.val_list:
					setattr(self, key, kw[key])
		except Exception as e:
			print(e)

	@abstractmethod
	def get_subwave(self):
		"""
		访问wave子数据
		:param start: 其实位置
		:param end: 中止位置，不包括end
		:return: 返回子数组（float数组）
		"""
		pass

	def is_obsolete(self):
		"""
		检测wave是否过期如果过期
		:return:过期：True 正常：False
		"""
		if (datetime.now() - self.timestamp) > self.obsolete:
			print(self.user_id+"_"+self.title+self.val_list[4]+" 缓存过时")
			return True
		else:
			print(self.user_id+"_"+self.title+"_"+self.val_list[4]+"_"+str(self.fs)+":"+str(self.obsolete)+"|"+str((datetime.now() - self.timestamp)))
			return False


class MemItem_Wave(MemItem):
	"""
	曲目条目定义类
	"""
	obsolete = timedelta(minutes=60)
	val_list = ["user_id", "title", "fs", "nfft", "wave", "timestamp", "obsolete"]	# 成员变量名称列表

	def get_subwave(self, start, end):
		"""
		访问wave子数据
		:param start: 起始位置
		:param end: 终止位置，不包括end
		:return: 返回子数组（float数组）
		"""
		sub = np.copy(self.wave[start: end])
		self.timestamp = datetime.now()
		return sub


class MemItem_Stft(MemItem):
	"""
	短时傅里叶变换缓存类
	"""
	obsolete = timedelta(minutes=60)
	val_list = ["user_id", "title", "fs", "nfft", "stft", "timestamp", "obsolete"]	# 成员变量名称列表

	def __init__(self, **kw):
		super(MemItem_Stft,self).__init__(**kw)
	def get_subwave(self, start, end):
		"""
		获取子stft数据
		:param start:起始位置
		:param end: 终止位置， 不包括end
		:high_cutoff: 截止频率
		:return: stft序列子数组
		"""
		sub = np.copy(self.stft[start:end])
		self.timestamp = datetime.now()
		return sub


class MemItem_spectrum_entropy(MemItem):
	"""
	短时傅里叶频谱熵缓存条目
	"""
	val_list = ["user_id", "title", "fs", "nfft", "spectrum_entropy", "timestamp", "obsolete"]	# 成员变量名称列表
	def get_subwave(self, start, end):
		"""
		获取谱熵子数组
		:param start:起始位置
		:param end: 终止位置，不包括end
		:return: 谱熵子数组
		"""
		sub = np.copy(self.spectrum_entropy[start:end])
		self.timestamp = datetime.now()
		return sub


class MemItem_rmse(MemItem):
	val_list = ["user_id", "title", "fs", "nfft", "rmse", "timestamp", "obsolete"]
	def get_subwave(self, start, end):
		sub = np.copy(self.rmse[start:end])
		self.timestamp = datetime.now()
		return sub

class WaveMem:
	"""
	曲目缓存类
	"""
	@abstractmethod
	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取制定片段，原始wave波形
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:return: float32array
		"""
		pass

	def supervisor(self):
		"""
		监督程序，负责序列维护
		:return:None
		"""
		tag = 1
		while tag == 1:
			for item_key in list(self.container.keys()):
				item = self.container[item_key]
				if item.is_obsolete() is True:
					item.rwLock.wlock.acquire()
					self.container.pop(item_key)  # 从容器中删除过时缓存
					item.rwLock.wlock.release()
			# 设置查询间隔
			time.sleep(5)

	def __init__(self):
		"""
		初始操作，包括轮询线程的启动
		"""
		self.container = {}  # 缓存容器
		self.rwLock_container = RWLock()
		thread = threading.Thread(target=self.supervisor)  # 创建监视线程
		thread.setDaemon(True)	# 设置为守护线程， 一旦用户线程消失，此线程自动回收
		thread.start()


class WaveMemWave(WaveMem):
	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取制定片段，原始wave波形
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:return: float32array
		"""
		sub_wave = []
		self.rwLock_container.rlock.acquire()
		try:
			waveKey = user_id + "_" + title + "_" + "wave_"+str(fs)	 # 例子 pi_秋风词_wave_44100
			if waveKey in self.container.keys():
				sub_wave = self.container[waveKey].get_subwave(start * nfft, end * nfft)
				print(waveKey + " 缓存命中")
			else:
				self.rwLock_container.rlock.release()
				self.rwLock_container.wlock.acquire()
				try:
					if waveKey in self.container.keys():
						sub_wave = self.container[waveKey].get_subwave(start * nfft, end * nfft)
						print(waveKey + " 次命中")
					else:
						# 如果再次判断没有key则此时写入写入数据
						wave = Wave.objects.get(create_user_id=user_id, title=title)
						stream = librosa.load(wave.waveFile, mono=False, sr=fs)[0][0]  # 以Fs重新采样
						mem_item = MemItem_Wave(user_id=user_id, title=title, fs=fs, nfft=nfft,
												timestamp=datetime.now(),
												wave=stream, obsolete=timedelta(minutes=120))
						self.container.update({waveKey: mem_item})
						sub_wave = self.container[waveKey].get_subwave(start * nfft, end * nfft)
						print(waveKey + " 未命中")
				except Exception as addcacheError:
					print("读取错误:"+addcacheError)
				finally:
					self.rwLock_container.wlock.release()
					self.rwLock_container.rlock.acquire()
		except Exception as e:
			print(e)
		finally:
			self.rwLock_container.rlock.release()
		return sub_wave


class WaveMemStft(WaveMem):
	def __init__(self, waveMem_wave):
		super(WaveMemStft, self).__init__()
		self.waveMem_wave = waveMem_wave

	def achieve_Stft(self, user_id, title, fs, nfft, start, end):
		"""
		获取短时傅里叶,此缓存粒度较粗，不提供单帧粒度，若是单帧fft获取，则直接调用数据库，此处设置缓存目的是求给予stft的谱熵等等
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:return: 短时傅里叶功率谱或者幅值谱
		"""
		sub_wave = []
		self.rwLock_container.rlock.acquire()
		try:
			waveKey = user_id + "_" + title + "_" + "stft"	# 例子 pi_秋风词_stft
			if waveKey in self.container.keys():
				sub_wave = self.container[waveKey].get_subwave(start, end)
				print(waveKey + " 缓存命中")
			else:
				self.rwLock_container.rlock.release()
				self.rwLock_container.wlock.acquire()
				try:
					if waveKey in self.container.keys():
						sub_wave = self.container[waveKey].get_subwave(start, end)
						print(waveKey + " 次命中")

					else:
						# 如果再次判断没有key则此时写入写入数据
						# 获取波形
						wave = Wave.objects.get(create_user_id=user_id, title=title)
						# 获取原始左声道波形
						stream = self.waveMem_wave.achieve(user_id, title, fs, nfft, 0, wave.frameNum)
						# 获取stft
						speech_stft, phase = librosa.magphase(
							librosa.stft(stream, n_fft=nfft, hop_length=nfft, window=scipy.signal.hamming))
						speech_stft = np.transpose(speech_stft)  # stft转置
						# 此处的stft仅仅为了求谱熵等，因此不需要特别长的生存时间，谱熵缓存可设置长一点
						mem_item = MemItem_Stft(user_id=user_id, title=title, fs=fs, nfft=nfft,
												timestamp=datetime.now(), stft=speech_stft,
												obsolete=timedelta(minutes=5))
						self.container.update({waveKey: mem_item})
						sub_wave = self.container[waveKey].get_subwave(start, end)
						print(waveKey + " 未命中")
				except Exception as addcacheError:
					print(addcacheError)
				finally:
					self.rwLock_container.wlock.release()
					self.rwLock_container.rlock.acquire()
		except Exception as e:
			print(e)
		finally:
			self.rwLock_container.rlock.release()
		return sub_wave

class WaveMemSpectrumEntropy(WaveMem):
	def __init__(self, waveMem_stft):
		super(WaveMemSpectrumEntropy, self).__init__()
		self.waveMem_stft = waveMem_stft
	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取谱熵
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:return: 谱熵
		"""
		sub_wave = []
		self.rwLock_container.rlock.acquire()
		spectrum_entropy=[]
		try:
			waveKey = user_id + "_" + title + "_" + "spectrum_entropy"	# 例子 pi_秋风词_stft
			if waveKey in self.container.keys():
				sub_wave = self.container[waveKey].get_subwave(start, end)
				print(waveKey + " 缓存命中")
			else:

				self.rwLock_container.rlock.release()
				self.rwLock_container.wlock.acquire()
				try:
					if waveKey in self.container.keys():
						sub_wave = self.container[waveKey].get_subwave(start, end)
						print(waveKey + " 次命中")
					else:
						# 尝试从数据库获取wave.ee
						try:
							wave = Wave.objects.get(create_user_id=user_id, title=title)
							if wave.ee is None or wave.ee == [] or len(wave.ee) < (wave.frameNum/2):
								# 不存在
								stft_ori = self.waveMem_stft.achieve_Stft(user_id, title, fs, nfft, 0, wave.frameNum)
								stft_ori = np.transpose(stft_ori)  # stft转置
								# 计算谱熵
								stft_for_ee = np.copy(stft_ori[0:np.int(nfft / fs * 4000)])  # 4000hz以下信号用于音高检测
								speech_stft_Enp = stft_for_ee[1:-1]
								speech_stft_prob = speech_stft_Enp / np.sum(speech_stft_Enp, axis=0)
								spectrum_entropy = np.sum(-np.log(speech_stft_prob) * speech_stft_prob, axis=0)
								spectrum_entropy = MaxMinNormalization(spectrum_entropy, 0, 1)
								pass
							else:
								# 存在
								spectrum_entropy = pickle.loads(wave.ee)
								pass
						except Exception as e:
							print(e)
						finally:
							# 获取
							wave = Wave.objects.get(create_user_id=user_id, title=title)
							if wave.ee is None or wave.ee == [] or len(wave.ee)<(wave.frameNum/2):
								wave.ee = pickle.dumps(spectrum_entropy)
								wave.save(update_fields=["ee"])
							pass
						# 此处的stft仅仅为了求谱熵等，因此不需要特别长的生存时间，谱熵缓存可设置长一点
						mem_item = MemItem_spectrum_entropy(user_id=user_id, title=title, fs=fs, nfft=nfft,
															timestamp=datetime.now(), spectrum_entropy=spectrum_entropy,
															obsolete=timedelta(minutes=5))
						self.container.update({waveKey: mem_item})
						sub_wave = self.container[waveKey].get_subwave(start, end)
						print(waveKey + " 未命中")
				except Exception as addcacheError:
					print(addcacheError)
				finally:
					self.rwLock_container.wlock.release()
					self.rwLock_container.rlock.acquire()
		except Exception as e:
			print(e)
		finally:
			self.rwLock_container.rlock.release()
		return sub_wave

class WaveMemRmse(WaveMem):
	def __init__(self, waveMem_wave):
		super(WaveMemRmse, self).__init__()
		self.waveMem_wave = waveMem_wave

	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取制定片段，原始wave波形
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:return: float32array
		"""
		sub_rmse = []
		self.rwLock_container.rlock.acquire()
		try:
			waveKey = user_id + "_" + title + "_" + "rmse"	# 例子 pi_秋风词_rmse
			if waveKey in self.container.keys():
				sub_rmse = self.container[waveKey].get_subwave(start, end)
				print(waveKey + " 缓存命中")
			else:
				self.rwLock_container.rlock.release()
				self.rwLock_container.wlock.acquire()
				try:
					if waveKey in self.container.keys():
						sub_rmse = self.container[waveKey].get_subwave(start, end)
						print(waveKey + " 次命中")
					else:
						# 如果再次判断没有key则此时写入写入数据
						# 尝试从数据库获取wave.rmse
						try:
							wave = Wave.objects.get(create_user_id=user_id, title=title)
							if wave.rmse is None or wave.rmse == [] or len(wave.rmse) < (wave.frameNum / 2):
								# 不存在
								# 计算rmse
								# 获取原始左声道波形
								stream = self.waveMem_wave.achieve(user_id, title, fs, nfft, 0, wave.frameNum)
								rmse = librosa.feature.rmse(y=stream, S=None, frame_length=nfft,
															hop_length=nfft, center=True,
															pad_mode='reflect')[0]
								rmse = MaxMinNormalization(rmse, 0, 1)
							else:
								# 存在
								rmse = pickle.loads(wave.rmse)
						except Exception as e:
							print(e)
						finally:
							# 获取
							wave = Wave.objects.get(create_user_id=user_id, title=title)
							if wave.rmse is None or wave.rmse == [] or len(wave.rmse) < (wave.frameNum / 2):
								wave.rmse = pickle.dumps(rmse)
								wave.save(update_fields=["rmse"])

						mem_item = MemItem_rmse(user_id=user_id, title=title, fs=fs, nfft=nfft,
															timestamp=datetime.now(), rmse=rmse,
															obsolete=timedelta(minutes=60))
						self.container.update({waveKey: mem_item})
						sub_rmse = self.container[waveKey].get_subwave(start, end)
						print(waveKey + " 未命中")
				except Exception as addcacheError:
					print(addcacheError)
				finally:
					self.rwLock_container.wlock.release()
					self.rwLock_container.rlock.acquire()
		except Exception as e:
			print(e)
		finally:
			self.rwLock_container.rlock.release()
		return sub_rmse

# Create your views here.
class TargetView(View):
	msg_from = '1214397815@qq.com'	# 发送方邮箱
	passwd = 'ruzdcenkznfhhijf'  # 填入发送方邮箱的授权码
	msg_to = '1214397815@qq.com'  # 收件人邮箱

	def __init__(self):
		"""
		重载初始化函数
		"""
		super(View, self).__init__()
		self.wave_mem_wave = WaveMemWave()	# 构建缓存对象
		self.wave_mem_stft = WaveMemStft(self.wave_mem_wave)
		self.wave_mem_spectrumEntropy = WaveMemSpectrumEntropy(self.wave_mem_stft)
		self.wave_mem_rmse = WaveMemRmse(self.wave_mem_wave)

	@classmethod
	@method_decorator(login_required)
	def index(cls, request):
		"""
		主要索引视图
		:param request:
		:return:
		"""
		# bt = loader.get_template("index.html")
		waves = Wave.objects.filter(create_user_id=request.user)
		for wave in waves:
			clips = Clip.objects.filter(title=wave.title, create_user_id=request.user)
			if clips.count() == 0:
				completion = 0
			else:
				candidateFrame = clips.aggregate(Max('startingPos'))['startingPos__max']
				candidateFrameNum = wave.frameNum  # 待测总帧数
				completion = round(candidateFrame / candidateFrameNum * 100, 1)
				completion = min(100,completion)
			wave.completion = completion
			wave.save()
		waves = Wave.objects.filter(create_user_id=request.user).order_by('frameNum')
		context = {'waves': waves}
		return render(request, 'index.html', context)

	@classmethod
	@method_decorator(login_required)
	def copywaves(cls, request):
		"""
		从其他用户获取wave,然后复制至特定用户
		:param request:
		:return:
		"""
		user_id = str(request.user)
		waves = Wave.objects.filter(~Q(create_user_id=user_id))
		wavenameAlready = Wave.objects.filter(create_user_id=user_id).values('title')
		name_exist = set()
		waves_filter = set()
		for wavename in wavenameAlready:
			name_exist.add(wavename["title"])
		for wave in waves:
			if wave.title not in name_exist:
				waves_filter.add(wave)

		waves = serializers.serialize("json", waves_filter)
		context = {'waves': waves}
		return render(request, 'copywaves.html', context)

	def sub_and_execute_copywaves(self, request):
		user_id = str(request.user)
		waves_selected=json.loads(request.GET.get("waves_selected"))

		for wave in waves_selected:
			create_user = wave["user_id"]
			title = wave["wave_title"]
			try:
				waveItem = Wave.objects.get(create_user_id=create_user, title=title)
				waveItem.save()
				waveItem.pk = None
				newfilepath_arr = waveItem.waveFile.split("/")
				newfilepath_arr.remove("")
				newfilepath_arr[len(newfilepath_arr)-2] = user_id
				fileName=""
				path_name=""
				counter=0
				for path_item in newfilepath_arr:
					fileName=fileName+"/"+path_item
					if counter < len(newfilepath_arr)-1:
						path_name = path_name+"/"+path_item
					counter=counter+1
				if os.path.exists(path_name) == False:
					os.mkdir(path_name)
				shutil.copyfile(waveItem.waveFile, fileName)
				waveItem.waveFile = fileName
				waveItem.create_user_id = user_id
				waveItem.save()
			except Exception as e:
				print(e)
		return HttpResponse("copy completed")

	@method_decorator(login_required)
	def labeling(self, request):
		title = request.GET.get('title')
		user_id = str(request.user)
		wave = Wave.objects.get(create_user_id=user_id, title=title)
		fs = wave.fs
		nfft = wave.nfft
		end = wave.frameNum
		ee = self.wave_mem_spectrumEntropy.achieve(user_id, title, fs, nfft, 0, end)
		ee = list(ee)
		rmse = self.wave_mem_rmse.achieve(user_id, title, fs, nfft, 0, end)
		rmse = list(rmse)
		try:
			labelinfo = Labeling.objects.get(create_user_id=user_id, title=title)
		except Exception as e:
			print("labelinfo no existed, a new labelinfo will be created.")
			Labeling(title=title,create_user_id=user_id,nfft=nfft,frameNum=wave.frameNum).save()
			labelinfo = Labeling.objects.get(create_user_id=user_id, title=title)
		thrartEE = labelinfo.vad_thrart_EE
		thrartRmse = labelinfo.vad_thrart_RMSE
		throp = labelinfo.vad_throp_EE
		vadrs = targetTools.vad(ee, rmse, thrartEE, thrartRmse, throp) 
		extend_rad = labelinfo.extend_rad
		tone_extend_rad = labelinfo.tone_extend_rad
		manual_pos= labelinfo.manual_pos
		if manual_pos<0:
			# 计算位置
			clips = Clip.objects.filter(title=title, create_user_id=request.user,nfft=nfft)
			if clips.count()==0:
				current_frame = 0
			else:
				candidateFrame = clips.aggregate(Max('startingPos'))['startingPos__max']
				current_frame = candidateFrame+1
				current_frame = min(wave.frameNum-1, current_frame)
		else:
			# 指定位置
			labelinfo.manual_pos=-1	# 指定位置只生效一次
			current_frame = manual_pos
			pass			
		labelinfo.current_frame=current_frame
		labelinfo.save()
		# 收集tones
		tones_start = max(current_frame-tone_extend_rad, 0)
		tones_end = min(current_frame+tone_extend_rad, wave.frameNum)
		tones_local_set = Tone.objects.filter(title=title,create_user_id=user_id, pos__range=(tones_start,tones_end))
		tones_local = serializers.serialize("json", tones_local_set)
		# comb及combDescan音高参考
		combRef=np.zeros(wave.frameNum)
		combDescanRef=[[0] * wave.frameNum, [0] * wave.frameNum]
		try:
			clips = Clip.objects.filter(title=title, create_user_id="combDescan", startingPos__lt=wave.frameNum)
			for clip in clips:
				pos=clip.startingPos
				tar=pickle.loads(clip.tar)
				index=0
				for pitch in tar:
					combDescanRef[index][pos]=pitch
					index=index+1
			clips = Clip.objects.filter(title=title, create_user_id="comb", startingPos__lt=wave.frameNum)
			for clip in clips:
				pos=clip.startingPos
				tar=pickle.loads(clip.tar)
				combRef[pos]=tar[0]				
		except Exception as e:
			print(e)
		# 已标记音高
		target = [[0] * wave.frameNum, [0] * wave.frameNum, [0] * wave.frameNum]  # 存储前三个音高的二维数组
		try:
			clips = Clip.objects.filter(title=title, create_user_id=request.user, startingPos__lt=wave.frameNum)
			for clip in clips:
				pos=clip.startingPos
				tar=pickle.loads(clip.tar)
				index=0
				for pitch in tar:
					target[index][pos] = pitch
					index = index+1
		except Exception as e:
			print(e)
		# fft及中间结果
		srcFFT=pickle.loads(Clip.objects.get(title=title, create_user_id="combDescan",startingPos=current_frame).src) 
		srcFFT[0:int(30*nfft/fs)]=0 # 清空30hz以下信号
		filter_rad = labelinfo.filter_rad  # 过滤带宽半径
		current_clip = Clip.objects.get(title=title, create_user_id="combDescan", startingPos=current_frame)
		current_tar = pickle.loads(current_clip.tar)[0]  # 当前帧主音高估计
		if current_tar>40:
			filter_fft = filterByBasefrq(srcFFT, current_tar, filter_rad, nfft, fs)  # 过滤后fft
		else:
			filter_fft = []
		detectorDescan = BaseFrqDetector(True)  # 去扫描线算法
		pitchCombDescan=detectorDescan.getpitch(srcFFT, fs, nfft, False)
		medium=pitchCombDescan[2]
		# 可能的位置
		if wave.chin is not None:
			# 获得chin class
			chin = pickle.loads(wave.chin)
			string_hzes = chin.get_hzes()
			string_notes = chin.get_notes()
			string_do = chin.get_do()
			pitch_scaling = chin.get_scaling()
			a4_hz = chin.get_ahz()
			print(a4_hz)
		else:
			# chin class 不存在
			chin = None
		if chin is not None:
			possiblePos = chin.cal_possiblepos(current_tar)[1].replace("\n", "<br>")
		else:
			possiblePos = "尚未设置chin信息"
		clipsLocalOri=Clip.objects.filter(title=title, create_user_id=user_id,
							startingPos__range=(current_frame-extend_rad, current_frame+extend_rad))
		clipsLocal=[]
		for clip in clipsLocalOri:
			clipsLocal.append({"id": clip.id, "startingPos":clip.startingPos,
									"length": clip.length, "tar": list(pickle.loads(clip.tar))})
		context = {'title': title,'fs':fs,'nfft': nfft, 'ee': ee, 'rmse': rmse, 'stopPos': list(vadrs['stopPos']),
					'manual_pos':manual_pos, 'combDescanPrimary':list(combDescanRef[0]), 'tones_local':tones_local,
					'combDescanSecondary':list(combDescanRef[1]), 'comb':list(combRef),'target':target,
					'startPos': list(vadrs['startPos']),'ee_diff':list(vadrs['ee_diff']),"srcFFT":list(srcFFT),
					'filter_fft':list(filter_fft), 'current_tar':current_tar,"filter_rad":filter_rad,'a4_hz':a4_hz,
					'string_hzes': string_hzes, 'string_notes': string_notes, 'string_do': string_do,'pitch_scaling':pitch_scaling,
					"medium":list(medium),"current_frame":current_frame,"extend_rad":extend_rad,'play_fs':labelinfo.play_fs,
					"tone_extend_rad":tone_extend_rad, "frame_num":end, 'vad_thrart_EE':thrartEE,"clipsLocal": clipsLocal,
					'vad_thrart_RMSE':thrartRmse, 'vad_throp_EE':throp, 'create_user_id':user_id,'possiblePos': possiblePos}
		return render(request, 'labeling.html', context)

	@method_decorator(login_required)
	def cal_pitch_pos(self, request):
		title = request.GET.get('title')
		user_id = str(request.user)
		primary_pitch = float(request.GET.get('primary_pitch'))
		wave = Wave.objects.get(create_user_id=user_id, title=title)
		if wave.chin is not None:
			# 获得chin class
			chin = pickle.loads(wave.chin)
		else:
			# chin class 不存在
			chin = None
		if chin is not None:
			possiblePos = chin.cal_possiblepos(primary_pitch)[1].replace("\n", "<br>")
		else:
			possiblePos = "尚未设置chin信息"
		return HttpResponse(possiblePos)

	@method_decorator(login_required)
	def filter_fft(selfs, request):
		title = request.GET.get('title')
		user_id = str(request.user)
		currentPos = int(request.GET.get('currentPos'))
		filter_frq = float(request.GET.get('filter_frq'))
		filter_width = float(request.GET.get('filter_width'))
		nfft = int(request.GET.get('nfft'))
		fs = int(request.GET.get('fs'))
		try:
			srcFFT=pickle.loads(Clip.objects.get(title=title, create_user_id="combDescan", startingPos=currentPos).src)
			srcFFT[0:int(30 * nfft / fs)] = 0  # 清空30hz以下信号
			fft_filtered = filterByBasefrq(srcFFT, filter_frq, filter_width, nfft, fs)  # 过滤后fft
			fft_filtered=fft_filtered.tolist()
			return HttpResponse(json.dumps(fft_filtered))
		except Exception as e:
			print(e)
			return None

	@classmethod
	@method_decorator(login_required)
	def wave_view(cls, request):
		"""
		曲目视图
		此函数返回统计过的pitches数组
		:return:
		"""
		class Item:
			title = ""
			length = 0
			tar = None
		t = loader.get_template("wave.html")
		title = request.GET.get('title')
		create_user=str(request.user)
		wave = Wave.objects.get(create_user_id=create_user, title=title)
		clips = Clip.objects.filter(title=title, create_user_id=request.user, startingPos__lt=wave.frameNum).order_by('startingPos')
		marked_phrases = MarkedPhrase.objects.filter(create_user_id=create_user, title=title)
		tones = Tone.objects.filter(create_user_id=create_user, title=title).order_by('pos')
		items = []	# 返回的clips
		pitchesArr = [[0] * wave.frameNum, [0] * wave.frameNum, [0] * wave.frameNum]  # 存储前三个音高的二维数组
		# pitchesArr = [pitchesArr]


		if wave.chin is not None:
			chin = pickle.loads(wave.chin)
		else:
			chin = None
		cutoff = int(4200 * wave.nfft / wave.fs)  # src 截断位置

		for clip in clips:
			item = Item()
			item.title = clip.title
			item.startingPos = clip.startingPos
			item.tar = pickle.loads(clip.tar)
			for index in np.arange(len(item.tar)):
				item.tar[index] = round(item.tar[index], 2)
			item.possiblePos = chin.cal_possiblepos(item.tar)[1].replace("\n", "<br>")
			item.id = clip.id
			for index in np.arange(len(item.tar)):
				try:
					pitchesArr[index][clip.startingPos] = item.tar[index]  # 收集已经标定的音高
				except Exception as e:
					print(e)
			items.append(item)

		if wave.chin is not None:
			string_hzes = chin.get_hzes()
			string_notes = chin.get_notes()
			string_do = chin.get_do()

		context = {'clips': items, 'wave': wave, 'pitches': pitchesArr, 'marked_phrases': marked_phrases,
				   'tones': tones, 'string_hzes': string_hzes, 'string_notes': string_notes, 'string_do': string_do}
		return render(request, 'wave.html', context)

	def get_phrase(self, request):
		"""
		获取音乐片段
		:return:音乐片段wav格式2进制流
		"""
		user_id = str(request.user)
		title = request.GET.get('title')
		start = int(request.GET.get('start'))
		end = int(request.GET.get('end'))
		nfft = int(request.GET.get('nfft'))
		fs = int(request.GET.get('fs'))

		# self.wave_mem.add_mem(title)	# 试图将完整曲目加入缓存
		wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  # 获取音频信号
		wave_arr = np.array(wave_arr) * 32767
		wave_arr = wave_arr.astype(np.int16)
		io_stream = BytesIO()  # 内存文件

		f = wave.open(io_stream, 'wb')	# 定位于内存镜像
		f.setnchannels(1)  # 设置为单通道
		f.setsampwidth(2)  # 16位采样
		f.setframerate(fs)	# 设置采样率
		# 将wav_data转换为二进制数据写入文件
		f.writeframes(wave_arr.tostring())	# 写入音频信息
		f.close()  # 关闭写入流
		seg = AudioSegment.from_wav(io_stream)
		io_stream_flac = BytesIO()	# 内存文件
		seg.export(io_stream_flac, format='wav')
		blob_ori = io_stream_flac.getvalue()
		return HttpResponse(blob_ori)

	def post_phrase(self, request):
		"""
		获取音乐片段
		:return:音乐片段wav格式2进制流
		"""
		user_id = str(request.user)
		title = request.GET.get('title')
		start = int(request.GET.get('start'))
		end = int(request.GET.get('end'))
		nfft = int(request.GET.get('nfft'))
		fs = int(request.GET.get('fs'))
		fileName = request.GET.get('fileName')

		#self.wave_mem.add_mem(title)  # 试图将完整曲目加入缓存
		wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  # 获取音频信号
		wave_arr = np.array(wave_arr) * 32767
		wave_arr = wave_arr.astype(np.int16)
		io_stream = BytesIO()  # 内存文件
		f = wave.open(io_stream, 'wb')	# 定位于内存镜像
		f.setnchannels(1)  # 设置为单通道
		f.setsampwidth(2)  # 16位采样
		f.setframerate(fs)	# 设置采样率
		# 将wav_data转换为二进制数据写入文件
		f.writeframes(wave_arr.tostring())	# 写入音频信息
		f.close()  # 关闭写入流"""
		subject = fileName	# 主题
		wav_patch = MIMEApplication(io_stream.getvalue())
		wav_patch.add_header('Content-Disposition', 'attachment', filename=('gbk', '', fileName + '.wav'))
		msg = wav_patch
		msg['Subject'] = subject
		msg['From'] = self.msg_from
		msg['To'] = self.msg_to
		self.sender = smtplib.SMTP_SSL("smtp.qq.com", 465)	# 邮件服务器及端口号
		self.sender.login(self.msg_from, self.passwd)
		self.sender.sendmail(self.msg_from, self.msg_to, msg.as_string())
		return HttpResponse("posted")

	@classmethod
	def db_access(cls, request):
		operation = request.GET.get('operation')  # 操作类型
		class_name = request.GET.get('class')  # 数据类型
		item_id = request.GET.get('id')  # 数据id
		rs = "ok"
		# 删除操作
		if operation == "delete":
			if class_name == "tone":
				item = Tone.objects.get(id=item_id)
				item.delete()
			if class_name == "clip":
				if request.user.has_perm('target.delete_clip'):  # 检查用户是否具有delete权限
					item = Clip.objects.get(id=item_id)
					item.delete()
					status = class_name+ item_id + "已经被删除 ";
				else:
					rs = "err";
		return HttpResponse(rs)

	@classmethod
	def get_clipfft(cls, request):
		id = request.GET.get('id')	# clip_id
		fs = int(request.GET.get('fs'))  # fs
		nfft = int(request.GET.get('nfft'))  # nfft
		try:
			clip = Clip.objects.get(id=id);
		except Exception as e:
			return HttpResponse(e)

		cutoff = int(4200 * nfft / fs)	# src 截断位置
		src = pickle.loads(clip.src)
		src = src.tolist()[0:cutoff]
		return HttpResponse(json.dumps(src))

	@classmethod
	def login(cls, request):
			next = request.GET.get('next', "")
			if request.method == 'GET':
				if request.user is not None and request.user.is_active:
					return redirect("/index/")
				form = UserFormWithoutCaptcha()
				return render(request, 'login.html', {'login_form': form, })
			else:
				form = UserFormWithoutCaptcha(request.POST)
				message = "请检查填写的内容！"
				if form.is_valid():
					username = request.POST.get('username', '')
					password = request.POST.get('password', '')
					user = auth.authenticate(username=username, password=password)
					if user is not None and user.is_active:
						auth.login(request, user)
						if next == "":
							return redirect("/index/")
						else:
							return redirect(next)
					else:
						message = "用户名或者密码错误";
						return render(request, 'login.html', {'login_form': form, 'message': message })
				else:
					message = "表单数据错误";
					return render(request, 'login.html', {'login_form': form, 'message': message})

	@classmethod
	def logout(cls, request):
		auth.logout(request)
		return redirect("/login/")

	@classmethod
	def register(cls, request):
		context = {}
		message = ""
		if request.method == 'POST':
			form = RegisterForm(request.POST)
			message = "请检查填写的内容！"
			if form.is_valid():
				# 获得表单数据
				username = form.cleaned_data['username']
				password = form.cleaned_data['password1']

				# 判断用户是否存在
				user = auth.authenticate(username=username,password = password)
				if user:
					message = "用户已经存在"
					return render(request, 'register.html', {'register_form': form, 'message': message})
				# 添加到数据库（还可以加一些字段的处理）
				user = User.objects.create_user(username=username, password=password)
				user.save()
				# 添加到session
				request.session['username'] = username
				# 调用auth登录
				auth.login(request, user)
				# 重定向到首页
				return redirect('/index')
			else:
				pass

		else:
			form = RegisterForm()
		#将req 、页面 、以及context{}（要传入html文件中的内容包含在字典里）返回
		return render(request, 'register.html',  {'register_form': form, 'message': message})
