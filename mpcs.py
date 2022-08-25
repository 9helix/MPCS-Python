import pyperclip as pc #from matplotlib.backend_bases import MouseButton
from PyQt5 import QtGui
from urllib import request
from bs4 import BeautifulSoup as bs
import validators
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import configparser as cp

config=cp.ConfigParser()
config.read('settings.ini')
fov=config['DEFAULT'].getint('FOV')
# processing website data

err = True


while err:
    url=input('Enter offset URL: ')
    #url = "https://cgi.minorplanetcenter.net/cgi-bin/uncertaintymap.cgi?Obj=P11wdHj&JD=2459810.791667&Form=Y&Ext=VAR&OC=000&META=apm00"
    obj_name = url[url.find('Obj=')+4:url.find('&JD')]
    if not validators.url(url):
        print("Invalid URL\n")
        continue
    print('Fetching data ...')
    try:
        response = request.urlopen(url)
    except:
        print("Invalid URL\n")
        continue
    page_source = response.read().decode('utf-8')
    if 'error' in page_source:
        print("Invalid URL\n")
        continue
    print('\nProcessing data ...')
    soup = bs(page_source, 'html.parser')
    if soup.find('pre') == None:
        print("Invalid URL\n")
        continue
    err = False
content = soup.find('pre').text
content = content.split('\n')[1:-1]
points = {}

for line in content:
    line = line.split()
    x, y = map(int, line[:2])
    coords = (x, y)
    indicator = line[-1]
    try:
        int(indicator)
        color = 'g'  # green
    except ValueError:
        if indicator == '!':
            color = 'tab:orange'  # orange
        elif indicator == '!!':
            color = 'r'  # red
        elif indicator == '***':
            color = 'k'  # black
        else:
            color = 'b'  # blue
    points[coords] = color




print('\nPlotting data ...\n')


class BlittedCursor:
    """
    A cross hair cursor using blitting for faster redraw.
    """

    def __init__(self, ax):
        self.ax = ax
        self.background = None

        self.rect=patches.Rectangle(width=fov,height=fov,color='c',lw=2,ls='-',xy=(0,0),fill=False)
        self.ax.add_patch(self.rect)
        self.text = ax.text(0.67, 0.93, '', transform=ax.transAxes)
        self._creating_background = False
        ax.figure.canvas.mpl_connect('draw_event', self.on_draw)

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.rect.get_visible() != visible

        self.rect.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            x, y = event.xdata, event.ydata
            self.rect.set(xy=(x-fov/2,y-fov/2))
            self.text.set_position((0.69-(0.02*len(str(int(x)))),0.93)) 
            #print(x,y)
            self.text.set_text('R.A.=%1.2f", Decl.=%1.2f"' % (x, y))

            self.ax.figure.canvas.restore_region(self.background)
            self.ax.draw_artist(self.rect)
            self.ax.draw_artist(self.text)
            self.ax.figure.canvas.blit(self.ax.bbox)


def zoom_factory(ax, base_scale=2.):
    def zoom_fun(event):
        # get the current x and y limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1/base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            # print event.button
        # set new limits
        ax.set_xlim([xdata - cur_xrange*scale_factor,
                     xdata + cur_xrange*scale_factor])
        ax.set_ylim([ydata - cur_yrange*scale_factor,
                     ydata + cur_yrange*scale_factor])
        plt.draw()  # force re-draw

    fig = ax.get_figure()  # get the figure of interest
    # attach the call back
    fig.canvas.mpl_connect('scroll_event', zoom_fun)

    # return the function
    return zoom_fun


fig, ax = plt.subplots()  # constrained_layout=True)

fig.canvas.manager.set_window_title(f'{obj_name}')
ax.set_title(f'{obj_name} Offset Map')
blitted_cursor = BlittedCursor(ax)
fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)
ax.grid(linestyle='--', linewidth=0.65)
ax.set_xlabel('R.A. Offset /"')
ax.set_ylabel('Decl. Offset /"')
ax.scatter(*zip(*list(points)), c=list(points.values()), s=5)
thismanager = plt.get_current_fig_manager()


class Click():
    def __init__(self, ax, func, button=1):
        self.ax = ax
        self.func = func
        self.button = button
        self.press = False
        self.move = False
        self.c1 = self.ax.figure.canvas.mpl_connect(
            'button_press_event', self.onpress)
        self.c2 = self.ax.figure.canvas.mpl_connect(
            'button_release_event', self.onrelease)
        self.c3 = self.ax.figure.canvas.mpl_connect(
            'motion_notify_event', self.onmove)

    def onclick(self, event):
        if event.inaxes == self.ax:
            if event.button == self.button:
                self.func(event)

    def onpress(self, event):
        self.press = True

    def onmove(self, event):
        if self.press:
            self.move = True

    def onrelease(self, event):
        if self.press and not self.move:
            self.onclick(event)
        self.press = False
        self.move = False

first=True
def coordclick(event):
    global first
    x, y = map(round, (event.xdata, event.ydata))

    if x<0:
        x=-x
        x_hr=-(x//3600)
        x_min=-((x-x_hr*3600)//60)
        x_sec=x-x_hr*3600-x_min*60
        x_min = str(x_min).zfill(2)
        x_sec = str(x_sec).zfill(2)
        x_hr = '-'+str(x_hr).zfill(2)
    else:
        x_hr=x//3600
        x_min=(x-x_hr*3600)//60
        x_sec=x-x_hr*3600-x_min*60
        x_min = str(x_min).zfill(2)
        x_sec = str(x_sec).zfill(2)
        x_hr = '+'+str(x_hr).zfill(2)

    if y<0:
        y=-y
        y_deg=-(y//3600)
        y_min=-((y-y_deg*3600)//60)
        y_sec=y-y_deg*3600-y_min*60
        y_min = str(y_min).zfill(2)
        y_sec = str(y_sec).zfill(2)        
        y_deg = '-'+str(y_deg).zfill(2)
    else:
        y_deg=y//3600
        y_min=(y-y_deg*3600)//60
        y_sec=y-y_deg*3600-y_min*60
        y_min = str(y_min).zfill(2)
        y_sec = str(y_sec).zfill(2)
        y_deg = '+'+str(y_deg).zfill(2)
    output=f'{x_hr}h {x_min}m {x_sec}s , {y_deg}° {y_min}\' {y_sec}"'

    print(output)
    pc.copy(output)
    print('Copied to clipboard.\n')
    if first:
        f=open('coords.txt','w')
        f.write(output+'\n')
        f.close()
        first=False
    else:
        f=open('coords.txt','a')
        f.write(output+'\n')
        f.close()
        


thismanager.window.setWindowIcon(QtGui.QIcon(
    r"D:\Preuzimanja\Icons\ICO\meteorite.ico"))  # os.path.dirname(__file__) + r"\ICO\meteorite.ico"
plt.gca().invert_xaxis()
plt.ticklabel_format(style='plain')
plt.tight_layout()
click = Click(ax, coordclick, button=1)
scale = 1.25
f = zoom_factory(ax, base_scale=scale)
plt.gca().set_aspect('equal', adjustable='box')
plt.show()
