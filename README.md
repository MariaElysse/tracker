To run the tracker  
================== 

1. `clone` this repository into a fresh directory on the Pi
2. Ensure the FONA 808 is correctly set up (using the USB Serial interface, connecting the cables as shown [here](https://learn.adafruit.com/adafruit-fona-808-cellular-plus-gps-breakout/wiring-to-usb)
3. Run with `sudo ./tracker.py`, or, what I did to ensure it's at least reasonably reliable, add `@reboot    /full/path/to/directory/tracker.py` to your `/etc/crontab`

Check the website! A new device should be available, with the uuid in `uuid.txt` (that was automatically created)

