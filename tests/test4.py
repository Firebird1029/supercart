#! /usr/bin/env python

import sys
import os

from com.dtmilano.android.viewclient import ViewClient

device, serialno = ViewClient.connectToDeviceOrExit(verbose=False)

print("start")
device.takeSnapshot().save("screenshottemp.png", 'PNG')
print("done")