# NEO Plotter&nbsp;<img src="https://cdn-icons-png.flaticon.com/512/1734/1734190.png" width="40">

MPCS stands for "Minor Planet Center Solver".<br>
This program plots data points from uncertainty maps from the Minor Planet Center website using Python so that the NEO observations could be planned more accurately.

<h2>INSTRUCTIONS&nbsp;<img src="https://cdn-icons-png.flaticon.com/512/5639/5639230.png" alt="drawing" width="30"/></h2>

The required modules for running this Python script are listed inside the `requirements.txt` file.

In `coord.txt` are the coordinates taken in the previous session. The last coordinate is copied to clipboard.
In `settings.ini` you can change your telescopes `FOV` (in arcseconds), default is 2562". Also you can change whether you want to be asked to process the next plot or just finish running the script (`LOOP`).
By default, the program will try to fetch data from your clipboard in order to get required variables which are number of exposures, exposure time, telescope FOV and MPC URL. The required data format is **`<number_of_exposures> <exposure_time> <URL> <FOV>`** (without <>).
If you prefer manual input you can enable it in `settings.ini`.

You run the program by opening the `mpcs.py` file. It will then fect the data and plot it in the new window.
When you hover with you mouse on the graph, a rectangle will appear which indicates the FOV of your telescope. When you have hovered over a desired area, left-click and the coordinates will be written to the `coords.txt` and copied to your clipboard. You can take as many coordinates as you want.
You can zoom in/out the graph by scrolling your mouse wheel up/down.
