#! /usr/bin/env python

import sys
import os
import time
import datetime
import urllib2

# Bot Setup
DEBUG = "-v" in sys.argv or "--verbose" in sys.argv
SCROLL = "-s" in sys.argv or "--scroll" in sys.argv
COP = "-c" in sys.argv or "--cop" in sys.argv

# Help Screen
if "-h" in sys.argv or "--help" in sys.argv:
	print("bot.py requires Python 2.7.")
	print("Usage: python bot.py [-opts]")
	print("\nOptions:")
	print("-c, --cop\tTurn on cop mode to auto-accept found batches, default: Off")
	print("-s, --scroll\tTurn on scroll mode to detect 4+ batches, default: Off")
	print("-v, --verbose\tTurn on debugging mode, default: Off")
	exit()

# Confirm Env Vars
try:
	endpoint = os.environ["WEBHOOK_ENDPOINT"]
	if DEBUG: print("WEBHOOK ENDPOINT: " + endpoint)
except:
	print("WEBHOOK_ENDPOINT not setup yet!")
	exit()

print("Debug: " + str(DEBUG))
print("Scroll: " + str(SCROLL))
print("Cop: " + str(COP))

# Setup AndroidViewClient
try:
	sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
	pass
from com.dtmilano.android.viewclient import ViewClient
device, serialno = ViewClient.connectToDeviceOrExit()
vc = ViewClient(device, serialno)
print("Setup complete")

# Test Case 1 -- $40+
MIN_EARNINGS = 39.0 # float, minimum batch payout
MAX_ORDERS = 2 # int, maximum full service orders (trips)
MAX_MILES = 14.9 # float, maximum driving distance
MAX_ITEMS = 29 # int, maximum items # 30
MAX_UNITS = 32 # int, maximum units -- batch must fulfill MAX_ITEMS and MAX_UNITS, not or
ONE_CITY = True # bool, only pick batches in certain city
MY_CITY = "honolulu" # string, only pick batches in certain city

# Test Case 2 -- Small Order
MIN_EARNINGS_2 = 30.0
MAX_ORDERS_2 = 2
MAX_MILES_2 = 12.9
MAX_ITEMS_2 = 9
MAX_UNITS_2 = 18
ONE_CITY_2 = True
MY_CITY_2 = "honolulu"

# Test Case 3 -- Mega Order
MIN_EARNINGS_3 = 70.0
MAX_ORDERS_3 = 3
MAX_MILES_3 = 18.9
MAX_ITEMS_3 = 40
MAX_UNITS_3 = 45
ONE_CITY_3 = True
MY_CITY_3 = "honolulu"

"""
# Test Case 3 -- Prescription/Tiny Order
MIN_EARNINGS_3 = 17.0
MAX_ORDERS_3 = 1
MAX_MILES_3 = 10.9
MAX_ITEMS_3 = 1
MAX_UNITS_3 = 4
ONE_CITY_3 = True
MY_CITY_3 = "Honolulu"
"""

# ViewClient Screen Dump Helper Function
def screenDump(vc=vc):
	try:
		vc.dump(sleep=0)
		return 0
	except KeyboardInterrupt:
		print("\nStopped program by keyboard interruption.")
		exit()
	except:
		print("Fatal Error: ViewClient dump failed. Please restart app.")
		return 1

# Scrape a view card found by AndroidViewClient into a dict
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
		batchDetails["city"] = batchDetails["location"][:batchDetails["location"].index(", HI")].lower() # "San Fran, CA\n..." --> "san fran"
		# "San Fran, CA\nCostco..." --> "costco", "Sam's Club" --> "sam's"
		batchDetails["store"] = batchDetails["location"][batchDetails["location"].index("\n")+1:batchDetails["location"].index(" ", batchDetails["location"].index("\n"))].lower()
		return batchDetails

# Print Batch Details Nicely to CLI
def prettyPrintBatch(batch):
	return "$" + str(batch["earnings"]) + " " + str(batch["items"]) + "/" + str(batch["units"]) + " " + str(batch["miles"]) + " mi " + str(batch["orders"]) + " " + batch["city"][:3] + " " + batch["store"][:3]

bestBatch = None
while bestBatch == None:
	# Refresh
	if SCROLL:
		device.drag((330, 165), (330, 1250), 100, 30, 0) # if scroll is on, re-scroll up first to top of page to refresh
		time.sleep(0.1)
	device.drag((330, 165), (330, 1250), 50, 20, 0)

	if screenDump() > 0: break # dump screen, exit program if dump fails

	# Check if Batches Exist
	if (vc.findViewById("com.instacart.shopper:id/is_virtualBatchList_emptyState_text")):
		# vc.findViewById("com.instacart.shopper:id/is_virtualBatchList_list")
		print("No batches exist")
		vc.findViewByIdOrRaise("id/no_id/3").touch()
		time.sleep(1.5)
		device.touch(330, 340, 0) # y: 340 without promo header, y: 475 with promo header
		continue # jump to top of main while loop

	# Scrape & Parse Batch List
	batchList = []
	batchListElement = None

	# Error Management
	try:
		batchListElement = vc.findViewByIdOrRaise("com.instacart.shopper:id/is_virtualBatchList_list")
	except:
		# Can't find virtual batch list, probably stuck on home screen
		print("Error: Unable to find is_virtualBatchList_list view, attempting to auto-fix...")
		if screenDump() > 0: break # dump screen, exit program if dump fails
		try:
			vc.findViewByIdOrRaise("com.instacart.shopper:id/is_dashboardVirtualBatchStatus_title").touch()
		except:
			print("Fatal Error: Failed to auto-fix. Unknown app state.")
			break # exit program
		continue # jump to top of main while loop

	# Parse Batch List
	for rawBatch in batchListElement.getChildren():
		batchDetails = parseBatch(rawBatch)
		if batchDetails == None:
			# if corrupted parsed batch, do not add to batch list
			continue # jump to next raw batch

		if DEBUG: print(batchDetails)
		batchList.append(batchDetails) # Assume not duplicate since top of screen

	# Scroll to Bottom if Scroll is Enabled
	if SCROLL and len(batchList) >= 3:
		# 4 batches would mean there MIGHT be additional batches, 3 batches means there might be additional batches too due to "Due to limited batches in your area..." header
		device.drag((330, 1340), (330, 310), 100, 20, 0)

		if screenDump() > 0: break # dump screen, exit program if dump fails

		# Parse Batch List Again
		for rawBatch in vc.findViewByIdOrRaise("com.instacart.shopper:id/is_virtualBatchList_list").getChildren():
			batchDetails = parseBatch(rawBatch, 1)
			if batchDetails == None:
				continue # jump to next raw batch

			# Check for duplicate in batch list, since scrolling might show the same batches
			if next((batch for batch in batchList if batch["earnings"] == batchDetails["earnings"] and batch["miles"] == batchDetails["miles"] and batch["units"] == batchDetails["units"]), None) == None:
				# not a duplicate
				if DEBUG: print(batchDetails)
				batchList.append(batchDetails)

	# Find Highest Paying Batch that Fulfills Requirements
	batchList.sort(key=lambda batch: batch["earnings"], reverse=True) # sort batch list by higest earnings to lowest earnings
	bestBatchIndex = -1

	# Test Case 1
	if DEBUG: print("Test Case 1")
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

	# Test Case 2
	if DEBUG: print("Test Case 2")
	if bestBatchIndex == -1:
		for i, batch in enumerate(batchList):
			if DEBUG: print("CHECKING", batch)
			if batch["earnings"] < MIN_EARNINGS_2:
				break # break not continue because batchList is sorted, all other batches are lower payout
			if batch["orders"] > MAX_ORDERS_2:
				continue
			if batch["miles"] > MAX_MILES_2:
				continue
			if batch["items"] > MAX_ITEMS_2 or batch["units"] > MAX_UNITS_2:
				continue
			if ONE_CITY_2 and batch["city"].count(MY_CITY_2) == 0:
				# handles "San Fran" and "San Fran (Cali County)"
				continue
			bestBatchIndex = i # set index of successfully found batch
			break

	# Test Case 3
	if DEBUG: print("Test Case 3")
	if bestBatchIndex == -1:
		for i, batch in enumerate(batchList):
			if DEBUG: print("CHECKING", batch)
			if batch["earnings"] < MIN_EARNINGS_3:
				break # break not continue because batchList is sorted, all other batches are lower payout
			if batch["orders"] > MAX_ORDERS_3:
				continue
			if batch["miles"] > MAX_MILES_3:
				continue
			if batch["items"] > MAX_ITEMS_3 or batch["units"] > MAX_UNITS_3:
				continue
			if ONE_CITY_3 and batch["city"].count(MY_CITY_3) == 0:
				# handles "San Fran" and "San Fran (Cali County)"
				continue
			bestBatchIndex = i # set index of successfully found batch
			break

	if bestBatchIndex > -1:
		# Batch found
		print("FOUND", datetime.datetime.now().strftime("%m-%d %I-%M-%S %p"))
		bestBatch = batchList[bestBatchIndex]

		# if scroll was enabled and found batch was at top of screen, need to re-scroll up
		if SCROLL and bestBatch["screenPos"] == 0 and len(batchList) >= 3:
			device.drag((330, 165), (330, 1250), 100, 30, 0)
			time.sleep(0.1)
	else:
		# No good batches found
		print(datetime.datetime.now().strftime("%m-%d %I-%M-%S %p"), [prettyPrintBatch(batch) for batch in batchList])
		# print("No good batches found out of " + str(len(batchList)) + " batches", [prettyPrintBatch(batch) for batch in batchList])

# Outside of while loop
if bestBatch != None:
	# Found highest paying batch that fulfills requirements
	print(bestBatch)
	device.touch(330, bestBatch["y"], 0) # click on the batch

	# Swipe to Accept Batch
	time.sleep(1)
	device.takeSnapshot().save("batch " + datetime.datetime.now().strftime("%m-%d %I-%M-%S %p") + ".png", "PNG") # save a screenshot, also adds in extra delay
	if COP:
		for i in range(5):
			# swipe multiple times in case batch screen loads slow
			device.drag((100, 1350), (630, 1350), 50, 20, 0) # swipe action
			time.sleep(0.15)

# Send Notification Thru 3rd Party API
response = urllib2.urlopen(os.environ["WEBHOOK_ENDPOINT"])
response.close()

print("Done")
