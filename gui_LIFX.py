 
import colorsys
import lazylights
import requests
import time
import threading
import pywemo
from timeit import default_timer as timer

try:
   import Tkinter as tk
   import Queue as queue
except ImportError:
   import tkinter as tk
   import queue as queue

LIFX_CONNECT = True # should make LIFX connection

global top
global impls
impls = []
global LAST_UPDATE

global tv_ip
tv_ip = '192.168.1.151'

### GUI INIT -- must run before any impl created
top = tk.Tk()
#top.attributes("-fullscreen", True)
top.configure(background = 'black')
w, h = top.winfo_screenwidth()/1.25, top.winfo_screenheight()/1.25
BAR_WIDTH = float(w/1.1) #600
BAR_HEIGHT = '100'
#top.overrideredirect(1)
top.geometry("%dx%d+0+0" % (w, h))
top.focus_set()
top.bind('<Escape>', lambda e: e.widget.quit())


class WemoImpl(object):
  global top
  global known_devices
  global devices

  # wemo device_name : readable name
  known_devices = { "Aaa": "TV Lights", \
                    "Rex": "Kitchen Lights", \
                    "mini": "Bedroom Yellows", \
                    "DINNER DIMMER": "Overhead Purple" \
  }
  def __init__(self, idstr, row, refresh=False):
    global devices
    self.logname = "[Wemo] "
    self.refreshing = False
    self.dev_id = idstr
    self.row = row
    self.ip = None #"10.42.0.39"
    self.btn_bg = '#001a00'
    self.btn_fg = '#004d00'

    try:
       if not devices:
          devices = set()
    except NameError:
       devices = set()

    if(refresh):
       self.refresh_devices_async()
    self.init_gui()

  def refresh_devices_async(self):
    print(self.logname + "Refreshing devices...")
    self.refreshing = True
    this = self
    def _run():
      try:
        ds = pywemo.discover_devices()
        print(self.logname + "Done discovery!")
        if ds == []:
          print(self.logname + "No devices found.")
          if this.ip is not None:
            # Nothing returned; attempt manual discovery via IP
            # TODO check if this works
            print(this.logname + "Attempting manual discovery on " + str(this.ip) + "...")
            port = pywemo.ouimeaux_device.probe_wemo(this.ip)
            url = 'http://%s:%i/setup.xml' % (this.ip, port)
            d = pywemo.discovery.device_from_description(url, None)
            print(this.logname + "Got Device: " + str(d))
            for d in ds:
               devices.add(d)
            return

        for d in ds:
           if True not in [str(d) == str(d2) for d2 in devices]:
              devices.add(d)# = { d : d.get_state(force_update=True) for d in ds }
        print(this.logname + "Got Device(s): " + str(devices)) 
        this.last_update = time.time()
        this.ds = ds
      except Exception as e:
        print(this.logname + "DISCOVERY FAILED! " + str(e))
        this.ds = []

      this.refreshing = False
      this.color_logic()

    t = threading.Thread(target=_run)
    #t.daemon = True ## ? async seems to work fine without this
    t.start()

  def get_name_from_id(self, dev_id):
     global known_devices
     return known_devices.get(dev_id, "<Unknown name>")
  
  def toggle(self):
    global devices
    _name = self.get_name_from_id(self.dev_id)
    print(str(time.time()) +": " + self.logname + "Toggling " + _name + "...")
    for k in devices:
      if str(self.dev_id) in str(k):
        k.toggle()
        _ns = str(k.get_state(force_update=True))
        print(self.logname + "Toggled " + _name + "... NewState " + _ns)
        self.color_logic()
        return
    print("Device " +  _name + " not found!")

  def color_logic(self):
    ''' handles state-based updates to the GUI elements for this implementation 
     might be better to parameterize device itself, but TODO
    '''
    global devices

    if not self.gui_init_complete:
       self.init_gui()
       return

    def _run():
       try:
          for k in devices_states.keys():
             # do for all known devices if unspecified
             if len(self.dev_id) == 0 or self.dev_id in str(k):
                istate = devices_states[k]
                if istate == 8 or istate == 1: # wemo mini 1 is on
                   # mark on button, ensure only one btn can be on at once
                   self.gui_elements[0].config(bg="#ffffff")
                   self.gui_elements[1].config(bg=self.btn_bg)
                elif istate == 0:
                   # mark off button, clear on button
                   self.gui_elements[1].config(bg="#ffffff")
                   self.gui_elements[0].config(bg=self.btn_bg)
       except RuntimeError:
          # Occurs due to race condition; ends up properly populated; too lazy to fix
          pass

    t = threading.Thread(target=_run)
    _devices = devices.copy()
    devices_states = { d : d.get_state(force_update=True) for d in _devices }
    t.start()
           
  def init_gui(self, _small=False):
    global top
    global known_devices
    on = tk.Button(top, text=("On/Off" if _small else known_devices[self.dev_id] + " On"), \
                   command=self.toggle, bg=self.btn_bg, fg=self.btn_fg)
    off = tk.Button(top, text=known_devices[self.dev_id] + " Off", \
                    command=self.toggle, bg=self.btn_bg, fg=self.btn_fg)

    print(self.dev_id)
    if(_small):
       on.grid(column = 2, columnspan = 1, row=self.row, sticky='nsew', pady='10')
       self.gui_elements = [on]
       self.gui_init_complete = True
       return

    on.grid(column = 1, columnspan = 1, row=self.row, sticky='nsew')
    off.grid(column = 0, columnspan = 1, row=self.row, sticky='nsew')
    top.rowconfigure(self.row, weight=4)
    self.gui_elements = [on, off]
    self.gui_init_complete = True
       
  def get_elements(self):
    ''' returns the GUI elements associated with this implementation '''
    return self.gui_elements

  def refresh(self):
     print(self.logname + "Refreshing status...")
     self.color_logic()

class DimmerImpl(WemoImpl):
   def __init__(self, idstr, row, _refresh=False):
      super(DimmerImpl, self).__init__(idstr, row, _refresh)

   def init_gui(self):
      ''' Instead of on/off, on/off with slider '''
      super(DimmerImpl, self).init_gui(_small=True)
      global top
      global BAR_WIDTH
      global BAR_HEIGHT
      self.gui_init_complete = False
      slider = tk.Canvas(top, width=str(BAR_WIDTH), height=BAR_HEIGHT, relief='raised', cursor='dot', bg='black')
      _sum = int(round(BAR_WIDTH / 2))
      gCanColorPoly = slider.create_polygon(0, 0, 0, BAR_HEIGHT, _sum, BAR_HEIGHT, _sum, 0, fill='purple')
      gCanBlackPoly = slider.create_polygon(_sum, 0, _sum, BAR_HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_WIDTH, 0, fill='black')
      slider.itemconfig(gCanColorPoly, tags=('colorPoly'))
      slider.itemconfig(gCanBlackPoly, tags=('blackPoly'))
      slider.grid(column=0, columnspan=2, row = self.row, sticky='w', padx='5')
      #self.gui_elements.append(slider)
      self.gui_init_complete = True

   def color_logic(self):
      ''' Do nothing for button, just override '''
      # TODO Slider updates?
      pass

def toggle_tv_power():
   global tv_ip
   print("Toggling TV power...")
   requests.get('http://' + tv_ip + "/tv_pow?cmd=power")

MIN_REFRESH_INTERVAL = 0.5
LAST_UPDATE = 0
lastUpdateTimestamp = 0


global br
class LIFXImpl(object):
   global br
   def __init__(self):
      this = self
      this.logname = "[LIFX] "
      this.states = []
      this.bulbs = []

      self.discover(True)

      if len(this.states) > 0 :
         br = this.states[0].kelvin

   def discover(self, verbose=False):
      ''' Discover bulbs & save rep '''
      print(self.logname + "Starting bulb discovery...")
      try:
         self.bulbs = lazylights.find_bulbs(expected_bulbs=1, timeout=5)
         self.states = lazylights.get_state(self.bulbs, timeout=5)
         if(verbose):
            print(self.logname + "Found: \tBulb(s): " + str(self.bulbs) + \
                  str("\n\t\tState(s): ") + " " + str(self.states))
      except:
         print("Exception during LIFX Discovery!")
   def color_logic(self):
      ''' handles state-based updates to the GUI elements for this implementation '''
      pass

   def get_elements(self):
      ''' returns the GUI elements associated with this implementation '''
      pass

   def refresh(self):
      print(self.logname + "Refreshing...")
      self.discover(True)

wimpl_rex = WemoImpl("Rex", 5, refresh=True)
wimpl_tv = WemoImpl("Aaa", 6, refresh=True)
wimpl_mini = WemoImpl("mini", 7, refresh=True)
wimpl_dimmer = DimmerImpl("DINNER DIMMER", 8, _refresh=False)

m_lifx = LIFXImpl()
impls.extend([wimpl_rex, wimpl_tv, wimpl_mini, wimpl_dimmer, m_lifx])


#### GUI 

#onButton = tk.Button(top, text="on", command=turnOn, bg="#001a00", fg='#004d00')
#onButton.grid(column = 1, columnspan = 1, row = 0, sticky='nsew')

offButton = tk.Button(top, text="TV POWER", command=toggle_tv_power, bg="#001a00", fg='#004d00')
offButton.grid(column = 0, columnspan = 2, row = 0, sticky='nsew')


top.update()

def refresh_impls():
   global impls
   print("Refreshing " + str(len(impls)) + " device(s)")
   for impl in impls:
      impl.refresh()

refButton = tk.Button(top, text="REFRESH", command=refresh_impls, bg="#22e622")
refButton.grid(column=0, columnspan=1, row=9, sticky='nsew')

quitButton = tk.Button(top, text=" == QUIT == ", command=lambda: top.quit() , bg="#ff00ff")
quitButton.grid(column = 2, columnspan = 1, row = 9, sticky='nsew')

sumR = int(round(BAR_WIDTH / 2))
sumG = int(round(BAR_WIDTH / 2))
sumB = int(round(BAR_WIDTH / 2))

rCan = tk.Canvas(top, width=str(BAR_WIDTH), height=BAR_HEIGHT, relief='raised', bg='black', cursor='dot')
rCanColorPoly = rCan.create_polygon(0, 0, 0, BAR_HEIGHT, sumR, BAR_HEIGHT, sumR, 0, fill = 'red')
rCanBlackPoly = rCan.create_polygon(sumR, 0, sumR, BAR_HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_WIDTH, 0, fill='black')
rCan.itemconfig(rCanColorPoly, tags=('colorPoly'))
rCan.itemconfig(rCanBlackPoly, tags=('blackPoly'))
rCan.grid(column=0, columnspan=2, row = 1, sticky='w', padx='5')

rCanStrVar = tk.StringVar()
rCanStrVar.set(str(sumR))
rCanLabel = tk.Label(top, anchor='center', bd=0, bg='black', cursor='cross', fg='red', textvariable=rCanStrVar)
rCanLabel.grid(column = 2, row = 1, sticky='w')

gCan = tk.Canvas(top, width=str(BAR_WIDTH), height=BAR_HEIGHT, relief='raised', cursor='dot', bg='black')
gCanColorPoly = gCan.create_polygon(0, 0, 0, BAR_HEIGHT, sumG, BAR_HEIGHT, sumG, 0, fill='green')
gCanBlackPoly = gCan.create_polygon(sumG, 0, sumG, BAR_HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_WIDTH, 0, fill='black')
gCan.itemconfig(gCanColorPoly, tags=('colorPoly'))
gCan.itemconfig(gCanBlackPoly, tags=('blackPoly'))
gCan.grid(column=0, columnspan=2, row = 2, sticky='w', padx='5')

gCanStrVar = tk.StringVar()
gCanStrVar.set(str(sumG))
gCanLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', bg='black', fg='green', textvariable=gCanStrVar)
gCanLabel.grid(column = 2, row = 2, sticky='w')

bCan = tk.Canvas(top, width=str(BAR_WIDTH), height=BAR_HEIGHT, relief='raised', cursor='dot', bg='black')
bCanColorPoly = bCan.create_polygon(0, 0, 0, BAR_HEIGHT, sumB, BAR_HEIGHT, sumB, 0, fill='blue')
bCanBlackPoly = bCan.create_polygon(sumB, 0, sumB, BAR_HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_WIDTH, 0, fill='black')
bCan.itemconfig(bCanColorPoly, tags=('colorPoly'))
bCan.itemconfig(bCanBlackPoly, tags=('blackPoly'))
bCan.grid(column=0, columnspan=2, row = 3, sticky='w', padx='5')

bCanStrVar = tk.StringVar()
bCanStrVar.set(str(sumB))
bCanLabel = tk.Label(top, anchor='center', bd=0, cursor='dot', fg='blue', bg='black', textvariable=bCanStrVar)
bCanLabel.grid(column = 2, row = 3, sticky='w')


#top.columnconfigure(0, weight=3)
#top.columnconfigure(1, weight=3)
#top.columnconfigure(2, weight=1)

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

def resend():
      global br
      global states
      print("resend!")

      top.update_idletasks()
      top.update()
      rgb = (float(rCanStrVar.get()) / BAR_WIDTH, float(gCanStrVar.get()) / BAR_WIDTH, float(bCanStrVar.get()) / BAR_WIDTH)
      hsb = colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2])

      if LIFX_CONNECT:
          print("Updating light(s)...")
          lazylights.set_state(m_lifx.bulbs, hsb[0]*360, hsb[1], hsb[2], 2500, 500)
          states = lazylights.refresh(expected_bulbs=1, timeout=1)


def updateHeight(can, val, _fill):
    global LAST_UPDATE
    global BAR_HEIGHT
    global BAR_WIDTH
    
    #Create new bar
    can.coords(can.find_withtag("colorPoly"), 0, 0, 0, BAR_HEIGHT, val, BAR_HEIGHT, val, 0)
    can.coords(can.find_withtag("blackPoly"), val, 0, val, BAR_HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_WIDTH, 0)

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
          # this conditional fixes bars being out of sync with light
          resend()


# Set GUI bar state to that of light:
if len(m_lifx.states) > 0:
  _max = 16.**4
  s = m_lifx.states[0]
  rgb = colorsys.hsv_to_rgb(s.hue/_max, s.saturation/_max, s.brightness/_max)
  updateHeight(rCan, rgb[0] * BAR_WIDTH, 'red')
  updateHeight(gCan, rgb[1] * BAR_WIDTH, 'green')
  updateHeight(bCan, rgb[2] * BAR_WIDTH, 'blue')

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


def get_timestamp():
   return time.time()

# Main program
LAST_UPDATE = timer()


if True:
#with lifx.run():
    #tk.Button(top, text="Quit", command=quit).pack()
    top.mainloop()

#top.quit()
