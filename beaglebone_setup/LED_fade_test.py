import Adafruit_BBIO.UART as UART
import serial, time

UART.setup("UART1")

ser = serial.Serial(port = "/dev/ttyO1", baudrate=9600)
ser.close()
ser.open()
if ser.isOpen():
    while True:
        redVal = 255
        blueVal = 0
        greenVal = 0
        for x in range(0, 255):
          greenVal += 1
          redVal -= 1
          ser.write("LED L " + str(255 - redVal) + " " + str(255 - greenVal) + " " + str(blueVal) + "\r\n")
          ser.write("LED R " + str(255 - redVal) + " " + str(255 - greenVal) + " " + str(blueVal) + "\r\n")
          
        redVal = 0
        blueVal = 0
        greenVal = 255
        for x in range(0, 255):
          blueVal += 1
          greenVal -= 1
          ser.write("LED L " + str(redVal) + " " + str(255 - greenVal) + " " + str(255 - blueVal) + "\r\n")
          ser.write("LED R " + str(redVal) + " " + str(255 - greenVal) + " " + str(255 - blueVal) + "\r\n")
          
        redVal = 0
        blueVal = 255
        greenVal = 0
        for x in range(0, 255):
          redVal += 1
          blueVal -= 1
          ser.write("LED L " + str(255 - redVal) + " " + str(greenVal) + " " + str(255 - blueVal) + "\r\n")
          ser.write("LED R " + str(255 - redVal) + " " + str(greenVal) + " " + str(255 - blueVal) + "\r\n")
          
ser.close()