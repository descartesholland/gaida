import time
import threading

import pywemo

from timeit import default_timer as timer
import lazylights
import colorsys

try:
   import Tkinter as tk
   import Queue as queue
except ImportError:
   import tkinter as tk
   import queue as queue

LIFX_CONNECT = True # should make LIFX connection

global top
global LAST_UPDATE


class WemoImpl(object):
  def __init__(self):
    self.logname = "[Wemo] "
    self.tv_id="1"
    self.rex_id="2"
    self.ip = None #"10.42.0.39"

    self.devices = {}
    self.refreshing = False
    self.refresh_devices_async()

  def refresh_devices_async(self):
    print("Refreshing devices...")
    self.refreshing = True
    this = self
    def _run():
      try:
        ds = pywemo.discover_devices()
        print(this.logname + "Done discovery!")
        if ds == []:
          print(this.logname + "No devices found.")
          if this.ip is not None:
            # Nothing returned; attempt manual discovery via IP
            # TODO check if this works
            print(this.logname + "Attempting manual discovery on " + str(this.ip) + "...")
            port = pywemo.ouimeaux_device.probe_wemo(this.ip)
            url = 'http://%s:%i/setup.xml' % (this.ip, port)
            d = pywemo.discovery.device_from_description(url, None)
            print(this.logname + "Got Device: " + str(d))
            this.devices = { d : d.get_state(force_update=True) }
            return

        this.devices = { d : d.get_state(force_update=True) for d in ds }
        print(this.logname + "Got Device(s): " + str(this.devices))
        this.last_update = time.time()
      except:
        print(this.logname + "DISCOVERY FAILED!")

      this.refreshing = False

    t = threading.Thread(target=_run)
    #t.daemon = True
    t.start()

  def toggle_tv(self):
    print("Toggling TV lights...")
    for k in self.devices:
      if self.tv_id in str(k):
        k.toggle()
        print("Toggled TV lights.")
        return

  def toggle_tank(self):
    print("Toggling Rex's lights...")
    for k in self.devices:
      if self.rex_id in str(k):
        k.toggle()
        print("Toggled Rex's lights.")
        return


MIN_REFRESH_INTERVAL = 0.5
LAST_UPDATE = 0
lastUpdateTimestamp = 0

impl = WemoImpl()

global br
bulbs = lazylights.find_bulbs(expected_bulbs=1, timeout=5)
states = lazylights.get_state(bulbs, timeout=5)
print "Found bulb(s): ", bulbs, "\nState(s): ", states
if len(states) > 0 :
  br = states[0].kelvin 
  print( "Set BR to " + str(br))

MAXIMUM = 40.0
buffSize = 30


top = tk.Tk()
#top.attributes("-fullscreen", True)
top.configure(background = 'black')
w, h = top.winfo_screenwidth()/1.25, top.winfo_screenheight()/1.25
#top.overrideredirect(1)
top.geometry("%dx%d+0+0" % (w, h))
top.focus_set()

top.bind('<Escape>', lambda e: e.widget.quit())# top.destroy())

def turnOn():
    lazylights.setpower(bulbs, True)

def turnOff():
    lazylights.setpower(bulbs, False)

onButton = tk.Button(top, text="on", command=turnOn, bg="#001a00", fg='#004d00')
onButton.grid(column = 1, columnspan = 1, row = 0, sticky='nsew')

offButton = tk.Button(top, text="off", command=turnOff, bg="#001a00", fg='#004d00')
offButton.grid(column = 0, columnspan = 1, row = 0, sticky='nsew')

filterOnButton = tk.Button(top, text="TV Lights On", command=impl.toggle_tv, bg="#001a00", fg='#004d00')
filterOnButton.grid(column = 1, columnspan = 1, row = 5, sticky='nsew')

filterOffButton = tk.Button(top, text="TV Lights Off", command=impl.toggle_tv, bg="#001a00", fg='#004d00')
filterOffButton.grid(column = 0, columnspan = 1, row = 5, sticky='nsew')

tankLightOnButton = tk.Button(top, text="Tank Lights On", command=impl.toggle_tank, bg="#001a00", fg='#004d00')
tankLightOnButton.grid(column = 1, columnspan = 1, row = 6, sticky='nsew')

tankLightOffButton = tk.Button(top, text="Tank Lights Off", command=impl.toggle_tank, bg="#001a00", fg='#004d00')
tankLightOffButton.grid(column = 0, columnspan = 1, row = 6, sticky='nsew')


#quitButton = tk.Button(top, text="quit", command=lambda: top.quit() , bg="#ff00ff")
#quitButton.grid(column = 0, columnspan = 1, row = 5, sticky='nsew')

BAR_WIDTH = float(w/1.1) #600

sumR = int(round(BAR_WIDTH / 2))
sumG = int(round(BAR_WIDTH / 2))
sumB = 0#int(round(BAR_WIDTH / 2))

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
bCanStrVar.set(str(sumB))
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
top.rowconfigure(6, weight=1)

def resend():

      global br
      global states
      print("resend!")

      top.update_idletasks()
      top.update()
    #if timer() > LAST_UPDATE + MIN_REFRESH_INTERVAL:
      rgb = (float(rCanStrVar.get()) / BAR_WIDTH, float(gCanStrVar.get()) / BAR_WIDTH, float(bCanStrVar.get()) / BAR_WIDTH)
      hsb = colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2])

      print 'HSB', hsb[0]*360, hsb[1], hsb[2]
      print 'From RGB', rgb[0], rgb[1], rgb[2]
      
      if LIFX_CONNECT:
          print("Updating light(s)...")
          lazylights.set_state(bulbs, hsb[0]*360, hsb[1], hsb[2], br, 500)
          states = lazylights.refresh(expected_bulbs=1, timeout=1)
          print("new state " + str(lazylights.get_state(bulbs, timeout=5)))



def updateHeight(can, val, _fill):
    global LAST_UPDATE

    #Create new bar
    can.coords(can.find_withtag("colorPoly"), 0, 0, 0, barHeight, val, barHeight, val, 0)
    can.coords(can.find_withtag("blackPoly"), val, 0, val, barHeight, BAR_WIDTH, barHeight, BAR_WIDTH, 0)

    
    if can == rCan:
        rCanStrVar.set(str(int(round(val))))
    elif can == gCan:
        gCanStrVar.set(str(int(round(val))))
    elif can == bCan:
        bCanStrVar.set(str(int(round(val))))

    hsb = colorsys.rgb_to_hsv(float(rCanStrVar.get()) / BAR_WIDTH, float(gCanStrVar.get()) / BAR_WIDTH, float (bCanStrVar.get()) / BAR_WIDTH)

    if timer() > LAST_UPDATE + MIN_REFRESH_INTERVAL:
        top.update_idletasks()
        top.update()
        LAST_UPDATE = timer()
        if float(bCanStrVar.get()) != 0:
          print("LAST_UPDATE " + str(LAST_UPDATE) + " " + str(float(bCanStrVar.get()) / BAR_WIDTH))
          resend()

# Set GUI bar state to that of light:
if len(states) > 0:
  _max = 16.**4
  s = states[0]
  rgb = colorsys.hsv_to_rgb(s.hue/_max, s.saturation/_max, s.brightness/_max)
  print("Pre seeding to " + str((rgb[0] * BAR_WIDTH, rgb[1]*BAR_WIDTH, rgb[2]*BAR_WIDTH)))
  updateHeight(rCan, rgb[0] * BAR_WIDTH, 'red')
  updateHeight(gCan, rgb[1] * BAR_WIDTH, 'green')
  updateHeight(bCan, rgb[2] * BAR_WIDTH, 'blue')
  print("Pre seed " + str(float(bCanStrVar.get()) / BAR_WIDTH))

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

#top.quit()
