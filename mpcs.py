import pyperclip as pc
from urllib import request
from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import configparser as cp
import string
from matplotlib.lines import Line2D
from math import *

config = cp.ConfigParser()
config.read('settings.ini')
fov = config['MAIN'].getint('FOV')
loop = config['MAIN'].getboolean('LOOP')
clip = config['MAIN'].getboolean('CLIPBOARD')


def clip_check(url_err=False):
    global exp_num
    global exp_dur
    global url
    global fov
    if url_err:
        input('Press enter to retry... ')
    if clip:
        ok = False
        while not ok:
            try:
                print('Fetching clipboard data...')
                data = pc.paste()
                data = data.split(' ')
                exp_num = int(data[0])
                exp_dur = int(data[1])
                url = data[2]
                fov = int(data[3])
                ok = True
            except:
                fed = input(
                    "Invalid data format in clipboard. Press enter to retry or n to exit... ")
                if fed.lower() == 'n':
                    exit()
                print('\n')


# processing website data
x_vals = []
y_vals = []
go = True
first = True
err = True
suffixes = list(string.ascii_lowercase)
while go:
    clip_check()
    suffix_pos = 0
    if not clip:
        exp_num = int(input('Number of exposures: '))
        exp_dur = int(input('Exposure duration (in seconds): '))
    while err:
        if not clip:
            url = input('Enter offset URL: ')
        obj_name = url[url.find('Obj=')+4:url.find('&JD')]
        print('\nFetching URL data ...')
        try:
            response = request.urlopen(url)
        except:
            print("Invalid URL\n")
            if clip:
                clip_check(url_err=True)
            continue
        page_source = response.read().decode('utf-8')
        if 'error' in page_source:
            print("Invalid URL\n")
            if clip:
                clip_check(url_err=True)
            continue
        print('\nProcessing data ...')
        soup = bs(page_source, 'html.parser')
        if soup.find('pre') == None:
            print("Invalid URL\n")
            if clip:
                clip_check(url_err=True)
            continue
        err = False

    content = soup.find('pre').text
    content = content.split('\n')[1:-1]
    points = {}

    link = soup.find('a')
    link = link['href']
    page = request.urlopen(link)
    page_source = page.read().decode('utf-8')
    soup = bs(page_source, 'html.parser')
    table = soup.find('pre').text
    table = table.split()
    try:
        table = table[table.index('Dist.')+2:]
    except:
        table = table[table.index('P.A.')+1:]
    yr = table[0]
    mth = table[1]
    day = table[2]
    hr = table[3]
    mag = table[11]
    ra_hr = int(table[4])
    ra_min = int(table[5])
    ra_sec = float(table[6])
    dec_deg = int(table[7])
    dec_min = int(table[8])
    dec_sec = int(table[9])
    final_output = ""
    black_counter = 0
    red_counter = 0
    orange_counter = 0
    green_counter = 0
    blue_counter = 0
    # pink_counter=0
    ra_sec_total = ra_hr*3600+ra_min*60+ra_sec
    if dec_deg < 0:
        dec_sec_total = dec_deg*3600-dec_min*60-dec_sec
    else:
        dec_sec_total = dec_deg*3600+dec_min*60+dec_sec
    final_output = ""

    for line in content:
        line = line.split()
        x, y = map(int, line[:2])
        coords = (x, y)
        indicator = line[-1]
        try:
            int(indicator)
            color = 'g'  # green
            green_counter += 1
        except ValueError:
            if indicator == '!':
                orange_counter += 1
                color = 'tab:orange'  # orange
            elif indicator == '!!':
                red_counter += 1
                color = 'r'  # red
            elif indicator == '***':
                black_counter += 1
                color = 'k'  # black
            else:
                blue_counter += 1
                color = 'b'  # blue
        points[coords] = color
        x_vals.append(x)
        y_vals.append(y)

    print('\nPlotting data ...\n')

    class BlittedCursor:
        """
        A cross hair cursor using blitting for faster redraw.
        """

        def __init__(self, ax):
            self.ax = ax
            self.background = None

            self.rect = patches.Rectangle(
                width=fov, height=fov, color='c', lw=2, ls='-', xy=(0, 0), fill=False)
            self.ax.add_patch(self.rect)
            self.text = ax.text(
                x=0.52, y=0.93, s='', transform=ax.transAxes, ha='center', fontsize='large')
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
            self.background = self.ax.figure.canvas.copy_from_bbox(
                self.ax.bbox)
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
                self.rect.set(xy=(x-fov/2, y-fov/2))
                # self.text.set_position((0.69-(0.02*len(str(int(x)))), 0.93))
                # print(x,y)
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

    fig, ax = plt.subplots()  # figsize=(9, 9))  # constrained_layout=True)

    fig.canvas.manager.set_window_title(f'MPCS - {obj_name}')
    ax.set_title(f'{obj_name} Offset Map')
    blitted_cursor = BlittedCursor(ax)
    fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)
    ax.grid(linestyle='--', linewidth=0.65)
    ax.set_xlabel('R.A. Offset / "')
    ax.set_ylabel('Decl. Offset / "')
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

    def coordclick(event):

        global first
        global suffix_pos
        global final_output
        x, y = tuple(round(num, 2) for num in (event.xdata, event.ydata))
        trace = patches.Rectangle(
            width=fov, height=fov, color='y', lw=2, ls='-', xy=(event.xdata-fov/2, event.ydata-fov/2), fill=False)
        ax.add_patch(trace)
        plt.draw()
        # ax.draw_artist(trace)

        ra_sec_total_final = ra_sec_total+x/(15*cos(dec_sec_total*pi/648000))

        dec_sec_total_final = dec_sec_total+y
        ra_hr_final = ra_sec_total_final//3600
        ra_min_final = (ra_sec_total_final-ra_hr_final*3600)//60
        ra_sec_final = round(ra_sec_total_final-ra_hr_final *
                             3600-ra_min_final*60, 1)

        if dec_sec_total_final >= 0:
            dec_deg_final = dec_sec_total_final//3600
            dec_min_final = (dec_sec_total_final-dec_deg_final*3600)//60
        else:
            dec_deg_final = dec_sec_total_final//3600+1
            dec_min_final = (dec_sec_total_final-dec_deg_final*3600)//60+1
        dec_sec_final = round(dec_sec_total_final -
                              dec_deg_final*3600-dec_min_final*60, 1)

        if ra_hr_final >= 24:
            ra_hr_final = ra_hr_final % 24
            '''
        if dec_deg_final > 90:
            dec_deg_final = 180-dec_deg_final
        if dec_deg_final < -90:
            dec_deg_final = -180-dec_deg_final'''

        ra_hr_final = f'{int(ra_hr_final):02}'
        ra_min_final = f'{abs(int(ra_min_final)):02}'
        ra_sec_final = f'{abs(ra_sec_final):04}'
        if dec_sec_total_final >= 0:
            dec_deg_final = f'{int(dec_deg_final):+03}'
        else:
            dec_deg_final = f'{int(dec_deg_final):03}'
        dec_min_final = f'{abs(int(dec_min_final)):02}'
        dec_sec_final = f'{abs(dec_sec_final):04}'

        output = f'{ra_hr_final} {ra_min_final} {ra_sec_final}   {dec_deg_final} {dec_min_final} {dec_sec_final}\n\n'

        header = f"* {obj_name}_{suffixes[suffix_pos]}     {mag}      {exp_num} x {exp_dur} sec\n{yr} {mth} {day} {hr}   "
        suffix_pos += 1
        output = header+output

        final_output += output

    def reset():
        global go

    def on_close(event):
        global final_output
        global first
        global go
        if final_output != "":
            print(final_output)

            pc.copy(final_output)
            print('Copied to clipboard!\n')
            if first:
                f = open('coords.txt', 'w')
                first = False
            else:
                f = open('coords.txt', 'a')
            f.write(final_output)
            f.close()

    leg = ax.legend(handles=[Line2D([0], [0], marker='o', color='w', label=f'{black_counter}',
                                    markerfacecolor='k', markersize=0),
                             Line2D([0], [0], marker='o', color='w', label=f'{red_counter}',
                                    markerfacecolor='r', markersize=0),
                             Line2D([0], [0], marker='o', color='w', label=f'{orange_counter}',
                                    markerfacecolor='tab:orange', markersize=0),
                             Line2D([0], [0], marker='o', color='w', label=f'{green_counter}',
                                    markerfacecolor='g', markersize=0),
                             Line2D([0], [0], marker='o', color='w', label=f'{blue_counter}',
                                    markerfacecolor='b', markersize=0)], loc='upper right', labelspacing=0.8, title="Counts")
    colors = ['k', 'r', 'tab:orange', 'g', 'b']
    colors_pos = 0

    for text in leg.get_texts():
        text.set_color(colors[colors_pos])
        colors_pos += 1
    #ax.format_coord = lambda x, y: f"R.A.={round(x)}\", Decl.={round(y)}\""

    plt.gca().invert_xaxis()
    plt.ticklabel_format(style='plain')

    click = Click(ax, coordclick, button=1)
    scale = 1.25
    f = zoom_factory(ax, base_scale=scale)
    fig.canvas.mpl_connect('close_event', on_close)
    plt.gca().set_aspect('equal', adjustable='datalim')

    centroid = (sum(x_vals)/len(x_vals), sum(y_vals)/len(y_vals))
    left_dist = abs(max(x_vals)-centroid[0])
    right_dist = abs(centroid[0]-min(x_vals))
    x_offset = max(left_dist, right_dist)

    x_range = max(x_vals)-min(x_vals)
    y_range = max(y_vals)-min(y_vals)

    bottom_dist = abs(min(y_vals)-centroid[1])
    top_dist = abs(centroid[1]-max(y_vals))
    y_offset = max(top_dist, bottom_dist)
    if fov < x_range or fov < y_range:
        ax.set_xlim(left=(centroid[0]+x_offset)*1.1,
                    right=(centroid[0]-x_offset)*1.1)
        ax.set_ylim(bottom=(centroid[1]-y_offset)
                    * 1.1, top=(centroid[1]+y_offset)*1.1)
        '''ax.set_xlim(left=(max(x_vals))*1.1,
                    right=(min(x_vals))*1.1)
        ax.set_ylim(bottom=(min(y_vals))
                    * 1.1, top=(max(y_vals))*1.1)'''
    else:
        ax.set_xlim(left=(centroid[0]+fov/2)*1.2,
                    right=(centroid[0]-fov/2)*1.2)
        ax.set_ylim(bottom=(centroid[1]-fov/2)
                    * 1.2, top=(centroid[1]+fov/2)*1.2)
    plt.tight_layout()
    plt.show()

    if loop:
        feed = input('Continue? (y/n) ')
        print()
        if feed.lower() == "n":
            go = False
        err = True
    else:
        go = False
