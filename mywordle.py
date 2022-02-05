#!/usr/bin/env python

"""
A simple implementation of Wordle using PySimpleGUI.
Written under exam conditions so could be significantly tidied up.

Run with: 

```
$ python mywordle.py
```

"""

import sys
import os
import string
import requests
import random

import PySimpleGUI as sg

n_rows, n_cols = 6, 5
cell_size = (2, 1)
CLOSE, RESTART = "CLOSE", "RESTART"
FIRST_WORDS_OF_ARRAYS = "cigar", "aahed"
letters = string.ascii_letters
words_cache = "words.txt"

bg_clear, bg_correct, bg_near = "white", "green", "orange"

words_to_use_max_index = None
words = None
focus = None
window = None
grid = None
target = None


def extract_word_lists(content):
  global words_to_use_max_index
  words = []

  for first_word in FIRST_WORDS_OF_ARRAYS:
    start = content.find(f'["{first_word}"')
    end = start + content[start:].find("]") + 1

    _words = eval(content[start:end])
    if not words_to_use_max_index:
        words_to_use_max_index = len(_words)

    words.extend(_words)

  return words

def load_words():
  if os.path.isfile(words_cache):
    print("[INFO] Reading from cached words.")
    return open(words_cache).read().split()

  content = requests.get("https://www.powerlanguage.co.uk/wordle/main.e65ce0a5.js").text
  words = extract_word_lists(content)

  # Write to cache
  with open(words_cache, "w") as writer:
    writer.write(" ".join(words))

  return words

def get_word(y):
  return "".join([grid[y][x].get() for x in range(n_cols)]).lower()

def set_focus(x, y):
  global focus, window
  focus = x, y

  if window:
    window["position"].update(f"({x}, {y})")
    highlight(x, y)

def highlight(x, y):
    for i in range(n_cols):
      if i == x:
        window[f"cell_{i}_{y}"].Widget.configure(highlightbackground='black', highlightthickness=2)
      else:
        window[f"cell_{i}_{y}"].Widget.configure(highlightthickness=0)

    # Tidy last row
    if x == 0 and y > 0:
      window[f"cell_{n_cols-1}_{y-1}"].Widget.configure(highlightthickness=0) 

def get_focus():
  return focus

def get_header():
  return [sg.Text("150 minute wordle challenge!", font=("Arial", 10, "bold"))]

def get_cell(x, y):
  return sg.Text("", size=cell_size, background_color=bg_clear, text_color="black", key=f"cell_{x}_{y}", justification='center')

def update_cell(x, y, clear=False, correct=False, near=False):
  cell = window[f"cell_{x}_{y}"]
  value = cell.get()
  bg_color = bg_clear

  if clear:
    bg_color = bg_clear
    value = ""
  elif value.lower() == target[x] or correct:
    bg_color = bg_correct
  elif value.lower() in target or near:
    bg_color = bg_near

  cell.update(value=value, background_color=bg_color)

def update_row(y, correct=False):
  for x in range(n_cols):
    update_cell(x, y, correct=correct)

def get_cell_value(x, y):
  return window[f"cell_{x}_{y}"].get()

def get_row(y):
  return [get_cell(x, y) for x in range(n_cols)]

def get_grid():
  return [get_row(y) for y in range(n_rows)]
  
def get_buttons():
  return [sg.Button(RESTART, key=RESTART), sg.Button(CLOSE, key=CLOSE)]

def get_layout(grid):
  return [get_header(), grid, get_buttons(), [sg.Text(f"{get_focus()}", key="position")]]

def init():
  # Load words
  global words, window, grid, target

  if not words:
    words = load_words()
    assert(words[0] == FIRST_WORDS_OF_ARRAYS[0])
    print(f"First word is as expected - words loaded :-)")

  target = random.choice(words[:words_to_use_max_index])

  # Create new window and grid
  if window: window.close()

  set_focus(0, 0)
  grid = get_grid()
  layout = get_layout(grid)

  window = sg.Window("Keyboard Test", layout,
                    return_keyboard_events=True, 
                    use_default_focus=False,
                    element_justification='c')

def get_letter(e):
    if type(e) is not str: return
    #with open('output.txt', 'w') as fw: fw.write(f"{e}\n{type(e)}\n{dir(e)}")
    l = e.upper().split(":")[0]
    if len(l) != 1: return 
    return l

def submit_word():
  # if x != (n_cols - 1): return
  x, y = get_focus()
  row_word = get_word(y)

  if row_word == target:
    update_row(y, correct=True)
    sg.popup("You did it")

  elif row_word in words:
    update_row(y)

    if y < (n_rows - 1):
      y += 1
      x = 0
      set_focus(x, y)
    else:
      sg.popup(f'Bad luck today. The word was: {target}')

  else:
    sg.popup(f"'{row_word}' is not a word!")

def retreat():
  x, y = get_focus()
  # If empty and not first cell
  if not get_cell_value(x, y) and x != 0: 
    set_focus(x-1, y)

  # Empty current
  x, y = get_focus()
  update_cell(x, y, clear=True)


def OLD():
  if x == 0:
    update_cell(x, y, clear=True)
  elif get_cell_value(x, y):
    update_cell(x, y, clear=True)
    set_focus(x-1, y)  
  else:
    set_focus(x-1, y) 
    update_cell(x, y, clear=True)

def advance():
  x, y = get_focus()
  if x < (n_cols - 1):
    x += 1
  set_focus(x, y)

# --- Initialise ---
init()

# ---===--- Loop taking in user input --- #
while True:
    event, values = window.read()

    x, y = get_focus()
    cell = window[f"cell_{x}_{y}"]
    full_row = x == (n_cols - 1)

    letter = get_letter(event)

    if event in (CLOSE, None):
        print("Exiting...bye")
        break

    elif event == RESTART:
        init()
    
    elif event == "BackSpace:22": 
        retreat()

    elif event == "Return:36" and full_row and cell.get():
        submit_word()

    elif letter and letter in letters:
        cell.update(letter)
        advance()


window.close()
