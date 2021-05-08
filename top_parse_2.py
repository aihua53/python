#!/usr/bin/python3.5
import sys
import matplotlib.pyplot as plt
import sys
import argparse
import os
from enum import Enum
import re
import time
from prettytable import PrettyTable
import numpy as np

cpu_user = [];
cpu_sys = [];
cpu_idle = [];
cpu_io = [];
cpu_irq = [];

cpu_all = {}
total_only = False
pid_only = []
count = -1;
level = 2
dic = []
class process_info:
    def __init__(self, name, pid):
        self.name = name
        self.pid = pid

def parse_total(total):
	backup_pattern = re.compile(r"400%cpu\s+(\d+)%user\s+(\d+)%nice\s+(\d+)%sys\s+(\d+)%idle\s+(\d+)%iow\s+(\d+)%irq\s+(\d+)%sirq\s+(\d+)%host.*")
	result = backup_pattern.search(total)
	global count
	count +=1
	if result != None:
		cpu_user.append(int(result.group(1)))
		cpu_sys.append(int(result.group(3)))
		cpu_idle.append(int(result.group(4)))
		cpu_irq.append(int(result.group(6)))

	else:
		print("not match",total)

def parse(path):
	global cpu_all, count, dic
	backup_pattern = re.compile(r"400%cpu\s+(\d+)%user\s+(\d+)%nice\s+(\d+)%sys\s+(\d+)%idle\s+(\d+)%iow\s+(\d+)%irq\s+(\d+)%sirq\s+(\d+)%host.*")
	filereader = open(path, "r");
	for row in filereader:
		if row.find("cpu") != -1:
			#print(row)
			row = row.strip('\n');
			str.rstrip(' ')
			parse_total(row)
		elif row.find("TIME+") != -1 or row.find("Tasks") != -1:
			continue
		else:
			row = row.strip('\n');
			res = list(filter(None,row.split(" ")))
			if len(res) > 10:
				print(res[0],res[8],res[11])
				if len(pid_only) != 0 and res[0] not in pid_only:
					continue
				if res[0] not in cpu_all.keys():
					cpus = []
					if count != 0:
						for i in range(count):
							cpus.insert(i, 0)
					cpus.insert(count, float(res[8]))
					info = process_info(res[11], res[0])
					info.cpus = cpus
					cpu_all.update({res[0]:info})
				else:
					if len(cpu_all[res[0]].cpus) < count:
						for i in range(len(cpu_all[res[0]].cpus), count):
							cpu_all[res[0]].cpus.insert(i, 0)
					cpu_all[res[0]].cpus.insert(count, float(res[8]))

	dic = sorted(cpu_all.items(), key = lambda kv:max(kv[1].cpus), reverse = True)
	for i in dic:
		print("pid",i[0],len(i[1].cpus))
		if len(i[1].cpus) < (count + 1):
			for j in range(len(i[1].cpus), count+1):
							i[1].cpus.insert(j, 0)
		
		print(i[1].cpus)
		print(len(i[1].cpus),"avg, ",np.mean(i[1].cpus))

def get_args():
 	parse = argparse.ArgumentParser()
 	parse.add_argument("-p", "--path", help="Input the log path", required=True)
 	parse.add_argument("-t", "--total_only", help="total_only", action="store_true")
 	parse.add_argument("-l", "--level", help="min level for cpu defalt 2%")
 	parse.add_argument("-T", "--pid", help="only this pid a,b,c")
 	return parse.parse_args();

def parse_pids(pids):
	global pid_only
	listpid = pids.split(',')
	for i in listpid:
		pid_only.append(i)
	print(pid_only)

def main(argv):
	global total_only, pid_only, level
	args = get_args()
	if os.path.exists(args.path) == False:
		print("Path %s not exists" %args.path)
		exit()
	if args.total_only == True:
		total_only = True
	if args.pid != None:
		parse_pids(args.pid)
	if args.level != None:
		level = int(args.level)
	parse(args.path)

def show():
	plt.style.use('ggplot')
	compare_list = []
	fig = plt.figure()
	count_will_show = 0
	count_panal = 1;
	if total_only != True:
		for i in dic:
			if max(i[1].cpus) >= level:
				count_will_show+=1
			else :
				break
		count_panal =  int(count_will_show/5)
		if count_panal%5 != 0:
			count_panal += 1
		count_panal +=1
		print("total %d will show %d count_panal %d"%(len(dic),count_will_show, count_panal))
	b = range(count + 1)
	ax1 = fig.add_subplot(3,1,1)
	ax1.plot(b, cpu_idle, 'g--', b, cpu_user, 'r--',  b, cpu_sys, 'c--')
	print("name is idle, Max %.1f, Min %.1f, avg %.1f"%(max(cpu_idle),
					min(cpu_idle), np.mean(cpu_idle)))
	print("name is user, Max %.1f, Min %.1f, avg %.1f"%(max(cpu_user),
					min(cpu_user), np.mean(cpu_user)))
	print("name is sys, Max %.1f, Min %.1f, avg %.1f"%(max(cpu_sys),
					min(cpu_sys), np.mean(cpu_sys)))
	#ax1.axis([0,400])
	ax1.legend(("idle", "user", "sys"), loc='upper right')
	ax1.set_yticks(np.linspace(0,300,10))
	rect1 = [0.14, 0.35, 0.77, 0.6]
	#ax1.set_figheight(200)
	if count_panal == 1:
		count_panal +=1
	for i in range(0, count_panal-1):
		if int(i+2)%3 == 1:
			fig = plt.figure()
		ax = fig.add_subplot(3,1,(i+1)%3 +1)
		name_list = []
		for j in range(5):
			if i*5 + j  <  len(dic):
				compare_list.append(dic[i*5 + j][0])
				if j == 0:
					ax.plot(b, dic[i*5][1].cpus, 'g--')
					name_list.append((dic[i*5][1].name))
				elif j == 1:
					ax.plot(b, dic[i*5+1][1].cpus, 'r--')
					name_list.append((dic[i*5 +1][1].name))
				elif j == 2:
					ax.plot(b, dic[i*5+2][1].cpus, 'c--')
					name_list.append((dic[i*5 +2][1].name))
				elif j == 3:
					ax.plot(b, dic[i*5+3][1].cpus, 'b--')
					name_list.append((dic[i*5 +3][1].name))
				elif j == 4:
					ax.plot(b, dic[i*5+4][1].cpus, 'y--')
					name_list.append((dic[i*5 +4][1].name))
				print("name is %s,pid is %s Max %.1f, Min %.1f, avg %.1f"%(dic[i*5 + j][1].name, dic[i*5 + j][1].pid, max(dic[i*5 + j][1].cpus),
					min(dic[i*5 + j][1].cpus), np.mean(dic[i*5 + j][1].cpus)))
		print(name_list)
		ax.legend(tuple(name_list), loc='upper right')
		#ax.plot(b, dic[i*5][1].cpus, 'g--', b, dic[i*5 +1][1].cpus, 'r--',  b, dic[i*5 + 2][1].cpus
		#	, 'c--', b, dic[i*5 + 3][1].cpus, 'b--', b, dic[i*5 + 4][1].cpus, 'y--')
		#ax.legend((dic[i*5][1].name, dic[i*5 +1 ][1].name, dic[i*5 +2 ][1].name, dic[i*5 +3][1].name, dic[i*5 +4][1].name), loc='upper right')
		#ax1.set_yticks(np.linspace(min(cpu_idle),max(cpu_idle),5))
	#ax2 = fig.add_subplot(3,1,2)
	#ax3 = fig.add_subplot(3,1,3)
	#b = []
	#for i in range(len(cpu_user)):
	#	b.append(i)
	#ax1.set_ylim(min(cpu_idle),max(cpu_idle))
	#ax1.set_xlim(0,len(cpu_idle))
	#ax1.set(ylim =(min(cpu_idle), max(cpu_idle)), xlim =(0, len(cpu_idle)), 
    #           autoscale_on = False)
	#ax1.set_yticks(np.linspace(min(cpu_idle),max(cpu_idle),5))
	#ax1.plot(b, cpu_idle, "b-")
	#ax2.set_ylim(0,200)
	#ax3.set_ylim(0,300)

	#plt.yticks([1, 200, 400])
	#fig.subplots_adjust(wspace=5, hspace=5)
	#ax2.set_yticks(0,200)
	
	#ax1.plot(cpu_sys)
	#ax1.plot(cpu_idle)
	
	compare_list = sorted(compare_list, key=lambda x:int(x))
	for i in compare_list:
		print("name is %s,pid is %s Max %.1f, Min %.1f, avg %.1f"%(cpu_all[i].name, cpu_all[i].pid, max(cpu_all[i].cpus),
					min(cpu_all[i].cpus), np.mean(cpu_all[i].cpus)))
	plt.show()

if __name__ == "__main__":
	main(sys.argv)
	
	#print(cpu_all)
	show()