 
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
global LAST_UPDATE

global tv_ip
tv_ip = '192.168.1.150'

### GUI INIT -- must run before any impl created
top = tk.Tk()
#top.attributes("-fullscreen", True)
top.configure(background = 'black')
w, h = top.winfo_screenwidth()/1.25, top.winfo_screenheight()/1.25
#top.overrideredirect(1)
top.geometry("%dx%d+0+0" % (w, h))
top.focus_set()
top.bind('<Escape>', lambda e: e.widget.quit())# top.destroy())


class WemoImpl(object):
  global top
  def __init__(self):
    self.logname = "[Wemo] "
    self.tv_id="1"
    self.rex_id="Rex"
    self.ip = None #"10.42.0.39"
    self.btn_bg = '#001a00'
    self.btn_fg = '#004d00'

    self.devices = {}
    self.refreshing = False
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
            this.devices = { d : d.get_state(force_update=True) }
            return

        this.devices = { d : d.get_state(force_update=True) for d in ds }
        print(this.logname + "Got Device(s): " + str(this.devices))
        this.last_update = time.time()
        this.ds = ds
      except Exception as e:
        print(this.logname + "DISCOVERY FAILED! " + str(e))
        this.ds = []

      this.refreshing = False

    t = threading.Thread(target=_run)
    #t.daemon = True ## ? async seems to work fine without this
    t.start()

  def toggle_tv_lights(self):
    print(self.logname + "Toggling TV lights...")
    for k in self.devices:
      if self.tv_id in str(k):
        k.toggle()
        print(self.logname + "Toggled TV lights.")
        self.color_logic(self.tv_id)
        return

  def toggle_tank(self):
    print(self.logname + "Toggling Rex's lights...")
    for k in self.devices:
      if self.rex_id in str(k):
        k.toggle()
        print(self.logname + "Toggled Rex's lights.")
        self.devices = { d : d.get_state(force_update=True) for d in self.ds }
        self.color_logic(self.rex_id)
        return

  def color_logic(self, device_id=''):
    ''' handles state-based updates to the GUI elements for this implementation 
     might be better to parameterize device itself, but TODO
    '''

    if not self.gui_init_complete:
       self.init_gui()

    if device_id is None:
       device_id = ''

    for k in self.devices:
      # do for all known devices if unspecified
      if len(device_id) == 0 or device_id in str(k):
        istate = self.devices[k]
        if istate == 8:
          # mark on button, ensure only one btn can be on at once
          self.gui_elements[0].config(bg="#ffffff")
          self.gui_elements[1].config(bg=self.btn_bg)
        elif istate == 0:
           # mark off button, clear on button
           self.gui_elements[1].config(bg="#ffffff")
           self.gui_elements[0].config(bg=self.btn_bg)
           
  def init_gui(self):
    global top
    on = tk.Button(top, text="Tank Lights On", \
                   command=self.toggle_tank, bg=self.btn_bg, fg=self.btn_fg)
    off = tk.Button(top, text="Tank Lights Off", \
                    command=self.toggle_tank, bg=self.btn_bg, fg=self.btn_fg)

    on.grid(column = 1, columnspan = 1, row = 6, sticky='nsew')
    off.grid(column = 0, columnspan = 1, row=6, sticky='nsew')
    self.gui_elements = [on, off]
    self.gui_init_complete = True

  def get_elements(self):
    ''' returns the GUI elements associated with this implementation '''
    return self.gui_elements


def toggle_tv_power():
   global tv_ip
   print("Toggling TV power...")
   requests.get('http://' + tv_ip + "/tv_pow")

MIN_REFRESH_INTERVAL = 0.5
LAST_UPDATE = 0
lastUpdateTimestamp = 0


global br
class LIFXImpl(object):
   global br
   def __init__(self):
      this = self
      this.logname = "[LIFX] "
      print(this.logname + "Starting bulb discovery...")
      this.bulbs = lazylights.find_bulbs(expected_bulbs=1, timeout=5)
      this.states = lazylights.get_state(this.bulbs, timeout=5)

      print(this.logname + "Found: \tBulb(s): " + str(this.bulbs) + \
            str("\n\t\tState(s): ") + " " + str(this.states))
      if len(this.states) > 0 :
         br = this.states[0].kelvin 

   def color_logic(self):
      ''' handles state-based updates to the GUI elements for this implementation '''
      pass

   def get_elements(self):
      ''' returns the GUI elements associated with this implementation '''
      pass
m_impl = WemoImpl()
m_lifx = LIFXImpl()


#### GUI 

#def turnOn():
#    lazylights.setpower(bulbs, True)

#def turnOff():
#    lazylights.setpower(bulbs, False)

#onButton = tk.Button(top, text="on", command=turnOn, bg="#001a00", fg='#004d00')
#onButton.grid(column = 1, columnspan = 1, row = 0, sticky='nsew')

offButton = tk.Button(top, text="TV POWER", command=toggle_tv_power, bg="#001a00", fg='#004d00')
offButton.grid(column = 0, columnspan = 2, row = 0, sticky='nsew')

filterOnButton = tk.Button(top, text="TV Lights On", command=m_impl.toggle_tv_lights, bg="#001a00", fg='#004d00')
filterOnButton.grid(column = 1, columnspan = 1, row = 5, sticky='nsew')

filterOffButton = tk.Button(top, text="TV Lights Off", command=m_impl.toggle_tv_lights, bg="#001a00", fg='#004d00')
filterOffButton.grid(column = 0, columnspan = 1, row = 5, sticky='nsew')

m_impl.color_logic(m_impl.rex_id)
top.update()
#tankLightOffButton.grid(column = 0, columnspan = 1, row = 6, sticky='nsew')


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
      rgb = (float(rCanStrVar.get()) / BAR_WIDTH, float(gCanStrVar.get()) / BAR_WIDTH, float(bCanStrVar.get()) / BAR_WIDTH)
      hsb = colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2])

      if LIFX_CONNECT:
          print("Updating light(s)...")
          lazylights.set_state(m_lifx.bulbs, hsb[0]*360, hsb[1], hsb[2], 1000, 500)
          states = lazylights.refresh(expected_bulbs=1, timeout=1)


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

# Main program
LAST_UPDATE = timer()


if True:
#with lifx.run():
    #tk.Button(top, text="Quit", command=quit).pack()
    top.mainloop()

#top.quit()
