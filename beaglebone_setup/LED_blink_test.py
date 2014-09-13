import Adafruit_BBIO.UART as UART
import serial, time
 
UART.setup("UART1")
 
ser = serial.Serial(port = "/dev/ttyO1", baudrate=9600)
ser.close()
ser.open()
if ser.isOpen():
    while True:
        ser.write("LED L 255 255 0\r\n")
        ser.write("LED R 255 255 0\r\n")
        time.sleep(0.05)
        ser.write("LED L 0 255 0\r\n")
        ser.write("LED R 0 255 0\r\n")
        time.sleep(0.05)
        ser.write("LED L 0 0 255\r\n")
        ser.write("LED R 0 0 255\r\n")
        time.sleep(0.05)
        ser.write("LED L 255 0 0\r\n")
        ser.write("LED R 255 0 0\r\n")
        time.sleep(0.05)
        ser.write("LED L 0 255 255\r\n")
        ser.write("LED R 0 255 255\r\n")
        time.sleep(0.05)
ser.close()
