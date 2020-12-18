# RobotBitNet
# Licence: MIT
# Limited memory coding style, doc in the same folder
import radio as ro
import utime as ut
import random as rn
from microbit import display as di
from microbit import button_a,button_b,compass, uart

lid = 0
ack = "~"
txc = 0#tx_cnt
rxc = 0#rx_cnt
uids = [] #used_ids
uidsn = [] #used_ids_next
ackd = False#ack_received
ms = 0#master_status
cs = 0#cmd_status
mid = 0#master id

def init():
    uart.init(115200)
    ro.config(queue=6,address=0x75626972,channel=4,data_rate=ro.RATE_1MBIT)
    ro.on()
    ut.sleep_ms(100)



def tx(did,v):
    global txc
    txc += 1
    txt = "%i:%i:%s" %(lid,did,str(v))
    ro.send(txt)
    print("T=%s" %(txt))
    leds(1,txc)

def txp(did,ty,v):
    if ty==1:
        txt = "1,1,%i,%i" %(ms,cs)
    if ty==2:
        txt = "1,2,%i,%i,%s" %(ms,cs,v)
    if ty==20:
        txt = "1,20,%s" %(v)

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
            di.show("F")
            uids = find_used_ids()
            gnid(uids)
            break

def show_id():
    di.clear()

    for id in uids:
        if id>0:
            uid = id - 1
            di.set_pixel(uid%5,int(uid/5),2)

    uid = lid - 1
    di.set_pixel(uid%5,int(uid/5),5)

    id = mid
    if id>0:
        uid = id-1
        di.set_pixel(uid%5,int(uid/5),9)

def leds(part,va):#pixel_debug
    va = va % 10
    if part==1: # tx
        va = va *3 % 10
        di.set_pixel(4, 4, va)
    elif part==0:# rxc
        di.set_pixel(0, 4, va)
    elif part==2:#master
        di.set_pixel(3, 4, va)
    else: #3 Rx
        va = va % 30
        for i in range(3):
            if va >=9:
                di.set_pixel(i, 4, 9)
            elif va<0:
                di.set_pixel(i, 4, 0)
            else:
                di.set_pixel(i, 4, va)
            va -=10
def leds_br():
    if ms==1:
        leds(2,9)
    elif mid>0:
        leds(2,5)
    else:
        leds(2,0)


init()

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
    rxc = 0
    txc = 0
    t_s = ut.ticks_us()
    lu = len(uids)
    #broadcast device exist every test period
    txp(0,2,lu)#compass.heading()
    mt()
    show_id()
    leds_br()
    

    while True: # start current measurement
        t_now = ut.ticks_us()
        t_use = ut.ticks_diff(t_now,t_s)
        if t_tick - t_use <0: # 10s
            if lc % 5==0:
                uids = uidsn
                uidsn = []
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
                txp(did,20,did)
                cidx +=1
        """        
        if uart.any():
            rl= uart.readline()
            if rl:
                di.set_pixel(0, 3, 9)
                b1 = str(rl, 'UTF-8')
                ur += b1.strip()
                pos = ur.find("=")
                if pos>=0:
                    ro.send(ur[:pos])
                    ur = ""
                #leds(0,txc)
                    #print("U=%s" % ur[:-pos])
                    #ur = ur[pos+1:]
            #print("3")
        """
        incoming = ro.receive()
        if incoming:
            rxc+=1
            items = incoming.split(":")
            if len(items)==3:

                sid,did,value = items
                sid = int(sid)
                did = int(did)
                if not sid in uids:
                    uids.append(sid)

                if not sid in uidsn:
                    uidsn.append(sid)

                if sid == lid: # sid collision
                    gnid(uids)


                if did == lid:
                    if value == ack:
                        ackd = True
                    else:
                        tx(sid,ack)
                print("R=%s" %(incoming))
                pvs = value.split(",")

                if did==0:
                    if pvs[0]=="1":
                        if pvs[1]=="1" or pvs[1]=="2":
                            if pvs[2]=="1":
                                mid = sid
                            if mid == sid and pvs[2]=="0":
                                mid = 0
                        if pvs[1]=="2":
                            #print("(sid=%i,%s)" % (sid,pvs[4]))
                            if lid-sid==1:
                                pass

                if did==lid:
                    if pvs[0]=="1":
                        if pvs[1]=="20": #action
                            di.show(pvs[2])


                del pvs
                del items

            leds(0,rxc)
        if button_b.was_pressed():
            ms^=1
            if ms == 1:
                mid=lid
            else:
                mid=0

    lc +=1
    #print("%i,%i" %(lid,mid))


