#!/usr/bin/env python

import sys
import socket
import threading
import struct
import time
from scipy import signal
import iir_filter
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import json
import zmq

mutex = [threading.Lock(), threading.Lock()]
mutex2 = [threading.Lock(), threading.Lock()]
g_wrench_l = [0, 0, 0, 0, 0, 0]
g_wrench_r = [0, 0, 0, 0, 0, 0]
bias_flag_l = 0
bias_flag_r = 0
sndToPlot = False

def list_to_setp(setp, list):
	for i in range(0,6):
		setp.external_force_torque[i] = list[i]
	return setp

def t_rtde(ip, rbindex):
    ROBOT_HOST = ip
    ROBOT_PORT = 30004
    config_filename = 'set_external_wrench.xml'
    conf = rtde_config.ConfigFile(config_filename)
    state_names, state_types = conf.get_recipe('state')
    setp_names, setp_types = conf.get_recipe('setp')
    watchdog_names, watchdog_types = conf.get_recipe('watchdog')
    frequencyset=500
    con = rtde.RTDE(ROBOT_HOST, ROBOT_PORT)
    con.connect()
    print('UR_connetok')
    con.get_controller_version()
    con.send_output_setup(state_names, state_types,frequency = frequencyset)
    setp = con.send_input_setup(setp_names, setp_types)
    watchdog = con.send_input_setup(watchdog_names, watchdog_types)
    setp.external_force_torque = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    watchdog.input_int_register_0 = 0
    if not con.send_start():
        print('RTDE con fail')
        sys.exit()
    while True:
        state = con.receive()
        if state is None:
            print('RTDE con fail')
            break
        mutex[rbindex].acquire()
        if rbindex == 0:
            global g_wrench_l
            wrench_filtered = g_wrench_l
        else:
            global g_wrench_r
            wrench_filtered = g_wrench_r
        mutex[rbindex].release()
        list_to_setp(setp, wrench_filtered)
        con.send(setp)
        con.send(watchdog)
	
    con.send_pause()
    print('RTDE pause')
    con.disconnect()
    print('RTDE discon')
    
def t_udp(port, rbindex):
    if sndToPlot == True:
        if port == 8886:
            contttt = zmq.Context()
            sockkk = contttt.socket(zmq.PUB)
            sockkk.bind('tcp://192.168.1.100:9871')
    bias = [0, 0, 0]
    sos1 = signal.cheby1(4, 0.5, [56.6, 76.6], 'bandstop', output='sos', fs=1000)
    sos2 = signal.cheby1(4, 0.5, 33, 'lowpass', output='sos', fs=1000)
    iir1 = []
    iir2 = []
    for i in range(6):
        iir1.append(iir_filter.IIR_filter(sos1))
        iir2.append(iir_filter.IIR_filter(sos2))

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('192.168.1.100', port))
    #b'\x51\xaa\x0d\x0a' 切换查询发送和持续发送模式
    t1 = time.time()
    rcv_buf = bytearray()
    while True:
        data = s.recv(1024)
        rcv_buf += data
        if len(rcv_buf) < 28:
            continue
        if (len(rcv_buf) == 28 and rcv_buf[0] == 0x48 and rcv_buf[1] == 0xaa and rcv_buf[26] == 0x0d and rcv_buf[27] == 0x0a) == False:
            print('data error:', len(rcv_buf), rcv_buf)
            rcv_buf = bytearray()
            continue
        wrench = [0,0,0,0,0,0]
        wrench_filtered = []
        for i in range(6):
            raw = rcv_buf[2+i*4 : 6+i*4]
            raw.reverse()
            wrench[i] = struct.unpack("!f", raw)[0] * 9.8
        if sndToPlot == True:
            if port == 8886:
                data = {'wrench': [wrench[0], wrench[1], wrench[2], wrench[3], wrench[4], wrench[5]]}
                sockkk.send_string(json.dumps(data))
        for i in range(6):
            wrench_filtered.append(iir2[i].filter(iir1[i].filter(wrench[i])))
            # wrench_filtered.append(wrench[i])
        mutex2[rbindex].acquire()
        if rbindex == 0:
            global bias_flag_l
            tmp_flag = bias_flag_l
            bias_flag_l = 0
        else:
            global bias_flag_r
            tmp_flag = bias_flag_r
            bias_flag_r = 0
        mutex2[rbindex].release()
        if tmp_flag == 1:
            bias[0] = -wrench_filtered[0]
            bias[1] = -wrench_filtered[1]
        if tmp_flag == 2:
            bias[2] = -wrench_filtered[2]
        if tmp_flag != 0:
            print(port, bias)
        wrench_filtered[0] += bias[0]
        wrench_filtered[1] += bias[1]
        wrench_filtered[2] += bias[2]
        # if port == 8885:
        #     print('{:0.3f}'.format(wrench_filtered[0]), '{:0.3f}'.format(wrench_filtered[1]), '{:0.3f}'.format(wrench_filtered[2]))
        mutex[rbindex].acquire()
        if rbindex == 0:
            global g_wrench_l
            g_wrench_l = wrench_filtered
        else:
            global g_wrench_r
            g_wrench_r = wrench_filtered
        mutex[rbindex].release()
        # print((time.time() - t1) * 1000)
        t1 = time.time() 
        rcv_buf = bytearray()
        
def t_cali_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server.bind(('127.0.0.1', 8680))
    server.listen(128)
    while True:
        client, addr = server.accept()
        th = threading.Thread(target=t_cali_subthread, args=(client, addr))
        th.setDaemon(True)
        th.start()
    server.close()
        
def t_cali_subthread(client, addr):
    rcv_cnt = 0
    while rcv_cnt < 2:
        raw = client.recv(1024)
        if len(raw) == 0:
            break
        msg = raw.decode()
        rcv_cnt = rcv_cnt + 1
        if msg == 'cali_xy_l' or msg == 'cali_z_l':
            mutex2[0].acquire()
            global bias_flag_l
            if msg == 'cali_xy_l':
                bias_flag_l = 1
            if msg == 'cali_z_l':
                bias_flag_l = 2
            mutex2[0].release()
        if msg == 'cali_xy_r' or msg == 'cali_z_r':
            mutex2[1].acquire()
            global bias_flag_r
            if msg == 'cali_xy_r':
                bias_flag_r = 1
            if msg == 'cali_z_r':
                bias_flag_r = 2
            mutex2[1].release()
    client.close()
        
tudp0 = threading.Thread(target=t_udp, args=(8886, 0))
tudp0.setDaemon(True)
tudp0.start()

tudp1 = threading.Thread(target=t_udp, args=(8885, 1))
tudp1.setDaemon(True)
tudp1.start()

tcali = threading.Thread(target=t_cali_server, args=())
tcali.setDaemon(True)
tcali.start()

trtde = threading.Thread(target=t_rtde, args=('192.168.1.102', 0))
trtde.setDaemon(True)
trtde.start()
t_rtde('192.168.1.101', 1)
