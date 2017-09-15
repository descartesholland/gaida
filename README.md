# gaida
Simple Python GUI application to interface a LIFX Color 1000

My use case requires an access point to be set up.
$ sudo add-apt-repository ppa:nilarimogard/webupd8
$ sudo apt-get update
$ sudo apt-get install ap-hotspot

If on Ubuntu 14.04:
$ cd /tmp
$ wget http://old-releases.ubuntu.com/ubuntu/pool/universe/w/wpa/hostapd_1.0-3ubuntu2.1_i386.deb
$ sudo dpkg -i hostapd*.deb
$ sudo apt-mark hold hostapd

Start AP using $ sudo ap-hotspot start

Performed On-Boarding process solely over Wi-Fi using the script found at:
https://github.com/tserong/lifx-hacks/blob/master/onboard.py
