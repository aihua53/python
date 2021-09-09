import string
import sys, os, re
import difflib
import time, json
from datetime import datetime
from string import digits
from tokenize import u

ANR = 'anr'
CRASH = 'crash'
NATIVE_CRASH = 'native_crash'
TOMBSTONE = 'tombstone'
WATCHDOG = 'watchdog'
RESTART = 'restart'
UNKNOWN = 'unknown'
# CRASH_RATIO = 0.95
# ANR_RATIO = 0.99
# TOMBSTONE_RATIO = 0.98
CRASH_RATIO = 1.0
ANR_RATIO = 1.0
TOMBSTONE_RATIO = 0.98
INVALID_STACK_TIMEOUT = 'TimeoutException'
INVALID_STACK_OOM = 'OutOfMemoryError'
INVALID_STACK_DATA = 'DataSupportException'
INVALID_STACK_CURSOR = 'CursorWindowAllocationException'
INVALID_TOMBSTONE_STACK = 'Abort message'
INVALID_TOMBSTONE_SINGLE = 'signal 6 (SIGABRT)'


class LogParser(object):
    def __init__(self, msg, logFile):
        self.msg = msg
        # read log file
        if not os.path.isfile(logFile):
            raise IOError("%s is not a file object or content is empty" % logFile)
        self.logFile = logFile
        with open(self.logFile, "r", encoding='utf-8', errors='ignore') as f:
            self.logContent = f.read()
        if not self.logContent:
            raise EOFError("%s is an empty log file!" % logFile)
        self.logFileName = self.logFile.split("/")[-1]
        self.content = self.logContent.split('\n')
        self.crash_backtrace = DropboxUtil.get_error_content_crash(logFile).split('\n')
        self.list_tag = [
            "data_app_crash", "system_app_crash", "system_app_native_crash", "TOMBSTONE", "system_app_anr",
            "data_app_anr",
            "watchdog", "system_server_crash", "SYSTEM_RESTART"
        ]
        self.key_crash_timestamp = "time: "
        self.format_time_a = "%Y-%m-%d-%H-%M-%S-%f"
        self.format_time_b = "%Y-%m-%d %H:%M:%S"
        self.format_time_c = "%Y-%m-%d-%H_%M_%S"
        self.key_appName_a = "Process: "
        self.key_appName_b = "Cmd line: "
        self.key_sw = "Build: "
        self.key_tombstone_sw = "Build fingerprint: "
        self.model = "M01"
        self._softwareVersion = ""
        self._tag = None
        self._occurAt = 0
        self._appName = ""
        self._title = ""
        self._occurBuild = ""
        self._summary = ""

    def getDeviceId(self):
        return self.msg["deviceId"]

    def getVin(self):
        return self.msg["vin"]

    def getEnvironmentStage(self):
        return json.loads(self.msg["data"])["environmentStage"]

    def getoccurBuild(self):
        if self._tag in ["TOMBSTONE"]:
            p = re.compile(r'%s(.*)' % self.key_tombstone_sw)
            result_find_build = list(filter(lambda x: re.findall(p, x), self.content[:20]))
            if result_find_build:
                self._occurBuild = result_find_build[0].strip(self.key_tombstone_sw).replace("'", "")
            # self._occurBuild = self.content[9].strip(self.key_tombstone_sw).replace("'", "")
            return self._occurBuild
        p = re.compile(r'%s(.*)' % self.key_sw)
        result_find_build = list(filter(lambda x: re.findall(p, x), self.content[:20]))
        if result_find_build:
            self._occurBuild = result_find_build[0].strip(self.key_sw)
        return self._occurBuild

    def getsoftwareVersion(self):
        ''' getOccurAt must be call after getTag'''
        return json.loads(self.msg["data"])["softwareVersion"]

    def getTag(self):
        for name in self.list_tag:
            if self.logFileName.find(name) != -1:
                self._tag = name
                break
        return self._tag

    def getOccurAt(self):
        ''' getOccurAt must be call after getTag'''
        # crash occurAt in dropbox
        if self._tag in ["data_app_crash", "system_app_crash", "system_app_native_crash"]:
            timestamp = self.content[0].strip(self.key_crash_timestamp)
            datetime_obj = datetime.strptime(timestamp, self.format_time_a)
            self._occurAt = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
        # elif self._tag in ["system_app_anr"] and self.logFileName.startswith("anr"):
        #     key_timestamp = re.compile(r'\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d')
        #     timestamp = re.findall(key_timestamp, self.content[1])[0]
        #     datetime_obj = datetime.strptime(timestamp, self.format_time_b)
        #     self._occurAt = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
        # anr occurAt in dropbox
        elif self._tag in ["system_app_anr", "data_app_anr"]:
            timestamp = self.content[0].strip(self.key_crash_timestamp)
            datetime_obj = datetime.strptime(timestamp, self.format_time_a)
            self._occurAt = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
        elif self._tag in ["system_server_crash"]:
            timestamp = self.logFileName[-23:-4]
            datetime_obj = datetime.strptime(timestamp, self.format_time_c)
            self._occurAt = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
        # tombstone occurAt in dropbox
        elif self._tag in ["TOMBSTONE", "watchdog"]:
            key_timestamp = re.compile(r'\d\d\d\d-\d\d-\d\d-\d\d_\d\d_\d\d')
            timestamp = re.findall(key_timestamp, self.logFileName)[0]
            datetime_obj = datetime.strptime(timestamp, "%Y-%m-%d-%H_%M_%S")
            self._occurAt = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
            # try:
            #     timestamp = self.content[6][-28:].replace("CST ", "")
            #     # tombstone time format is "%a %b %d %H:%M:%S %Y"
            #     self._occurAt = int(time.mktime(time.strptime(timestamp, "%a %b %d %H:%M:%S %Y")) * 1000)
            # except:
            #     print("the formatted tombstone log file is not standard!")
        return self._occurAt

    def getAppName(self):
        if self._tag in ["data_app_crash", "system_app_crash", "system_server_anr"]:
            self._appName = self.content[1].replace(self.key_appName_a, "")
        # elif self._tag in ["anr"] and self.logFileName.startswith("anr"):
        #     self._appName = self.content[2].replace(self.key_appName_b, "")
        elif self._tag in ["system_app_anr", "data_app_anr"]:
            self._appName = self.content[1].replace(self.key_appName_a, "")
        elif self._tag in ["system_server_crash", "watchdog"]:
            self._appName = "system_server"
        elif self._tag in ["TOMBSTONE", "system_app_native_crash"]:
            p = re.compile(r'>>> (.*) <<<')
            try:
                result_find_appName = list(filter(lambda x: re.findall(p, x), self.content[:20]))
                if result_find_appName:
                    self._appName = re.findall(p, result_find_appName[0])[0]
                    # self._appName = result_find_appName[0].strip(self.key_sw)
            except:
                print("getAppName failed! The formatted tombstone log file is not standard!")
        return self._appName

    @staticmethod
    def title_handle(title) -> list:
        if '@' in str(title):
            p1_title = str(title).split("@", 1)[0]
            title_list = DropboxUtil.remove(p1_title)
        elif '0x' in str(title):
            address_start = str(title).find("0x")
            address_end = str(title).find(' ', address_start, len(str(title)) - 1)
            p_title = str(title)[address_end:]
            p1_title = str(title)[0:address_start].join(p_title)
            title_list = DropboxUtil.remove(p1_title)
        else:
            title_list = DropboxUtil.remove(str(title))
        return [title_list]

    def getTitle(self):
        if self._tag in ["data_app_crash", "system_app_crash"]:
            title_lists = self.content[8]
            title_list = self.title_handle(title_lists)
            # self._title = self.content[8]
            p = re.compile(r"Caused by: ")
            # split_line = "--------- beginning of main\n"
            # index_stack2log = 50 if split_line not in self.content else self.content.index(split_line)
            result_find_title = list(filter(lambda x: re.findall(p, x), self.crash_backtrace))
            for title in result_find_title:
                titles = self.title_handle(title)
                title_list.append(titles)
            self._title = '\n'.join('%s' % id for id in title_list)
        elif self._tag == "system_server_anr":
            self._title = re.findall(r"Subject: (.*)\n", self.logContent)[0]
        elif self._tag == "system_server_crash":
            self._title = self.content[3]
        elif self._tag in ["system_app_anr", "data_app_anr"]:
            self._title = self.content[6].strip("Subject: ")
        elif self._tag in ["TOMBSTONE", "system_app_native_crash"]:
            p = r"signal "
            s = r"Abort message: |Cause:"
            result_find_tag = list(filter(lambda x: re.findall(s, x), self.content[:20]))
            result_find_title = list(filter(lambda x: re.findall(p, x), self.content[:20]))
            self._title = ''.join(result_find_title) + '\t\n' + '\n'.join(result_find_tag)
            # for title in result_find_title:
            # self._title += title
        return self._title

    def getSummary(self):
        self._summary = "\n".join(self.content[:40])
        return self._summary


def yesterday():
    """
    return the date of yesterday that format like '20210401'
    """
    today = datetime.datetime.today()
    return (today - datetime.timedelta(days=1)).strftime('%Y%m%d')


class DropboxUtil(object):
    """"
    get error type/subject/content
    """

    @staticmethod
    def get_error_type(filename) -> str:
        filename = filename.lower()
        if 'app_crash' in filename:
            return CRASH
        elif 'system_server_crash' in filename:
            return CRASH
        elif 'anr' in filename:
            return ANR
        elif 'tombstone' in filename or 'native_crash' in filename:
            return TOMBSTONE
        elif 'watchdog' in filename:
            return WATCHDOG
        elif 'restart' in filename:
            return RESTART
        return ''

    @staticmethod
    def get_error_package(error_type, filepath) -> str:
        if error_type == 'restart':
            return ''
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            count = 0
            while line:
                if count > 20:
                    return ""
                if error_type in [CRASH, ANR, WATCHDOG] and line.strip().startswith('Process:'):
                    return line.split('Process:')[-1].strip()
                if error_type == TOMBSTONE and line.strip().startswith('pid:'):
                    matchs = re.search(r'>>>(.+?)<<<', line)
                    return matchs.groups()[0].strip()
                line = f.readline()
                count += 1
        return ''

    @staticmethod
    def get_error_subject(error_type, filepath) -> str:
        """
        crash:Build:xxx后不为空的第一行，beginning行break
        anr：Subject:XXX,提取该行Subject后内容,直至CPU usage from
        tombstone:signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0,提取fault前内容
        -------pid行前break
        :param error_type:
        :param filepath:
        :return:str
        """
        subject = ''
        start_flag = False
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                if error_type == CRASH:
                    if line.startswith('Build:'):
                        start_flag = True
                        line = f.readline()
                        continue
                    if start_flag and line.strip() != '':
                        subject += line.strip()
                        break
                    if 'beginning' in line:
                        break
                elif error_type == ANR:
                    if line.strip().startswith('Subject:'):
                        subject += line.split('Subject:')[-1]
                        break
                    if line.strip().startswith('CPU usage from'):
                        break
                elif error_type == TOMBSTONE:
                    if line.strip().startswith('signal'):
                        subject += ','.join(line.split(',')[:2])
                        line = f.readline()
                        if line.startswith('Cause:'):
                            subject += line.strip()
                        if line.startswith('Abort message:'):
                            subject += line.strip()
                        break
                    if line.strip().startswith('backtrace'):
                        break
                elif error_type == WATCHDOG:
                    if line.strip().startswith('Subject:'):
                        subject += line.split('Subject:')[-1]
                        line = f.readline()
                        continue
                    if line.strip().startswith('----- pid'):
                        break

                line = f.readline()

        return subject

    @staticmethod
    def get_error_content_anr(filepath) -> str:
        """
        摘取----- pid XXX到----- end XXX 的进程相关的信息段，XXX为发生ANR的PID；
        通过判断摘取的信息段sysTid和发生ANR的PID相同来确保是主线程，摘取主线程的堆栈信息；
        :param filepath:
        :return:
        """
        content = ''
        is_pid = False
        is_main_pid = False
        pid = -1
        start = False
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                if line.startswith('PID:'):
                    pid = int(line.split('PID:')[-1].strip())
                    if pid == 0:
                        return ''
                if '----- pid %s' % pid in line:
                    is_pid = True
                if is_pid and 'main' in line and 'tid=1' in line:
                    is_main_pid = True
                if is_pid and is_main_pid and line.strip().startswith('| sysTid=%s' % pid):
                    start = True
                if start and not line.strip().startswith('|'):
                    content += line
                if start and line.strip() == '':
                    break
                if '----- end %s' % pid in line:
                    break
                line = f.readline()
        return content

    @staticmethod
    def get_error_content_tombstone(filepath) -> str:
        """
        backtrace后至stack或beginning前的内容
        :param filepath:
        :return:
        """
        content = ''
        start = False
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                if start and line.strip().startswith('stack') or 'beginning' in line:
                    break
                if start and line.strip() != '':
                    # print("enter t==========" + content)
                    content += '/' + '/'.join(line.split('/')[1:])
                    # print("contenst=========="+content)
                    line = f.readline()
                    # print("left t==========" + content)
                    continue
                if line.strip().startswith('backtrace'):
                    start = True
                line = f.readline()
        return content

    @staticmethod
    def get_error_tombstone_dict(filepath) -> str:
        """
        backtrace后至stack或beginning前的内容
        :param filepath:
        :return:
        """
        content = ''
        start = False
        tombstone_dict = {}
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                if start and line.strip().startswith('stack') or 'beginning' in line:
                    break
                if start and line.strip() != '':
                    # content += '/' + '/'.join(line.split('/')[1:])
                    if '+' in line:
                        content = '/' + '/'.join(line.split('/')[1:])
                        tombstone_stack = content.split('+', 1)
                        stack_str = {tombstone_stack[0]: tombstone_stack[1]}
                    elif 'offset' in line:
                        content = '/' + '/'.join(line.split('/')[1:])
                        tombstone_stack = content.split('offset', 1)
                        stack_str = {tombstone_stack[0]: tombstone_stack[1]}
                    else:
                        if '+' not in line and 'offset' not in line:
                            content = '/' + '/'.join(line.split('/')[1:])
                            stack_str = {content: ''}
                    tombstone_dict.update(stack_str)
                    line = f.readline()
                    continue
                if line.strip().startswith('backtrace'):
                    start = True
                line = f.readline()
        return tombstone_dict

    @staticmethod
    def get_error_content_crash(filepath) -> str:
        backtrace = ''
        start = False
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                if start and 'beginning' in line:
                    break
                if start and line.strip() != '':
                    backtrace += line
                    line = f.readline()
                    continue
                if line.strip().startswith('Build'):
                    start = True
                line = f.readline()
        return backtrace

    @staticmethod
    def get_backtrace(error_type, filepath) -> str:
        '''
        RESTART:return 文件内容
        WATCHDOG 按anr处理
        :param error_type:
        :param filepath:
        :return:
        '''
        if error_type in [RESTART, WATCHDOG]:
            return open(filepath, 'r', encoding='UTF-8').read()
        error_type = (error_type == WATCHDOG) and ANR or error_type
        if error_type == ANR:
            return DropboxUtil.get_error_content_anr(filepath)
        if error_type == TOMBSTONE:
            return DropboxUtil.get_error_content_tombstone(filepath)
        if error_type == CRASH:
            return DropboxUtil.get_error_content_crash(filepath)

    @staticmethod
    def get_backtrace_title(error_type, filepath, p) -> str:
        '''
        RESTART:return 文件内容
        WATCHDOG 按anr处理
        :param error_type:
        :param filepath:
        :return:
        '''
        if error_type in [RESTART, WATCHDOG]:
            return open(filepath, 'r', encoding='UTF-8').read()
        error_type = (error_type == WATCHDOG) and ANR or error_type
        if error_type == ANR:
            return p.getTitle().replace('\n', '\t')
        if error_type == TOMBSTONE:
            return p.getTitle().split("\t\n")[0].replace('\n', '\t')
        if error_type == CRASH:
            return DropboxUtil.get_error_crash_type(filepath)

    @staticmethod
    def get_backtrace_tag(error_type, filepath, p) -> str:
        '''
        RESTART:return 文件内容
        WATCHDOG 按anr处理
        :param error_type:
        :param filepath:
        :return:
        '''
        if error_type in [RESTART, WATCHDOG]:
            return open(filepath, 'r', encoding='UTF-8').read()
        error_type = (error_type == WATCHDOG) and ANR or error_type
        if error_type == ANR:
            return DropboxUtil.get_backtrace(error_type, filepath).split('\n')[0]
        if error_type == TOMBSTONE:
            backtrace_tag = p.getTitle().split("\t\n")[1]
            if '\n' in backtrace_tag:
                return backtrace_tag.replace('\n', '\t')
            else:
                print("----------------------------------------" + backtrace_tag)
                return backtrace_tag
        if error_type == CRASH:
            tag = p.getTitle()
            backtrace_tag = tag.replace('\n', '\t')
            return backtrace_tag

    @staticmethod
    def remove(text):
        remove_chars = '[0-9’!"#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}~]+'
        return re.sub(remove_chars, '', text)

    @staticmethod
    def get_error_crash_type(filepath) -> str:
        crash_subject = DropboxUtil.get_error_content_crash(filepath).split("\n", 1)[0]
        # print('crash_type:' + crash_subject)
        if ':' in crash_subject:
            crash_type = crash_subject.split(':', 1)[0]
        else:
            crash_type = crash_subject
        return crash_type

    @staticmethod
    def get_error_dict(error_type, filepath) -> str:
        '''
        RESTART:return 文件内容
        :param error_type:
        :param filepath:
        :return:
        '''
        if error_type == TOMBSTONE:
            return DropboxUtil.get_error_tombstone_dict(filepath)
        if error_type == CRASH:
            return DropboxUtil.get_crash_dict(filepath)

    @staticmethod
    def get_crash_dict(filepath) -> str:
        crash_dict = {}
        start = False
        with open(filepath, 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                if start and 'beginning' in line:
                    break
                if start and line.strip() != '':
                    if ':' in line and 'Caused by' not in line:
                        crash_stack = line.split(':', 1)
                        stack_str = {crash_stack[0]: crash_stack[1]}

                    else:
                        if 'Caused by' not in line:
                            stack_str = {line.strip(): ''}
                    crash_dict.update(stack_str)
                    line = f.readline()
                    continue
                if '\t' in line and line.strip().startswith('at'):
                    start = True
                line = f.readline()
            # print('crash dict:' + str(crash_dict))
        return crash_dict


def search_dropbox_path(log_path):
    ll = []
    filenames = os.listdir(log_path)
    for filename in filenames:
        filepath = os.path.join(log_path, filename)
        if os.path.isdir(filepath):
            ll.append(filepath)
    return ll


def _get_error_info(filepath: str, p) -> dict:
    """
        anr pid为0或堆栈信息为空或MessageQueue存在，问题类型置为unkown
    :param filepath:
    :return:
    """
    filename = os.path.split(filepath)[-1]
    error = {"package": "", 'type': DropboxUtil.get_error_type(filename), "subject": "", "content": "", "times": 1,
             "error_time": "", "file": ""}
    if error['type'] == '':
        return error
    error["package"] = DropboxUtil.get_error_package(error['type'], filepath)

    time_millis = int(filename[filename.find("@") + 1:filename.find(".")]) if filename.find("@") >= 0 else 0
    error["error_time"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                        time.localtime(time_millis / 1000)) if time_millis else filename[-23:-4]
    error["subject"] = DropboxUtil.get_error_subject(error["type"], filepath)
    error['content'] = DropboxUtil.get_backtrace(error["type"], filepath)
    error['title'] = DropboxUtil.get_backtrace_title(error["type"], filepath, p)
    error['tag'] = DropboxUtil.get_backtrace_tag(error["type"], filepath, p)
    error['file'] = filepath
    if error['type'] == ANR:
        if error['content'] == '' or 'android.os.MessageQueue.nativePollOnce' in error['content']:
            error['type'] = UNKNOWN
    if error['type'] == CRASH or error['type'] == TOMBSTONE:
        error['dict'] = DropboxUtil.get_error_dict(error["type"], filepath)
        # error['dict'] = DropboxUtil.get_crash_dict(filepath)
    else:
        error['dict'] = ''
    return error


def check_ratio(ratio, error_type):
    if error_type == CRASH:
        if ratio >= CRASH_RATIO:
            return True
    if error_type == ANR:
        if ratio >= ANR_RATIO:
            return True
    if error_type == TOMBSTONE:
        if ratio >= TOMBSTONE_RATIO:  # 判断相似bug
            return True

    return False


def log_parse(log_path, type):
    logpath = log_path + '/' + type
    filenames = os.listdir(logpath)

    i = 0.0
    length = len(filenames)
    err_grp = []
    for filename in filenames:
        t1 = round(time.time() * 1000)
        # print(filename)
        if not any([filename.endswith(".txt"), filename.endswith(".log")]):
            print("not a log file, skip: %s" % filename)
            continue
        i = i + 1
        file_path = logpath + '/' + filename
        print('input %s[%2.1f]: %s' % (type, i / length * 100, file_path))
        f = open(file_path, "r", encoding='utf-8', errors='ignore')
        if not f.read():
            print("  %s is an empty file, skip it!" % file_path)
            continue
        f.close()

        datas = {
            "deviceId": "111111111",
            "vin": "111111111000000000",
            "data": "{\"softwareVersion\": \"new software\", \"environmentStage\": \"mytest\"}",
        }
        p = LogParser(datas, file_path)
        dict_dropbox = {
            # "ua_id": "123456",
            "tag": p.getTag(),
            "package": p.getAppName(),
            # "grp_id": -1,
            "firstTime": p.getOccurAt(),
            "occurBuild": p.getoccurBuild(),
            # "file": filename
        }

        total_times = {ANR: 0, CRASH: 0, TOMBSTONE: 0, WATCHDOG: 0, RESTART: 0, UNKNOWN: 0}  # 按类型归类错误
        packages = {}  # 按包名归类错误

        error = _get_error_info(file_path, p)
        """
        content = ""
        content1 = 'fault addr 0x3f800000000003d0'
        if content in error["tag"] and content1 in error["title"]:
            print("filepath" + file_path)
            break
        """
        if error['type'] == '':  # 压缩文件及非错误信息文件,不做分析
            print('  error type is empty')
            continue
        elif error["package"] == '' and error['type'] != RESTART:  # 错误类型不为restart时,如果包名为空,错误信息无效
            print('  error package is empty or error type is restart')
            continue

        if error['type'] == 'unknown':
            for item in err_grp:
                if item['package'] == error["package"] and item['type'] == error['type']:
                    print('  old unknown grp: ' + error["package"] + '-' + str(
                        len(error["content"])) + ' occurCount is ' + str(item['occurCount']))
                    item['occurCount'] += 1
                    break
            else:
                print('  new unknown grp: ' + error["package"] + '-' + str(len(error["content"])))
                new_item = {
                    "type": error['type'],
                    "content": error['content'].replace('\n', '\t'),
                    "package": error['package'],
                    "title": error['title'].replace('\n', '\t'),
                    "tag": error['content'].split('\n')[0],
                    "dict": error['dict'],
                    "occurCount": 1
                }
                err_grp.append(new_item)
        else:
            # totaltimes&packages
            total_times[error['type']] += 1
            if error["package"] not in packages.keys():
                packages[error["package"]] = {ANR: 0, CRASH: 0, TOMBSTONE: 0, WATCHDOG: 0, RESTART: 0, UNKNOWN: 0}
                packages[error["package"]][error['type']] += 1

            # 去重
            # print(' err_grp %s:%s size is %d' % (error["package"], error["type"], len(err_grp)))
            for item in err_grp:
                if item['package'] == error["package"] and item['type'] == error['type']:
                    if item['type'] == CRASH:
                        if item['title'] == error['title']:
                            if INVALID_STACK_DATA in item['title'] or INVALID_STACK_TIMEOUT \
                                    in item['title'] or INVALID_STACK_OOM in item['title'] \
                                    or INVALID_STACK_CURSOR in item['title']:
                                item['occurCount'] += 1
                                break
                            else:
                                if item['tag'] == error['tag']:
                                    # differ = set(item['dict'].items()) ^ set(error['dict'].items())
                                    differ = set(item['dict'].keys()) ^ set(error['dict'].keys())
                                    print("differ---------------------:" + str(differ))
                                    if len(differ) < 1:
                                        item['occurCount'] += 1
                                        break
                    if item['type'] == TOMBSTONE:
                        if INVALID_TOMBSTONE_STACK in item['tag'] and INVALID_TOMBSTONE_SINGLE in item['title'] \
                                and INVALID_TOMBSTONE_STACK in error['tag']:
                            item_tag = LogParser.title_handle(item['tag'].replace('\n', '\t'))
                            error_tag = LogParser.title_handle(error['tag'])
                            print("enter tombstone===============" + str(item_tag) + 'error_title' + str(error_tag))
                            if str(item_tag) in str(error_tag) or str(error_tag) in str(item_tag):
                                item['occurCount'] += 1
                                break
                        else:
                            # differ = set(item['dict'].items()) ^ set(error['dict'].items())
                            differ = set(item['dict'].keys()) ^ set(error['dict'].keys())
                            # print("differ---------------------:" + str(differ))
                            if len(differ) < 1:
                                item['occurCount'] += 1
                                break
                    else:
                        ratio1 = difflib.SequenceMatcher(None, error["content"].replace('\n', '\t'),
                                                         item['content']).quick_ratio()
                        # print('item.content ' + str(len(item['content'])) + ': ' + str(ratio1))
                        if check_ratio(ratio1, error["type"]):
                            # print('  old grp ' + str(len(error["content"])) + ': ' + str(ratio1))
                            item['occurCount'] += 1
                            break
            else:
                print('  new grp, difflib: ' + ', content size: ' + str(len(error["content"])) + ', type: ' +
                      error['type'])
                # print(error)
                new_item = {
                    "type": error['type'],
                    "content": error['content'].replace('\n', '\t'),
                    "package": error['package'],
                    "title": error['title'].replace('\n', '\t'),
                    "tag": error['tag'],
                    "dict": error['dict'],
                    "occurCount": 1
                }
                err_grp.append(new_item)

        # t2 = t1; t1 = round(time.time() * 1000); print('    line: ' + str(sys._getframe().f_lineno) + ', time: ' + str(t1-t2))

    return err_grp


def unzip_file(file_path, target_path, rm_old_file=True, max_size=2000):
    """
    unzip log.zip/gz file to target_path
    param file_path: .zip/gz file path
    param target_path: unzip file to target_path
    param target_path: remove the file under `file_path` after unzip if it's True, default is `True`
    """

    print(file_path)
    print(target_path)

    anr_unzip_path = os.path.join(target_path, "anr")
    crash_unzip_path = os.path.join(target_path, "crash")
    tombstone_unzip_path = os.path.join(target_path, "tombstone")
    for unzip_path in [anr_unzip_path, crash_unzip_path, tombstone_unzip_path]:
        if not os.path.isdir(unzip_path):
            print('mkdir -p %s' % unzip_path)
            os.system('mkdir -p %s' % unzip_path)

    file_list = os.listdir(file_path)

    if len(file_list) <= 0:
        return False

    for file_name in file_list[0: max_size]:
        # file_name = file_path.split("/")[-1]
        log_path = os.path.join(file_path, file_name)
        print("unzip %s" % log_path)
        if re.search('system_app_anr', file_name) or re.search('data_app_anr', file_name):
            u.unzip_file(log_path, anr_unzip_path)
            # os.system('unzip -o %s -d %s' % (log_path, anr_unzip_path))
            # os.system('gzip -df %s/%s' % (anr_unzip_path, file_name[:-4]))
        elif re.search('system_app_crash', file_name) or re.search('data_app_crash', file_name) or re.search(
                'system_server_crash', file_name):
            u.unzip_file(log_path, crash_unzip_path)
            # os.system('gzip -cd %s > %s/%s' % (log_path, crash_unzip_path, file_name[:-3]))
        # os.system('tar -zxf data/' + file_name + ' -C data/')
        elif re.search('SYSTEM_TOMBSTONE', file_name):
            u.unzip_file(log_path, tombstone_unzip_path)
            # os.system('gzip -cd %s > %s/%s' % (log_path, tombstone_unzip_path, file_name[:-3]))
        if rm_old_file:
            # print('rm -rf ' + file_path + '/' + file_name)
            os.system('rm -f ' + file_path + '/' + file_name)

    return True


def main_func(err_type):
    if sys.version_info.major == 3:
        begin_time = time.perf_counter()
    else:
        begin_time = time.perf_counter()

    log_path = "data"
    print('grp_parse')
    err_grp = []

    if err_type == 'all':
        err_grp += log_parse(log_path, 'anr')
        err_grp += log_parse(log_path, 'crash')
        err_grp += log_parse(log_path, 'tombstone')
    else:
        err_grp += log_parse(log_path, err_type)

    # save result to output file
    os.system('rm -f data/output.csv')
    result_fd = open('data/output.csv', 'w')
    item_str = 'type'
    item_str += ',' + 'occurCount'
    item_str += ',' + 'package'
    item_str += ',' + 'title'
    item_str += ',' + 'tag'
    item_str += ',' + 'content'
    result_fd.write(item_str + '\n')
    for item in err_grp:
        # print(item)
        item_str = item['type']
        item_str += ',' + str(item['occurCount'])
        item_str += ',' + item['package'].replace(',', ';')
        item_str += ',' + item['title'].replace(',', ';')
        item_str += ',' + item['tag'].replace(',', ';')
        item_str += ',' + item['content'].replace(',', ';')
        result_fd.write(item_str + '\n')

    result_fd.close()

    if sys.version_info.major == 3:
        end_time = time.perf_counter()
    else:
        end_time = time.clock()

    run_time = end_time - begin_time
    print('progress run time is:%s Seconds' % (run_time))
    print("Parse finished")

    return 'stability'
