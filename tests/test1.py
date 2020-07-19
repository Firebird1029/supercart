#! /usr/bin/env python

import time
import os
import urllib2

try:
	sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
	pass

from com.dtmilano.android.viewclient import ViewClient
device, serialno = ViewClient.connectToDeviceOrExit()
vc = ViewClient(device, serialno)
print("Setup complete")

DEBUG = False
SCROLL = True
MIN_EARNINGS = 40.0 # float, minimum batch payout
MAX_ORDERS = 1 # int, maximum full service orders (trips)
MAX_MILES = 10.0 # float, maximum driving distance
MAX_ITEMS = 30 # int, maximum items
MAX_UNITS = 32 # int, maximum units -- batch must fulfill MAX_ITEMS and MAX_UNITS, not or
ONE_CITY = True # bool, only pick batches in certain city
MY_CITY = "Honolulu" # string, only pick batches in certain city

# Scroll up to refresh
# device.drag((330, 350), (330, 950), 50, 20, 0)
# device.dragDip((150.0, 200.0), (150.0, 400.0), 40, 20, 0)
# vc.findViewByIdOrRaise(u"com.instacart.shopper:id/fragment_dashboard_native_card_recyclerview").uiScrollable.flingBackward()

# Touch
# vc.findViewWithTextOrRaise(u'Order now').touch()

# Swipe
# device.drag((100, 1350), (660, 1350), 45, 20, 0)

def parseBatch(rawBatch, screenPos=0):
		batchDetails = {"screenPos": screenPos, "y": rawBatch.getY() + 25}
		rawBatchDetails = [detail.getText() for detail in rawBatch.getChildren()] # scrape batch card

		# Ignore "Due to limited batches..." card and cropped cards
		if (len(rawBatchDetails) < 9):
			return None

		# Parse card
		batchDetails["earnings"] = float(rawBatchDetails[0][1:]) # "$9.50" --> 9.5, "$9" --> 9.0
		batchDetails["orders"] = int(rawBatchDetails[1][:rawBatchDetails[1].index(" F")]) # "1 Full Service Order" --> 1, "2 Full Service Orders" --> 2
		batchDetails["miles"] = float(rawBatchDetails[4][:rawBatchDetails[4].index(" m")]) # "1.7 miles" --> 1.7
		batchDetails["items"] = int(rawBatchDetails[6][:rawBatchDetails[6].index(" i")]) # " 5 items / 12 units" --> 5
		batchDetails["units"] = int(rawBatchDetails[6][rawBatchDetails[6].index("/") + 2:rawBatchDetails[6].index(" u")]) # " 5 items / 12 units" --> 12
		batchDetails["location"] = rawBatchDetails[8]
		batchDetails["city"] = batchDetails["location"][:batchDetails["location"].index(", HI")] # "Honolulu, HI\n..." --> "Honolulu"
		return batchDetails

bestBatch = None
while bestBatch == None:
	# Refresh
	if SCROLL: device.drag((330, 350), (330, 950), 50, 20, 0) # if scroll is on, re-scroll up first to top of page to refresh
	device.drag((330, 350), (330, 950), 50, 20, 0)

	vc.dump(sleep=0)

	# Check if Batches Exist
	if (vc.findViewById("com.instacart.shopper:id/is_virtualBatchList_emptyState_text")):
		# vc.findViewById("com.instacart.shopper:id/is_virtualBatchList_list")
		print("No batches exist")
		vc.findViewByIdOrRaise("id/no_id/3").touch()
		time.sleep(2.5)
		device.touch(330, 340, 0)
		continue

	# Scrape & Parse Batch List
	batchList = []
	for rawBatch in vc.findViewByIdOrRaise("com.instacart.shopper:id/is_virtualBatchList_list").getChildren():
		batchDetails = parseBatch(rawBatch)
		if batchDetails == None:
			continue

		# Assume not duplicate since top of screen
		if DEBUG: print(batchDetails)
		batchList.append(batchDetails)

	# Scroll to Bottom (Hacky)
	if SCROLL and len(batchList) >= 3:
		# 4 batches would mean there MIGHT be additional batches, 3 batches means there might be additional batches too due to "Due to limited batches in your area..." header
		device.drag((330, 1340), (330, 310), 100, 20, 0)

		vc.dump(sleep=0)

		# Parse Batch List Again
		for rawBatch in vc.findViewByIdOrRaise("com.instacart.shopper:id/is_virtualBatchList_list").getChildren():
			batchDetails = parseBatch(rawBatch, 1)
			if batchDetails == None:
				continue

			# Check for duplicate
			if next((batch for batch in batchList if batch["earnings"] == batchDetails["earnings"] and batch["miles"] == batchDetails["miles"] and batch["units"] == batchDetails["units"]), None) == None:
				# not a duplicate
				if DEBUG: print(batchDetails)
				batchList.append(batchDetails)

	# Find Highest Paying Batch that Fulfills Requirements
	batchList.sort(key=lambda batch: batch["earnings"], reverse=True) # sort batch list by higest earnings to lowest earnings
	bestBatchIndex = -1
	for i, batch in enumerate(batchList):
		if DEBUG: print("CHECKING", batch)
		if batch["earnings"] < MIN_EARNINGS:
			break # break not continue because batchList is sorted, all other batches are lower payout
		if batch["orders"] > MAX_ORDERS:
			continue
		if batch["miles"] > MAX_MILES:
			continue
		if batch["items"] > MAX_ITEMS or batch["units"] > MAX_UNITS:
			continue
		if ONE_CITY and batch["city"].count(MY_CITY) == 0:
			# handles "San Fran" and "San Fran (Cali County)"
			continue
		bestBatchIndex = i # set index of successfully found batch
		break

	if bestBatchIndex > -1:
		print("FOUND")
		bestBatch = batchList[bestBatchIndex]

		# if scroll was enabled and batch was at top of screen, need to re-scroll up
		if SCROLL and bestBatch["screenPos"] == 0 and len(batchList) > 4:
			device.drag((330, 350), (330, 950), 50, 20, 0)
	else:
		print("No good batches found out of " + str(len(batchList)) + " batches")

# Outside of while loop
if bestBatch != None:
	# Found highest paying batch that fulfills requirements
	print(bestBatch)
	device.touch(330, bestBatch["y"], 0)

	# Swipe to Accept Batch
	time.sleep(1) # or 1.5?
	device.takeSnapshot().save("screenshot.png", "PNG") # TODO REMOVE LATER
	# device.drag((100, 1350), (660, 1350), 45, 20, 0)

# Call my Number to Notify
response = urllib2.urlopen(os.environ["WEBHOOK_ENDPOINT"])
response.close()

print("Done")
