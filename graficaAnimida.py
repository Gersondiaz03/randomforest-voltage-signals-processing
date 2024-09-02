#en esta parte va un ejemplo de uso del modulo animation
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd

t = np.linspace(0, 10, 10000)
v = np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 180 * t)
v_swell = v.copy()
v_swell[2000:4000] = v[2000:4000] * 1.1

def update(frame):
    ax.clear()
    xlim_start = frame % 10  
    xlim_end = (frame + 0.04) % 10
    if xlim_end < xlim_start: 
        xlim_end += 10

    ax.set_xlim(xlim_start, xlim_end)
    ax.plot(t, v, 'r')
    ax.plot(t, v_swell, 'k')

    swell_mask = (t >= xlim_start) & (t <= xlim_end)
    ax.fill_between(t[swell_mask], v[swell_mask], v_swell[swell_mask], color='yellow', alpha=0.5)

    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Voltaje')
    ax.legend()

fig, ax = plt.subplots()

def frame_gen():
    frame = 0
    while True:
        yield frame
        frame += 0.09

ani = FuncAnimation(fig, update, frames=frame_gen(), interval=50)

plt.show()
