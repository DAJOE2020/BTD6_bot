#global variables
import time, math, random, threading, ctypes, getpass
from mem_edit import Process
from pynput.mouse import Button, Controller
from datetime import datetime
from PIL import ImageGrab, Image

times = [None]*12
mouse = Controller()
click_delay = 0.3
scroll_delay = 0.2
towers = []

#place tower
def place(x,y,tower):
	
	global times
	global mouse
	global click_delay
	global scroll_delay
	global towers

	#get tower icon coord
	column_xcoords = [930,1300]
	icon_x = column_xcoords[tower%2]
	icon_y = math.floor((tower%12)/2)*75+211
	scroll = math.floor(tower/12)*(-14)

	towers.append([tower,(x,y)])

	#prevent all upgrades menu
	current_time = datetime.now()
	prev_time = times[tower%12]
	if prev_time != None:
		time_difference = current_time-prev_time
		time_difference = math.floor(time_difference.microseconds/10000)/100
		time.sleep(max(0.8-time_difference,0))
		current_time = datetime.now()
	prev_time = current_time

	#placing the tower
	mouse.position = (icon_x,icon_y)
	if scroll != 0:
		mouse.scroll(0,scroll)
		time.sleep(scroll_delay)
	mouse.click(Button.left)
	time.sleep(click_delay)
	if scroll != 0:
		mouse.scroll(0,-scroll)
		time.sleep(scroll_delay)
	mouse.position = (x,y)
	mouse.click(Button.left)
	time.sleep(click_delay)
	mouse.position = (x,767)
	time.sleep(0.4)

#modify tower
def modify(index,action):
	
	global towers
	global mouse
	global click_delay

	tpos = towers[index][1]
	mouse.position = tpos
	mouse.click(Button.left)
	time.sleep(click_delay)

	if action == "sell":
		if tpos[0] <= 480:
			mouse.position = (838,573)
		else:
			mouse.position = (235,576)
		mouse.click(Button.left)
		time.sleep(click_delay)

def start_round():

	global mouse
	global click_delay

	mouse.position = (998,604)
	mouse.click(Button.left)
	time.sleep(click_delay)
	mouse.position = (998,767)

def is_round():
	button = ImageGrab.grab((981,585,1014,617))
	paused_button = Image.open("resources/play_button.png")
	return list(button.getdata()) == list(paused_button.getdata())

def is_dead():
	death = ImageGrab.grab((345,254,371,283))
	death_image = Image.open("resources/dead.png")
	return list(death.getdata()) == list(death_image.getdata())

def main():

	#find money address
	pid = Process.get_pid_by_name(f"Z:\home\{getpass.getuser()}\.local\share\Steam\steamapps\common\BloonsTD6\BloonsTD6.exe")
	if not pid:
		raise(Exception("Could not find BloonsTD6 PID"))

	game = next(Process.open_process(pid).gen)
	print("Locating money memory address...")
	addrs = game.search_all_memory(ctypes.c_double(850))
	place(852,608,2)
	modify(0,"sell")

	money_addr = game.search_addresses(addrs,ctypes.c_double(783))
	if len(money_addr) != 1:
		raise(Exception(f"There were {len(money_addr)} possible addresses instead of 1"))
	money_addr = money_addr[0]
	print("Found!")

	#find health address
	print("Locating health memory address...")
	addrs = game.search_all_memory(ctypes.c_double(200))

	start_round()
	start_round()
	while not is_round():
		time.sleep(1/15)
	start_round()
	while not is_round():
		time.sleep(1/15)
	game_round = 2

	health_addr = game.search_addresses(addrs,ctypes.c_double(191))
	if len(health_addr) != 1:
		print(health_addr)
		raise(Exception(f"There were {len(health_addr)} possible addresses instead of 1"))
	health_addr = health_addr[0]
	print("Found!")

	#round loop
	money = 783
	health = 191
	while True:

		#run round
		start_round()
		game_round += 1
		while not is_round():
			if is_dead():
				print("I died!")
				quit()
			time.sleep(1/15)

		#post round activities
		money = game.read_memory(money_addr,ctypes.c_double()).value
		health = game.read_memory(health_addr,ctypes.c_double()).value
		print(f"Round {game_round} done!")
		print(f"I have {money}$")
		print(f"I have {health} health")

if __name__ == "__main__":
	main()
