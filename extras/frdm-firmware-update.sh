#!/usr/bin/env bash 

DEVICE="$1" # 1st command line argument, e.g /dev/sdc
FIRMWARE="$2" # 2nd command line argument, e.g /path/to/CMSIS-DAP_OpenSDA.S19
MNTPOINT="$3" # 3rd command line argument, e.g /mnt/myfolder created with 'sudo mkdir /mnt/myfolder 
sudo mkdir -p "$MNTPOINT" # create a mount point, dont complain if it exists
if [ ! -e "$DEVICE" ]; then echo "Can't find device"; exit 1; fi # check if device exists
sudo umount "$DEVICE" # unmount automounted device
sudo modprobe msdos # wake msdos module
sudo mount -t msdos "$DEVICE" "$MNTPOINT" # mount device with msdos type
sudo cp "$FIRMWARE" "$MNTPOINT" # copy the firmware
sync # write any data buffered in memory out to disk
sleep 1 # delay for flash erase/program
sudo umount "$DEVICE" # unmount

