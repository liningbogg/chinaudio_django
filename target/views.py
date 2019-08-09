# coding = utf-8
import json
import pickle
import smtplib
from datetime import timedelta
from email.mime.application import MIMEApplication
from io import BytesIO
import threading
import librosa
import numpy as np
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
import wave as waveout
from pydub import AudioSegment
from django.db.models import Q
import os
import shutil
from target.models import Clip
from target.models import MarkedPhrase
from target.models import Tone
from target.models import Wave
from target.models import Labeling
from target.models import Stft
from target.models import AlgorithmsClips
from target.models import AlgorithmsMediums
from target.models import LabelingAlgorithmsConf
from target.models import Tune
from .forms import RegisterForm
from chin import Chin
from .forms import UserFormWithoutCaptcha
from abc import abstractmethod
import scipy
import scipy.signal.windows
from target.targetTools import targetTools
from baseFrqComb import BaseFrqDetector
from scipy.interpolate import interp1d
from scipy.fftpack import fft
from cacheout import Cache
import multiprocessing
import time


# 归一化函数
def maxminnormalization(x, minv, maxv):
	min_val = np.min(x)
	max_val = np.max(x)
	y = (x - min_val) / (max_val - min_val + 0.0000000001) * (maxv - minv) + minv
	return y


# filter by basefrq
def filter_by_base(src, basefrq, width, nfft, fs):
	width = width*nfft/fs
	basefrq = basefrq*nfft/fs
	tar = np.copy(src)
	num = min(int(len(src) / basefrq), 30)
	for i in np.arange(num):
		frq = i * basefrq
		tar[int(frq - width):int(frq + width)] = min(src[int(frq - width)], src[int(frq + width)])
	return tar


# 缓存类基类
class MemItem:
	"""
	曲目条目定义类
	"""
	@abstractmethod
	def get_subwave(self, start, end):
		"""
		访问wave子数据
		:param start: 其实位置
		:param end: 中止位置，不包括end
		:return: 返回子数组（float数组）
		"""
		pass


# wave类
class MemitemWave(MemItem):
	"""
	曲目条目定义类
	"""
	obsolete = timedelta(minutes=60)
	val_list = ["user_id", "title", "fs", "nfft", "wave", "obsolete"]  # 成员变量名称列表

	def __init__(self, user_id, title, fs, nfft, wave, obsolete):
		self.user_id = user_id
		self.title = title
		self.fs = fs
		self.nfft = nfft
		self.wave = wave
		self.obsolete = obsolete

	def get_subwave(self, start, end):
		"""
		访问wave子数据
		:param start: 起始位置
		:param end: 终止位置，不包括end
		:return: 返回子数组（float数组）
		"""
		if start == end and start == 0:
			sub = np.copy(self.wave)
		else:
			sub = np.copy(self.wave[start: end])
		return sub


# stft类
class MemItemStft(MemItem):
	"""
	短时傅里叶变换缓存类
	"""

	def __init__(self, user_id, title, fs, nfft, stft, obsolete):
		self.user_id = user_id
		self.title = title
		self.fs = fs
		self.nfft = nfft
		self.stft = stft
		self.obsolete = obsolete

	def get_subwave(self, start, end):
		"""
		获取子stft数据
		:param start:起始位置
		:param end: 终止位置， 不包括end
		:high_cutoff: 截止频率
		:return: stft序列子数组
		"""
		if start == end and start == 0:
			sub = np.copy(self.stft)
		else:
			sub = np.copy(self.stft[start:end])
		return sub


# ee类
class MemItemSpectrumEntropy(MemItem):
	"""
	短时傅里叶频谱熵缓存条目
	"""
	
	def __init__(self, user_id, title, fs, nfft, spectrum_entropy, obsolete):
		self.user_id = user_id
		self.title = title
		self.fs = fs
		self.nfft = nfft
		self.spectrum_entropy = spectrum_entropy
		self.obsolete = obsolete

	def get_subwave(self, start, end):
		"""
		获取谱熵子数组
		:param start:起始位置
		:param end: 终止位置，不包括end
		:return: 谱熵子数组
		"""
		if start == end and start == 0:
			sub = np.copy(self.spectrum_entropy)
		else:
			sub = np.copy(self.spectrum_entropy[start:end])
		return sub


# rmse类
class MemItemRmse(MemItem):

	def __init__(self, user_id, title, fs, nfft, rmse, obsolete):
		self.user_id = user_id
		self.title = title
		self.fs = fs
		self.nfft = nfft
		self.rmse = rmse
		self.obsolete = obsolete

	def get_subwave(self, start, end):
		if start == end and start == 0:
			sub = np.copy(self.rmse)
		else:
			sub = np.copy(self.rmse[start:end])
		return sub


# 缓存基类
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
		:param user_id 用户id
		:param fs: 采样率
		:return: float32array
		"""
		pass

	def __init__(self, maxsize):
		"""
		初始操作，包括轮询线程的启动
		"""
		try:
			self.container = Cache(maxsize=maxsize)  # 缓存容器
		except Exception as e:
			print(e)


class WaveMemWave(WaveMem):
	def __init__(self, maxsize):
		super(WaveMemWave, self).__init__(maxsize)

	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取制定片段，原始wave波形
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:param user_id 用户id
		:param fs: 采样率
		:return: float32array
		"""
		sub_wave = []
		try:
			wave_key = user_id + "_" + title + "_" + "wave_"+str(fs)	 # 例子 pi_秋风词_wave_44100
			sub_wave_item = self.container.get(wave_key)
			if sub_wave_item is None:

				try:
					t0 = time.clock()
					# 如果再次判断没有key则此时写入写入数据
					wave = Wave.objects.get(create_user_id=user_id, title=title)
					stream = librosa.load(wave.waveFile, mono=False, sr=fs)[0][0]  # 以Fs重新采样
					t1 = time.clock()
					mem_item = MemitemWave(
						user_id,
						title,
						fs,
						nfft,
						stream,
						timedelta(minutes=120)
					)

					self.container.set(wave_key, mem_item)
					sub_wave = mem_item.get_subwave(start * nfft, end * nfft)
					print(wave_key + " 未命中")

					print(t1-t0)
				except Exception as addcacheError:
					print("读取错误:"+repr(addcacheError))
				finally:
					pass
			else:
				print(wave_key + " 命中")
				sub_wave = sub_wave_item.get_subwave(start * nfft, end * nfft)
		except Exception as e:
			print(e)
		finally:
			pass
		return sub_wave


class WaveMemStft(WaveMem):
	def __init__(self, wavemem_wave, maxsize):
		super(WaveMemStft, self).__init__(maxsize)
		self.wavemem_wave = wavemem_wave

	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取短时傅里叶,此缓存粒度较粗，不提供单帧粒度，若是单帧fft获取，则直接调用数据库，此处设置缓存目的是求给予stft的谱熵等等
		:param user_id: 用户id
		:param fs: 采样率
		:param title: 名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:return: 短时傅里叶功率谱或者幅值谱
		"""
		sub_wave = []
		try:
			wave_key = user_id + "_" + title + "_" + "stft"	 # 例子 pi_秋风词_stft
			sub_wave_item = self.container.get(wave_key)
			if sub_wave_item is None:
				# 获取原始左声道波形
				stream = self.wavemem_wave.achieve(user_id, title, fs, nfft, 0, 0)
				# 获取stft
				speech_stft, phase = librosa.magphase(
					librosa.stft(stream, n_fft=nfft, hop_length=nfft, window=scipy.signal.windows.hann, center=False)
				)
				speech_stft = np.transpose(speech_stft)  # stft转置
				# 此处的stft仅仅为了求谱熵等，因此不需要特别长的生存时间，谱熵缓存可设置长一点
				mem_item = MemItemStft(
					user_id,
					title,
					fs,
					nfft,
					speech_stft,
					timedelta(minutes=5)
				)
				self.container.set(wave_key, mem_item)
				sub_wave = mem_item.get_subwave(start, end)
				print(wave_key + " 未命中")
			else:
				sub_wave = sub_wave_item.get_subwave(start, end)
				print(wave_key + " 命中")
		except Exception as e:
			print(e)
		finally:
			pass
		return sub_wave


class WaveMemSpectrumEntropy(WaveMem):
	def __init__(self, wavemem_stft, maxsize):
		super(WaveMemSpectrumEntropy, self).__init__(maxsize)
		self.wavemem_stft = wavemem_stft

	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取谱熵
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param end: 终止帧
		:param user_id: 用户id
		:param fs: 采样率
		:return: 谱熵
		"""
		sub_wave = []
		try:
			wave_key = user_id + "_" + title + "_" + "spectrum_entropy"  # 例子 pi_秋风词_stft
			sub_wave_item = self.container.get(wave_key)
			if sub_wave_item is None:
				# 尝试从数据库获取wave.ee
				print(wave_key + " 未命中")
				wave = Wave.objects.get(create_user_id=user_id, title=title)
				spectrum_entropy = pickle.loads(wave.ee)
				print(spectrum_entropy)
				mem_item = MemItemSpectrumEntropy(
					user_id,
					title,
					fs,
					nfft,
					spectrum_entropy,
					timedelta(minutes=5)
				)
				self.container.set(wave_key, mem_item)
				sub_wave = mem_item.get_subwave(start, end)
			else:
				sub_wave = sub_wave_item.get_subwave(start, end)
				print(wave_key + " 命中")
		except Exception as e:
			print(e)
		finally:
			pass
		return sub_wave


class WaveMemRmse(WaveMem):
	def __init__(self, wavemem_wave, maxsize):
		super(WaveMemRmse, self).__init__(maxsize)
		self.wavemem_wave = wavemem_wave

	def achieve(self, user_id, title, fs, nfft, start, end):
		"""
		获取制定片段，原始wave波形
		:param title:名称
		:param nfft: 帧长度
		:param start: 起始帧
		:param user_id: 用户id
		:param fs: 采样率
		:param end: 终止帧
		:return: float32array
		"""
		sub_rmse = []
		try:
			wave_key = user_id + "_" + title + "_" + "rmse"  # 例子 pi_秋风词_rmse
			sub_rmse_item = self.container.get(wave_key)
			if sub_rmse_item is None:
				# 尝试从数据库获取wave.rmse
				print(wave_key + " 未命中")
				wave = Wave.objects.get(create_user_id=user_id, title=title)
				rmse = pickle.loads(wave.rmse)
				mem_item = MemItemRmse(
					user_id,
					title,
					fs,
					nfft,
					rmse,
					obsolete=timedelta(minutes=60)
				)
				self.container.set(wave_key, mem_item)
				sub_rmse = mem_item.get_subwave(start, end)
			else:
				print(wave_key + " 命中")
				sub_rmse = sub_rmse_item.get_subwave(start, end)

		except Exception as e:
			print(e)
		finally:
			pass
		return sub_rmse


def algorithm_cal_async(labeling, detector, stft, rmse, fs, nfft, algorithms_name, current_pos):
	try:
		reference_pitch = detector.getpitch(stft, fs, nfft, False)
		reference_pitch_filtered = 0  # 过滤后的ｓｔｆｔ

		if reference_pitch[0] > 65 and rmse > 0.1:
			filtered_sgn = filter_by_base(stft, reference_pitch[0], 30, nfft, fs)
			filtered = detector.getpitch(filtered_sgn, fs, nfft, False)
			reference_pitch_filtered = filtered[0]

		tar = list()  # 得到的pitch
		tar.append(reference_pitch[0])
		tar.append(reference_pitch_filtered)
		algorithm_clip = AlgorithmsClips(
			labeling=labeling,
			algorithms=algorithms_name,
			startingPos=current_pos,
			length=1,
			tar=pickle.dumps(tar)
		)
		algorithm_clip.save()
		algorithm_medium = AlgorithmsMediums(
			labeling=labeling,
			algorithms=algorithms_name,
			startingPos=current_pos,
			length=1,
			medium=pickle.dumps(reference_pitch[2])
		)
		algorithm_medium.save()
	except Exception as e:
		print(e)


# Create your views here.
class TargetView(View):
	msg_from = '1214397815@qq.com'  # 发送方邮箱
	passwd = 'ruzdcenkznfhhijf'  # 填入发送方邮箱的授权码
	msg_to = '1214397815@qq.com'  # 收件人邮箱

	def __init__(self):
		"""
		重载初始化函数
		"""
		super(View, self).__init__()
		self.wave_mem_wave = WaveMemWave(32)  # 构建缓存对象
		self.wave_mem_stft = WaveMemStft(self.wave_mem_wave, 32)
		self.wave_mem_spectrumEntropy = WaveMemSpectrumEntropy(self.wave_mem_stft, 32)
		self.wave_mem_rmse = WaveMemRmse(self.wave_mem_wave, 32)
		self.sender = None

	@classmethod
	@method_decorator(login_required)
	def index(cls, request):
		"""
		主要索引视图
		:param request:
		:return:
		"""
		waves = Wave.objects.filter(create_user_id=request.user)
		for wave in waves:
			clips = Clip.objects.filter(title=wave.title, create_user_id=request.user)
			if clips.count() == 0:
				completion = 0
			else:
				candidate_frame = clips.aggregate(Max('startingPos'))['startingPos__max']
				candidate_frame_num = wave.frameNum  # 待测总帧数
				completion = round(candidate_frame / candidate_frame_num * 100, 1)
				completion = min(100, completion)
			wave.completion = completion
			wave.save(update_fields=["completion"])
		waves = Wave.objects.filter(create_user_id=request.user).order_by('frameNum')
		tunes = None
		try:
			tunes = Tune.objects.filter(create_user_id=request.user)
		except Exception as e:
			print(e)
		context = {'waves': waves, 'tunes': tunes}
		return render(request, 'index.html', context)

	@method_decorator(login_required)
	def add_tune(self, request):
		print("hello")
		tune_name = str(request.GET.get('tune_name'))
		a4_hz = request.GET.get('a4_hz')
		print(a4_hz)

		do = str(request.GET.get('do'))
		note1 = str(request.GET.get('note1'))
		note2 = str(request.GET.get('note2'))
		note3 = str(request.GET.get('note3'))
		note4 = str(request.GET.get('note4'))
		note5 = str(request.GET.get('note5'))
		note6 = str(request.GET.get('note6'))
		note7 = str(request.GET.get('note7'))
		print(note5)
		try:
			Tune.objects.update_or_create(
				create_user_id=request.user,
				tune_name=tune_name,
				defaults={
					'a4_hz': a4_hz,
					'do': do,
					'note1': note1,
					'note2': note2,
					'note3': note3,
					'note4': note4,
					'note5': note5,
					'note6': note6,
					'note7': note7
				},
			)
		except Exception as e:
			print(e)
			return HttpResponse("err")
		return HttpResponse("ok")

	@method_decorator(login_required)
	def strings_reset(self, request):
		strings_str = request.GET.get('strings')
		do = request.GET.get('do')
		a4_hz = float(request.GET.get('a4_hz'))
		f_list = strings_str.split(',')
		strings = []
		for item in f_list:
			print(item)
			strings.append(float(item))
		print(strings)
		try:
			wave_id = request.GET.get('wave_id')
			wave = Wave.objects.get(id=wave_id)
			chin = Chin()
			print(do)
			print(a4_hz)
			chin.set_ahz(a4_hz)
			chin.set_do(do)
			print(strings)
			print(chin)
			chin.set_hzes(strings)
			wave.chin = pickle.dumps(chin)
			wave.save()
		except Exception as e:
			print(e)
			return HttpResponse(e)
		return HttpResponse("ok")

	@classmethod
	def handle_upload_file(cls, upload_file, path, user_id):

		if not os.path.exists(path):
			os.makedirs(path)
			print("文件夹已经创建:"+path)
		file_name = path + upload_file.name
		print(file_name)
		wave_name = upload_file.name.split(".")[0]
		print(wave_name)
		already = Wave.objects.filter(create_user_id=user_id, title=wave_name)  # 已经存在的wave
		if already.count() == 0:
			try:
				destination = open(file_name, 'wb+')
				for chunk in upload_file.chunks():
					destination.write(chunk)
				destination.close()
				# 插入数据库
				stream, stream_fs = librosa.load(file_name, mono=False, sr=None)
				duration = librosa.core.get_duration(y=stream[0], sr=stream_fs)
				nfft = round(stream_fs / 10)
				speech_stft, phase = librosa.magphase(
					librosa.stft(stream[0], n_fft=nfft, hop_length=nfft, window=scipy.signal.windows.hann))
				speech_stft = np.transpose(speech_stft)  # stft转置
				frame_num = np.size(speech_stft, 0)
				# chin 设置
				chin = Chin()
				chin.set_ahz(440)
				wave = Wave(
					create_user_id=user_id,
					title=wave_name,
					waveFile=file_name,
					frameNum=frame_num,
					duration=duration,
					chin=pickle.dumps(chin),
					fs=stream_fs,
					nfft=nfft,
					completion=0
				)
				wave.save()
				return "success"
			except Exception as e:
				print(e)
				return "err"
		else:
			print(wave_name + " already existed")
			return "err"

	@classmethod
	@method_decorator(login_required)
	def addwaves(cls, request):
		if request.method == 'POST':
			content = request.FILES.getlist("upload_wave")
			if not content:
				return HttpResponse("没有上传内容")
			user_id = str(request.user)
			path = "/home/liningbo/waveFiles/"+user_id+"/"
			for wave in content:
				cls.handle_upload_file(wave, path, user_id)
		return HttpResponse("add waves done")

	@classmethod
	@method_decorator(login_required)
	def copywaves(cls, request):
		"""
		从其他用户获取wave,然后复制至特定用户
		:param request:
		:return:
		"""
		user_id = str(request.user)
		waves = Wave.objects.filter(~Q(create_user_id=user_id)).values('id', 'title', 'create_user_id')
		wave_name_already = Wave.objects.filter(create_user_id=user_id).values('title')
		name_exist = set()
		waves_filter = []
		for wave_name in wave_name_already:
			name_exist.add(wave_name["title"])
		for wave in waves:
			print(wave)
			if wave['title'] not in name_exist:
				waves_filter.append(wave)

		context = {'waves': waves_filter}
		return render(request, 'copywaves.html', context)

	@staticmethod
	def sub_and_execute_copywaves(request):
		user_id = str(request.user)
		waves_selected = json.loads(request.GET.get("waves_selected"))

		for wave in waves_selected:
			create_user = wave["user_id"]
			title = wave["wave_title"]
			try:
				wave_item = Wave.objects.get(create_user_id=create_user, title=title)
				wave_item.save()
				wave_item.pk = None
				newfilepath_arr = wave_item.waveFile.split("/")
				newfilepath_arr.remove("")
				newfilepath_arr[len(newfilepath_arr)-2] = user_id
				file_name = ""
				path_name = ""
				counter = 0
				for path_item in newfilepath_arr:
					file_name = file_name+"/"+path_item
					if counter < len(newfilepath_arr)-1:
						path_name = path_name+"/"+path_item
					counter = counter+1
				if os.path.exists(path_name) is False:
					os.mkdir(path_name)
				shutil.copyfile(wave_item.waveFile, file_name)
				wave_item.waveFile = file_name
				wave_item.create_user_id = user_id
				wave_item.save()
			except Exception as e:
				print(e)
		return HttpResponse("copy completed")

	@method_decorator(login_required)
	def labeling(self, request):
		title = request.GET.get('title')
		user_id = str(request.user)
		wave = Wave.objects.get(create_user_id=user_id, title=title)
		wave_id = wave.id
		fs = wave.fs
		nfft = wave.nfft
		end = wave.frameNum
		try:
			labelinfo = Labeling.objects.get(create_user_id=user_id, title=title)
		except Exception as e:
			print(e)
			Labeling(title=title, create_user_id=user_id, nfft=nfft, frameNum=wave.frameNum).save()
			labelinfo = Labeling.objects.get(create_user_id=user_id, title=title)
		thrart_ee = labelinfo.vad_thrart_EE
		thrart_rmse = labelinfo.vad_thrart_RMSE
		throp = labelinfo.vad_throp_EE
		tone_extend_rad = labelinfo.tone_extend_rad
		manual_pos = labelinfo.manual_pos
		if manual_pos < 0:
			# 计算位置
			clips = Clip.objects.filter(title=title, create_user_id=request.user, nfft=nfft)
			if clips.count() == 0:
				current_frame = 0
			else:
				candidate_frame = clips.aggregate(Max('startingPos'))['startingPos__max']
				current_frame = candidate_frame+1
				current_frame = min(wave.frameNum-1, current_frame)
		else:
			# 指定位置
			labelinfo.manual_pos = -1  # 指定位置只生效一次
			current_frame = manual_pos
			pass			
		labelinfo.current_frame = current_frame
		labelinfo.save()
		extend_rad = labelinfo.extend_rad
		ee = self.wave_mem_spectrumEntropy.achieve(
			user_id, title, fs, nfft,
			max(current_frame-extend_rad, 0),
			min(current_frame+extend_rad, end)
		)
		ee = list(ee)
		rmse = self.wave_mem_rmse.achieve(
			user_id,
			title,
			fs,
			nfft,
			max(current_frame-extend_rad, 0),
			min(current_frame+extend_rad, end)
		)
		rmse = list(rmse)
		vadrs = targetTools.vad(ee, rmse, thrart_ee, thrart_rmse, throp)
		# 收集tones
		tones_start = max(current_frame-tone_extend_rad, 0)
		tones_end = min(current_frame+tone_extend_rad, wave.frameNum)
		tones_local_set = Tone.objects.filter(
			title=title,
			create_user_id=user_id,
			pos__range=(tones_start, tones_end-1)
		)
		tones_local = serializers.serialize("json", tones_local_set)
		# comb及combDescan音高参考
		reference = {}  # 算法支撑数据
		labeling_algorithms_conf = labelinfo.labelingalgorithmsconf_set.all()  # 算法支持数据配置
		start_ref = max(current_frame - extend_rad, 0)  # 起始位置
		end_ref = min(current_frame + extend_rad, end)  # 终止位置
		for algorithmsConf in labeling_algorithms_conf:
			reference_name = algorithmsConf.algorithms
			local_reference_clips = labelinfo.algorithmsclips_set.filter(
				algorithms=reference_name,
				startingPos__range=(current_frame-extend_rad, current_frame+extend_rad-1)
			)
			primary_arr = np.zeros(end_ref-start_ref)  # 算法主数据
			for reference_clip in local_reference_clips:
				primary_arr[reference_clip.startingPos-tones_start] = pickle.loads(reference_clip.tar)[0]
			reference.update({reference_name: list(primary_arr)})
			if algorithmsConf.is_filter is True:
				reference_name = reference_name+"_filter"
				filter_arr = np.zeros(end_ref - start_ref)  # 算法主数据
				for reference_clip in local_reference_clips:
					filter_arr[reference_clip.startingPos-tones_start] = pickle.loads(reference_clip.tar)[1]
				reference.update({reference_name: list(filter_arr)})
		target = [[0] * (end_ref-start_ref), [0] * (end_ref-start_ref), [0] * (end_ref-start_ref)]  # 存储前三个音高的二维数组
		try:
			clips = Clip.objects.filter(
				title=title, create_user_id=request.user,
				startingPos__range=(current_frame-extend_rad, current_frame+extend_rad-1)
			)
			for clip in clips:
				pos = clip.startingPos
				tar = pickle.loads(clip.tar)
				index = 0
				for pitch in tar:
					target[index][pos-tones_start] = pitch
					index = index+1
		except Exception as e:
			print(e)
		# fft及中间结果
		try:
			src_fft = pickle.loads(labelinfo.stft_set.get(startingPos=current_frame, length=1).src)
			src_fft[0:int(30 * nfft / fs)] = 0  # 清空30hz以下信号
			filter_rad = labelinfo.filter_rad  # 过滤带宽半径
			current_clip = labelinfo.algorithmsclips_set.get(
				algorithms=labelinfo.primary_ref,
				startingPos=current_frame,
				length=1
			)
			current_tar = pickle.loads(current_clip.tar)[0]  # 当前帧主音高估计
			if current_tar > 40:
				filter_fft = filter_by_base(src_fft, current_tar, filter_rad, nfft, fs)  # 过滤后fft
				filter_fft = [round(i, 4) for i in filter_fft]
			else:
				filter_fft = []
			medium = pickle.loads(
				labelinfo.algorithmsmediums_set.get(
					algorithms=labelinfo.primary_ref,
					startingPos=current_frame,
					length=1
				).medium
			)
			# 重新采样(降低采样), 只降低中间结果
			is_resampling = labelinfo.medium_resampling
			if is_resampling is True:
				processing_x = np.arange(0, len(medium))
				len_processing_x = len(processing_x)
				processing_y = medium
				finterp = interp1d(processing_x, processing_y, kind="linear")

				x_pred = np.linspace(
					0, processing_x[len_processing_x - 1] * 1.0,
					int(processing_x[len_processing_x - 1] / 10) + 1
				)
				resampling_y = finterp(x_pred)
				medium = resampling_y
				src_fft = [round(i, 4) for i in src_fft]
				medium = [round(i, 4) for i in medium]
		except Exception as e:
			medium = []
			src_fft = []
			filter_fft = []
			current_tar = 0
			filter_rad = 0
			print(e)
		# 可能的位置
		chin = None
		string_hzes = None
		string_notes = None
		string_do = None
		pitch_scaling = None
		a4_hz = None
		if wave.chin is not None:
			# 获得chin class
			try:
				chin = pickle.loads(wave.chin)
				a4_hz = chin.get_ahz()
				string_hzes = chin.get_hzes()
				string_notes = chin.get_notes()
				string_do = chin.get_do()
				pitch_scaling = chin.get_scaling()
				print(a4_hz)
			except Exception as e:
				pitch_scaling = 1

				print(e)
		else:
			# chin class 不存在
			chin = None
		if chin is not None:
			try:
				possible_pos = chin.cal_possiblepos(current_tar)[1].replace("\n", "<br>")
			except Exception as e:
				possible_pos = ""
				print(e)
		else:
			possible_pos = "尚未设置chin信息"
		clips_local_ori = Clip.objects.filter(
			title=title, create_user_id=user_id,
			startingPos__range=(current_frame-extend_rad, current_frame+extend_rad-1)
		)
		clips_local = []
		for clip in clips_local_ori:
			clips_local.append({
				"id": clip.id,
				"startingPos": clip.startingPos,
				"length": clip.length,
				"tar": list(pickle.loads(clip.tar))
			})
		tunes = None
		try:
			tunes = Tune.objects.filter(create_user_id=request.user)
		except Exception as e:
			print(e)
		context = {
			'title': title,
			'fs': fs,
			'nfft': nfft,
			'ee': ee,
			'rmse': rmse,
			'stopPos': list(vadrs['stopPos']),
			'tunes': tunes,
			'manual_pos': manual_pos,
			'tones_local': tones_local,
			'target': target,
			'reference': reference,
			'primary_ref': labelinfo.primary_ref,
			'startPos': list(vadrs['startPos']),
			'ee_diff': list(vadrs['ee_diff']),
			"src_fft": list(src_fft),
			"medium": list(medium),
			'filter_fft': list(filter_fft),
			'current_tar': current_tar,
			"filter_rad": filter_rad,
			'a4_hz': a4_hz,
			'wave_id': wave_id,
			'string_hzes': string_hzes,
			'string_notes': string_notes,
			'string_do': string_do,
			'pitch_scaling': pitch_scaling,
			"current_frame": current_frame,
			"extend_rad": extend_rad,
			"labeling_id": labelinfo.id,
			'play_fs': labelinfo.play_fs,
			"tone_extend_rad": tone_extend_rad,
			"frame_num": end,
			'vad_thrart_ee': thrart_ee,
			"clips_local": clips_local,
			'vad_thrart_RMSE': thrart_rmse,
			'vad_throp_EE': throp,
			'create_user_id': user_id,
			'possible_pos': possible_pos
		}

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
			possible_pos = chin.cal_possiblepos(primary_pitch)[1].replace("\n", "<br>")
		else:
			possible_pos = "尚未设置chin信息"
		return HttpResponse(possible_pos)

	@method_decorator(login_required)
	def tune_reset(self, request):
		try:
			wave_id = request.GET.get('wave_id')
			tune_id = request.GET.get('tune_id')
			tune = Tune.objects.get(id=tune_id)
			wave = Wave.objects.get(id=wave_id)
			chin = Chin()
			chin.set_ahz(tune.a4_hz)
			chin.set_do(tune.do)

			notes = [tune.note1, tune.note2, tune.note3, tune.note4, tune.note5, tune.note6, tune.note7]
			chin.set_notes(notes)
			wave.chin = pickle.dumps(chin)
			wave.save()
		except Exception as e:
			print(e)
			return HttpResponse(e)
		return HttpResponse("ok")

	@method_decorator(login_required)
	def filter_fft(self, request):
		current_pos = int(request.GET.get('current_pos'))
		labeling_id = int(request.GET.get('labeling_id'))
		filter_frq = float(request.GET.get('filter_frq'))
		filter_width = float(request.GET.get('filter_width'))
		nfft = int(request.GET.get('nfft'))
		fs = int(request.GET.get('fs'))
		try:
			labeling = Labeling.objects.get(id=labeling_id)
			src_fft = pickle.loads(labeling.stft_set.get(startingPos=current_pos, length=1).src)
			src_fft[0:int(30 * nfft / fs)] = 0  # 清空30hz以下信号
			fft_filtered = filter_by_base(src_fft, filter_frq, filter_width, nfft, fs)  # 过滤后fft
			fft_filtered = fft_filtered.tolist()
			fft_filtered = [round(i, 2) for i in fft_filtered]
			return HttpResponse(json.dumps(fft_filtered))
		except Exception as e:
			print(e)
			return None

	# 自定义重新采样函数
	@staticmethod
	def resampling(src, target_len):
		processing_x = np.arange(0, len(src))
		len_processing_x = len(processing_x)
		processing_y = src
		finterp = interp1d(processing_x, processing_y, kind="linear")
		x_pred = np.linspace(0, processing_x[len_processing_x - 1] * 1.0, int(target_len) + 1)
		resampling_y = finterp(x_pred)
		return resampling_y

	@method_decorator(login_required)
	def cal_custom_pitch(self, request):
		title = request.GET.get('title')
		user_id = str(request.user)
		nfft = int(request.GET.get('nfft'))
		fs = int(request.GET.get('fs'))
		start = int(request.GET.get('start'))
		end = int(request.GET.get('end'))
		labeling_id = int(request.GET.get('labeling_id'))
		try:
			wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  #
			wave_len = len(wave_arr)
			wave_fft_src = fft(wave_arr)  # 自定义序列的fft
			wave_fft = abs(wave_fft_src)[0:int((len(wave_fft_src)+1)/2)]
			fft_len = len(wave_fft)
			target_len = 2205
			print(wave_len, fft_len)
			labeling = Labeling.objects.get(id=labeling_id)
			algorithms_name = labeling.primary_ref
			detector = None
			
			if algorithms_name == "combDescan":
				detector = BaseFrqDetector(True)  # 去扫描线算法
			if algorithms_name == "comb":
				detector = BaseFrqDetector(False)  # 不去扫描线算法
			reference_pitch_allinfo = detector.getpitch(wave_fft, fs, wave_len, False)
			src = TargetView.resampling(wave_fft, target_len)[0:int(4000*4410/fs)]  # 重新采样后的适合显示的fft
			primary_pitch = reference_pitch_allinfo[0]  # 主音高
			medium = reference_pitch_allinfo[2]  # 中间结果
			is_resampling = labeling.medium_resampling
			if is_resampling is True:
				medium = TargetView.resampling(medium, int(len(medium)/10))
			if primary_pitch > 40:
				filter_fft = filter_by_base(src, primary_pitch, labeling.filter_rad, nfft, fs)  # 过滤后fft
				filter_fft = [round(i, 4) for i in filter_fft]
			else:
				filter_fft = []
			wave = Wave.objects.get(create_user_id=user_id, title=title)
			if wave.chin is not None:
				chin = pickle.loads(wave.chin)
			else:
				chin = None
			print(chin)
			possible_pos = chin.cal_possiblepos(primary_pitch)[1].replace("\n", "<br>")
			print(possible_pos)
			context = {
				'primary_pitch': primary_pitch, 'src': list(src), 'filter_fft': filter_fft,
				'medium': list(medium),
				"possible_pos": possible_pos
			}
			return HttpResponse(json.dumps(context))
		except Exception as e:
			print(e)
			return None

	@method_decorator(login_required)
	def algorithm_select(self, request):
		algorithms_name = request.GET.get('algorithm_name')
		labeling_id = int(request.GET.get('labeling_id'))
		print(labeling_id)
		labeling = Labeling.objects.get(id=labeling_id)
		clips = labeling.algorithmsclips_set.filter(algorithms=algorithms_name)
		clips_num = clips.count()
		frame_num = labeling.frameNum
		context = {'clips_num': clips_num, 'frame_num': frame_num}
		return HttpResponse(json.dumps(context))

	@method_decorator(login_required)
	def algorithm_clear(self, request):
		clips_num = 0
		try:
			algorithms_name = request.GET.get('algorithm_name')
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			clips_all = labeling.algorithmsclips_set.filter(algorithms=algorithms_name)
			clips_num = clips_all.count()
			clips_all.delete()
		except Exception as e:
			print(e)
		context = {'clips_num_delete': clips_num}
		return HttpResponse(json.dumps(context))

	@staticmethod
	def algorithm_cal_thread(labeling, detector, stft_arr, rmse_arr, fs, nfft, algorithms_name):
		thread_num = 4
		pool = multiprocessing.Pool(processes=thread_num)
		for i in range(len(rmse_arr)):
			stft = np.copy(stft_arr[i])
			stft[0:int(30 * nfft / fs)] = 0  # 清零３０ｈｚ以下信号
			pool.apply_async(
				algorithm_cal_async,
				args=(labeling, detector, stft, rmse_arr[i], fs, nfft, algorithms_name, i,)
			)
		pool.close()
		pool.join()

	@method_decorator(login_required)
	def algorithm_cal(self, request):
		clips_num_oncreate = None
		try:
			algorithms_name = request.GET.get('algorithm_name')
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			clips_all = labeling.algorithmsclips_set.filter(algorithms=algorithms_name)
			clips_num = clips_all.count()
			clips_all.delete()
			print("删除算法参考数据"+str(algorithms_name)+str(clips_num)+"条")
			medium_all = labeling.algorithmsmediums_set.filter(algorithms=algorithms_name)
			medium_all.delete()
			print("删除算法中间结果" + str(algorithms_name) + str(clips_num) + "条")
			# 创建数据
			clips_num_oncreate = labeling.frameNum  # 需要创建数据总条目
			user_id = labeling.create_user_id
			title = labeling.title
			fs = labeling.fs
			nfft = labeling.nfft

			stft_arr = self.wave_mem_stft.achieve(user_id, title, fs, nfft, 0, 0)  # 短时傅里叶谱
			rmse_arr = self.wave_mem_rmse.achieve(user_id, title, fs, nfft, 0, 0)  # 获取ｒｍｓｅ
			detector = None
			if algorithms_name == "combDescan":
				detector = BaseFrqDetector(True)  # 去扫描线算法
			if algorithms_name == "comb":
				detector = BaseFrqDetector(False)  # 不去扫描线算法
			thread = threading.Thread(
				target=self.algorithm_cal_thread,
				args=(labeling, detector, stft_arr, rmse_arr, fs, nfft, algorithms_name)
			)  # 创建监视线程
			thread.setDaemon(True)  # 设置为守护线程， 一旦用户线程消失，此线程自动回收
			thread.start()

		except Exception as e:
			print(e)
		context = {'clips_num_oncreate': clips_num_oncreate}
		return HttpResponse(json.dumps(context))

	@method_decorator(login_required)
	def reference_select(self, request):
		algorithms_name = request.GET.get('algorithm_name')
		labeling_id = int(request.GET.get('labeling_id'))
		labeling = Labeling.objects.get(id=labeling_id)
		algorithms_clips = labeling.labelingalgorithmsconf_set.filter(algorithms=algorithms_name)
		algorithms_num = algorithms_clips.count()
		context = {'algorithms_num': algorithms_num}
		return HttpResponse(json.dumps(context))

	@method_decorator(login_required)
	def add_reference(self, request):
		try:
			algorithms_name = request.GET.get('algorithm_name')
			labeling_id = int(request.GET.get('labeling_id'))
			is_filter = int(request.GET.get('is_filter'))
			if is_filter == 0:
				is_filter = False
			if is_filter == 1:
				is_filter = True
			labeling = Labeling.objects.get(id=labeling_id)
			newlabeling_algorithms_conf = LabelingAlgorithmsConf(
				labeling=labeling,
				algorithms=algorithms_name,
				is_filter=is_filter
			)
			newlabeling_algorithms_conf.save()
		except Exception as e:
			print(e)
		return HttpResponse("reference added ")

	# 删除算法支持数据配置
	@method_decorator(login_required)
	def del_reference(self, request):
		try:
			algorithms_name = request.GET.get('algorithm_name')
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			labeling_algorithms_conf = labeling.LabelingAlgorithmsConf_set.get(algorithms=algorithms_name)
			labeling_algorithms_conf.delete()
		except Exception as e:
			print(e)
		return HttpResponse("reference deleted ")

	@method_decorator(login_required)
	def cal_stft(self, request):
		try:
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			labeling.stft_set.all().delete()
			user_id = str(request.user)
			wave_key = user_id + "_" + labeling.title + "_" + "stft"  # 例子 pi_秋风词_stft
			wave = Wave.objects.get(create_user_id=user_id, title=labeling.title)
			# 获取原始左声道波形
			stream = self.wave_mem_wave.achieve(user_id, labeling.title, labeling.fs, labeling.nfft, 0, 0)
			# 获取stft
			speech_stft, phase = librosa.magphase(
				librosa.stft(stream, n_fft=wave.nfft, hop_length=wave.nfft, window=scipy.signal.windows.hann, center=False)
			)
			speech_stft = np.transpose(speech_stft)  # stft转置
			# 此处的stft仅仅为了求谱熵等，因此不需要特别长的生存时间，谱熵缓存可设置长一点
			mem_item = MemItemStft(
				user_id,
				labeling.title,
				labeling.fs,
				labeling.nfft,
				speech_stft,
				timedelta(minutes=5)
			)
			self.wave_mem_stft.container.set(wave_key, mem_item)

			stft_arr = speech_stft
			# 短时傅里叶谱
			list_stft = []
			for i in range(len(stft_arr)):
				stft = Stft(startingPos=i, length=1, labeling=labeling, src=pickle.dumps(stft_arr[i]))
				list_stft.append(stft)
			labeling.stft_set.bulk_create(list_stft)
			labeling.frameNum = len(stft_arr)
			labeling.save()
			wave.frameNum = len(stft_arr)
			wave.save(update_fields=["frameNum"])
		except Exception as e:
			print(e)
			return HttpResponse("STFT ERR")
		return HttpResponse("STFT calculated ")

	@method_decorator(login_required)
	def cal_ee(self, request):
		try:
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			user_id = labeling.create_user_id
			title = labeling.title
			fs = labeling.fs
			nfft = labeling.nfft

			# 获取原始左声道波形
			stream = self.wave_mem_wave.achieve(user_id, title, fs, nfft, 0, 0)
			# 获取stft
			speech_stft, phase = librosa.magphase(
				librosa.stft(
					stream,
					n_fft=nfft,
					hop_length=nfft,
					window=scipy.signal.windows.hann,
					center=False
				)
			)
			stft_ori = speech_stft  # stft转置
			# 计算谱熵
			stft_for_ee = np.copy(stft_ori[0:np.int(nfft / fs * 4000)])  # 4000hz以下信号用于音高检测
			speech_stft_enp = stft_for_ee[1:-1]
			speech_stft_prob = speech_stft_enp / (np.sum(speech_stft_enp, axis=0) + 0.00000000000000001)
			spectrum_entropy = np.sum(
				-np.log(speech_stft_prob + 0.0000000000000001) * speech_stft_prob,
				axis=0
			)
			spectrum_entropy = maxminnormalization(spectrum_entropy, 0, 1)
			wave = Wave.objects.get(create_user_id=user_id, title=title)
			wave.ee = pickle.dumps(spectrum_entropy)
			wave.save(update_fields=["ee"])

		except Exception as e:
			print(e)
			return HttpResponse("EE ERR")
		return HttpResponse("EE calculated ")

	@method_decorator(login_required)
	def cal_rmse(self, request):
		try:
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			user_id = labeling.create_user_id
			title = labeling.title
			fs = labeling.fs
			nfft = labeling.nfft

			stream = self.wave_mem_wave.achieve(user_id, title, fs, nfft, 0, 0)
			rmse = librosa.feature.rmse(
				y=stream, S=None, frame_length=nfft,
				hop_length=nfft, center=False
			)[0]
			rmse = maxminnormalization(rmse, 0, 1)
			wave = Wave.objects.get(create_user_id=user_id, title=title)
			wave.rmse = pickle.dumps(rmse)
			wave.frameNum = len(rmse)
			wave.save(update_fields=["rmse", "frameNum"])
			labeling.frameNum = len(rmse)
			labeling.save(update_fields=["frameNum"])
		except Exception as e:
			print(e)
			return HttpResponse("RMSE ERR")
		return HttpResponse("RMSE calculated ")

	@method_decorator(login_required)
	def set_primary(self, request):
		try:
			algorithms_name = request.GET.get('algorithm_name')
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			labeling.primary_ref = algorithms_name
			labeling.save()
		except Exception as e:
			print(e)
		return HttpResponse("primary set ")

	@method_decorator(login_required)
	def set_ref_filter(self, request):
		try:
			algorithms_name = request.GET.get('algorithm_name')
			labeling_id = int(request.GET.get('labeling_id'))
			is_filter = int(request.GET.get('is_filter'))
			if is_filter == 0:
				is_filter = False
			if is_filter == 1:
				is_filter = True
			labeling = Labeling.objects.get(id=labeling_id)
			labeling_conf = labeling.labelingalgorithmsconf_set.get(algorithms=algorithms_name)
			labeling_conf.is_filter = is_filter
			labeling_conf.save()
		except Exception as e:
			print(e)
		return HttpResponse("primary filter configure set ")

	@method_decorator(login_required)
	def set_manual_pos(self, request):
		try:
			manual_pos = int(request.GET.get('manual_pos'))
			labeling_id = int(request.GET.get('labeling_id'))
			labeling = Labeling.objects.get(id=labeling_id)
			labeling.manual_pos = manual_pos
			labeling.save(update_fields=['manual_pos'])
		except Exception as e:
			print(e)
			return HttpResponse("err")
		return HttpResponse("ok")

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
		title = request.GET.get('title')
		create_user = str(request.user)
		wave = Wave.objects.get(create_user_id=create_user, title=title)
		clips = Clip.objects.filter(
			title=title,
			create_user_id=request.user,
			startingPos__lt=wave.frameNum
		).order_by('startingPos')
		marked_phrases = MarkedPhrase.objects.filter(create_user_id=create_user, title=title)
		tones = Tone.objects.filter(create_user_id=create_user, title=title).order_by('pos')
		# 返回的clips
		items = []
		# 存储前三个音高的二维数组
		pitches_arr = [[0] * wave.frameNum, [0] * wave.frameNum, [0] * wave.frameNum]
		# pitches_arr = [pitches_arr]

		if wave.chin is not None:
			chin = pickle.loads(wave.chin)
		else:
			chin = None

		for clip in clips:
			item = Item()
			item.title = clip.title
			item.startingPos = clip.startingPos
			item.tar = pickle.loads(clip.tar)
			for index in np.arange(len(item.tar)):
				item.tar[index] = round(item.tar[index], 2)
			item.possible_pos = chin.cal_possiblepos(item.tar)[1].replace("\n", "<br>")
			item.id = clip.id
			for index in np.arange(len(item.tar)):
				try:
					pitches_arr[index][clip.startingPos] = item.tar[index]  # 收集已经标定的音高
				except Exception as e:
					print(e)
			items.append(item)
		string_notes = None
		string_hzes = None
		string_do = None
		if wave.chin is not None:
			try:
				string_hzes = chin.get_hzes()
				string_notes = chin.get_notes()
				string_do = chin.get_do()
			except Exception as e:
				string_hzes = None
				string_notes = None
				string_do = None
				print(e)

		context = {
			'clips': items, 'wave': wave, 'pitches': pitches_arr, 'marked_phrases': marked_phrases,
			'tones': tones, 'string_hzes': string_hzes, 'string_notes': string_notes,
			'string_do': string_do
		}
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

		f = waveout.open(io_stream, 'wb')  # 定位于内存镜像
		f.setnchannels(1)  # 设置为单通道
		f.setsampwidth(2)  # 16位采样
		f.setframerate(fs)  # 设置采样率
		# 将wav_data转换为二进制数据写入文件
		f.writeframes(wave_arr.tostring())  # 写入音频信息
		f.close()  # 关闭写入流
		seg = AudioSegment.from_wav(io_stream)
		io_stream_flac = BytesIO()  # 内存文件
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
		file_name = request.GET.get('file_name')
		# self.wave_mem.add_mem(title)  # 试图将完整曲目加入缓存
		wave_arr = self.wave_mem_wave.achieve(user_id, title, fs, nfft, start, end)  # 获取音频信号
		wave_arr = np.array(wave_arr) * 32767
		wave_arr = wave_arr.astype(np.int16)
		io_stream = BytesIO()  # 内存文件
		f = waveout.open(io_stream, 'wb')  # 定位于内存镜像
		f.setnchannels(1)  # 设置为单通道
		f.setsampwidth(2)  # 16位采样
		f.setframerate(fs)  # 设置采样率
		# 将wav_data转换为二进制数据写入文件
		f.writeframes(wave_arr.tostring())  # 写入音频信息
		f.close()  # 关闭写入流"""
		subject = file_name  # 主题
		wav_patch = MIMEApplication(io_stream.getvalue())
		wav_patch.add_header(
			'Content-Disposition', 'attachment',
			file_name=('gbk', '', file_name + '.wav')
		)
		msg = wav_patch
		msg['Subject'] = subject
		msg['From'] = self.msg_from
		msg['To'] = self.msg_to
		self.sender = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
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
				else:
					rs = "err"
		return HttpResponse(rs)

	@classmethod
	def get_clip_fft(cls, request):
		clip_id = request.GET.get('id')  # clip_id
		fs = int(request.GET.get('fs'))  # fs
		nfft = int(request.GET.get('nfft'))  # nfft
		try:
			clip = Clip.objects.get(id=clip_id)
		except Exception as e:
			return HttpResponse(e)

		cutoff = int(4200 * nfft / fs)  # src 截断位置
		src = pickle.loads(clip.src)
		src = src.tolist()[0:cutoff]
		return HttpResponse(json.dumps(src))

	@classmethod
	def login(cls, request):
		file_next = request.GET.get('next', "")
		if request.method == 'GET':
			if request.user is not None and request.user.is_active:
				return redirect("/index/")
			form = UserFormWithoutCaptcha()
			return render(request, 'login.html', {'login_form': form, })
		else:
			form = UserFormWithoutCaptcha(request.POST)
			if form.is_valid():
				username = request.POST.get('username', '')
				password = request.POST.get('password', '')
				user = auth.authenticate(username=username, password=password)
				if user is not None and user.is_active:
					auth.login(request, user)
					if file_next == "":
						return redirect("/index/")
					else:
						return redirect(file_next)
				else:
					message = "用户名或者密码错误"
					return render(request, 'login.html', {'login_form': form, 'message': message})
			else:
				message = "表单数据错误"
				return render(request, 'login.html', {'login_form': form, 'message': message})

	@classmethod
	def logout(cls, request):
		auth.logout(request)
		return redirect("/login/")

	@classmethod
	def register(cls, request):
		message = ""
		if request.method == 'POST':
			form = RegisterForm(request.POST)
			message = "请检查填写的内容！"
			if form.is_valid():
				# 获得表单数据
				username = form.cleaned_data['username']
				password = form.cleaned_data['password1']

				# 判断用户是否存在
				user = auth.authenticate(username=username, password=password)
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
		# 将req 、页面 、以及context{}（要传入html文件中的内容包含在字典里）返回
		return render(request, 'register.html',  {'register_form': form, 'message': message})
