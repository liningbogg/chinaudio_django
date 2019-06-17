import math
import re
from itertools import combinations
from string import digits

import librosa
import numpy as np


class Chin:
    """
    Chin:
    用于处理古琴定音，音位分析，指法分析的类
    以十二平均律标记音高，hz为7条弦音高标识的主键，定调为__do对应的note值
    音分散音 按音 泛音分别标记为 S A F
    相对徽位位置用来标记按音着弦点和有效弦长，另外有效弦长也可用相对弦长标识，最大相对弦长为1
    """
    __noteslist = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    __tonesList = [0, 2, 4, 5, 7, 9, 11]
    huiList = [0, 1.0 / 8, 1.0 / 6, 1.0 / 5, 1.0 / 4, 1.0 / 3, 2.0 / 5, 0.5, 3.0 / 5, 2.0 / 3, 3.0 / 4, 4.0 / 5,
               5.0 / 5, 7.0 / 8, 1]
    fanyintimes = [8.0, 6.0, 5.0, 4.0, 3.0, 5.0, 2.0, 5.0, 3.0, 4.0, 5.0, 6.0, 8.0]

    @staticmethod
    def pos2hui(pos):
        count = 0
        for hui in Chin.huiList:
            if pos > hui:
                count = count + 1
                continue
            else:
                break
        start = Chin.huiList[count - 1]
        end = Chin.huiList[count]
        return count - 1 + (pos - start) / (end - start)

    def note2tone(self, note):
        grade = int(re.findall("\d+", note)[0]) - int(re.findall("\d+", self.__do)[0])
        remove_digits = str.maketrans('', '', digits)
        re__do = note.translate(remove_digits)
        tone = 0
        re__do=re__do[0:len(re__do)-1]
        try:
            tone = self.__tones.index(re__do) + 1
        except Exception as e:
            try:
                if len(re__do) == 2:
                    tone = self.__tones.index(re__do[0]) + 1 + 0.5
                else:
                    sharp = re__do + "#"
                    tone = self.__tones.index(sharp) + 1 - 0.5
            except:
                tone = 0
        return [tone, grade]

    def cal___tones(self):
        """
        确定唱名对应的音阶
        :return:
        """
        self.__tones = []
        remove_digits = str.maketrans('', '', digits)
        re__do = self.__do.translate(remove_digits)
        initpos = Chin.__noteslist.index(re__do)
        count = 0
        for item in Chin.__tonesList:
            item = item + initpos
            pos = item % 12
            self.__tones.append(Chin.__noteslist[pos])
            count = count + 1
        print(self.__tones)

    @staticmethod
    def cal_position(basefrq, frq):
        """
        根据散音音高，待求位置的频率，求有效相对弦长，也就是着弦位点
        音高可以是相对音高，也可是绝对音高
        :param basefrq:散音基频
        :param frq:目标频率
        :return:着弦位点
        """
        return 1.0 * basefrq / frq

    @staticmethod
    def cal_notesposition(rightboundary):
        """
        计算12平均律相对音阶对应的位置，一般作为初始化的常量设置
        :param rightboundary: 琴弦右侧边界，对应最小有效相对弦长
        :return:12平均律音阶对应的位置
        """
        # pitches:计算各个音阶相对音高
        pitches = 2 ** np.arange(1 / 12, 4, 1 / 12)
        pos = []
        for pitch in pitches:
            poscan = 1.0 / pitch
            if poscan > rightboundary:
                pos.append(poscan)

        return pos

    def cal_sanyinpred(self, pitch, thr):
        """
        匹配散音
        :param pitch: 待匹配音高
        :param thr: 匹配阈值
        :return:匹配结果
        """
        rs = []
        dist = abs(self.__hzes - pitch)  # 音高距离
        candidate = np.argmin(dist)  # 候选散音
        try:
            score = math.log(pitch, 2.0 ** (1.0 / 12)) - math.log(self.__hzes[candidate], 2.0 ** (1.0 / 12))
            if abs(score) < thr:
                rs.append([candidate + 1, score])
        except Exception as e:
            print(e)

        return rs

    def cal_anyinstring(self, stringPitch, pitch, thr, spaceThr):
        """
        单一弦按音推测
        :param stringPitch 散音音高
        :param pitch:音高
        :param thr: 音准阈值
        :param spaceThr 绝对距离阈值
        :return:
        """

        positionR = self.cal_position(stringPitch, pitch)  # 相对位置
        if positionR > 0.96:
            return 0
        __notesR = math.log(pitch / stringPitch, 2 ** (1 / 12))  # 相对散音音高
        candidateNoteR = np.round(__notesR)  # 候选相对散音音高
        errR = __notesR - candidateNoteR  # 相对散音音高误差
        if abs(errR) > thr:
            if Chin.pos2hui(positionR) > 1.5:
                return -1.0 * Chin.pos2hui(positionR)
            else:
                return 0
        else:
            candidate_positionR = 1 / ((2 ** (1 / 12)) ** candidateNoteR)
            if abs(positionR - candidate_positionR) < spaceThr and Chin.pos2hui(positionR) > 1.5:
                return Chin.pos2hui(positionR)
            else:
                return 0

    def cal_anyinpred(self, pitch, thr, spaceThr):
        """
        七弦按音推测
        :param pitch:音高
        :param thr:音位阈值
        :spaceThr：音位绝对位置阈值，反映手指精度
        :return:
        """
        rs = []
        for i in np.arange(7):
            anyin = self.cal_anyinstring(self.__hzes[i], pitch, thr, spaceThr)
            if anyin != 0:
                rs.append([i + 1, anyin])
        return rs

    def cal_fanyinstring(self, stringpitch, pitch, thr):
        """
        获取指定弦泛音音位
        :param stringpitch:  散音频率
        :param pitch:  输入频率
        :param thr:  匹配误差阈值
        :param spacethr:  音位绝对距离误差阈值
        :return: 可能的音位
        """
        # 泛音由于5倍泛音 7倍泛音的关系，不采用2**1/12做误差分析

        times = pitch / stringpitch  # 频率比
        if times < 1.5:
            return []
        candidate_time = np.round(times)  # 候选倍数
        err = times - np.round(times)
        rs = []
        if abs(err) < thr:
            for i in np.arange(13):
                if Chin.fanyintimes[i] == candidate_time:
                    rs.append(i + 1)
        return rs

    def cal_fanyinpred(self, pitch, thr):
        """
        预测可能的泛音音位
        :parweiam pitch:  音高
        :param thr:  note百分比误差阈值
        :param spacethr: 音位绝对距离阈值
        :return:返回可能的泛音音位
        """
        rs = []
        for i in np.arange(7):
            fanyin = self.cal_fanyinstring(self.__hzes[i], pitch, thr)
            if fanyin != []:
                rs.append([i + 1, fanyin])
        return rs

    def cal_possiblepos(self, pitches):
        """
        计算可能的音类及音位
        :param pitches:待解析的音高集合
        :return: 特定音高对应的可能的音位集合
        """
        if isinstance(pitches,(list,np.ndarray)) is not True:
            pitch=pitches
            pitches = []
            pitches.append(pitch)
        number = len(pitches)
        possiblepos = []  # 结果
        formatStr = ""  # 格式化结果，用于打印
        for i in range(number):
            possiblepos.append([])
        thrsanyin = 0.2
        thranyin = 0.2
        thranyinspace = 0.02 / 1.2
        thrfanyin = 0.0875  # 有待确定，确定这点比较难

        for i in np.arange(number):
            pitch = pitches[i]
            formatStr = formatStr + "%.2f&nbsp&nbsp&nbsp&nbsp" % pitch
            if pitch>20:
                noteTone = librosa.hz_to_note(pitch / self.get_scaling(), cents=True)  # 用于测量tone的note，不求百分数
                formatStr = formatStr + noteTone + "&nbsp&nbsp&nbsp&nbsp"
                tone = self.note2tone(noteTone)  # 计算音高 ，因为程序编写费时间，不提供直接设置tone的方式
                tonestr = '%.1f_%d' % (tone[0], tone[1])  # tone[0] 是音高， tone[1]是grade
                formatStr = formatStr + tonestr + "\n"
            else:
                formatStr = ""

            # 散音检测
            sanyinPred = self.cal_sanyinpred(pitch, thrsanyin)
            if sanyinPred != []:
                possiblepos[i].append(sanyinPred)
                formatStr = formatStr + "s:%d弦散音 e:%.2f\n" % (sanyinPred[0][0], sanyinPred[0][1])
            # 按音检测
            anyinPrep = self.cal_anyinpred(pitch, thranyin, thranyinspace)
            if anyinPrep != []:
                possiblepos[i].append(anyinPrep)
                formatStr = formatStr + "a:"
                for anyin in anyinPrep:
                    formatStr = formatStr + "%d弦%.2f徽  " % (anyin[0], anyin[1])
                formatStr = formatStr + "\n"
            # 泛音音位
            fanyinpred = self.cal_fanyinpred(pitch, thrfanyin)
            if fanyinpred != []:
                possiblepos[i].append(fanyinpred)
                formatStr = formatStr + "f:"
                for fanyin in fanyinpred:
                    for huiwei in fanyin[1]:
                        formatStr = formatStr + "%d弦%d徽  " % (fanyin[0], huiwei)
                formatStr = formatStr + "\n"
        return [possiblepos, formatStr]

    def __init__(self, **kw):
        """
        :param __notes:
        七条弦依次对应的note（十二平均律标识）
        :param __a4_hz:
        a4对应的频率
        :param __do:
        唱名为__do的note标识
        """
        self.__notes = None
        self.__do = None
        self.__a4_hz = None
        self.__hzes = None
        self.__tones = None
        self.__scaling = 1
        self.pos = self.cal_notesposition(0.125)
        self.__hui = None
        self.__harmony = None
        for key in kw:
            try:
                if key == "__notes":
                    setattr(self, key, kw[key])
                    string_num = len(self.__notes)
                    if string_num != 7:
                        raise Exception("string number err:__notes number err %d!" % string_num)
                    self.__hzes = np.zeros(7)
                    for i in np.arange(string_num):
                        self.__hzes[i] = librosa.note_to_hz(self.__notes[i]) * self.__scaling
                if key == "__hzes":
                    setattr(self, key, kw[key])
                    string_num = len(self.__hzes)
                    if string_num != 7:
                        raise Exception("string number err:__hzes number err %d!" % string_num)
                    self.__notes = [None] * 7
                    for i in np.arange(string_num):
                        self.__notes[i] = librosa.hz_to_note(self.__hzes[i], cents=True)
                if key == "__a4_hz":
                    setattr(self, key, kw[key])
                    self.__scaling = self.__a4_hz / 440.0
            except Exception as e:
                print(e)

    def get_notes(self):
        """
        __notes bean get
        :return: 返回__notes
        """
        if self.__notes is None:
            return None
        else:
            return list(np.copy(self.__notes))

    def updateNotesFromHzes(self):
        """
        由notes更新频率
        :return:None
        """
        if self.__notes is None:
            self.__notes = [""] * 7
        for i in np.arange(7):
            self.__notes[i] = librosa.hz_to_note(self.__hzes[i] / self.__scaling)

    def updateHzesFromNotes(self):
        """
        由频率更新notes
        :return:None
        """
        if self.__hzes is None:
            self.__hzes = np.zeros(7)
        for i in np.arange(7):
            self.__hzes[i] = librosa.note_to_hz(self.__notes[i]) * self.__scaling

    def set_notes(self, notes):
        """
        __notes bean set
        :param __notes: 七弦音高的十二平均律标识设置，H代表不改变此前音高
        :return: None
        """
        self.__notes = np.where(notes == "H", self.__notes, notes)
        self.updateHzesFromNotes()

    def get_hzes(self):
        """
        :return:
        bean 返回__hzes
        """
        return list(np.copy(self.__hzes))

    def set_hzes(self, __hzes):
        """
        设置七条弦音高，hz标识
        :param __hzes: hz为-1表示不改变之前设置
        :return: None
        """
        self.__hzes = np.where(__hzes == -1, self.__hzes, __hzes)
        self.updateNotesFromHzes()

    def get_ahz(self):
        return self.__a4_hz

    def set_ahz(self, a_hz):
        self.__a4_hz = a_hz
        self.__scaling = self.__a4_hz / 440.0

    def get_do(self):
        return self.__do

    def set_do(self, __do):
        self.__do = __do
        self.cal___tones()

    def get_scaling(self):
        return self.__scaling

    def set_hz(self, strID, hz):
        self.__hzes[strID] = hz
        # 更新notes
        self.updateNotesFromHzes()

    def set_note(self, strID, note):
        self.__notes[strID] = note
        # 更新hzes
        self.updateHzesFromNotes()

    def get_hui(self):
        """
        获取已知明徽
        :return: [string,pos]
        """
        return self.__hui

    def cal_hui(self):
        """
        重新计算徽位信息
        :return:True 计算无误，False 计算错误

        """
        if self.get_hzes() is None:
            return False
        rs = []  # 徽位及其音高
        for string in np.arange(7):
            for pos in np.arange(13):
                rs.append([string, pos, self.fanyintimes[pos] * self.__hzes[string]])
        self.__hui = rs

    @staticmethod
    def harmony(pitch_a, pitch_b, validity_threshold, harmony_threshold, is_sanyin):
        """
        原始频率对和谐性评估函数，阈值单位为音分
        :param pitch_a:频率a
        :param pitch_b:频率b
        :param validity_threshold:评估起点阈值
        :param harmony_threshold:和谐阈值
        :param is_sanyin:是否是散音，如果是则容忍倍频
        :return:返回是否和谐及其参数，None表示不参与计算
        """
        try:
            relation = pitch_a / pitch_b  # 音比
            note = abs(math.log(relation, 2 ** (1 / 12)))  # 计算音分关系
            possible_note = np.round(note)  # 候选音计算， 需要四舍五入
            note_div12_remainder = possible_note % 12  # 除以12的余数，用以判断是否是倍频
            if is_sanyin and note_div12_remainder != 0:
                return None
            if is_sanyin is False and possible_note != 0:
                return None
            err = abs(note - possible_note)
            time = 1.0
            if relation > 1:
                time = -1.0
            if err > validity_threshold:  # 检测门限
                return None
            else:
                if err < harmony_threshold:
                    return [True, err * time]  # 和谐
                else:
                    return [False, err * time]  # 不和谐

        except Exception as e:
            return None

    def cal_harmony(self):
        """
        计算和谐性
        包括散音和谐性，容忍八度关系
        计算泛音和谐性，不容同弦及八度关系
        :return: 和谐音对以及不和谐音对，包括散泛音
        """
        rs = {'T': [], 'F': [], 'ScoreS': 0, 'ScoreF': 0}  # 计算结果字典
        try:
            distS = []
            distF = []
            # 估算散音和谐参数：和谐的弦对及不和谐的弦对
            combinas = combinations(np.arange(7), 2)  # 待测试组合
            for stringPair in combinas:
                # 暂时设置为 0.30 0.15
                harmony_result = Chin.harmony(self.__hzes[stringPair[0]], self.__hzes[stringPair[1]], 0.30, 0.15, True)
                if harmony_result is not None:
                    distS.append(harmony_result[1])
                    if harmony_result[0] is True:
                        rs['T'].append(['s', stringPair[0], stringPair[1], harmony_result[1]])
                    else:
                        rs['F'].append(['s', stringPair[0], stringPair[1], harmony_result[1]])
            # 估算泛音和谐参数：和谐的徽对及不和谐的徽对
            self.cal_hui()  # 重新计算徽位
            hui_all = self.get_hui()
            # 挑选6徽以上的徽位
            hui_simi = [simi for simi in hui_all if (simi[1] > 5)]
            # 粗算用于比对的徽位对组合
            combinas_rough = combinations(hui_simi, 2)
            combinas_fanyin = []  # 待测泛音组合
            # 过滤同弦徽对
            for rough in combinas_rough:
                if rough[0][0] != rough[1][0]:
                    combinas_fanyin.append(rough)
            # 计算徽对组合是否和谐
            for fanyin_pair in combinas_fanyin:
                harmony_result = Chin.harmony(fanyin_pair[0][2], fanyin_pair[1][2], 0.3, 0.15, False)
                if harmony_result is not None:
                    distF.append(harmony_result[1])
                    if harmony_result[0] is True:
                        rs['T'].append(
                            ['f', [fanyin_pair[0][0], fanyin_pair[0][1]], [fanyin_pair[1][0], fanyin_pair[1][1]],
                             harmony_result[1]])
                    else:
                        rs['F'].append(
                            ['f', [fanyin_pair[0][0], fanyin_pair[0][1]], [fanyin_pair[1][0], fanyin_pair[1][1]],
                             harmony_result[1]])
            rs['ScoreS'] = np.mean(np.abs(distS))
            rs['ScoreF'] = np.mean(np.abs(distF))
            self.__harmony = rs

        except Exception as e:
            print(e)

    def get_harmony(self):
        """
        获取弦和谐参数
        :return:
        """
        return self.__harmony
