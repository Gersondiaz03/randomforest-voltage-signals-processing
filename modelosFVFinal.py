import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from joblib import load

# Cargar los modelos entrenados
model_swell = load('Modelos_RandomForest/modelo_random_forest_swell.joblib')
model_sag = load('Modelos_RandomForest/modelo_random_forest_sag.joblib')
model_armonico = load('Modelos_RandomForest/modelo_random_forest_arm.joblib')

# Generar la señal de tiempo y voltaje
t = np.linspace(0, 10, 10000)
v = np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 180 * t)

# Introducir fenómenos en la señal
v_combined = v.copy()
v_combined[5000:6000] = v[5000:6000] * 1.1  # Swell
v_combined[2000:2500] = v[2000:2500] * 0.4  # Sag
v_combined[5000:5500] = v[5000:5500] * 0.9  # Sag

# Parámetros para el armónico
A_1 = 1  # Amplitud
a_1 = 0  # Fase
omega = np.sqrt(2)  # Frecuencia angular
x = np.linspace(0, 2*np.pi, 2000)
y1 = np.sqrt(2) * A_1 * np.sin(9*x + 9*(a_1))

v_combined[6000:8000] = y1  # Armónico

# Función para actualizar y visualizar la señal en tiempo real
def update(frame):
    ax.clear()
    xlim_start = frame % 10  
    xlim_end = (frame + 0.04) % 10
    if xlim_end < xlim_start: 
        xlim_end += 10

    ax.set_xlim(xlim_start, xlim_end)
    ax.plot(t, v, 'r')
    ax.plot(t, v_combined, 'k')

    mask = (t >= xlim_start) & (t <= xlim_end)
    ax.fill_between(t[mask], v[mask], v_combined[mask], color='yellow', alpha=0.5)

    # Usar los modelos para detectar fenómenos
    X = np.column_stack((v[mask], v_combined[mask]))  # Solo se incluyen los valores de voltaje relevantes
    
    # Detección de swell
    swell_detected = model_swell.predict(X) == 1
    ax.plot(t[mask][swell_detected], v_combined[mask][swell_detected], 'g*', label='Swell detectado')
    
    # Detección de sag
    sag_detected = model_sag.predict(X) == 1
    ax.plot(t[mask][sag_detected], v_combined[mask][sag_detected], 'b*', label='Sag detectado')
    
    # Detección de armónicos
    arm_detected = model_armonico.predict(X) == 1
    ax.plot(t[mask][arm_detected], v_combined[mask][arm_detected], 'm*', label='Armónico detectado')

    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Voltaje')
    ax.legend()

fig, ax = plt.subplots()

# Generador de frames para la animación
def frame_gen():
    frame = 0
    while True:
        yield frame
        frame += 0.09

# Configuración de la animación
ani = FuncAnimation(fig, update, frames=frame_gen(), interval=50)

# Visualización
plt.show()