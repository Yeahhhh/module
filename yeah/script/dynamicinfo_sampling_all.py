#!/usr/bin/env python3

#
# sample system status
# generate input data for InfluxDB
#
# dependencies
#     /proc/stat
#     /proc/meminfo
#     /proc/vmstat
#
# tested environement
#     Linux 2.6.32
#     Linux 3.16.0
#
# reference
# http://www.brendangregg.com/USEmethod/use-linux.html



import time
import datetime
import subprocess
import socket


time_epoch = datetime.datetime.utcfromtimestamp(0)
hostname = socket.gethostname()


# example: t = run_shell("head -n 1 /proc/stat")
def run_shell(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, err) = p.communicate()
    return out


def print_dict(d):
    for key in d.keys():
        print(key, d[key]);


def generate_timetag():
    time_now = datetime.datetime.utcnow()
    a = (time_now - time_epoch).total_seconds()
    return a


def proc_stat_cpu(line):
    d = {} # dictionary

    words = line.split()
    words_n= len(words)
    times = [None] * words_n
    times_percent = [None] * words_n
    times_sum = 0
    for i in range(1, words_n - 2):
        a = float(words[i])
        times[i] = a
        times_sum += a
    for i in range(1, words_n - 2):
        times_percent[i] =  times[i] / times_sum * 100.0
    #print(times)
    #print(times_percent)
    d["stat_cpu_percent_user"] = times_percent[1]
    d["stat_cpu_percent_nice"] = times_percent[2] # low priority user mode
    d["stat_cpu_percent_sys"] = times_percent[3]
    d["stat_cpu_percent_idle"] = times_percent[4]
    d["stat_cpu_percent_iowait"] = times_percent[5]
    d["stat_cpu_percent_irq"] = times_percent[6] # interrupts
    d["stat_cpu_percent_softirq"] = times_percent[7]
    d["stat_cpu_percent_steal"] = times_percent[8] # hosting VM
    d["stat_cpu_percent_guest"] = times_percent[9] # hosting virtual CPU

    #print_dict(d)
    return d





# processor, process
# man proc "/proc/stat"
def proc_stat():
    lines = [] # list
    d = {} # dictionary

    with open("/proc/stat") as f:
        lines = f.readlines()

    for line in lines:
        words = line.split()
        words_n= len(words)
        key = words[0]

        #print(line)
        #print(words)
        #print(words_n)

        if words_n == 2:
            val = float(words[1])
            d["stat_" + key] = val
        if (key == "cpu"): # all CPU
            d_cpu = proc_stat_cpu(line)
            d = dict(d.items() | d_cpu.items())

    #print_dict(d)
    return d


def proc_meminfo():
    lines = [] # list
    d = {} # dictionary

    with open("/proc/meminfo") as f:
        lines = f.readlines()
    for line in lines:
        words = line.split()
        key = "meminfo_" + words[0][:-1]
        val = float(words[1]) / 1000.0  # in MB
        d[key] = val

    d["meminfo_percent_MemFree"] = d["meminfo_MemFree"] / d["meminfo_MemTotal"]
    d["meminfo_percent_Active"] = d["meminfo_Active"] / d["meminfo_MemTotal"]
    d["meminfo_percent_Inactive"] = d["meminfo_Inactive"] / d["meminfo_MemTotal"]

    #print_dict(d)
    return d



def proc_vmstat():
    lines = [] # list
    d = {} # dictionary

    with open("/proc/vmstat") as f:
        lines = f.readlines()
    for line in lines:
        words = line.split()
        key = "vmstat_" + words[0]
        val = float(words[1])
        d[key] = val

    #print_dict(d)
    return d




def print_stdout(d,keys):
    line = "%.3f\n" % generate_timetag()
    for key in keys:
        line += "%30s\t\t%.3f\n" % (key, d[key])
    print(line)


def print_influxdb(d, keys):
    line = "%s," % "syssampling"
    for key in keys:
        line += "%s=%.3f," % (key, d[key])
    line += "hostname=%s " % hostname
    line += "value=0 "
    line += "%.3f" % generate_timetag()
    print(line)



def sampling():
    d_stat = proc_stat()
    d_meminfo = proc_meminfo()
    d_vmstat = proc_vmstat()
    d = dict(d_stat.items() | d_meminfo.items() | d_vmstat.items())

    keys = ["stat_cpu_percent_user",
            "stat_cpu_percent_nice",
            "stat_cpu_percent_sys",
            "stat_cpu_percent_iowait",
            "stat_cpu_percent_idle",
            "stat_procs_running",
            "stat_procs_blocked", # procs blocked waiting for I/O
            "meminfo_MemFree",
            "meminfo_Buffers",
            "meminfo_Cached",
            "meminfo_Active",
            "meminfo_percent_MemFree",
            "meminfo_percent_Active",
            "meminfo_percent_Inactive"
            ]
    #print_dict(d)
    #print(d.items())
    print_stdout(d, keys)
    #print_influxdb(d, keys)





def main():
    #sampling()

    while 1:
        sampling()
        time.sleep(0.5) # seconds


if __name__ == "__main__":
    main()


