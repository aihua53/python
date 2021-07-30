#!/usr/bin/python3.5

import sys
import argparse
import os
from enum import Enum
import re
import time
from prettytable import PrettyTable

DEBUG_FILE  = "/logcatd_debug"
S820A_DIR = "/S820A"
ANDROID_DIR = S820A_DIR + "/Android"
MONKEY_LOG = "/log"
MONKEY_LOGCAT = "/logcat"

class log_state(Enum):
	STDIO_LOG = 0
	S820A = 1
	ANDROID = 2
	ONE_ANDROID = 3
	MONKEY = 4
	MCU = 5
	ERROR = -1

class common_file():
	def __init__(self, path):
		self.path = path;
	def parse(self):
		print("parse")

	def commit(self):
		print(self.path)

class crash_info():
	def __init__(self, pid, process_name):
		self.name = process_name
		self.pids = [pid]
	def add_crash_info(self, pid, process_name):
		if process_name == self.name:
			self.pids.append(pid)
			return 0
		return -1
	def __str__(self):
		error = "%s crash pid:"%(self.name);
		for pid in self.pids[:5]:
			error += "%s,"%(pid)
		if len(self.pids) > 5:
			error += "...."
		return error

	def merge(self, other):
		if self.name == other.name:
			self.pids += other.pids
			return 0
		else :
			return -1

class system_error():
	def __init__(self, pid):
		self.pid = pid
		self.count = 1
	def add_error(self, pid):
		if pid == self.pid:
			self.count += 1
			return 0;
		return -1
	def __str__(self):
		return  "pid %s: System.error %d"%(self.pid, self.count)

	def merge(self, other):
		if self.pid == other.pid:
			self.count += other.count
			return 0
		else:
			return -1

class android_log_file(common_file):
	line_pattern = re.compile(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}).\d{3}"
                            + "\s+(\d+)\s+(\d+)\\s+([A-Z])\\s+"
                            + "(.+?)\\s*: (.*)$")
	filename_pattern = re.compile(r"^.*-(.*)-(.*)-(\d{4}-\d{2}-\d{2}-\d{2}_\d{2}_\d{2}).log")

	am_proc_start = re.compile(r"^\[\d+,(\d+),\d+,(.+),.+?,.+?\]$")
	am_crash = re.compile(r"^\[(\d+),\d+,(.+),\d+,.+\]$")
	system_error = re.compile(r"^(.+):\s+(.+)")
	anr_in = re.compile(r"^ANR in (.+)$")
	reboot = re.compile(r"^Rebooting, reason: (.+)$")
	def __init__(self, path):
		super().__init__(path)                        
		self.lines = 0
		self.bytes = 0
		self.pid_len = {}
		self.pid_len_sort = []
		self.tag_len = {}
		self.tag_len_sort = []
		self.isBegin = False
		self.isShutdown = False
		self.isWakeup = False
		self.isSleep = False
		self.needRepairTime = False
		self.check_time_jump = False
		self.file_time = 0
		self.end_time = 0
		self.start_time = 0
		self.last_time = 0
		self.process_info = {}
		self.crash_infos = []
		self.system_errors = []
		self.anr_process = []
		self.reboot_reason = ""


		resalt = self.filename_pattern.match(os.path.basename(self.path))
		if resalt != None :
			self.vin = resalt.group(2)
			self.file_time = time.strptime(resalt.group(3),"%Y-%m-%d-%H_%M_%S")
			if self.file_time.tm_year < 2019 :
				self.needRepairTime = True

	def add_system_error(self, pid):
		for error in self.system_errors:
			if error.add_error(pid) == 0:
				return
		self.system_errors.append(system_error(pid))

	def add_crash_info(self, pid, name):
		if pid not in self.process_info.keys():
			self.process_info.update({pid:name})
		for info in self.crash_infos:
			if info.add_crash_info(pid, name) == 0:
				return
		self.crash_infos.append(crash_info(pid, name))

	def parse_process_info(self, pid, time, level, tag, msg):
		if tag == "am_proc_start":
			resalt = self.am_proc_start.match(msg)
			if resalt != None:
				self.process_info.update({resalt.group(1):resalt.group(2)})
		elif tag == "am_crash":
			resalt = self.am_crash.match(msg)
			if resalt != None:
				#self.process_info.update({resalt.group(1):resalt.group(2)})
				self.add_crash_info(resalt.group(1), resalt.group(2))
		elif tag == "System.err":
			resalt = self.system_error.match(msg)
			if resalt != None:
				#self.process_info.update({resalt.group(1):resalt.group(2)})
				self.add_system_error(pid)
		elif tag == "ActivityManager" and level == "E":
			resalt = self.anr_in.match(msg)
			if resalt != None:
				self.anr_process.append(resalt.group(1))
		elif tag == "ShutdownThread":
			resalt = self.reboot.match(msg)
			if resalt != None:
				self.reboot_reason = resalt.group(1)

	def parse_log(self, pid, time, level, tag, msg):
		self.parse_process_info(pid, time, level, tag, msg)

	def parse_line(self,line):
		resalt = self.line_pattern.match(line)
		self.lines += 1;
		self.bytes += len(line)
		if (resalt != None):
			#print(resalt.group(0))
			if resalt.group(2) in self.pid_len:
				self.pid_len[resalt.group(2)] = len(line) + self.pid_len[resalt.group(2)]
			else :
				self.pid_len[resalt.group(2)] = len(line)

			if resalt.group(5) in self.tag_len:
				self.tag_len[resalt.group(5)] = len(line) + self.tag_len[resalt.group(5)]
			else :
				self.tag_len[resalt.group(5)] = len(line)
			year = ""
			#if self.needRepairTime != True and self.file_time :
			year = str(self.file_time.tm_year)
			#else :
			#	year = str(2020)

			time_string = year + "-" + resalt.group(1);
			tmp_time = time.mktime(time.strptime(time_string,"%Y-%m-%d %H:%M:%S"))
			if self.start_time == 0:
				self.start_time = tmp_time
				
			elif self.needRepairTime:
				if (self.last_time - tmp_time if self.last_time > tmp_time else
					tmp_time - self.last_time) > 300:
					self.start_time = tmp_time
					self.check_time_jump = True

			self.last_time = tmp_time
			self.end_time = tmp_time
			self.parse_log(resalt.group(2), tmp_time, resalt.group(4), resalt.group(5),resalt.group(6))
		else :

			if re.match(".*--------- beginning of .*", line) :
				self.isBegin = True
			#else :
			#	print("line not match:%s" %line)
	def pid2process(self, pid):
		if pid in self.process_info.keys():
			return self.process_info[pid]
		else:
			return pid
	def parse(self):
		with open(self.path, 'rb') as file_object:
			pos = 0;
			line = []
			while 1:
				line = file_object.readline()
				try :
					msg = line.decode('utf-8')
				except UnicodeDecodeError:
					print("'utf-8' codec can't decode byte %s" %(self.path))
					#file_object.seek(pos+1024, 1)
				#for line in file_object:
				else :
					if len(line) == 0:
						break
					self.parse_line(msg)

	def commit(self):
		print("Vin:%s    time: %s  --- %s" %(self.vin, time.strftime("%Y-%m-%d %H:%M:%S", 
			time.localtime(self.start_time)), time.strftime("%Y-%m-%d %H:%M:%S", 
			time.localtime(self.end_time))))

		print("%s line sum:%d, bytes is:%d" %(os.path.basename(self.path),self.lines, self.bytes))
		self.pid_len_sort = sorted(self.pid_len.items(),key=lambda x:x[1],reverse=True)
		self.tag_len_sort = sorted(self.tag_len.items(),key=lambda x:x[1],reverse=True)
		for key in self.pid_len_sort[:3]:
			print("process:%s len is %d"%(self.pid2process(key[0]), key[1]))
		for key in self.tag_len_sort[:3]:
			print("tag:%s len is %d"%(key[0], key[1]))

		for info in self.crash_infos:
			print(info)
		for error in self.system_errors:
			print(error)
		if len(self.reboot_reason) > 0:
			print("Check reboot reason " + reboot_reason)


class android_log_backup(android_log_file):
	def __init__(self, path):
		super().__init__(path)
		self.backup_pattern = re.compile(r"^S820A-backup-.*-(\d{4}-\d{2}-\d{2}-\d{2}_\d{2}_\d{2}).log")
		resalt = self.backup_pattern.match(os.path.basename(self.path))
		self.file_time = time.strptime(resalt.group(1),"%Y-%m-%d-%H_%M_%S")
		#print(self.file_time)
	def commit():
		print("reserve")


class android_log_dir(common_file):
	def __init__(self, path):
		super().__init__(path)
		self.isExist = os.path.exists(self.path)
		self.files = []
		self.backup_files = []

	def parse(self, debug = None) :
		if not self.isExist:
			return
		files = os.listdir(self.path);
		for file in files:
			if file[0] == '.':
				continue
			if file.find("merge_file_") != -1:
				continue
			elif file.find("backup") != -1:
				backup_file = android_log_backup(self.path + "/" + file)
				backup_file.parse()
				self.backup_files.append(backup_file)
			else :
				log_file = android_log_file(self.path + "/" + file)
				self.files.append(log_file)
				log_file.parse()
				if debug != None:
					if debug.add_log(log_file) != 0:
						print("file %s is not in debug_file" %os.path.basename(log_file.path))
				self.files = sorted(self.files, key=lambda x:x.start_time)
		#for file in self.files:
		#	print("start %d ----file %s", file.start_time, file.path)
			#log_file.commit()
	def fix(self, android_config = None):
		for file in self.files:
			if file.needRepairTime:
				print("FILE %s maybe you need, about time:%s -- %s"
					%(os.path.basename(file.path), time.strftime("%Y-%m-%d %H:%M:%S", 
			time.localtime(file.start_time)), time.strftime("%Y-%m-%d %H:%M:%S", 
			time.localtime(file.end_time))))

	def commit(self): 
		for file in self.files:
			file.commit()

class S820A_log_dir(common_file):
	def __init__(self, path):
		super().__init__(path)
		self.isExist = os.path.exists(self.path)
		self.backup_files = []
		self.line_pattern = re.compile(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}).(\d{3})"
                            + ".*$")
	def parse(self, debug = None) :
		if not self.isExist:
			return
		files = os.listdir(self.path)
		for file in files:
			if file == "Android":
				self.android_dir = android_log_dir(self.path + "/Android")
				self.android_dir.parse(debug)
				print("android")
			elif file.find("backup") != -1:
				backup_file = android_log_backup(self.path + "/" + file)
				backup_file.parse()
				self.backup_files.append(backup_file)
				
				#print(backup_file.start_time)

	def get_android_log_time(self, line):
		#print(line)
		resalt = self.line_pattern.match(line.decode('utf-8'))
		if resalt != None :
			time_string = str(2020) + "-" + resalt.group(1);
			ms = int(resalt.group(2))
			tmp_time = time.mktime(time.strptime(time_string,"%Y-%m-%d %H:%M:%S"))
			#	print(ms, tmp_time)
			return (tmp_time, ms)
		else :
			return (0, 0)

	def get_vald_line(self, obj_r, b_write, obj_w):
		while True:
			log = obj_r.readline()
			if len(log) == 0:
				return (None, (0,0))
			time = self.get_android_log_time(log[:30])
			if b_write and time == (0, 0):
				obj_w.write(log)
			else:
				return (log, time)

	def merge_file(self, android, backups) :
		print("begin meld file %s %s"%(backups, android))
		new_file = os.path.dirname(android) + "/merge_file_" + os.path.basename(android)
		print("BEGING create new_file: " +  new_file)
		with open(new_file, "wb") as new_file_obj:
			with open(android, "rb") as android_obj:
				(android_log, andorid_time) = self.get_vald_line(android_obj, True, new_file_obj)
				for file in backups:
					with open(file, "rb") as backup_obj:
						while True:
							(backup_log, backup_time) = self.get_vald_line(backup_obj, False, None)
							if (backup_time[0] > andorid_time[0] or 
								(backup_time[0] == andorid_time[0] and backup_time[1] > andorid_time[1])) :
								break
						while True:
							if (backup_time[0] > andorid_time[0] or 
								(backup_time[0] == andorid_time[0] and backup_time[1] >= andorid_time[1])):
								new_file_obj.write(android_log)
								(android_log, andorid_time) = self.get_vald_line(android_obj, True, new_file_obj)
								if android_log == None:
									return
							else:
								new_file_obj.write("====".encode('utf-8'))
								new_file_obj.write(backup_log)
								(backup_log, backup_time) = self.get_vald_line(backup_obj, False, None)
								if backup_log == None:
									break
				while android_log != None:
					new_file_obj.write(android_log)
					(android_log, andorid_time) = self.get_vald_line(android_obj, True, new_file_obj)

	def fix(self) :
		for android_log in self.android_dir.files :
			merge_files = []
			for file in self.android_dir.backup_files:
			#print("start:%s end:%s file %s" %(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(file.start_time)), 
			#	time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(file.end_time)), file.path))

			
				#print("-----start:%s end:%s file:%s" %(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(android_log.start_time)), 
				#time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(android_log.end_time)), android_log.path))
				if android_log.start_time > file.end_time or file.start_time > android_log.end_time:
					continue
				merge_files.append(file.path)
			if len(merge_files) != 0:
				self.merge_file(android_log.path, merge_files)
		

	def commit(self) :
		print("reserver")

class sleep_cycle():
	def __init__(self):
		self.files = []
		self.start_time = 0
		self.end_time = 0
		self.pid_len = {}
		self.tag_len = {}
		self.process_info = {}
		self.crash_infos = []
		self.system_errors = []
		self.anr_process = []
		self.reboot_reason = ""

	def add_file(self, file):
		self.files.append([file, None])

	def rename(self, org, new):
		try:
			index = self.files.index(org)
		except ValueError:
			return -1
		else :
			self.files[index] = new
			return 0
	def file_to_str(self):
		filename = ""
		for file in self.files:
			filename = filename + os.path.basename(file[0]).strip() +"\n"
		return filename
	def add_log(self, log):
		for file in self.files:
			if os.path.basename(file[0]) == os.path.basename(log.path):
				file[1] = log
				return 0;
		return -1

	def pre_commit(self):
		for file in self.files:
			if file[0].find("Android") != -1 and file[1] != None:
				if self.start_time == 0 :
					self.start_time = file[1].start_time
				self.end_time = file[1].end_time
				self.pid_len.update(file[1].pid_len)
				self.tag_len.update(file[1].tag_len)
				self.process_info.update(file[1].process_info)
				self.anr_process += file[1].anr_process
				if len(file[1].reboot_reason) > 0:
					self.reboot_reason = file[1].reboot_reason

				for new_crash in  file[1].crash_infos:
					has_merge = 0
					for crash in self.crash_infos:
						if crash.merge(new_crash) == 0:
							has_merge = 1
							break

					if has_merge == 0:
						self.crash_infos.append(new_crash)

				for new_error in file[1].system_errors:
					has_merge = 0
					for error in self.system_errors:
						if error.merge(new_error) == 0:
							has_merge = 1
							break
					if has_merge == 0:
						self.system_errors.append(new_error)

	def time_to_str(self):
		if self.start_time == 0:
			return "New"
		time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)) + " -- "
		time_str += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time))
		if len(self.reboot_reason) > 0:
			time_str += "\n reboot reason "  + self.reboot_reason
		return time_str
	def get_reset_reason(self):
		for file in self.files:
			if file[0].find("MCU") != -1 and file[1] != None:
				return mcu_log_file.reset_reason_to_string(file[1].reset_reason)
		return "None"

	def get_supply_reason(self):
		for file in self.files:
			if file[0].find("MCU") != -1 and file[1] != None:
				return mcu_log_file.supply_reason_to_str(file[1].supply_reason)
		return "None"

class life_cycle():
	def __init__(self):
		self.sleep_cycles = []
		self.files = []
		self.start_time = 0
		self.end_time = 0
		self.bad = "NO"
		self.current_sleep_cycle = sleep_cycle()
		self.sleep_cycles.append(self.current_sleep_cycle)
		self.pid_len = {}
		self.tag_len = {}
		self.process_info = {}
		self.crash_infos = []
		self.system_errors = []
		self.anr_process = []

	def add_file(self, file):
		self.files.append(file)
		self.current_sleep_cycle.add_file(file)

	def set_sleep_flag(self):
		if len(self.current_sleep_cycle.files) == 0:
			self.sleep_cycles.remove(self.current_sleep_cycle)
		self.current_sleep_cycle = sleep_cycle()
		self.sleep_cycles.append(self.current_sleep_cycle)

	def rename(self, org, new):
		try:
			index = self.files.index(org)
		except ValueError:
			return -1
		else :
			self.files[index] = new
			for cycle in self.sleep_cycles:
				if cycle.rename(org, new) == 0:
					return 0
			return 0
	def set_bad(self):
		self.bad = "Yes"

	def add_log(self, log) :
		for sleep in self.sleep_cycles:
			if sleep.add_log(log) == 0:
				return 0
		return -1

	def time_to_str(self):
		if self.start_time == 0:
			return "New"
		time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)) + " -- "
		time_str += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time))
		return time_str

	def pre_commit(self):
		for sleep in self.sleep_cycles:
			sleep.pre_commit()
			if self.start_time == 0 and sleep.start_time != 0:
				self.start_time = sleep.start_time
			if sleep.end_time != 0:
				self.end_time = sleep.end_time
			self.pid_len.update(sleep.pid_len)
			self.tag_len.update(sleep.tag_len)
			self.process_info.update(sleep.process_info)
			self.anr_process += sleep.anr_process
			if len(sleep.reboot_reason) > 0:
					self.reboot_reason = sleep.reboot_reason
			for new_crash in  sleep.crash_infos:
				has_merge = 0
				for crash in self.crash_infos:
					if crash.merge(new_crash) == 0:
						has_merge = 1
						break
				if has_merge == 0:
					self.crash_infos.append(new_crash)

			for new_error in sleep.system_errors:
				has_merge = 0
				for error in self.system_errors:
					if error.merge(new_error) == 0:
						has_merge = 1
						break
				if has_merge == 0:
					self.system_errors.append(new_error)

	def pid2process(self, pid):
		if pid in self.process_info.keys():
			return self.process_info[pid]
		else:
			return pid

	def statistics_to_str(self):
		pid_len_sort = sorted(self.pid_len.items(),key=lambda x:x[1],reverse=True)
		tag_len_sort = sorted(self.tag_len.items(),key=lambda x:x[1],reverse=True)
		txt = ""

		for pid in pid_len_sort[:6]:
			txt += "%s  bytes: %d\n" %(self.pid2process(pid[0]), pid[1])
		txt += "\n"
		for tag in tag_len_sort[:6]:
			txt += "%s  bytes: %d\n" %(tag[0], tag[1])
		return txt

	def system_error_to_str(self):
		error_str = ""
		errors = sorted(self.system_errors, key=lambda x:x.count,reverse=True)
		for error in errors[:6]:
			error_str += "%s count %d\n" %(self.pid2process(error.pid), error.count)
		return error_str

	def crash_to_str(self):
		crash_str = ""
		for crash in self.crash_infos:
			crash_str += str(crash) + "\n"
		for anr in self.anr_process:
			crash_str += "%s ANR\n"%anr
		return crash_str

	def commit(self, list_file = False, statistics = False, wakeup = False, crash = False):
		if self.start_time == 0:
			return
		table = PrettyTable()
		#table.field_names = ["life", "on line", "bad", "file", "reset_reason", "supply_reason"]
		#table.field_names = ["life", "on line", "bad",  "reset_reason", "supply_reason"]
		field = ["(" +self.time_to_str()+")", "bad"]
		if wakeup:
			field.append("reset_reason")
			field.append("supply_reason")
		if list_file:
			field.append("file")
		if statistics:
			field.append("statistics")
			field.append("system.error")
		if crash:
			field.append("crash")
			
		table.field_names = field
		table.align["statistics"] = "l"
		table.align["system.error"] = "l"
		table.align["crash"] = "l"
		#table.align["file"] = "l"
		first = self.sleep_cycles[0]

		#table.add_row([first.time_to_str(), self.bad, #first.file_to_str(),
		#	first.get_reset_reason(), first.get_supply_reason()])
		for sleep in self.sleep_cycles:
			row = [sleep.time_to_str(), self.bad]
			if wakeup:
				row.append(sleep.get_reset_reason())
				row.append(sleep.get_supply_reason())
			if list_file:
				row.append(sleep.file_to_str())
			if statistics:
				if sleep == self.sleep_cycles[0]:
					row.append(self.statistics_to_str())
					row.append(self.system_error_to_str())
				else:
					row.append("--")
					row.append("--")
			if crash:
				if sleep == self.sleep_cycles[0]:
					row.append(self.crash_to_str())
				else:
					row.append("--")

			table.add_row(row)
		print(table)

class debug_file(common_file):
	def __init__(self, path):
		super().__init__(path)
		self.current_life = life_cycle()
		self.lifes = []
		
	def parse(self):
		if not os.path.exists(self.path):
			return
		with open(self.path, "r") as file_object:
			for line in file_object:
				if line == "create id 0\n" :
					if len(self.current_life.files) != 0:
						self.lifes.insert(0, self.current_life)
					self.current_life = life_cycle()

					
				if line.find("create file ") != -1 :
					pos = line.find("all len")
					self.current_life.add_file(line[12:pos-1])

				if line.find("read: unexpected EOF!") != -1:
					self.current_life.set_bad()

				if line.find("power change off!") != -1:
					self.current_life.set_sleep_flag()

				if line.find("rename file") != -1:
					resalt = re.match(r"rename file\s+(.*)\s+->\s+(.*)\n$", line)
					if resalt != None:
						for life in self.lifes:
							if life.rename(resalt.group(1), resalt.group(2)):
								break

			if len(self.current_life.files) != 0:
				self.lifes.insert(0, self.current_life)

	def add_log(self, log):
		for life in self.lifes:
			if life.add_log(log) == 0:
				return 0
		return -1

	def commit(self, list_file = False, statistics = False, wakeup = False, crash = False):
		if list_file == False and statistics == False and wakeup == False and crash == False :
			return

		for life in self.lifes:
			life.pre_commit()
			life.commit(list_file, statistics, wakeup, crash)

class mcu_log_file(common_file):
	line_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\]"
                            + "\^+[A-Z]\^+.*\^\^.*\^\^(.*)")

	def __init__(self, path):
		super().__init__(path)
		self.reset_reason =  -1
		self.supply_reason = -1

	@staticmethod
	def reset_reason_to_string(reason) :
		if reason == 0x06:
			return "mcu cold boot"
		elif reason == 0x09:
			return "Hardware watchdog reset flag"
		elif reason == 0x13:
			return "Soc Request Reset/lcd abnormal reset"
		elif reason == 0x1B:
			return "soc request reset by run error 55 02"
		elif reason == 0x22:
			return "lin key force system reset"
		elif reason == 0x27:
			return "1HZ signal timeout"
		elif reason == 0x28:
			return "wait soc 5501 message timeout reset"
		elif reason == 0x2d:
			return "spi communicate timeout"
		elif reason == 0x2e:
			return "voltage abnormal 5minutes timeout reset"
		elif reason == 0x31:
			return "9v resume"
		elif reason == 0x32:
			return "6v resume"
		elif reason == 0x33:
			return "acc on"
		elif reason == 0x35:
			return "can bus wakeup"
		elif reason == 0x38:
			return "rtc wakeup"
		elif reason == 0x39:
			return "G sensor wakeup"
		elif reason == 0x3A:
			return "4G wakeup"
		elif reason == 0x3c:
			return "soc request ota reset 55 02"
		elif reason == 0x3D:
			return "soc request reset 7X24 hour reset self 5502"
		elif reason == 0x3E:
			return "Soc wakeup"
		return "None"
	@staticmethod
	def supply_reason_to_str(reason):
		if reason == 0x01:
			return "首次上电"
		elif reason == 0x02:
			return "1HZ 信号超时"
		elif reason == 0x03:
			return "Soc 请求重启"
		elif reason == 0x04:
			return "Soc 进入 RAMPDOWN重启"
		elif reason == 0x05:
			return "SPI 发送超时重启"
		elif reason == 0x06:
			return "SPI 握手异常重启"
		elif reason == 0x07:
			return "MCU Watchdog 超时重启"
		elif reason == 0x08:
			return "休眠时等待 SOC POSTONE 消息超时"
		elif reason == 0x09:
			return "休眠时等待 SOC 反馈 PIN 超时"
		elif reason == 0x0A:
			return "连续 10 秒未唤醒SOC 断电";
		elif reason == 0x0B:
			return "6V5 低压关机"
		elif reason == 0x0C:
			return "等待 SOC 5501 消息超时"
		elif reason == 0x0D:
			return "低压等待 SOC5502 消息超时"
		elif reason == 0x0E:
			return "<9V 上电SOC 仍处于激活状态时,断电"
		elif reason == 0x0F:
			return "SOC LCD 异常请求重启,断电"
		return "None"

	def parse(self):
		with open(self.path, "r") as file_object:
			try:
				line = file_object.readline()
				if line == "--------- beginning of mcu\n":
					line = file_object.readline()
			except UnicodeDecodeError:
				print("file error %s" %os.path.basename(self.path))
				return
			resalt = mcu_log_file.line_pattern.match(line)
			if resalt != None:
				state = resalt.group(2)
				if len(state) == 40:
					self.reset_reason = int(state[2:4], 16)
					self.supply_reason = int(state[30], 16)
			else:
				print("not match %s" %line)
	def commit(self):
		table = PrettyTable()
		field = ["reset", "supply"]
		table.field_names = field
		row = [self.reset_reason_to_string(self.reset_reason), self.supply_reason_to_str(self.supply_reason)]
		table.add_row(row)
		print(table)

class mcu_log_dir(common_file):
	def __init__(self, path):
		super().__init__(path)
		self.logs = []

	def parse(self, debug = None):
		files = os.listdir(self.path)
		for file in files:
			if file[0] == ".":
				continue
			mcu_log = mcu_log_file(self.path + "/" + file)
			self.logs.append(mcu_log)
			mcu_log.parse()
			if debug != None:
				if debug.add_log(mcu_log) != 0:
					print("file %s is not in debug_file" %os.path.basename(mcu_log.path))

	def commit(self):
		for log in self.logs:
			log.commit()
		
class M01_log(common_file):
	def __init__(self, path):
		super().__init__(path)
		self.S820A = S820A_log_dir(self.path + S820A_DIR)
		self.debug = debug_file(self.path + DEBUG_FILE)
		self.mcu = mcu_log_dir(self.path + "/HU_MCU")

	def parse(self, debug = None):
		self.debug.parse()
		if len(self.debug.lifes) != 0:
			self.S820A.parse(self.debug)
			self.mcu.parse(self.debug)
		else: 
			#self.S820A.parse()
			self.mcu.parse()
	def commit(self, list_file = False, statistics = False, wakeup = False, crash = False):
		self.debug.commit(list_file, statistics, wakeup, crash)
		#self.S820A.commit()
		#self.mcu.commit()

	def fix(self):
		self.S820A.fix()
		
	

def get_args():
	parse = argparse.ArgumentParser()
	parse.add_argument("-p", "--path", help="Input the log path", required=True)
	parse.add_argument("-f", "--fix", help="Merge backup log", action="store_true")
	parse.add_argument("-l", "--list", help="list the file in time", action="store_true")
	parse.add_argument("-S", "--statistics", help="Output statistics", action="store_true")
	parse.add_argument("-w", "--wakeup", help="Wakeup reason", action="store_true")
	parse.add_argument("-c", "--crash", help="crash info", action="store_true")

	return parse.parse_args();

def check_path(path):
	if os.path.isdir(path):
		if os.path.exists(path + DEBUG_FILE):
			return log_state.STDIO_LOG
		elif  os.path.exists(path + MONKEY_LOG) and os.path.exists(path + MONKEY_LOGCAT):
			return log_state.MONKEY
		#if os.path.exists(path + )
		files = os.listdir(path);
		if len(files) == 0:
			print("Dir is empty!!")
			exit()
		for file in files:
			if file.find("S820A-Android-") != -1:
				return  log_state.ANDROID
			if file == "Android" and os.path.isdir(path +"/Android"):
				return log_state.S820A
		print("Can not find log file....");
		exit()
	else:
		file = os.path.basename(path)
		if file.find("Android") != -1:
			return log_state.ONE_ANDROID
		if file.find("backup") != -1:
			return log_state.ONE_ANDROID
		elif file.find("MCU") != -1:
			return log_state.MCU
		else:
			return log_state.ERROR

def main(argv):
	args = get_args()
	if os.path.exists(args.path) == False:
		print("Path %s not exists" %args.path)
		exit()
	print("!!!!!!!!!!请确认VIN码正确!!!!!!!!!!")
	print("!!!!!!!!!!请确认时间正确!!!!!!!!!!!")
	file_state = check_path(args.path)
	#print(file_state)
	if (file_state == log_state.ONE_ANDROID):
		if args.fix:
			print("One file can not fix!!")
			exit()

		file = android_log_file(args.path);
		file.parse()
		file.commit()

	elif file_state == log_state.ANDROID :
		android_dir = android_log_dir(args.path);
		android_dir.parse()
		if args.fix:
			android_dir.fix()

	elif file_state == log_state.S820A:
		S820A_dir = S820A_log_dir(args.path)
		S820A_dir.parse()
		S820A_dir.commit()
		if args.fix:
			S820A_dir.fix()

	elif file_state == log_state.STDIO_LOG:
		m01 = M01_log(args.path)
		m01.parse()
		m01.commit(args.list, args.statistics, args.wakeup, args.crash)
		if args.fix:
			m01.fix()

	elif file_state == log_state.MCU:
		mcu_log = mcu_log_file(args.path)
		mcu_log.parse()
		mcu_log.commit()

if __name__ == "__main__":
	main(sys.argv)
	
