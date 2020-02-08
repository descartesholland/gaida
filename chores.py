from datetime import datetime as dt
from datetime import timedelta as td
import pickle
import os 
import requests
import time
import threading
from timeit import default_timer as timer
import util
try:
   import Tkinter as tk
   import Queue as queue
except ImportError:
   import tkinter as tk
   import queue as queue

global top
global OUTPUT_FN
OUTPUT_FN = os.path.join(os.getcwd(), "chores_output.txt")

### GUI INIT -- must run before any impl created
top = tk.Tk()
#top.attributes("-fullscreen", True)
top.configure(background = 'black')
w, h = top.winfo_screenwidth()/1.25, top.winfo_screenheight()/1.25
top.geometry("%dx%d+0+0" % (w, h))
top.focus_set()
top.bind('<Escape>', lambda e: e.widget.quit())


class ChoreStore(object):
    global OUTPUT_FN
    global BACKUP_FN
    BACKUP_FN = os.path.join(os.getcwd(), "BKUP_CHORES.bkup")

    def __init__(self, load=True):
        global BACKUP_FN
        self.TAG = "[ChoreStore] "
        self.store = {}
        if(load):
           self.store = pickle.load(open(BACKUP_FN, 'rb'))
           _headstr = "LOADED STORE (" + str(self.count()) + ")"
           _tailstr = ''
           i = 1
           while i <= 105:
              _tailstr+= '-'
              i+=1
           _tailstr+="|"
           _headstr+="\n" + _tailstr
           _str = "\n"
           for k in self.store.keys():
              for kk in self.store[k]:
                 _str+= str(kk) + "\n"
           self.log(_headstr + _str + _tailstr)
              #self.log( + str([self.store[k] for k in self.store.keys()]))
        self.log("Instantiated!")

    def count(self):
        return sum([len(self.store[k]) for k in self.store.keys()])

    def add_bulk(self, cs, save=True):
        for c in cs:
            self.add(c)
        if save:
           self.backup()

    def add(self, c):
        if(isinstance(c, list)):
            self.add_bulk(c)
            return
        self.log("Adding " + str(c.category) + " task " + str(c.name) + "...")
        _cat = str(c.category)
        if _cat in self.store:
            m = self.store[_cat]
            m.append(c)
            self.store[_cat] = m
        else:
            self.store[_cat] = [c]
        self.log("Success! " + _cat + " now has " + str(len(self.store[_cat])) + " item(s).")

    def backup(self):
        global BACKUP_FN
        a = str(self.count())
        pickle.dump(self.store, open(BACKUP_FN, 'wb'))
        print(a + " chores saved.")

    def log(self, _s):
        print(self.TAG + str(_s))


class Chore(object):
    global OUTPUT_FN

    def __init__(self, category, name, freq, date=time.time()):
       #date = (dt(2019, 12, 2)- dt(1970,1,1)).total_seconds()
        self.category = category
        self.name = name
        self.freq = self.interpret_datestr(freq)
        self.dates = [] # hold long!
        self.update(date, silent=True)
        self.log("Created " + self.category + " instance:\n" + str(self))

    '''
    Compute and return the timestamp of the next time this should be done.
    '''
    def getNext(self):
        if not self.dates or len(self.dates) == 0 or not self.freq:
            self.log("getNext() failing fast! figure why")
            return ""
        _next = self.freq + self.dates[-1]
        return _next


    '''
    Mark this object as having a new completion instance
    - date epoch timestamp as long
    '''
    def update(self, date, silent=False):
        if(date is None or isinstance(date, str)):
            self.log("update() DATE input is None or str type! Failing fast.")
            return
        self.dates.append(date)
        if not silent:
           self.log("Recorded " + self.category + " task '" + self.name + "' as having been completed on " + str(date))
           notify()
        self.getNext()


    def interpret_datestr(self, datestr):
        try:
            _num = float(datestr[:-1])
        except:
            self.log("Failed to interpret date string " + str(datestr))
            return
        if datestr.endswith('m'):
            return util.mo2sec(_num)
        elif datestr.endswith('w'):
            return util.wk2sec(_num)
        elif datestr.endswith('d'):
            return util.day2sec(_num)


    def __repr__(self):
       _t = ""
       i = 1
       while i <= 105:
          if i in [9, 25, 73, 90]:
             _t+='||'
             i+=2
             continue
          _t+= '-'
          i+=1
       _t+="|"   
       return _t + "\n\t|| " + self.category + "\t|| " + self.name + ("\t\t\t\t\t\t" if len(self.name) < 6 else ("\t\t\t\t\t" if len(self.name) < 12 else ("\t\t\t\t" if len(self.name) < 23 else ("\t\t\t" if len(self.name) < 28 else ("\t\t" if len(self.name) < 36 else "\t"))))) + "|| Last: " + util.beaut(self.dates[-1]) + "   || Next: " + util.beaut(self.getNext()) + "  |"

    def log(self, _s):
        global OUTPUT_FN
        print(_s)
        with open(OUTPUT_FN, 'a') as f:
            f.write("[" + util.beaut(time.time(), False) + "] " + _s + "\n")


#### GUI 
top.update()

def refresh_impls():
   print("Refreshing...")

def get_timestamp():
   return util.beaut(time.time())

def notify():
   cs.backup()


''' INITIAL SETUP OF CHORESTORE AS DEFINED ARBITRARILY. USE WITH CAUTION '''
def seed(cs):
    cleaning = [
        Chore("Cleaning", "Toilet", "2w"),
        Chore("Cleaning", "Sink & Fixtures", "14d"),
        Chore("Cleaning", "Mirror", "3w"),
        Chore("Cleaning", "Tub", "1.5m"),
        Chore("Cleaning", "Mold Control: Bath Tile", "1.5w"),
        Chore("Cleaning", "Mold Control: Kitchen Sink", "1.5w"),
        Chore("Cleaning", "Kitchen Table", "1m"),
        Chore("Cleaning", "Kitchen Counters", "3w"),
        Chore("Cleaning", "Oven & Stove", "3w"),
        Chore("Cleaning", "Desk", "2w")
    ]
    cs.add_bulk(cleaning, save=False)

    d = "Dusting"
    dusting = [
        Chore(d, "Bedroom: Lights, Sills, Doors", "1m"),
        Chore(d, "LR: Lights, Sills, Doors, Media Center", "1m"),
        Chore(d, "Bathroom: Lights, Doors, Heater", "1m")
    ]
    cs.add_bulk(dusting, save=False)

    s = "Sweeping"
    sweeping = [
        Chore(s, "LR", "3.5w"),
        Chore(s, "Hallway", "3w"),
        Chore(s, "Kitchen", "3w"),
        Chore(s, "Bathroom", "3.5w"),
        Chore(s, "Bedroom", "3w")
    ]
    cs.add_bulk(sweeping, save=False)

    v = "Vacuuming"
    vacuuming = [
        Chore(v, "Hallway", "3w"),
        Chore(v, "Bedroom", "2w")
    ]
    cs.add_bulk(vacuuming, save=False)


cs = ChoreStore(load=True)
#seed(cs)
#cs.backup()

''' too lazy to figure out how to parse input correctly without
getting a nameerror, so just catch the exception and parse the 
name into the string like i wanted '''
def jank_hack():
   try:
      return str(input())
   except NameError as e:
      return str(e)[str(e).index("'")+1:str(e).rindex("'")]

def edit():
   global _ss
   _ss = []
   def present():
      global _ss
      _ss = []
      for k in cs.store.keys():
         _ss.extend(cs.store[k])
      _ss = sorted(_ss, key=Chore.getNext)
      for i in range(len(_ss)):
         print(str(_ss[i]) + "(" + str(i) + ") " )

   e = "e"
   a = "a" # not needed
   _in = jank_hack()
   print("INPUT: '" + str(_in) + "'")
   if _in == 's':
      cs.backup()
      
   elif _in == 'e':
      present()
      # Await numeric selection
      _num = int(input())
      print("INPUT: '" + str(_num) + "'")
      print("Selection:  " + str(_ss[_num]))
      print("NEW? ")

      # Await str input
      _in= jank_hack() + "/2020"
      d = dt.strptime(_in, "%m/%d/%Y") + td(hours=dt.today().hour)
      _ss[_num].update( (d - dt(1970,1,1)).total_seconds() )
      present()
      
   elif _in == 'a':
      # Add new listing 
      present()
      print("Category: ")
      _cat = jank_hack()

      print("Name: ")
      _name = jank_hack()
      print("Got name '" + str(_name) + "'")

      print("Freq: ")
      _freq = jank_hack()

      print("Last Complete (include year): ")
      _lc = jank_hack()
      if len(_lc) > 1:
         d = dt.strptime(_lc, "%m/%d/%Y") + td(hours=dt.today().hour)
         _lc = (d - dt(1970,1,1)).total_seconds()
      else:
         _lc = time.time()

      new_chore = Chore(_cat,_name,_freq,_lc)
      cs.add(new_chore)
      present()
      cs.backup()

   elif _in == 'd':
      # Delete existing
      present()
      print("Make selection: " )
      _num = int(input())
      print("Selection:  " + str(_ss[_num]))

      for k in cs.store.keys():
         if _ss[_num] in cs.store[k]:
            print("(Found. Confirm Y/N):")
            _in = jank_hack()
            if _in in ["y", "Y"]:
               cs.store[k].remove(_ss[_num])
               cs.backup()
               present()
                  

refButton = tk.Button(top, text="REFRESH", command=edit, bg="#22e622")
refButton.grid(column=0, columnspan=1, row=9, sticky='nsew')

quitButton = tk.Button(top, text=" == QUIT == ", command=lambda: top.quit() , bg="#ff00ff")
quitButton.grid(column = 2, columnspan = 1, row = 9, sticky='nsew')

top.columnconfigure(0, weight=3)
top.columnconfigure(1, weight=3)
top.columnconfigure(2, weight=1)

top.rowconfigure(0, weight=4)
top.rowconfigure(1, weight=2)
top.rowconfigure(2, weight=2)
top.rowconfigure(3, weight=2)
top.rowconfigure(4, weight=4)
top.rowconfigure(8, weight=4)
top.rowconfigure(9, weight=2)

#edit()
while True:
#with lifx.run():
   edit()
   #top.mainloop()




