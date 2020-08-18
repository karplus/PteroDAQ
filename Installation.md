## Hardware requirements

One of

* A supported [Arduino](http://www.arduino.cc) board or clone (includes most boards based on the ATMega168/328P, ATMega32U4, and ATMega1280/2560 processors) with appropriate USB cable (varies with Arduino board);  
* A [Teensy 3.1 or 3.2](https://www.pjrc.com/teensy/teensy31.html) or [Teensy LC](https://www.pjrc.com/teensy/teensyLC.html) board with 
    * USB to Micro USB B, 
    * male and female headers to connect to board (two 1×14 male headers to use with breadboard, plus a 1×3 and 1×5 female header to get access to other through-hole I/O); or
* A FRDM-KL25Z board ([list of distributors](http://www.freescale.com/webapp/shoppingcart.buynow.framework?partnumber=FRDM-KL25Z)) with
    * USB A to Mini B cable
    * Headers to solder to the FRDM-KL25Z board. It uses one 2x10, two 2x8, and one 2x6 through-hole female headers with 0.1 inch pitch.
    * For the initial setup of the FRDM-KL25Z board, a computer running either Linux or Windows 7.

We recommend the Teensy LC board as the best price/performance ratio, breadboard compatibility, and easiest installation, but the Teensy 3.1/3.2 is a good choice also at a higher price.  The FRDM-KL25Z board is a good choice if you want compatibility with Arduino shield hardware, but compiling and uploading software is less convenient than the Teensyduino IDE.  The Arduino boards are not nearly as good for PteroDAQ as the Teensy boards, and are supported mainly for people who already have spare Arduino boards—don't buy a new Arduino board just for PteroDAQ!

## Software setup

There is now a [YouTube video](https://youtu.be/Yvg109QyVI0) explaining installation of PteroDAQ on macos.

Download and extract PteroDAQ, using the "Clone or download" button on the [main page](https://github.com/karplus/PteroDAQ) or download the [zip file](https://github.com/karplus/PteroDAQ/archive/master.zip) directly.
This will get the latest version of the code—you can also request earlier, named releases, if the latest version seems to be buggy.

Ensure you have a recent version of Python installed (2.6, 2.7, 3.3 through 3.5, and 3.8 have been tested; version 3.0 through 3.2 and 3.6 through 3.7 may also work but have not been tested). Python is available to download from [the Python site](http://python.org), but most testing has been done with the [Anaconda python distribution](https://www.anaconda.com/products/individual). When installing, make sure you include support for Tcl/Tk and Tkinter. On Linux and OS X, the Python installer will probably add itself to your bash path; if not, edit your `~/.bashrc` file manually. On Windows, make sure you select having Python on your path, so that it is runnable from the Command window.

## Arduino setup (not needed with Teensy boards, only Arduino boards)

1. Instruction for installing the Arduino software are available on [the Arduino site](https://www.arduino.cc/en/Guide/HomePage).
2. Once you have installed the Arduino IDE and (if necessary) drivers, open the PteroDAQ file `firmware/firmware.ino` with the Arduino app. All the files in `firmware` folder are needed, and the folder must have the name `firmware`, as the Arduino app compiles all the C and C++ files in the folder to make the program, and it checks that the folder has the same name as the .ino file. 
3. Select your board and its serial port from the Arduino Tools menu, and press the Upload button.

## Teensy setup

1. See the [Teensyduino download page](https://www.pjrc.com/teensy/td_download.html) and follow the instructions there for installing Teensyduino.
3. Once you have installed the Arduino IDE and (if necessary) drivers, open the PteroDAQ file `firmware/firmware.ino` with the Arduino app. All the files in `firmware` folder are needed, and the folder must have the name `firmware`, as the Arduino app compiles all the C and C++ files in the folder to make the program, and it checks that the folder has the same name as the .ino file. 
4. Select your board (Teensy 3.1/3.2 with 72MHz clocking or Teensy LC with 48MHz clocking) and its serial port from the Arduino Tools menu. Select optimization for fastest rather than smallest code size, and press the Upload button.  On the first download, you may be instructed by the Teensy loader to press the button on the board—if so, do so.

## FRDM-KL25Z setup  (not recently tested—may no longer work, as mbed may have changed)

The FRDM-KL25Z board has two USB ports, one of which is labeled "SDA" on the board. The SDA port is only for firmware updates; normal usage is with the non-SDA port. Each of the operating systems has somewhat different techniques for doing the initial setup. There are two main steps: getting the mbed firmware onto the board for downloading, and getting the PteroDAQ code onto the board for running.

### Windows for FRDM-KL25Z

Instructions for loading the mbed interface firmware on Windows 7 are available on [the mbed site](https://developer.mbed.org/handbook/Firmware-FRDM-KL25Z). The steps are fairly simple:

1. Download the latest version of the mbed firmware from  [the mbed site](https://developer.mbed.org/handbook/Firmware-FRDM-KL25Z).  It will have a name like 20140530_k20dx128_kl25z_if_opensda.s19
2. Hold down the reset button (the small button between the USB ports) while plugging the USB cable into the SDA port.  This should make a flash drive called BOOTLOADER appear on your computer.  This can take a while, as Windows insists on installing new drivers for each new flash drive it sees.
3. Drag the mbed firmware onto the BOOTLOADER drive.
4. Unplug the USB cable, and plug it back in **without** holding down the reset button.
5. The board should now appear as a flash drive called MBED.  (Again, this might take a while as Windows once again installs drivers.)
6. Drag the PteroDAQ file `extras/PteroDAQ_KL25Z.bin` to this drive. The drive will vanish, then reappear. Once it reappears, wait a couple seconds and unplug the USB cable.
7. Plug the USB cable into the other, non-SDA port. 
8. Go to Device Manager, right-click on the device (its name may be something like "mbed serial" or "PteroDAQ"), and choose "Update driver software". In the popup, choose "Browse my computer for driver software", and select the PteroDAQ file `extras/mbed-usb-windows.inf`.

The PteroDAQ system should now be ready to run.

On Windows 8.1 systems you may run into problems with step 3, getting files to transfer to the BOOTLOADER.  The workaround we've seen suggested is to use GPEDIT to edit group policies and enable `Computer Configuration \ Administrative Templates \ Windows Components \ Search \ Do not allow locations on removable drives to be added to libraries`.  We do not have a Windows 8.1 system on which to test this workaround.

On Windows 8 machines, there is also a problem with the last step, as Windows 8 does not allow installing unsigned drivers. The workaround to disable this check is nicely explained in a [Sparkfun tutorial](https://learn.sparkfun.com/tutorials/disabling-driver-signature-on-windows-8), but the instructions are too complicated to repeat here, especially as we don't have a Windows 8 machine to check the procedure with.

### Mac OS X for FRDM-KL25Z

On Mac OS X computers, there does not seem to be any workaround that allows the poorly written P&E Micro bootloader to work.  You will need to install the mbed firmware either on a Windows machine using steps 1–4 or on a Linux machine using steps 1–5 of those instructions.

After the mbed firmware is installed, the PteroDAQ code is easy to load onto the board:

1. Plug the USB cable into the SDA port **without** holding down the reset button.
2. The board should now appear as a flash drive called MBED.  You may see an alert saying that the "MBED CMIS-DAP" network interface has not been set up.  Cancel that alert—the serial port is not really a network.
3. Drag the PteroDAQ file `extras/PteroDAQ_KL25Z.bin` to this drive. The drive will vanish, then reappear. (Possibly warning you that the disk was not ejected properly and that the "MBED CMIS-DAP" network has not been setup.  Ignore or cancel these alerts.)
4. Once MBED reappears, wait a couple seconds and unplug the USB cable.
5. Plug the USB cable into the other, non-SDA port.  You are now ready to run PteroDAQ.

Note: don't ever hold down reset again while plugging a cable into the SDA port.  Doing so wipes out the mbed firmware, and you will have to go back to a Windows or Linux machine to reload it.
 
### Linux for FRDM-KL25Z

On Linux computers, if you have root (administrator) privileges, you can download the mbed firmware to KL25Z boards.  Without root privileges, you will have to find a Windows machine and follow steps 1–4 of instructions there to install the mbed firmware.

1. Download the mbed interface firmware from [the mbed site](https://developer.mbed.org/handbook/Firmware-FRDM-KL25Z), and note where it is (for example, `~/Downloads/20140530_k20dx128_kl25z_if_opensda.s19`). 
2. Open a command line. Without the FRDM-KL25Z board plugged in, run `ls /dev/sd*` to see what drives are currently on your system. 
3. With the reset button on the board held down, plug the USB cable into the SDA port of the FRDM-KL25Z board. 
4. Run `ls /dev/sd*` again and note what new drive shows up—this is the bootloader drive (for example, `/dev/sdc`). 
5. From the PteroDAQ `extras` folder, run
    `./frdm-firmware-update-linux.sh /dev/sdc ~/Downloads/20140530_k20dx128_kl25z_if_opensda.s19 /mnt/frdmtmp`
    with the file paths replaced with the ones you noted. You will be prompted to enter your password. After the command completes, wait at least fifteen seconds before unplugging the USB cable from the board.
6. Unplug the USB cable, and plug it back in **without** holding down the reset button.
7. The board should now appear as a flash drive called MBED.
8. Drag the PteroDAQ file `extras/PteroDAQ_KL25Z.bin` to this drive. The drive will vanish, then reappear. Once it reappears, wait a couple seconds and unplug the USB cable.
9. Plug the USB cable into the other, non-SDA port. You are now ready to run PteroDAQ.
