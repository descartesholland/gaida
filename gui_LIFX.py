import time
import threading
from timeit import default_timer as timer
import lazylights
import colorsys

try:
   import Tkinter as tk
   import Queue as queue
except ImportError:
   import tkinter as tk
   import queue as queue

LIFX_CONNECT = True

global top
global LAST_UPDATE

MIN_REFRESH_INTERVAL = 0.5
LAST_UPDATE = 0
lastUpdateTimestamp = 0

bulbs = lazylights.find_bulbs(expected_bulbs=1, timeout=10)
print "Found bulb(s): ", bulbs, "\nState", lazylights.get_state(bulbs, timeout=5)

MAXIMUM = 40.0
buffSize = 30


top = tk.Tk()
#top.attributes("-fullscreen", True)
top.configure(background = 'black')
w, h = top.winfo_screenwidth()/1.25, top.winfo_screenheight()/2.
#top.overrideredirect(1)
top.geometry("%dx%d+0+0" % (w, h))
top.focus_set()

top.bind('<Escape>', lambda e: e.widget.quit())# top.destroy())

def turnOn():
    lazylights.setpower(bulbs, True)

def turnOff():
    lazylights.setpower(bulbs, False)

onButton = tk.Button(top, text="on", command=lambda x : turnOn, bg="#001a00", fg='#004d00')
onButton.grid(column = 1, columnspan = 1, row = 0, sticky='nsew')

offButton = tk.Button(top, text="off", command=lambda x: turnOff, bg="#001a00", fg='#004d00')
offButton.grid(column = 0, columnspan = 1, row = 0, sticky='nsew')

quitButton = tk.Button(top, text="quit", command=lambda: top.quit() , bg="#ff00ff")
quitButton.grid(column = 0, columnspan = 1, row = 5, sticky='nsew')

BAR_WIDTH = 600

sumR = BAR_WIDTH / 2
sumG = BAR_WIDTH / 2
sumB = BAR_WIDTH / 2

barHeight = '100'
rCan = tk.Canvas(top, width=str(BAR_WIDTH), height=barHeight, relief='raised', bg='black', cursor='dot')
rCanColorPoly = rCan.create_polygon(0, 0, 0, barHeight, sumR, barHeight, sumR, 0, fill = 'red')
rCanBlackPoly = rCan.create_polygon(sumR, 0, sumR, barHeight, BAR_WIDTH, barHeight, BAR_WIDTH, 0, fill='black')
rCan.itemconfig(rCanColorPoly, tags=('colorPoly'))
rCan.itemconfig(rCanBlackPoly, tags=('blackPoly'))
rCan.grid(column=0, columnspan=2, row = 2, sticky='w', padx='5')

rCanStrVar = tk.StringVar()
rCanStrVar.set(str(sumR))
rCanLabel = tk.Label(top, anchor='center', bd=0, bg='black', cursor='cross', fg='red', textvariable=rCanStrVar)
rCanLabel.grid(column = 2, row = 2, sticky='w')

gCan = tk.Canvas(top, width=str(BAR_WIDTH), height=barHeight, relief='raised', cursor='dot', bg='black')
gCanColorPoly = gCan.create_polygon(0, 0, 0, barHeight, sumG, barHeight, sumG, 0, fill='green')
gCanBlackPoly = gCan.create_polygon(sumG, 0, sumG, barHeight, BAR_WIDTH, barHeight, BAR_WIDTH, 0, fill='black')
gCan.itemconfig(gCanColorPoly, tags=('colorPoly'))
gCan.itemconfig(gCanBlackPoly, tags=('blackPoly'))
gCan.grid(column=0, columnspan=2, row = 3, sticky='w', padx='5')

gCanStrVar = tk.StringVar()
gCanStrVar.set(str(sumG))
gCanLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', bg='black', fg='green', textvariable=gCanStrVar)
gCanLabel.grid(column = 2, row = 3, sticky='w')

bCan = tk.Canvas(top, width=str(BAR_WIDTH), height=barHeight, relief='raised', cursor='dot', bg='black')
bCanColorPoly = bCan.create_polygon(0, 0, 0, barHeight, sumB, barHeight, sumB, 0, fill='blue')
bCanBlackPoly = bCan.create_polygon(sumB, 0, sumB, barHeight, BAR_WIDTH, barHeight, BAR_WIDTH, 0, fill='black')
bCan.itemconfig(bCanColorPoly, tags=('colorPoly'))
bCan.itemconfig(bCanBlackPoly, tags=('blackPoly'))
bCan.grid(column=0, columnspan=2, row = 4, sticky='w', padx='5')

bCanStrVar = tk.StringVar()
bCanStrVar.set(str(BAR_WIDTH))
bCanLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', fg='blue', bg='black', textvariable=bCanStrVar)
bCanLabel.grid(column = 2, row = 4, sticky='w')


top.columnconfigure(0, weight=3)
top.columnconfigure(1, weight=3)
top.columnconfigure(2, weight=1)
top.rowconfigure(0, weight=2)
top.rowconfigure(1, weight=1)
top.rowconfigure(2, weight=1)
top.rowconfigure(3, weight=1)
top.rowconfigure(4, weight=1)
top.rowconfigure(5, weight=1)


def RGBtoHSB(r, g, b):
   print("R", r, "G", g, "B", b)
   hue = 0
   sat = 0
   bright = 0

   _max = max(r, g, b)/float(255)
   _min = min(r, g, b)/float(255)
   delta = float(_max - _min)
   
   bright = float(_max)
   if _max != 0:
      sat = delta / float(_max)
   else:
      sat = 0
   if sat != 0:
      if r == max(r, g, b):
         hue = float(g/float(255) - b/float(255)) / delta
      elif g == max(r, g, b):
         hue = 2 + (b/float(255) - r/float(255)) / delta
      else:
         hue = 4 + float(r/float(255) - g/float(255)) / delta
   else:
      hue = -1
   hue = hue * 60
   if hue < 0:
      hue+= 360
         
   return (hue, sat, bright)


def resend():
    #if timer() > LAST_UPDATE + MIN_REFRESH_INTERVAL:
      #hsb = RGBtoHSB(float(rCanStrVar.get()), float(gCanStrVar.get()), float(bCanStrVar.get()))
      hsb = colorsys.rgb_to_hsv(float(rCanStrVar.get()) / BAR_WIDTH, float(gCanStrVar.get()) / BAR_WIDTH, float(bCanStrVar.get()) / BAR_WIDTH)

      #hsb[0] = hsb[0] * 360

      print 'HSB', hsb[0]*360, hsb[1], hsb[2]
      
      if LIFX_CONNECT:
          print("Updating light(s)...")
          #lifx.set_light_state(hsb[0], hsb[1], hsb[2], 2400)
          lazylights.set_state(bulbs, hsb[0]*360, hsb[1], hsb[2], 5000, 500)

      top.update_idletasks()
      top.update()

def updateHeight(can, val, _fill):
    global LAST_UPDATE

    #Create new bar
    can.coords(can.find_withtag("colorPoly"), 0, 0, 0, barHeight, val, barHeight, val, 0)
    can.coords(can.find_withtag("blackPoly"), val, 0, val, barHeight, BAR_WIDTH, barHeight, BAR_WIDTH, 0)

    
    if can == rCan:
        rCanStrVar.set(str(val))
    elif can == gCan:
        gCanStrVar.set(str(val))
    elif can == bCan:
        bCanStrVar.set(str(val))

    hsb = colorsys.rgb_to_hsv(float(rCanStrVar.get()) / BAR_WIDTH, float(gCanStrVar.get()) / BAR_WIDTH, float (bCanStrVar.get()) / BAR_WIDTH)

    if timer() > LAST_UPDATE + MIN_REFRESH_INTERVAL:
        top.update_idletasks()
        top.update()
        LAST_UPDATE = timer()
        resend()


#Attach Motion Event Listeners

#rCan.bind("<Button-1>", lambda event:updateHeight(event.widget, event.x, 'red'))
rCan.tag_bind(rCan.find_withtag("colorPoly"), "<B1-Motion>", lambda event:updateHeight(rCan, event.x, 'red'))
rCan.tag_bind(rCan.find_withtag("blackPoly"), "<B1-Motion>", lambda event:updateHeight(rCan, event.x, 'red'))

#gCan.bind("<Button-1>", lambda event:updateHeight(event.widget, event.x, 'green'))
gCan.tag_bind(gCan.find_withtag("colorPoly"), "<B1-Motion>", lambda event:updateHeight(gCan, event.x, 'green'))
gCan.tag_bind(gCan.find_withtag("blackPoly"), "<B1-Motion>", lambda event: updateHeight(gCan, event.x, 'green'))


#bCan.bind("<Button-1>", lambda event:updateHeight(event.widget, event.x, 'blue'))
bCan.tag_bind(bCan.find_withtag("colorPoly"), "<B1-Motion>", lambda event:updateHeight(bCan, event.x, 'blue'))
bCan.tag_bind(bCan.find_withtag("blackPoly"), "<B1-Motion>", lambda event:updateHeight(bCan, event.x, 'blue'))


buffR = queue.Queue()
buffG = queue.Queue()
buffB = queue.Queue()

# Main program
LAST_UPDATE = timer()

if True:
#with lifx.run():
    #tk.Button(top, text="Quit", command=quit).pack()
    top.mainloop()

top.quit()
