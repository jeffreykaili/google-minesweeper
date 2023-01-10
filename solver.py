import pytesseract
import cv2
from PIL import Image 
import pyautogui 
import keyboard
import sys
import numpy as np
import time 

# Plays Google's Minesweeper game (HARD), found at 
# https://www.google.com/search?q=minesweeper

board_left = 652 
board_top = 336
board_width = 600 
board_height = 500 
square_size = 24 

brown_RGB = (229, 194, 159)
brown_RGB2 = (215, 184, 153)
green_RGB = (162, 209, 73)
green_RGB2 = (170, 215, 81)
border_RGB = (135, 175, 58)

def get_grid():
	pyautogui.screenshot("grid.png", region = (board_left, board_top, board_width, board_height))
	grid_img = Image.open("grid.png").convert("RGB")
	S = set()
	grid_vals = [[None for j in range(24)] for i in range(20)]
	for x1 in range(0, board_width, square_size + 1):
		for y1 in range(0, board_height, square_size + 1):
			x2, y2 = x1 + square_size, y1 + square_size
			cell = grid_img.crop((x1, y1, x2, y2))
			cell_rgb = cell.load() 

			# FOR DEBUGGING, remove .load() in previous line: cell.save(f"images/{x1}-{y1}.png", "PNG") 

			scaled_x1 = x1 // (square_size + 1)
			scaled_y1 = y1 // (square_size + 1)

			# Now, determine what type of cell we have:
			# -1 = not revealed, 0 = revealed with no mine or number, 1-9 = number  

			cell_C = cell_rgb[square_size // 2, square_size // 2]	
			if cell_C == brown_RGB or cell_C == brown_RGB2:
				# this cell is revealed and doesn't contain a mine or number 
				grid_vals[scaled_y1][scaled_x1] = 0 
			elif cell_C == green_RGB or cell_C == green_RGB2:
				# this cell hasn't been clicked yet 
				grid_vals[scaled_y1][scaled_x1] = -1 
			else: 
				# we need to read the number, we convert it to a black and white image for pytesseract 

				# first, we further crop the image to get rid of other colours 
				cell = cell.crop((4, 4, 21, 21))
				# cell.save(f"images3/{x1}-{y1}.png", "PNG")

				cell.save(f"cell.png", "PNG")
				cell_cv2 = cv2.imread("cell.png")
				gray = cv2.cvtColor(cell_cv2, cv2.COLOR_BGR2GRAY) # convert to greyscale 

				# our squares are small, so we need to sharpen the blurred sections 
				# so, we use a sharpening kernal to enhance the blurred sections 
				sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]) 
				sharpen = cv2.filter2D(gray, -1, sharpen_kernel)
				thresh = cv2.threshold(sharpen, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

				number = pytesseract.image_to_string(thresh, lang='eng', config='--psm 10 digits').strip()

				if len(number) != 1: return get_grid()
				try: 
					grid_vals[scaled_y1][scaled_x1] = int(number) 
				except: # if we took a screenshot during the animation 
					return get_grid() 

	return grid_vals 

def click_cell(cell):
	y, x = cell
	print(y, x)
	pyautogui.click(x = board_left + square_size // 2 + x * (1 + square_size), y = board_top + square_size // 2 + y * (1 + square_size)) 
	pyautogui.moveTo(board_left // 2, board_top + square_size // 2 + y * square_size)
	time.sleep(0.2)

def process(y, x, grid):
	d = {"unknown" : [], "safe" : [], "num_around" : 0}
	for i in range(y - 1, y + 2):
		for j in range(x - 1, x + 2):
			if i < 0 or i > 19 or j < 0 or j > 23 or (i == y and j == x):
				continue 
			d["num_around"] += 1 
			if grid[i][j] == -1: 
				d["unknown"].append([i, j])
			else:
				d["safe"].append([i, j])
	return d 

def solve_grid(grid):
	# TODO: improve solving methods for higher winrate 

	flags = [[0 for j in range(24)] for i in range(20)]
	for y in range(20):
		for x in range(24):
			if grid[y][x] != -1 and grid[y][x] != 0: 
				tiles = process(y, x, grid)
				num_mines = grid[y][x] 
				if num_mines == len(tiles["unknown"]):
					# all of these unclicked squares are mines 
					for FLAG in tiles["unknown"]: 
						flags[FLAG[0]][FLAG[1]] = 1 

	guess_cells = []
	# find if we can click anything 
	for y in range(20):
		for x in range(24):
			if grid[y][x] != -1 and grid[y][x] != 0: 
				tiles = process(y, x, grid)
				good = []
				mines = 0 
				num_mines = grid[y][x] 
				for cell in tiles["unknown"]:
					yy, xx = cell
					if flags[yy][xx]: 
						mines += 1 
					else:
						good.append([yy, xx])

				if mines == num_mines and len(good): 
					click_cell(good[0])
					return

				for cell in good: 
					guess_cells.append(cell)

	print(guess_cells[0])
	click_cell(guess_cells[0]) # if we have to guess 

def done(grid):
	for x in grid:
		for y in x:
			if y == -1: return False 
	return True 

def play():
	keyboard.wait("q") # Press Q once tabbed into the minesweeper window 
	pyautogui.moveTo(board_left // 2, board_top + board_height >> 1) 
	click_cell([9, 11])
	time.sleep(0.5)

	grid = get_grid() 
	while not done(grid): 
		solve_grid(grid)
		grid = get_grid()
	print(done(grid))

play()