from oled.fonts import ubuntu_mono_15, ubuntu_mono_20
from oled import Write, GFX, SSD1306_I2C
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import framebuf
import math

from machine import Pin, I2C
import utime
import binascii


#----------Temp From Picos Onboard Sensor-----------#
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)


#----------OLED-------------#
i2c_2=I2C(1,sda=Pin(14), scl=Pin(15), freq=600000)
oled = SSD1306_I2C(128, 64, i2c_2)
oled.contrast(1)                                                    # Brightness

#Fonts
write15 = Write(oled, ubuntu_mono_15)
write20 = Write(oled, ubuntu_mono_20)

# Clear the oled display in case it has junk on it.
oled.fill(0)

print("I2C Address of OLED      : "+hex(i2c_2.scan()[0]).upper())   # Display device address
print("I2C Configuration: "+str(i2c_2))                             # Display I2C config

#---------RTC------------#
I2C_PORT = 0
I2C_SDA = 0
I2C_SCL = 1

class ds3231(object):
#            13:45:00 Mon 24 May 2021
#  the register value is the binary-coded decimal (BCD) format
#               sec min hour week day month year

    NowTime = b'\x00\x45\x13\x02\x24\x05\x21'
    w  = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
    address = 0x68
    start_reg = 0x00
    alarm1_reg = 0x07
    control_reg = 0x0e
    status_reg = 0x0f
    
    def __init__(self,i2c_port,i2c_scl,i2c_sda):
        self.bus = I2C(i2c_port,scl=Pin(i2c_scl),sda=Pin(i2c_sda))

    def set_time(self,new_time):
        hour = new_time[0] + new_time[1]
        minute = new_time[3] + new_time[4]
        second = new_time[6] + new_time[7]
        week = "0" + str(self.w.index(new_time.split(",",2)[1])+1)
        year = new_time.split(",",2)[2][2] + new_time.split(",",2)[2][3]
        month = new_time.split(",",2)[2][5] + new_time.split(",",2)[2][6]
        day = new_time.split(",",2)[2][8] + new_time.split(",",2)[2][9]
        now_time = binascii.unhexlify((second + " " + minute + " " + hour + " " + week + " " + day + " " + month + " " + year).replace(' ',''))
        #print(binascii.unhexlify((second + " " + minute + " " + hour + " " + week + " " + day + " " + month + " " + year).replace(' ','')))
        #print(self.NowTime)
        self.bus.writeto_mem(int(self.address),int(self.start_reg),now_time)
    
    def read_time(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        a = t[0]&0x7F  #second
        b = t[1]&0x7F  #minute
        c = t[2]&0x3F  #hour
        d = t[3]&0x07  #week
        e = t[4]&0x3F  #day
        f = t[5]&0x1F  #month
        #---------------------OLED PRINT----------------------------#
        write15.text(repr("20%x/%02x/%02x" %(t[6],t[5],t[4])),23,50)# Date
        write20.text(repr("%02x:%02x:%02x" %(t[2],t[1],t[0])),17,26)# Time
        write15.text(repr("%s" %(self.w[t[3]-1])),10,8)             # Day
        #---------------------OLED PRINT----------------------------#
        
    def year(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        hi = int((t[6]&0x70)/16) * 10
        lo = t[6]&0x0F
        return hi + lo
        
    def sec(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        hi = int((t[0]&0x70)/16) * 10
        lo = t[0]&0x0F
        return hi + lo
    
    def minute(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        hi = int((t[1]&0x70)/16) * 10
        lo = t[1]&0x0F
        return hi + lo
    
    def hour(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        hi = int((t[2]&0x30)/16) * 10
        lo = t[2]&0x0F
        return hi + lo
    
    def week(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        lo = t[3]&0x07
        return lo
    
    def day(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        hi = int((t[4]&0x30)/16) * 10
        lo = t[4]&0x0F
        return hi + lo
    
    def month(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        hi = int((t[5]&0x10)/16) * 10
        lo = t[5]&0x0F
        return hi + lo
    
    def day_name(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        return(self.w[t[3]-1])
        
    def temperature(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),19)
        whole = t[17]&0xFF        
        decimal = ((t[18]& 192)/64) *0.25
        temp = whole + decimal
        if (t[17]&0xFF) > 127:
            temp = temp * -1
        return temp

rtc = ds3231(I2C_PORT,I2C_SCL,I2C_SDA)

#rtc.set_time('08:54:30,Tuesday,2022-12-27')     #Uncomment to set the time
rtc.read_time()

while True:
    time = rtc.read_time()
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    write15.text(str(round(temperature)),80,8)
    write15.text("*C",96,8)
    oled.show()
