#1. Ubuntu on the BeagleBone Black

Download ubuntu SD card image from [http://www.armhf.com/index.php/boards/beaglebone-black/](http://www.armhf.com/index.php/boards/beaglebone-black/)

Copy to SD card from a Mac:

```
➤ diskutil list
➤ sudo diskutil unmountDisk /dev/sdcard
➤ sudo dd if=ubuntu.img of=/dev/rsdcard bs=1m
```

Boot BeagleBone Black from SD card holding boot button

Download ubuntu image to SD card:

```
➤ wget imgage_url
```

Copy image to on-board flash:

```
➤ sudo -i
➤ xz -cd ubuntu.img > /dev/mmcblk1
```

May need to unmout on-board flash before copying:

```
➤ umount /dev/mmcblk1
```

#2. Basic setup

Update repository lists and installed packages:

```
➤ apt-get update
➤ apt-get upgrade
```

Probably set locale:

```
➤ sudo locale-gen en_GB.UTF-8
```

Install good things:

```
➤ apt-get install git fish vim
```

Change username, home directory and password:

```
➤ usermod -l newusername oldusername
➤ usermod -d /home/newhomedir -m newusername
➤ mv /home/oldhomedir /home/newhomedir
➤ passwd newusername
```

Add $SLOTS and $PINS to path (these are used for managing the BBB's Capes)

- For bash: 

```
➤ export SLOTS=/sys/devices/bone_capemgr.9/slots
➤ export PINS=/sys/kernel/debug/pinctrl/44e10800.pinmux/pins
 ```
- For fish, add lines to config.fish:

```
set -x SLOTS /sys/devices/bone_capemgr.9/slots
set -x PINS /sys/kernel/debug/pinctrl/44e10800.pinmux/pins
```


#3. Serial Setup

- Tutorial for device tree compiler is [here](https://github.com/derekmolloy/boneDeviceTree)
- Video and instructions [here](http://derekmolloy.ie/gpios-on-the-beaglebone-black-using-device-tree-overlays/ )
- Basic dts file template taken from [here](http://hipstercircuits.com/enable-serialuarttty-on-beaglebone-black/)
- Another tutorial [here](http://learn.adafruit.com/introduction-to-the-beaglebone-black-device-tree)

Install device tree compiler for BBB I/O:

```
➤ apt-get install device-tree-compiler
```

Patch device tree compiler to allow modifications without recompiling bootloader (patch file in this repository as dtc_patcher.sh as a mirror):

```
➤ wget -c https://raw.github.com/RobertCNelson/tools/master/pkgs/dtc.sh
➤ chmod +x dtc.sh
➤ ./dtc.sh
```

Compile device tree source file to enable UART1 (*/dev/ttyO1*) (source file is included in this repo as BB-UART1.dts):

```
➤ dtc -O dtb -o BB-UART1-00A0.dtbo -b 0 -@ BB-UART1.dts
```

Copy compiled file, BB-UART1-00A0.dtbo, to */lib/firmware*:

```
➤ cp BB-UART1-00A0.dtbo /lib/firmware
```

Check pin configurations have changed by running this before and after next step:

```
➤ cat $PINS | grep -e "984\|980"
```

Add device tree to slots:

```
➤ cd /lib/firmware
➤ echo BB-UART1 > $SLOTS
```

This setting will be cleared at reboot, to enable on startup:

```
➤ mkdir /media/beagle
➤ mount /dev/mmcblk0p1 /media/beagle
➤ vim	/mnt/boot/uEnv.txt
```

To the optargs line of *uEnv.txt*, add:

```
capemgr.enable_partno=BB-UART1
```

#4. Python Libraries for GPIO  

Install python and python libraries for BBB GPIO:

```
➤ apt-get update
➤ apt-get install build-essential python-dev python-setuptools python-pip python-smbus -y
```

Use pip to install the adafruit GPIO library:

```
➤ sudo pip install Adafruit_BBIO
➤ pip install pyserial
```

pip might refuse to install the library, might need to run:

```
➤ pip install distribute --upgrade
```

Full instructions [here](http://learn.adafruit.com/setting-up-io-python-library-on-beaglebone-black/installation-on-ubuntu)

#5. Connecting BBB to AVR Board

Pinout [here](http://elinux.org/File:BeagleBone_p9_pinout.jpg) for reference:

    BBB Header & Pin    |       AVR Board
    --------------------------------------------------
    GND - P9, Pin 2     |   GND on power header 
    5V  - P9, Pin 8     |   VCC on power header 
    Gnd - P9, Pin 1     |   GND on serial header 
    TXD - P9, Pin 24    |   RXD on serial header
    RXD - P9, Pin 26    |   TXD on serial header

#6. Test Connection 

Files included in repo, lights should flash: 

```
➤ sudo python LED_blink_test.py
➤ sudo python LED_fade_test.py
```

#7. Wifi Setup

Using:

- [http://kerneldriver.wordpress.com/2012/10/21/configuring-wpa2-using-wpa_supplicant-on-the-raspberry-pi/](http://kerneldriver.wordpress.com/2012/10/21/configuring-wpa2-using-wpa_supplicant-on-the-raspberry-pi/)
- [http://ubuntuforums.org/showthread.php?t=263136](http://ubuntuforums.org/showthread.php?t=263136)

Install and configure **ifplugd**:

```
➤ sudo apt-get install ifplugd
➤ vim /etc/default/ifplugd
```

to the INTERFACES variable, add:

```
eth0, wlan0
```


Edit */etc/network/interfaces*:

```
# interfaces(5) file used by ifup(8) and ifdown(8)

# loopback network interface
auto lo
iface lo inet loopback

# Ethernet
allow-hotplug eth0
iface eth0 inet dhcp

# WiFi
auto wlan0
allow-hotplug wlan0
iface wlan0 inet dhcp
        wpa-conf /etc/wpa_supplicant/extreme.conf
```

Edit */etc/wpa_supplicant/yourssid.conf*:

```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#update_config=1
#ap_scan=2

network={
    ssid="Extreme"
    scan_ssid=1
    proto=RSN
    key_mgmt=WPA-PSK
    pairwise=CCMP TKIP
    group=CCMP TKIP
    psk="3Re(uij+-="
}

network={
    ssid="ECS-WLAN"
    scan_ssid=1
    proto=RSN
    key_mgmt=NONE
}
```

psk entries are generated with:

```
wpa_passphrase your_ssid your_psk
```

#8. Sound Setup

Need to disable the HDMI cape, otherwise the HDMI sound interferes with the USB sound card:

```
➤ mkdir /media/beagle
➤ mount /dev/mmcblk0p1 /media/beagle
➤ vim	/mnt/boot/uEnv.txt
```

To the optargs line of *uEnv.txt*, add:

```
quiet capemgr.disable_partno=BB-BONELT-HDMI,BB-BONELT-HDMIN
```

and reboot. This means the Mini-HDMI port will no longer work, reverse the changes to re-enable.

Edit */etc/asound.conf*:

```
pcm.!default {
    type plug
    slave {
        pcm "hw:0,0"
        channels 2
    }
}

ctl.!default {
    type hw
    card 0
}
```

where the first number in *"hw:0,0"* is the card number, and the second is the subdevice number, given by:

```
➤ aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: Set [C-Media USB Headphone Set], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```
Finally, edit the alsa base config file:

```
➤ vim /etc/modprobe.d/alsa-base.conf
```
Ensure that there is only one occurence of the line:

```
options snd-usb-audio index=0
```
and ensure that `index=0`.

Reboot and test with:

```
➤ mplayer mp3file
```
or

```
➤ espeak "Hello, I am Nabaztag"
```

- Follow instructions [here](http://blog.scphillips.com/2013/01/sound-configuration-on-raspberry-pi-with-alsa/) for setting default volume to 100%.
- Follow instructions [here](http://alien.slackbook.org/blog/adding-an-alsa-software-pre-amp-to-fix-low-sound-levels/) for adding a software preamp to the output.

