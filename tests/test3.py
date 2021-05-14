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

while True:
	vc.dump()
	vc.findViewByIdOrRaise("id/no_id/3").touch()
	batchesAvailable = False
	while not batchesAvailable:
		device.drag((350, 350), (350, 950), 50, 20, 0)
		print("Dumping")
		vc.dump()

		status = vc.findViewByIdOrRaise("com.instacart.shopper:id/is_dashboardVirtualBatchStatus_title").getText();
		if status.count("available!") == 1:
			print("Found")
			# batches are available
			batchesAvailable = True
			vc.findViewByIdOrRaise("com.instacart.shopper:id/is_dashboardVirtualBatchStatus_title").touch()
		else:
			print("none")

print("Done")
