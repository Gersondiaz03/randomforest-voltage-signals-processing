import io
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from joblib import load
import time
import csv
from tkinter import BOTH, LEFT, NW, RIGHT, VERTICAL, W, Y, Button, Frame, Tk, messagebox, ttk
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import threading

if sys.platform.startswith('linux'):
    import smbus2 as smbus
else:
    smbus = None


ADDRESS = 0x48
CHANNEL = 0
CONFIG_REG = 0x01
CONVERSION_REG = 0x00
GAIN = 1/2


def read_adc(): 
    bus = smbus.SMBus(1)
    config = (0b100 << 10) | (CHANNEL << 9) | (0b111 << 5) | 0b100
    bus.write_i2c_block_data(ADDRESS, CONFIG_REG, [(config >> 8) & 0xFF, config & 0xFF])
    time.sleep(0.05)
    data = bus.read_i2c_block_data(ADDRESS, CONVERSION_REG, 2)
    value = (data[0] << 8 | data[1]) & 0xFFFF
    if value > 0x7FFF:
        value -= 0xFFFF
    voltage = value * ( 2.048 / 32767) / GAIN
    return voltage

def write_to_csv(filename, data):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)
        return None
    
            
def save_csv_to_db(filename):
    connection = create_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        with open(filename, 'r') as file:
            csv_data = file.read()
        fecha_guardado = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO adquisiciones (archivo_csv, fecha_guardado) VALUES (?, ?)", (csv_data, fecha_guardado))
        connection.commit()
        cursor.close()
        connection.close()
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([])
        return None
            

def create_sqlite_connection():
    try:
        connection = sqlite3.connect('registros.db')
        return connection
    except sqlite3.Error as e:
        print(f"Error: {e}")
    return None


class MainWindow(Tk):
    def __init__(self):
        super().__init__()
        self.title('Analizador de Calidad de la Energia')
        icon_path = os.path.join("C:/", "Users", "ASUS", "OneDrive", "Escritorio", "FenomenosV", "imgInterfaz", "icono.jpg")
        self.iconphoto(False, self.load_image(icon_path))
        self.geometry('1240x700')
        self.resizable(False, False)
        self.center_window(1240,700)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.acquiring = False
        self.initUI()
        

    def initUI(self):
        main_frame = Frame(self)
        main_frame.pack(fill=BOTH, expand=True)

        self.panel1 = Frame(main_frame, width=150, height=600)
        self.panel1.place(x=0, y=40)  # Posición exacta del panel1
        self.panel1.pack_propagate(False)

        self.panel2 = Frame(main_frame, width=440, height=275, bg='white', relief='solid',highlightthickness=0)
        self.panel2.place(x=150, y=40)  # Posición exacta del panel2
        self.panel2.pack_propagate(False)

        self.panel3 = Frame(main_frame, width=600, height=600)
        self.panel3.place(x=600, y=40)  # Posición exacta del panel3
        self.panel3.pack_propagate(False)

        self.panel4 = Frame(main_frame, width=440, height=275, bg='white', relief='solid', highlightthickness=0)
        self.panel4.place(x=150, y=325)  # Posición exacta del panel4
        self.panel4.pack_propagate(False)

        btn_adquirir_datos = Button(self.panel1, text='Run Data', bg='#5cb85c', fg='white', width=15, height=8, command=self.start_acquisition)
        btn_adquirir_datos.place(x=10, y=0)

        btn_finalizar_adq = Button(self.panel1, text='Stop Adquisición', bg='#5bc0de', fg='white', width=15, height=8, command=self.stop_acquisition)
        btn_finalizar_adq.place(x=10, y=160)

        btn_visualizar_datos = Button(self.panel1, text='Visualización', bg='#f0ad4e', fg='white', width=15, height=8,command=self.visualizar_datos)
        btn_visualizar_datos.place(x=10, y=320)

        btn_eliminar_datos = Button(self.panel1, text='Eliminar', bg='#d9534f', fg='white', width=15, height=5, command=self.eliminar_datos)
        btn_eliminar_datos.place(x=10, y=480)

        btn_real_time = Button(self.panel1, text='Grafica en tiempo real', bg='#d9534f', fg='white', width=15, height=5, command=self.star_real_time)
        btn_real_time.place(x=10, y=580)

        self.pause_button = Button(self, text='Pausar', bg='#d9534f', fg='white', command=self.toggle_pause)
        self.pause_button.pack(pady=10)

        self.init_table(self.panel2)
        self.init_animation(self.panel3)
        self.init_bar_chart(self.panel4)

    
    def init_table(self, panel):
        table_frame = Frame(panel, width=440, height=275, bg='white')
        table_frame.place(x=0, y=0, anchor=NW)
        table_frame.pack_propagate(False)  

        self.tree = ttk.Treeview(table_frame, columns=("ID", "CSV", "Fecha"), show='headings', style='Treeview')
        self.tree.heading("ID", text="ID")
        self.tree.heading("CSV", text="Archivo CSV")
        self.tree.heading("Fecha", text="Fecha de Guardado")

        # Adjust column widths
        self.tree.column("ID", width=20, anchor=W)
        self.tree.column("CSV", width=100, anchor=W)
        self.tree.column("Fecha", width=100, anchor=W)

        style = ttk.Style()
        style.configure('Treeview',
                        background='white',
                        foreground='black',
                        fieldbackground='white',
                        rowheight=50,
                        borderwidth=1,
                        relief='solid') 
        style.configure('Treeview.Heading',
                        background='lightgray',
                        foreground='black',
                        borderwidth=1,
                        relief='solid')

        
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.load_table_data()

    def load_table_data(self):
        connection = create_sqlite_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM adquisiciones")
            rows = cursor.fetchall()
            for row in rows:
                self.tree.insert('', 'end', values=row)
            cursor.close()
            connection.close()
    
    def on_tree_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.selected_csv = item['values'][1]
            for row in self.tree.get_children():
                self.tree.item(row, tags="")
            self.tree.item(selected_item, tags=("selected",))
            self.tree.tag_configure("selected", background="blue")

    def eliminar_datos(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            selected_id = item['values'][0]
            connection = create_sqlite_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM adquisiciones WHERE id = ?", (selected_id,))
                self.tree.delete(selected_item)
                connection.commit()
                cursor.execute("SELECT id FROM adquisiciones ORDER BY id")
                rows = cursor.fetchall()
                for index, row in enumerate(rows, start=1):
                    cursor.execute("UPDATE adquisiciones SET id = ? WHERE id = ?", (index, row[0]))
                connection.commit()
                cursor.close()
                connection.close()
                self.clear_panel_two()
                self.init_table(self.panel2)
                messagebox.showinfo("Eliminar", "Registro eliminado y IDs actualizados correctamente")
            else:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
        else:
            messagebox.showwarning("Seleccionar", "Por favor seleccione un registro de la tabla para eliminar")

        
    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f'{width}x{height}+{x}+{y}')

    def load_image(self, path):
        try:
            image = Image.open(path)
            return ImageTk.PhotoImage(image)
        except IOError:
            print(f"No se pudo cargar la imagen en {path}.")
            return None
    
    def init_animation(self, panel):
        datos = pd.read_csv('data/adc_datsa.csv', header=None, names=['tiempo', 'voltaje'])
        datos = datos.astype(float)
        t = datos['tiempo'].values
        v = datos['voltaje'].values

        def detect_ascent_peaks(voltage_series):
            ascent_peaks = np.zeros_like(voltage_series, dtype=bool)

            for i in range(1, len(voltage_series) - 1):
                if voltage_series[i - 1] < voltage_series[i] and voltage_series[i] > voltage_series[i + 1]:
                    ascent_peaks[i] = True

            return ascent_peaks
        ascent_peaks = detect_ascent_peaks(v)
        
        voltage_nominal = 220
        lower_threshold = voltage_nominal * 1.1
        upper_threshold = voltage_nominal * 1.8

        labels = np.zeros_like(v)
        labels[(v >= lower_threshold) & (v <= upper_threshold)] = 1

        X = np.column_stack((v[:-1], v[1:]))
        y = labels[1:]

        model_path = 'Modelos_RandomForest/modelo_random_forest_swell.joblib'
        model = load(model_path)
        swell_detected = np.zeros_like(labels)
        swell_detected[1:] = model.predict(X)
        swell_detected = np.logical_and(swell_detected, ascent_peaks)

        fig, ax = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, master=panel)
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        self.paused = False
        self.t = t
        self.v = v
        self.swell_detected = swell_detected

        def update(frame):
            if not self.paused:
                ax.clear()
                xlim_start = frame % self.t[-1]
                xlim_end = (frame + 10) % self.t[-1]
                if xlim_end < xlim_start: 
                    xlim_end += self.t[-1]

                ax.set_xlim(xlim_start, xlim_end)
                ax.plot(self.t, self.v,'r')

                swell_mask = (self.t >= xlim_start) & (self.t <= xlim_end)
                detected_mask = np.logical_and(self.swell_detected, swell_mask)
                ax.plot(self.t[detected_mask], self.v[detected_mask], 'go')
                ax.set_xlabel('Tiempo (s)')
                ax.set_ylabel('Voltaje (V)')

        def frame_gen():
            frame = 0
            while True:
                yield frame
                frame += 1

        self.ani = FuncAnimation(fig, update, frames=frame_gen(), interval=200,cache_frame_data=False)

    def init_bar_chart(self, panel):
        self.fig, self.ax = plt.subplots()
        self.ax.set_title('Cantidad de fenomenos encontrados')
        self.ax.set_xlabel('Swell')
        self.ax.set_ylabel('Cantidad')

        self.canvas = FigureCanvasTkAgg(self.fig, master=panel)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        self.update_bar_chart()
    

    def update_bar_chart(self):
        swell_count = self.count_swells()

        self.ax.clear()
        self.ax.bar(['Swells'], [swell_count])
        self.ax.set_title('Cantidad de fenomenos encontrados')
        self.ax.set_xlabel('Swell')
        self.ax.set_ylabel('Cantidad')
        self.canvas.draw()
    
    
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.ani.event_source.stop()
            self.pause_button.config(text='play')
        else:
            self.ani.event_source.start()
            self.pause_button.config(text='stop')

    
    def count_swells(self):
        datos = pd.read_csv('data/adc_datsa.csv', header=None, names=['tiempo', 'voltaje'])
        datos = datos.astype(float)
        t = datos['tiempo'].values
        v = datos['voltaje'].values

        def detect_ascent_peaks(voltage_series):
            ascent_peaks = np.zeros_like(voltage_series, dtype=bool)

            for i in range(1, len(voltage_series) - 1):
                if voltage_series[i - 1] < voltage_series[i] and voltage_series[i] > voltage_series[i + 1]:
                    ascent_peaks[i] = True

            return ascent_peaks
        ascent_peaks = detect_ascent_peaks(v)
        
        voltage_nominal = 220
        lower_threshold = voltage_nominal * 1.1
        upper_threshold = voltage_nominal * 1.8

        labels = np.zeros_like(v)
        labels[(v >= lower_threshold) & (v <= upper_threshold)] = 1

        X = np.column_stack((v[:-1], v[1:]))
        y = labels[1:]

        model_path = 'Modelos_RandomForest/modelo_random_forest_swell.joblib'
        model = load(model_path)
        swell_detected = np.zeros_like(labels)
        swell_detected[1:] = model.predict(X)
        swell_detected = np.logical_and(swell_detected, ascent_peaks)
        swell_count = np.count_nonzero(swell_detected)
        return swell_count
    
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.ani.event_source.stop()
            self.pause_button.config(text='play')
        else:
            self.ani.event_source.start()
            self.pause_button.config(text='stop')

    def start_acquisition(self):
        acquisition_thread = threading.Thread(target=self.acquire_data)
        acquisition_thread.start()
	
    def acquire_data(self):
        self.acquiring = True
        filename = "adc_data.csv"
        start_time = time.time()
        while self.acquiring:
            try:
                adc_value = read_adc()
                elapsed_time = time.time() - start_time
                write_to_csv(filename, [elapsed_time, adc_value])
                time.sleep(0.1)
            except Exception as e:
                messagebox.showerror("Error", f"Error al leer ADC: {e}")
                self.acquiring = False
                break

    def start_real_time_graph(self):
        self.clear_panel()

        fig,ax = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, master=self.panel3)
        canvas.get_tk_widget().pack(fill='both', expand=True)

        self.t = []
        self.v = []
        self.paused = False

        def update(frame):
            if not self.paused:datos = pd.read_csv('adc_data.csv', header=None, names=['tiempo', 'voltaje'])
            self.t = datos['tiempo'].values.astype(float)
            self.v = datos['voltaje'].values.astype(float)

            ax.clear()
            xlim_start = self.t[-1] - 10 if self.t[-1] > 10 else 0
            ax.set_xlim(xlim_start, self.t[-1])
            ax.plot(self.t, self.v, 'r')

            ax.set_xlabel('Tiempo (s)')
            ax.set_ylabel('Voltaje (AC)')
            ax.set_title('Adquisición en Tiempo Real del ADC')
            ax.grid(True)
            canvas.draw()

    
    def star_real_time(self):
        graph_thread = threading.Thread(target=self.start_real_time_graph)
        graph_thread.start()

    def stop_acquisition(self):
        self.acquiring = False
        self.procesar_y_guardar()
        self.clear_panel_two()
        self.init_table(self.panel2)
    
    def procesar_y_guardar(self):
        sensor_values = np.array([0.275, 0.418, 0.425, 0.426, 0.427, 0.428, 0.696])
        real_values = np.array([129.1, 193.3, 196.2, 196.5, 196.6, 197.0, 220.0])
        coefficients = np.polyfit(sensor_values, real_values, 1)
        m, b = coefficients
        datos_convertidos = []
        
        with open('adc_data.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                # Verifica que la fila tenga exactamente 2 elementos
                if len(row) == 2:
                    tiempo, voltage_adc = map(float, row)
                    voltage_real = (m * voltage_adc + b)-120
                    datos_convertidos.append([tiempo, voltage_real])
                else:
                    print(f"Fila ignorada debido a un número incorrecto de elementos: {row}")

        with open('adc_data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(datos_convertidos)
        
        save_csv_to_db('adc_data.csv')


    def clear_panel(self):
        for widget in self.panel3.winfo_children():
            widget.destroy()
    
    def clear_panel_two(self):
        for widget in self.panel2.winfo_children():
            widget.destroy()

    def clear_panel_four(self):
        for widget in self.panel4.winfo_children():
            widget.destroy()
    

    def clear_panel(self):
        for widget in self.panel3.winfo_children():
            widget.destroy()
    
    def clear_panel_two(self):
        for widget in self.panel2.winfo_children():
            widget.destroy()

    def clear_panel_four(self):
        for widget in self.panel4.winfo_children():
            widget.destroy()

    def init_bar_chart_two(self, panel):
        self.fig, self.ax = plt.subplots()
        self.ax.set_title('Cantidad de fenomenos encontrados')
        self.ax.set_xlabel('Swell')
        self.ax.set_ylabel('Cantidad')

        self.canvas = FigureCanvasTkAgg(self.fig, master=panel)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        self.update_bar_chart_two(self.swell_count)
    

    def update_bar_chart_two(self, swell_count):
        self.ax.clear()
        self.ax.bar(['Swells'], [swell_count])
        self.ax.set_title('Cantidad de fenomenos encontrados')
        self.ax.set_xlabel('Swell')
        self.ax.set_ylabel('Cantidad')
        self.canvas.draw()
    

    def visualizar_datos(self):
        if not hasattr(self, 'selected_csv'):
            messagebox.showerror("Error", "Seleccione un archivo CSV en la tabla primero.")
            return
        self.clear_panel()

        connection = create_sqlite_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT archivo_csv FROM adquisiciones WHERE archivo_csv = ?", (self.selected_csv,))
            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if result:
                csv_data = result[0]
                csv_buffer = io.StringIO(csv_data)
                datos = pd.read_csv(csv_buffer, header=None, names=['tiempo', 'voltaje'])
                datos['tiempo'] = datos['tiempo']
                datos['voltaje'] = datos['voltaje']
                
                t = datos['tiempo'].values.astype(float)
                v = datos['voltaje'].values.astype(float) 

                sorted_indices = np.argsort(t)
                t = t[sorted_indices]
                v = v[sorted_indices]

                def detect_ascent_peaks(voltage_series):
                    ascent_peaks = np.zeros_like(voltage_series, dtype=bool)
                    for i in range(1, len(voltage_series) - 1):
                        if voltage_series[i - 1] < voltage_series[i] and voltage_series[i] > voltage_series[i + 1]:
                            ascent_peaks[i] = True
                    return ascent_peaks
                ascent_peaks = detect_ascent_peaks(v)

                voltage_nominal = 220
                lower_threshold = voltage_nominal * 1.1
                upper_threshold = voltage_nominal * 1.8

                labels = np.zeros_like(v)
                labels[(v >= lower_threshold) & (v <= upper_threshold)] = 1

                X = np.column_stack((v[:-1], v[1:]))
                y = labels[1:]

                model_path = 'Modelos_RandomForest/modelo_random_forest_swell.joblib'
                model = load(model_path)
                swell_detected = np.zeros_like(labels)
                swell_detected[1:] = model.predict(X)
                swell_detected = np.logical_and(swell_detected, ascent_peaks)
                self.swell_count = np.count_nonzero(swell_detected)
                self.clear_panel_four()
                self.init_bar_chart_two(self.panel4)
                self.update_bar_chart_two(self.swell_count)

                fig, ax = plt.subplots()
                canvas = FigureCanvasTkAgg(fig, master=self.panel3)
                canvas.get_tk_widget().pack(fill=BOTH, expand=True)
                self.paused = False
                self.t = t
                self.v = v
                self.swell_detected = swell_detected

                def update(frame):
                    if not self.paused:
                        ax.clear()
                        xlim_start = frame % self.t[-1]
                        xlim_end = (frame + 10) % self.t[-1]
                        if xlim_end < xlim_start:
                            xlim_end += self.t[-1]

                        ax.set_xlim(xlim_start, xlim_end)
                        ax.plot(self.t, self.v, 'r')

                        swell_mask = (self.t >= xlim_start) & (self.t <= xlim_end)
                        detected_mask = np.logical_and(self.swell_detected, swell_mask)
                        ax.plot(self.t[detected_mask], self.v[detected_mask], 'go')
                        ax.set_xlabel('Tiempo (s)')
                        ax.set_ylabel('Voltaje (AC)')
                        ax.set_title('Voltaje vs Tiempo')
                        ax.grid(True)

                def frame_gen():
                    frame = 0
                    while True:
                        yield frame
                        frame += 1

                self.ani = FuncAnimation(fig, update, frames=frame_gen(), interval=100, cache_frame_data=False)
            else:
                messagebox.showerror("Error", "No se encontró el archivo CSV seleccionado.")

    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Realmente quieres salir?"):
            self.cleanup()
            self.destroy()
            os._exit(os.EX_OK)

    def cleanup(self):
	    self.acquisition_running = False
        

if __name__ == '__main__':
    import claseLogin
    login_window = claseLogin.LoginWindow()
    login_window.mainloop()