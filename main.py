#libraries
import time, math, random, threading, ctypes, getpass
from mem_edit import Process
from pynput.mouse import Button, Controller
from datetime import datetime
from PIL import ImageGrab, Image

class GameController:

	def __init__(self):

		#variable init
		self.times = [None]*12
		self.mouse = Controller()
		self.click_delay = 0.3
		self.scroll_delay = 0.2
		self.towers = []
		self.column_xcoords = [930,1300]

	def place(self,x,y,tower):
		
		#get tower icon coord
		icon_x = self.column_xcoords[tower%2]
		icon_y = math.floor((tower%12)/2)*75+211
		scroll = math.floor(tower/12)*(-14)

		#add tower to tower list
		self.towers.append([tower,(x,y)])

		#time delay between placing towers
		current_time = datetime.now()
		prev_time = self.times[tower%12]
		if prev_time != None:
			time_difference = current_time-prev_time
			time_difference = math.floor(time_difference.microseconds/10000)/100
			time.sleep(max(0.8-time_difference,0))
			current_time = datetime.now()
		self.times[tower%12] = current_time

		#placing the tower
		self.mouse.position = (icon_x,icon_y)
		if scroll != 0:
			self.mouse.scroll(0,scroll)
			time.sleep(self.scroll_delay)
		self.mouse.click(Button.left)
		time.sleep(self.click_delay)
		if scroll != 0:
			self.mouse.scroll(0,-scroll)
			time.sleep(self.scroll_delay)
		self.mouse.position = (x,y)
		self.mouse.click(Button.left)
		time.sleep(self.click_delay)
		self.mouse.position = (x,767)
		time.sleep(0.4)

	def modify(self,index,action):

		#clicking the tower
		tpos = self.towers[index][1]
		self.mouse.position = tpos
		self.mouse.click(Button.left)
		time.sleep(self.click_delay)

		#selling the tower
		if action == "sell":
			if tpos[0] <= 480:
				self.mouse.position = (838,573)
			else:
				self.mouse.position = (235,576)
			self.mouse.click(Button.left)
			time.sleep(self.click_delay)
			self.towers.pop(index)

	def start_round(self):

		#click start round button
		self.mouse.position = (998,604)
		self.mouse.click(Button.left)
		time.sleep(self.click_delay)
		self.mouse.position = (998,767)

	def is_round(self):
		
		#check if button is in playing mode
		button = ImageGrab.grab((981,585,1014,617))
		paused_button = Image.open("resources/play_button.png")
		return list(button.getdata()) == list(paused_button.getdata())

	def is_dead(self):

		#check for death menu
		death = ImageGrab.grab((345,254,371,283))
		death_image = Image.open("resources/dead.png")
		return list(death.getdata()) == list(death_image.getdata())

class MemoryReader:

	def __init__(self,game_controller):

		#grabbing pid
		pid = Process.get_pid_by_name(f"Z:\home\{getpass.getuser()}\.local\share\Steam\steamapps\common\BloonsTD6\BloonsTD6.exe")
		if not pid:
			raise(Exception("Could not find BloonsTD6 PID"))

		#variable init
		self.game = next(Process.open_process(pid).gen)
		self.money_addr, self.health_addr = None, None
		self.game_controller = game_controller
	
	def get_money_addr(self):

		#search for doubles of value 850
		print("Locating money memory address...")
		addrs = self.game.search_all_memory(ctypes.c_double(850))

		#change money value to 783
		self.game_controller.place(852,608,2)
		self.game_controller.modify(0,"sell")

		#search for changes to 783
		self.money_addr = self.game.search_addresses(addrs,ctypes.c_double(783))
		if len(self.money_addr) != 1:
			raise(Exception(f"There were {len(self.money_addr)} possible addresses instead of 1"))
		self.money_addr = self.money_addr[0]
		print("Found!")
	
	def get_health_addr(self):

		#search for doubles of value 200
		print("Locating health memory address...")
		addrs = self.game.search_all_memory(ctypes.c_double(200))

		#lose two rounds
		self.game_controller.start_round()
		self.game_controller.start_round()
		while not self.game_controller.is_round():
			time.sleep(1/15)
		self.game_controller.start_round()
		while not self.game_controller.is_round():
			time.sleep(1/15)

		#check for changed values to 191
		self.health_addr = self.game.search_addresses(addrs,ctypes.c_double(191))
		if len(self.health_addr) != 1:
			print(self.health_addr)
			raise(Exception(f"There were {len(self.health_addr)} possible addresses instead of 1"))
		self.health_addr = self.health_addr[0]
		print("Found!")
	
	def read_money(self):

		#read the money memory address if it exists
		if not self.money_addr:
			raise(Exception("The money address has not been found yet!"))
		return self.game.read_memory(self.money_addr,ctypes.c_double()).value
	
	def read_health(self):

		#read the health memory address if it exists
		if not self.health_addr:
			raise(Exception("The health address has not been found yet!"))
		return self.game.read_memory(self.health_addr,ctypes.c_double()).value

class Main:
	def __init__(self):

		#variable init
		self.money = 783
		self.health = 191
		self.game_round = 2
		self.game_controller = GameController()
		self.memory_reader = MemoryReader(self.game_controller)

		#get memory addresses
		self.memory_reader.get_money_addr()
		self.memory_reader.get_health_addr()
		while True:
			self.round_loop()
	
	def round_loop(self):

		#run round
		self.game_controller.start_round()
		self.game_round += 1
		while not self.game_controller.is_round():
			if self.game_controller.is_dead():
				print("I died!")
				quit()
			time.sleep(1/15)

		#post round activities
		self.money = self.memory_reader.read_money()
		self.health = self.memory_reader.read_health()
		print(f"Round {self.game_round} done!")
		print(f"I have {self.money}$")
		print(f"I have {self.health} health")
		
if __name__ == "__main__":
	main = Main()
