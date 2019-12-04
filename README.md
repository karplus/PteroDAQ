# PteroDAQ

An open-source data acquisition system supporting the [Freedom KL25Z](http://www.freescale.com/webapp/sps/site/prod_summary.jsp?code=FRDM-KL25Z) board, the [Teensy 3.1 or 3.2](https://www.pjrc.com/teensy/teensy31.html) board, the [Teensy LC](https://www.pjrc.com/teensy/teensyLC.html) board, and those [Arduino](http://arduino.cc) boards that are based on ATMega processors. 

Currently in beta release (v0.2b1): tested to work with Python 3.4 and 2.7 on Mac OS 10.6.8 and 10.7, Windows 7, and Ubuntu Linux 14.04.  (Currently, works only at 72MHz on Teensy 3.1/3.2 and only at 48MHz on Teensy LC.)

PteroDAQ is made available under the terms of the MIT License, included in the LICENSE.txt file.

## Documentation

* [Installation](./Installation.md) (includes download links and list of hardware requirements)
* [Usage] (not written yet)
* [Description of internals] (not written yet, see source code)

## Release notes

v0.2b1 is an enormous speedup over v0.1, removes the PySerial dependency, and provides support for Arduino boards, in addition to many minor bug fixes and improvements.
