#MbitBot remote control car
#Features:
#   drive mbot by remote microbit
#   current command show on LEDs
#   debug LED flashing when TxRx radio
#   motor values by plotter
#Connection:
#   M1: left motor, M2: right motor
#Usage:
#   start by Button-A: controller, Button-B: car
#   stop by controller: buttom-a
#protocol:
#   integer(2 digit x, 2 digit y), 0-99 map to -50 to 49
#LICENSE: MIT
#Author: WuLung Hsu, wuulong@gmail.com
from microbit import *
import radio

#library
def mymap(x, in_min, in_max, out_min, out_max):
    value = int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)
    if value>= out_max:
        value = out_max -1
    elif value < out_min:
        value = out_min

    return value

#board related
def i2c_init():
    import struct

    buf1=struct.pack('>H', 16)
    buf2=struct.pack('>H', 254 * 256 + 123)
    buf3=struct.pack('>H', 0)
    i2c.write(64, buf1)
    i2c.write(64, buf2)
    i2c.write(64, buf3)
    pass

def motor(Spin, Speed):
    import struct
    TM1 = int(Speed % 256)
    TM2 = int(Speed / 256)
    CH = (Spin - 1) * 4 + 8
    CH1 = int((CH <<8) + TM1)
    CH2 = int(((CH + 1) <<8) + TM2)
    buf1=struct.pack('>H', CH1)
    buf2=struct.pack('>H', CH2)
    i2c.write(64, buf1)
    i2c.write(64, buf2)

#ex: move_motor_port(1,100)
def move_motor_port(MPort, usevalue):
    if(usevalue>100):
        usevalue = 100
    if(usevalue<-100):
        usevalue = -100
    dir=0
    #MP2 may have bug
    if MPort==2:
        usevalue=-usevalue

    if usevalue<0:
        usevalue = -usevalue
        dir=1

    usevalue = mymap(usevalue, 0, 100, 0, 4095)		
	
    port_start = [13,15,11,9]
    if dir==0:
        motor(port_start[MPort-1], usevalue)
        motor(port_start[MPort-1]+1, 0)
    else:
        motor(port_start[MPort-1], 0)
        motor(port_start[MPort-1]+1, usevalue)


def pixel_debug(value):
    value = value % 10
    display.set_pixel(4, 4, value)

def game_acc():
    radio.config(queue=6,address=0x75626972,channel=4,data_rate=radio.RATE_1MBIT)
    radio.on()
    sleep(100)

    while True:
        if button_a.was_pressed(): #Tx, remote controller
            mode=1
            break
        if button_b.was_pressed(): #Rx, Car
            mode=0
            break

    px_cur = 0
    py_cur = 0
    trx_cnt = 0
    if mode == 1: # Controller
        while True:
            if button_a.was_pressed(): #stop and break
                radio.send(str(5050))
                break
            [x,y,z] = accelerometer.get_values()
            px = mymap(x,-1000,1000,0,5)
            py = mymap(y,-1000,1000,0,5)
            print("(%i,%i,%i,%i,%i)"%(x,y,z,px,py))

            if px_cur != px or py_cur != py:
                display.set_pixel(px_cur, py_cur, 0)
            display.set_pixel(px, py, 9)
            px_cur = px
            py_cur = py

            px_cmd = mymap(x,-1000,1000,0,100)
            py_cmd = mymap(y,-1000,1000,0,100)



            cmd = px_cmd *100 + py_cmd

            radio.send(str(cmd))
            trx_cnt +=1
            pixel_debug(trx_cnt)


            sleep(50)
    else: # Car
        i2c_init()
        while True:

            incoming = radio.receive()
            if incoming:
                trx_cnt +=1
                pixel_debug(trx_cnt)
                cmd = int(incoming)
                px_cmd = int(cmd/100)
                py_cmd = cmd % 100

                px = mymap(px_cmd,0,100,0,5)
                py = mymap(py_cmd,0,100,0,5)
                if px_cur != px or py_cur != py:
                    display.set_pixel(px_cur, py_cur, 0)
                display.set_pixel(px, py, 9)

                px_cur = px
                py_cur = py

                go_value = -(py_cmd-50)*2
                percent = (px_cmd-50)

                value1 = go_value-percent
                value2 = go_value+percent

                move_motor_port(1,value1)
                move_motor_port(2,value2)
                print("(%i,%i)" %(value1,value2))


game_acc()