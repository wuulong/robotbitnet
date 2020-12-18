#MoonCar python library
#Features:
#   support MoonCar extension board: motor
#   support RGB-led, color sensor( in V1 )
#LICENSE: MIT
#AUTHOR: WuLung Hsu, wuulong@gmail.com
#VERSION: 0.1
from microbit import *
import neopixel
from random import randint
import struct


def mymap(x, in_min, in_max, out_min, out_max):
    value = int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)
    if value>= out_max:
        value = out_max -1
    elif value < out_min:
        value = out_min
    return value

#board related
# F13 PASS: RGB*8
def rgb_demo(self):
    np = neopixel.NeoPixel(pin12, 8)
    
    while True:
        #Iterate over each LED in the strip
    
        for pixel_id in range(0, len(np)):
            red = randint(0, 60)
            green = randint(0, 60)
            blue = randint(0, 60)

            # Assign the current LED a random red, green and blue value between 0 and 60
            np[pixel_id] = (red, green, blue)

            # Display the current pixel data on the Neopixel strip
            np.show()
            sleep(100)


# F17 PASS: 馬達
def move_motor(num1,num2,num3,num4):
    pin2.write_analog(num1)
    pin8.write_analog(num2)
    pin13.write_analog(num3)
    pin14.write_analog(num4)

# 1: Forward, 2: Back, 3: Left, 4: Right, 5: Stop
def moon_car_go(go_dir,movespeed):
    if movespeed>100:
        movespeed = 100
    if movespeed < 0 :
        movespeed = 0 
    movespeed = int(mymap(movespeed,0,100,0,1023))
    
    if go_dir == 1:
        move_motor(movespeed, movespeed, 0, 0)
    if go_dir == 2:
		move_motor(0, 0, movespeed, movespeed)
    if go_dir == 3:
		move_motor(movespeed, 0, 0, movespeed)
    if go_dir == 4:
		move_motor(0, movespeed, movespeed, 0)
    if go_dir == 5:
        move_motor(0, 0, 0, 0)

#F19 : color sensor, V1 pass. V2(Fail)
def i2c_init():
    buf1=struct.pack('>H', 33276)
    buf2=struct.pack('>H', 32771)
    i2c.write(41, buf1)
    i2c.write(41, buf2)
    sleep(10)

def color_sensor_read():
        #pin11 in button mode, fail
        #pin11.write_digital(0) 
        buf=struct.pack('<B', 178)
        i2c.write(41, buf)
        buf=struct.pack('<B', 179)
        i2c.write(41, buf)
    
        buf=struct.pack('<B', 182)
        i2c.write(41, buf)
        TCS_RED=i2c.read(41,2)
        red=struct.unpack("H",TCS_RED)
    
        buf=struct.pack('<B', 184)
        i2c.write(41, buf)
        TCS_GREEN=i2c.read(41,2)
        green=struct.unpack("H",TCS_GREEN)
    
        buf=struct.pack('<B', 186)
        i2c.write(41, buf)
        TCS_BLUE=i2c.read(41,2)
        blue=struct.unpack("H",TCS_BLUE)
        
        return [int(red[0]),int(green[0]),int(blue[0])]
    



#moon_car_go(5,30)