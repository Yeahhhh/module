#!/usr/bin/env python3

#
# dependencies
#     /proc/stat
#     /proc/meminfo
#     /proc/vmstat
#     /proc/net/dev
#     /proc/diskstats
#
# tested environement
#     Linux 2.6.32
#     Linux 3.16.0
#
# reference
# http://www.brendangregg.com/USEmethod/use-linux.html
#





import argparse
import os
import sys
import time

import datetime
import subprocess
import socket
import numpy


MAX_CPU_FIELDS = 12
MAX_CPU_CORE = 300
MAX_NET_FIELDS = 20
MAX_NET_DEV = 8
MAX_DISK_FIELDS = 16
MAX_DISK_DEV = 64

time_epoch = datetime.datetime.utcfromtimestamp(0)
hostname = socket.gethostname()
output_format = "stdout"  # stdout, influxdb
cpu_vals_old = numpy.zeros((MAX_CPU_CORE, MAX_CPU_FIELDS))
net_dev_vals_old = numpy.zeros((MAX_NET_DEV, MAX_NET_FIELDS))
disk_vals_old = numpy.zeros((MAX_DISK_DEV, MAX_DISK_FIELDS))





# example: t = run_shell("head -n 1 /proc/stat")
def run_shell(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, err) = p.communicate()
    return out


def print_dict(d):
    for key in d.keys():
        print(key, d[key]);


# epoch time
def generate_timetag():
    time_now = datetime.datetime.utcnow()
    a = (time_now - time_epoch).total_seconds()
    return a

def epoch_to_iso8601(epoch):
    a = datetime.datetime.fromtimestamp(epoch).isoformat()
    return a

def epoch_to_myformat(epoch):
    #t = datetime.datetime.fromtimestamp(epoch)
    #a = time.gmtime()
    #a = time.strftime("%Y%m%d.%H.%M.%S", t)
    a = datetime.datetime.fromtimestamp(epoch).strftime("%Y%m%d.%H%M%S")
    return a



def proc_stat_cpu(line, idx):
    d = {} # dictionary

    words = line.split()
    words_n= len(words)
    vals = [0.0] * words_n
    vals_percent = [0.0] * words_n
    vals_sum = 0
    for i in range(1, words_n):
        a = float(words[i])
        delta = a - cpu_vals_old[idx][i]
        cpu_vals_old[idx][i] = a
        vals[i] = delta
        vals_sum += delta
    for i in range(1, words_n):
        vals_percent[i] =  vals[i] / vals_sum * 100.0

    #print("cpu")
    #print(vals)
    #print(vals_percent)
    d["stat_cpu_percent_user"] = vals_percent[1]
    d["stat_cpu_percent_nice"] = vals_percent[2] # low priority user mode
    d["stat_cpu_percent_sys"] = vals_percent[3]
    d["stat_cpu_percent_idle"] = vals_percent[4]
    d["stat_cpu_percent_iowait"] = vals_percent[5]
    d["stat_cpu_percent_irq"] = vals_percent[6] # interrupts
    d["stat_cpu_percent_softirq"] = vals_percent[7]
    d["stat_cpu_percent_steal"] = vals_percent[8] # hosting VM
    d["stat_cpu_percent_guest"] = vals_percent[9] # hosting virtual CPU

    #print_dict(d)
    return d





# processor, process
# man proc "/proc/stat"
# times in "/proc/stat" are monotonically increasing
def proc_stat():
    lines = [] # list
    d = {} # dictionary

    with open("/proc/stat") as f:
        lines = f.readlines()

    idx = 0
    for line in lines:
        idx += 1
        words = line.split()
        words_n = len(words)
        key = words[0]

        #print(line)
        #print(words)
        #print(words_n)

        if words_n == 2:
            val = float(words[1])
            d["stat_" + key] = val
        if (key == "cpu"): # all CPU
            d_cpu = proc_stat_cpu(line, idx)
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

    d["meminfo_percent_Active"] = d["meminfo_Active"] / d["meminfo_MemTotal"] * 100.0
    d["meminfo_percent_MemFree"] = d["meminfo_MemFree"] / d["meminfo_MemTotal"] * 100.0
    d["meminfo_percent_Inactive"] = d["meminfo_Inactive"] / d["meminfo_MemTotal"] * 100.0
    d["meminfo_percent_Cached"] = d["meminfo_Cached"] / d["meminfo_MemTotal"] * 100.0
    d["meminfo_percent_Buffers"] = d["meminfo_Buffers"] / d["meminfo_MemTotal"] * 100.0
    d["meminfo_my_SwapUsed"] = d["meminfo_SwapTotal"] - d["meminfo_SwapFree"]

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


def proc_net_dev():
    lines = [] # list
    d = {} # dictionary

    with open("/proc/net/dev") as f:
        lines = f.readlines()

    idx = 0
    #for line in lines[3:4]: # line 2-3
    for line in lines[2:]: # line 2-3
        idx += 1

        words = line.split()
        words_n = len(words)
        vals = [0.0] * words_n
        device = words[0][:-1]

        #print(idx)
        #print(device)
        #print("old")
        #print(net_dev_vals_old[idx])
        #print("new")
        #print(words)

        for i in range(1, words_n):
            a = float(words[i])
            delta = a - net_dev_vals_old[idx][i]
            net_dev_vals_old[idx][i] = a
            vals[i] = delta


        #print("delta")
        #print(vals)
        #print("record")
        #print("")

        d["net_dev_%s_%s" % (device, "rx_bytes")] = vals[1]
        d["net_dev_%s_%s" % (device, "rx_packets")] = vals[2]
        d["net_dev_%s_%s" % (device, "rx_errs")] = vals[3]
        d["net_dev_%s_%s" % (device, "rx_drops")] = vals[4]
        d["net_dev_%s_%s" % (device, "tx_bytes")] = vals[9]
        d["net_dev_%s_%s" % (device, "tx_packets")] = vals[10]
        d["net_dev_%s_%s" % (device, "tx_errs")] = vals[11]
        d["net_dev_%s_%s" % (device, "tx_drops")] = vals[12]

    #print_dict(d)
    return d



def proc_diskstats():
    lines = [] # list
    d = {} # dictionary

    with open("/proc/diskstats") as f:
        lines = f.readlines()
    idx = 0
    for line in lines:
        idx += 1

        words = line.split()
        words_n = len(words)
        vals = [0.0] * words_n
        device = words[2]

        if (words[0] == '8'):
            for i in range(3, words_n):
                a = float(words[i])
                delta = a - disk_vals_old[idx][i]
                disk_vals_old[idx][i] = a
                vals[i] = delta

            d["diskstats_%s_%s" % (device, "reads_completed_successfully")] = vals[3]
            d["diskstats_%s_%s" % (device, "reads_merged")] = vals[4]
            d["diskstats_%s_%s" % (device, "sectors_read")] = vals[5]
            d["diskstats_%s_%s" % (device, "time_on_reading")] = vals[6] # ms
            d["diskstats_%s_%s" % (device, "writes_completed")] = vals[7]
            d["diskstats_%s_%s" % (device, "writes_merged")] = vals[8]
            d["diskstats_%s_%s" % (device, "sectors_read")] = vals[9]
            d["diskstats_%s_%s" % (device, "time_on_writing")] = vals[10] # ms
            d["diskstats_%s_%s" % (device, "io_progress")] = vals[11]
            d["diskstats_%s_%s" % (device, "time_on_io")] = vals[12] # ms
            d["diskstats_%s_%s" % (device, "weighted_time_on_io")] = vals[12] # ms

    #print_dict(d)
    return d




def format_stdout(d,keys):
    t = generate_timetag()
    line = "%.3f\n" % t
    line += "%s\n" % epoch_to_myformat(t)
    for key in keys:
        line += "%50s\t\t%13.3f" % (key, d[key])
        if "percent" in key:
            line += " %"
        elif "meminfo" in key:
            line += " MB"
        line += "\n"
    return line



def format_influxdb(d, keys):
    t = generate_timetag()
    line = "%s," % "syssampling"
    line += "hostname=%s " % hostname
    for key in keys:
        line += "%s=%.3f," % (key, d[key])
    line += "time_tag=%s " % epoch_to_myformat(int(t))
    line += "%d" % (int(t * 1000.0) * 1000000)
    return line

def my_print(d, keys):
    line = format_stdout(d,keys)
    #line = format_influxdb(d,keys)
    print(line)



def send_sample_to_influxdb(d, keys):
    host="us-aus-stormon1.austin.arm.com"
    port="8086"
    db_name="yeah"

    line = format_influxdb(d,keys)
    cmd = "curl -i -XPOST 'http://%s:%s/write?db=%s' --data-binary '%s'" \
            % (host, port, db_name, line)
    #print(cmd)
    os.system(cmd)


def send_file_to_influxdb(fn):
    host="us-aus-stormon1.austin.arm.com"
    port="8086"
    db_name="yeah"

    cmd = "curl -i -XPOST 'http://%s:%s/write?db=%s' --data-binary @%s" \
            % (host, port, db_name, fn)
    #print(cmd)
    os.system(cmd)




def sampling():
    d_stat = proc_stat()
    d_meminfo = proc_meminfo()
    d_vmstat = proc_vmstat()
    d_net_dev = proc_net_dev()
    d_diskstats = proc_diskstats()
    d_dummy = {"dummy" : 0.0}
    d = dict(d_stat.items() | \
            d_meminfo.items() | \
            d_vmstat.items() | \
            d_net_dev.items() | \
            d_diskstats.items() | \
            d_dummy.items())

    keys = ["stat_cpu_percent_user",
            "stat_cpu_percent_nice",
            "stat_cpu_percent_sys",
            "stat_cpu_percent_iowait",
            "stat_cpu_percent_idle",
            "stat_procs_running",
            "stat_procs_blocked", # procs blocked waiting for I/O

            "meminfo_Active", # active RAM
            "meminfo_Inactive", # inactive RAM
            "meminfo_MemFree",
            "meminfo_my_SwapUsed",

            "meminfo_Cached",  # page cache
            "meminfo_Buffers", # buffer cache
            "meminfo_SwapCached",  # swap cache
            "meminfo_Mapped", # mmap()

            "meminfo_Dirty", #
            "meminfo_Writeback", #

            "meminfo_percent_Active",
            "meminfo_percent_Inactive",
            "meminfo_percent_MemFree",
            "meminfo_percent_Cached",
            "meminfo_percent_Buffers",

            "net_dev_lo_rx_bytes",
            "net_dev_lo_rx_packets",
            #"net_dev_lo_rx_errs",
            #"net_dev_lo_rx_drops",
            "net_dev_lo_tx_bytes",
            "net_dev_lo_tx_packets",
            #"net_dev_lo_tx_errs",
            #"net_dev_lo_tx_drops",

            "net_dev_eth0_rx_bytes",
            "net_dev_eth0_rx_packets",
            #"net_dev_eth0_rx_errs",
            #"net_dev_eth0_rx_drops",
            "net_dev_eth0_tx_bytes",
            "net_dev_eth0_tx_packets",
            #"net_dev_eth0_tx_errs",
            #"net_dev_eth0_tx_drops",

            "diskstats_sda_reads_completed_successfully",
            "diskstats_sda_reads_merged",
            "diskstats_sda_sectors_read",
            "diskstats_sda_time_on_reading",
            "diskstats_sda_writes_completed",
            "diskstats_sda_writes_merged",
            "diskstats_sda_sectors_read",
            "diskstats_sda_time_on_writing",
            #"diskstats_sda_io_progress",
            "diskstats_sda_time_on_io",
            "diskstats_sda_weighted_time_on_io",

            "dummy"
            ]
    #print_dict(d)
    #print(d.items())
    if (output_format == "stdout"):
        my_print(d, keys)
    line = format_influxdb(d, keys)
    return line



def main_stdout():
    while 1:
        sample = sampling()
        time.sleep(0.2) # seconds


def main_influxdb():
    #sampling()

    samples = []
    out_fn = "/tmp/a.py.influxdb_request"

    while 1:
        for i in range(0, 100):
            sample = sampling()
            samples.append(sample)
            time.sleep(0.1) # seconds

        samples = "\n".join(samples)
        with open(out_fn, "w") as f:
            f.write(samples)
        send_file_to_influxdb(out_fn)
        samples = []




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = "sample system status"
        )
    parser.add_argument(
        "-m",
        "--mod",
        default = "stdout",
        type = str,
        help = "stdout / influxdb"
        )
    args = parser.parse_args()

    if (len(sys.argv[1:]) == 0):
        output_format = "stdout"
        main_stdout()
    else:
        output_format = args.mod
        if (output_format == "stdout"):
            main_stdout()
        elif (output_format == "influxdb"):
            main_influxdb()
        else:
            parser.print_help()
            parser.exit()



