#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Mar 13, 2012

@author: diego
'''


# import re
# import sys
# import os
# import string

import time

try:
	sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
	pass

from com.dtmilano.android.viewclient import ViewClient

device, serialno = ViewClient.connectToDeviceOrExit()
vc = ViewClient(device, serialno)

print("Setup complete")

device.dragDip((150.0, 200.0), (150.0, 400.0), 40, 20, 0) # scroll down to refresh
# vc.findViewByIdOrRaise(u"com.instacart.shopper:id/fragment_dashboard_native_card_recyclerview").uiScrollable.flingBackward()

print(vc.findViewByIdOrRaise("com.instacart.shopper:id/is_dashboardVirtualBatchStatus_title").getText())
# print(vc.findViewByIdOrRaise("com.instacart.shopper:id/fragment_dashboard_native_card_recyclerview").getChildren())
# for child in vc.findViewByIdOrRaise("com.instacart.shopper:id/fragment_dashboard_native_card_recyclerview").getChildren():
#     print(child)

for i in range(0, 5):
	device.dragDip((150.0, 200.0), (150.0, 400.0), 40, 20, 0)
	time.sleep(1)
