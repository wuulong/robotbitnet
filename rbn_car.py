# RobotBitNet Car
# Licence: MIT
# Limited memory coding style, doc in the same folder
import radio as ro
import utime as ut
import random as rn
from microbit import display as di
from microbit import button_a,button_b, i2c
import struct

def mymap(x, in_min, in_max, out_min, out_max):
    value = int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)
    if value>= out_max:
        value = out_max -1
    elif value < out_min:
        value = out_min

    return value
#board related
def i2c_init():

    i2c.write(64, struct.pack('>H', 16))
    i2c.write(64, struct.pack('>H', 254 * 256 + 123))
    i2c.write(64, struct.pack('>H', 0))

def motor(Spin, Speed):
    TM1 = int(Speed % 256)
    TM2 = int(Speed / 256)
    CH = (Spin - 1) * 4 + 8
    CH1 = int((CH <<8) + TM1)
    CH2 = int(((CH + 1) <<8) + TM2)
    i2c.write(64, struct.pack('>H', CH1))
    i2c.write(64, struct.pack('>H', CH2))

def move_motor_port(MPort, usevalue):
    if(usevalue>100):
        usevalue = 100
    if(usevalue<-100):
        usevalue = -100
    dir=0
    #MP2 may have bug
    mpid = 13
    if MPort==2:
        usevalue=-usevalue
        mpid = 15

    if usevalue<0:
        usevalue = -usevalue
        dir=1

    usevalue = mymap(usevalue, 0, 100, 0, 4095)

    if dir==0:
        motor(mpid, usevalue)
        motor(mpid+1, 0)
    else:
        motor(mpid, 0)
        motor(mpid+1, usevalue)

def init():
    ro.config(queue=3,address=0x75626972,channel=4,data_rate=ro.RATE_1MBIT)
    ro.on()
    ut.sleep_ms(100)



def tx(did,v):
    txt = "%i:%i:%s" %(lid,did,str(v))
    ro.send(txt)

def txp(did,ty,v):
    if ty==1:
        txt = "1,1,%i,%i" %(ms,cs)
    elif ty==2:
        txt = "1,2,%i,%i,%s" %(ms,cs,v)
    else:
        txt = "1,%i,%s" %(ty,v)

    tx(did,txt)

def gnid(used_ids):#get_new_id
    global ms,mid,lid
    for id in range(1,20):
        if not id in used_ids:
            break
    if id==1:
        lid=1
        ms=1
        mid=1
    else:
        lid=id

def mt():
    global uids,mid
    if not mid in uids:
        mid=0

def find_used_ids():
    used_ids=[]
    t_s = ut.ticks_us()

    while True: # start current measurement
        t_now = ut.ticks_us()
        t_use = ut.ticks_diff(t_now,t_s)
        if 1500000 - t_use <0: # 1.5s
            break
        incoming = ro.receive()
        if incoming:
            items = incoming.split(":")
            if len(items)==3:
                sid = int(items[0])
                if not (sid in used_ids):
                    used_ids.append(sid)
    return used_ids

def wait_start():
    global uids,lid
    while True:
        if button_a.was_pressed():
            di.show("R")
            uids = find_used_ids()
            gnid(uids)
            break



ver = 1
lid = 0
uids = [] #used_ids
ackd = False#ack_received
ms = 0#master_status
cs = 0#cmd_status
mid = 0#master id


init()
i2c_init()
move_motor_port(1,0)
move_motor_port(2,0)


#rbn
cur_num_tx = 0
ur=""
wait_start()
tp = 1 #test_period s
t_tick = int(tp * 1000000)

rt=0.5
send_tick = int(t_tick/rt)
t_l = ut.ticks_us()
cidx=0
lc = 1

while True:
    t_s = ut.ticks_us()
    lu = len(uids)
    #broadcast device exist every test period
    txp(0,2,lu)#compass.heading()
    mt()

    while True: # start current measurement
        t_now = ut.ticks_us()
        t_use = ut.ticks_diff(t_now,t_s)
        if t_tick - t_use <0: # 10s
            break

        t_last = ut.ticks_diff(t_now,t_l)
        if send_tick - t_last <0: # should send
            t_l = t_now
            if ackd:
                cur_num_tx = cur_num_tx+1
            ackd = False
            if lu>0:
                cidx %= lu
                did = uids[cidx]
                #txp(did,20,did)
                txp(did,10,lid)
                cidx +=1

        line = ro.receive()
        if line:
            items = line.split(":")
            if len(items)==3:
                sid,did,value = items
                sid = int(sid)
                did = int(did)
                if not sid in uids:
                    uids.append(sid)

                if sid == lid: # sid collision
                    gnid(uids)

                pvs = value.split(",")

                if did==0:
                    if pvs[0]=="1":
                        if pvs[1]=="1" or pvs[1]=="2":
                            if pvs[2]=="1":
                                mid = sid
                            if mid == sid and pvs[2]=="0":
                                mid = 0
                if did==lid:
                    if pvs[0]=="1":
                        if pvs[1]=="22":
                            di.show("G")
                            px_cmd = int(pvs[2])
                            py_cmd = int(pvs[3])

                            go_value = -(py_cmd-50)*2
                            percent = (px_cmd-50)

                            value1 = go_value-percent
                            value2 = go_value+percent

                            move_motor_port(1,value1)
                            move_motor_port(2,value2)

                del pvs
                del items

    if lc % 5==0:
        if lu>0:
            del uids[0]

    lc +=1
    di.show("R")
