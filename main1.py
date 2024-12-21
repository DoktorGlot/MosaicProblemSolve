import sys
import asyncio
import math
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from concurrent.futures import ThreadPoolExecutor

# Добавление путей
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP\math")
sys.path.append(r"C:\Users\nadto\Desktop\Kursach_TIMP")

from bins import Bin
from part import Part
from vector import Vector
from packer import Packer

def calculate_polygon_area(points):
    """Вычисляет площадь многоугольника по его вершинам."""
    n = len(points)
    if n < 3:
        return 0  # Многоугольник должен иметь как минимум три вершины
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y - points[j].x * points[i].y
    return abs(area) / 2

parts = []
config = {
    'spacing': 0,
    'rotationSteps': 200,
    'population': 20,
    'generations': 10,
    'mutationRate': 0.25,
    'seed': 0,
}
packer = Packer()
loop = asyncio.get_event_loop()

# Variable to track the figure (packing visualization)
current_figure = None

def calculate_new_positions(parts, placements):
    result = []
    for placement in placements:
        part_id = placement["part"]
        position = placement["position"]
        rotation = placement["rotation"]
        part = next(p for p in parts if p.id == part_id)
        new_points = []
        for point in part.points:
            x_rot = point.x * math.cos(rotation) - point.y * math.sin(rotation)
            y_rot = point.x * math.sin(rotation) + point.y * math.cos(rotation)
            x_new = x_rot + position.x
            y_new = y_rot + position.y
            new_points.append(Vector(x_new, y_new))
        result.append((part_id, new_points))
    return result

def visualize_parts(original_parts, transformed_parts):
    global current_figure
    if current_figure:
        plt.close(current_figure)  # Close the previous figure if it exists

    # Create new figure for the new packing
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    ax[0].set_title("Original Parts")
    for part in original_parts:
        x = [p.x for p in part.points] + [part.points[0].x]
        y = [p.y for p in part.points] + [part.points[0].y]
        ax[0].plot(x, y, marker='o')
    ax[1].set_title("Transformed Parts")
    for part_id, points in transformed_parts:
        x = [p.x for p in points] + [points[0].x]
        y = [p.y for p in points] + [points[0].y]
        ax[1].plot(x, y, marker='o', label=f"Part {part_id}")
    for a in ax:
        a.set_aspect('equal')
    plt.tight_layout()

    current_figure = fig  # Update the current figure reference
    plt.show()

async def pack_parts(update_progress):
    def on_evaluation(e):
        progress = int(e["progress"] * 100)  # Assuming progress is between 0 and 1
        root.after(0, lambda: update_progress(progress))

    result = await packer.start(
        bins, parts, config, {
            'onEvaluation': on_evaluation,
            'onPacking': lambda e: print(e),
            'onPackingCompleted': lambda e: print("Packing completed!")
        }
    )
    placements = [vars(i) for i in result]
    transformed_parts = calculate_new_positions(parts, placements)
    visualize_parts(parts, transformed_parts)
    return placements

def load_file():
    global parts, bins
    filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if not filepath:
        return
    try:
        with open(filepath, "r") as file:
            parts = []  # Очистить существующие части
            total_area = 0
            invalid_parts = 0  # Счётчик некорректных фигур

            for line in file:
                data = line.strip().split(";")
                part_id = int(data[0])
                points = [Vector(*map(float, point.split(","))) for point in data[1:]]

                # Проверка на минимальное количество точек
                if len(points) < 3:
                    invalid_parts += 1
                    continue

                # Проверка на уникальность координат
                seen_points = set()
                for point in points:
                    if (point.x, point.y) in seen_points:
                        raise ValueError(f"Duplicate coordinates found for part {part_id}.")
                    seen_points.add((point.x, point.y))

                parts.append(Part(part_id, points, {}))
                total_area += calculate_polygon_area(points)
            
            # Обновить размеры Bin
            bin_side = 1.2 * math.sqrt(total_area)
            bins = [Bin(1, bin_side, bin_side, {})]

            if invalid_parts > 0:
                messagebox.showwarning(
                    "Warning",
                    f"{invalid_parts} part(s) were skipped due to insufficient number of coordinates."
                )
            messagebox.showinfo("Success", "Parts loaded successfully!")
    except ValueError as e:
        messagebox.showerror("Error", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")

def start_packing():
    if not parts:
        messagebox.showwarning("Warning", "Please load parts data first!")
        return

    # Close any previous figure before starting a new packing
    if current_figure:
        plt.close(current_figure)

    try:
        # Проверка на целочисленность значений
        config['rotationSteps'] = int(rotation_steps_entry.get())
        config['population'] = int(population_entry.get())
        config['generations'] = int(generations_entry.get())

        # Проверка на плавающую запятую для mutationRate
        config['mutationRate'] = float(mutation_rate_entry.get())
        
        # Проверка на целочисленность для seed
        config['seed'] = int(seed_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric values.")
        return

    def update_progress(value):
        progress_bar["value"] = value
        progress_label["text"] = f"Progress: {value}%"
        root.update_idletasks()

    async def run_async_packing():
        progress_bar["value"] = 0
        progress_label["text"] = "Packing started..."
        await pack_parts(update_progress)
        progress_label["text"] = "Packing finished!"

    loop.create_task(run_async_packing())

# Tkinter UI configuration
root = tk.Tk()
root.title("Packing Application")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

# ToolTip class for displaying maximum values
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="lightyellow", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# Buttons for loading parts and starting packing
load_button = tk.Button(frame, text="Load Parts File", command=load_file, width=20)
load_button.grid(row=0, column=0, padx=5, pady=5)

start_button = tk.Button(frame, text="Start Packing", command=start_packing, width=20)
start_button.grid(row=0, column=1, padx=5, pady=5)

# Progress bar and label
progress_label = tk.Label(frame, text="Progress: 0%", anchor="w")
progress_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=300)
progress_bar.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

# Configuration entries for user input
rotation_steps_label = tk.Label(frame, text="Rotation Steps:")
rotation_steps_label.grid(row=4, column=0, padx=5, pady=5)
rotation_steps_entry = tk.Entry(frame)
rotation_steps_entry.insert(0, str(config['rotationSteps']))
rotation_steps_entry.grid(row=4, column=1, padx=5, pady=5)
ToolTip(rotation_steps_entry, "Max: 5000")

population_label = tk.Label(frame, text="Population:")
population_label.grid(row=5, column=0, padx=5, pady=5)
population_entry = tk.Entry(frame)
population_entry.insert(0, str(config['population']))
population_entry.grid(row=5, column=1, padx=5, pady=5)

generations_label = tk.Label(frame, text="Generations:")
generations_label.grid(row=6, column=0, padx=5, pady=5)
generations_entry = tk.Entry(frame)
generations_entry.insert(0, str(config['generations']))
generations_entry.grid(row=6, column=1, padx=5, pady=5)

mutation_rate_label = tk.Label(frame, text="Mutation Rate:")
mutation_rate_label.grid(row=7, column=0, padx=5, pady=5)
mutation_rate_entry = tk.Entry(frame)
mutation_rate_entry.insert(0, str(config['mutationRate']))
mutation_rate_entry.grid(row=7, column=1, padx=5, pady=5)
ToolTip(mutation_rate_entry, "Max: 1")

seed_label = tk.Label(frame, text="Seed:")
seed_label.grid(row=8, column=0, padx=5, pady=5)
seed_entry = tk.Entry(frame)
seed_entry.insert(0, str(config['seed']))
seed_entry.grid(row=8, column=1, padx=5, pady=5)

# Periodic asyncio loop integration
def periodic_loop():
    loop.stop()
    loop.run_forever()
    root.after(100, periodic_loop)

root.after(100, periodic_loop)
root.mainloop()
