#! /usr/bin/env python

import time

try:
	sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
	pass

from com.dtmilano.android.viewclient import ViewClient
device, serialno = ViewClient.connectToDeviceOrExit()
vc = ViewClient(device, serialno)
print("Setup complete")

# Jodi's Demo Order
vc.findViewWithTextOrRaise(u'Safeway Demo - 5 items', root=vc.findViewByIdOrRaise('id/no_id/6')).touch()
time.sleep(4)
device.drag((100, 1350), (660, 1350), 45, 20, 0)
time.sleep(0.7)
device.drag((100, 1350), (660, 1350), 45, 20, 0)

print("Done")
