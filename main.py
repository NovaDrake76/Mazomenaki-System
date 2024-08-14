import tkinter as tk
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class CrazyTimeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crazy Time Prediction")
        self.root.geometry("1280x768")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")
        self.font_large = ("Helvetica", 14, "bold")
        self.font_medium = ("Helvetica", 12)
        self.font_small = ("Helvetica", 10)

        self.canvas = tk.Canvas(root, width=600, height=600, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(pady=20)

        self.wheel_segments = [
            "1", "10", "1", "5", "1", "CASH HUNT", "1", "2", "5", "1", "2", "COINFLIP", "2", "1", "10", 
            "2", "1", "CRAZY TIME", "1", "2", "5", "1", "2", "PACHINKO", "1", "5", "1", "2", "1", 
            "COINFLIP", "1", "2", "1", "10", "2", "CASH HUNT", "1", "2", "1", "5", "1", "COINFLIP", 
            "1", "5", "2", "10", "1", "PACHINKO", "1", "2", "5", "1", "2", "COINFLIP"
        ]

        self.segment_colors = {
            "1": "#9ec5d3",
            "2": "#eebf56",
            "5": "#f6c5ce",
            "10": "#ac9bdc",
            "CASH HUNT": "#1d8e52",
            "COINFLIP": "#222599",
            "PACHINKO": "#ff5be0",
            "CRAZY TIME": "#b01824"
        }

        #averages
        self.avg_slots_passed_cw = 0
        self.avg_slots_passed_ccw = 0
        self.cw_count = 0
        self.ccw_count = 0

        #prediction success rate tracking
        self.total_predictions = 0
        self.successful_predictions = 0

        self.current_position = 0
        self.sensitivity = 1.5
        self.slots_passed = 0
        self.initial_angle = None
        self.previous_slot_index = None
        self.game_started = False
        self.spin_direction = None
        self.predicted_positions = None

        self.start_game_button_ccw = tk.Button(root, text="Start Game Counterclockwise", command=lambda: self.start_spin(-1), font=self.font_medium, bg="#f76c6c", fg="white")
        self.start_game_button_ccw.pack(side=tk.LEFT, padx=20)

        self.start_game_button_cw = tk.Button(root, text="Start Game Clockwise", command=lambda: self.start_spin(1), font=self.font_medium, bg="#6cf76c", fg="white")
        self.start_game_button_cw.pack(side=tk.RIGHT, padx=20)

        self.end_game_button = tk.Button(root, text="End Game", command=self.end_game, font=self.font_medium, bg="#6c8ef7", fg="white")
        self.end_game_button.pack(pady=10)

        self.status_label = tk.Label(root, text="Set the starting position and click 'Start Game'", font=self.font_medium, bg="#f0f0f0")
        self.status_label.pack()

        self.slot_info_label = tk.Label(root, text="Current Slot: None", font=self.font_large, bg="#f0f0f0")
        self.slot_info_label.pack()

        self.slots_passed_label = tk.Label(root, text="Slots Passed: 0", font=self.font_large, bg="#f0f0f0")
        self.slots_passed_label.pack()

        self.draw_wheel()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.data = pd.DataFrame(columns=['start_position', 'spin_direction', 'slots_passed', 'stopping_position'])
        self.load_data()

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.trained = False
        self.train_if_ready()

    def draw_wheel(self, highlight_positions=None):
        self.canvas.delete("all")
        angle_per_segment = 360 / len(self.wheel_segments)
        
        for i, segment in enumerate(reversed(self.wheel_segments)):
            start_angle = (i * angle_per_segment + self.current_position) % 360
            end_angle = start_angle + angle_per_segment
            color = self.segment_colors[segment]
            
            # Highlight the predicted slots
            if highlight_positions and (len(self.wheel_segments) - 1 - i) in highlight_positions:
                color = "orange"
                
            self.canvas.create_arc((50, 50, 550, 550), start=start_angle, extent=angle_per_segment, fill=color, outline='black')
            
            text_angle = start_angle + angle_per_segment / 2
            text_x = 300 + 230 * np.cos(np.radians(text_angle))
            text_y = 300 - 230 * np.sin(np.radians(text_angle))
            self.canvas.create_text(text_x, text_y, text=segment, fill='black', font=("Helvetica", 10, "bold"))
        
        self.canvas.create_oval(200, 200, 400, 400, fill="red", outline="black")
        self.canvas.create_text(300, 300, text="CRAZY TIME", fill="white", font=("Helvetica", 16, "bold"))
        
        self.canvas.create_polygon([290, 40, 310, 40, 300, 20], fill="black")

        top_position_angle = (self.current_position) % 360
        current_slot_index = int((top_position_angle + 270) % 360 / angle_per_segment) % len(self.wheel_segments)
        current_slot = self.wheel_segments[current_slot_index]
        
        self.slot_info_label.config(text=f"Current Slot: {current_slot}")

    def update_wheel(self, delta_angle):
        self.current_position = (self.current_position + delta_angle) % 360
        angle_per_segment = 360 / len(self.wheel_segments)
        current_slot_index = int(self.current_position / angle_per_segment)

        if self.game_started:
            if current_slot_index != self.previous_slot_index:
                self.slots_passed += self.spin_direction
            self.previous_slot_index = current_slot_index
            self.slots_passed_label.config(text=f"Slots Passed: {self.slots_passed}")

        self.draw_wheel(highlight_positions=self.predicted_positions)

    def on_click(self, event):
        self.initial_angle = np.degrees(np.arctan2(300 - event.y, event.x - 300)) % 360

    def on_drag(self, event):
        new_angle = np.degrees(np.arctan2(300 - event.y, event.x - 300)) % 360
        delta_angle = (new_angle - self.initial_angle)
        if delta_angle > 180:
            delta_angle -= 360
        elif delta_angle < -180:
            delta_angle += 360
        delta_angle /= self.sensitivity
        self.update_wheel(delta_angle)
        self.initial_angle = new_angle

    def start_spin(self, direction):
        self.game_started = True
        self.spin_direction = direction
        self.slots_passed = 0
        self.previous_slot_index = int(self.current_position / (360 / len(self.wheel_segments)))
        self.status_label.config(text="Game started. Spin the wheel.")
        self.predict_winning_slots()

    def end_game(self):
        stop_position = int(self.current_position / (360 / len(self.wheel_segments)))
        
        if self.predicted_positions and stop_position in self.predicted_positions:
            self.successful_predictions += 1
        self.total_predictions += 1

        success_rate = (self.successful_predictions / self.total_predictions) * 100
        self.status_label.config(text=f"Success Rate: {success_rate:.2f}%")

        #save the spin result
        self.save_spin_result(self.previous_slot_index, self.spin_direction, abs(self.slots_passed), stop_position)
        self.reset_spin()
        self.status_label.config(text=f"Game ended. Stop position: {stop_position}. Start a new game.")
        self.predicted_positions = None
        self.draw_wheel()

    def reset_spin(self):
        self.game_started = False
        self.slots_passed = 0
        self.spin_direction = None

    def load_data(self):
        try:
            self.data = pd.read_csv('crazy_time_data.csv')
            print("Data loaded.")
        except FileNotFoundError:
            print("No existing data found. Starting fresh.")

    def save_data(self):
        self.data.to_csv('crazy_time_data.csv', index=False)
        print("Data saved.")

    def save_spin_result(self, start_position, spin_direction, slots_passed, stop_position):
        # Calculate and update averages
        if spin_direction == 1:
            self.avg_slots_passed_cw = (self.avg_slots_passed_cw * self.cw_count + slots_passed) / (self.cw_count + 1)
            self.cw_count += 1
        else:
            self.avg_slots_passed_ccw = (self.avg_slots_passed_ccw * self.ccw_count + slots_passed) / (self.ccw_count + 1)
            self.ccw_count += 1

        #save data
        self.data.loc[len(self.data)] = [start_position, spin_direction, slots_passed, stop_position]
        self.save_data()
        self.train_if_ready()

    def train_if_ready(self):
        if len(self.data) >= 10:
            X = self.data[['start_position', 'spin_direction', 'slots_passed']]
            y = self.data['stopping_position']
            self.model.fit(X, y)
            self.trained = True
            self.status_label.config(text="Model trained with current data.")
            print("Model trained with current data.")
        else:
            self.status_label.config(text="Not enough data to predict results.")

    def predict_winning_slots(self):
        if self.trained:
            predicted_position = self.predict(self.previous_slot_index, self.spin_direction, self.slots_passed)
            if predicted_position is not None:
                predicted_position = int(predicted_position[0])

                possible_winning_slots = [(predicted_position + i) % len(self.wheel_segments) for i in range(-3, 4)]
                self.predicted_positions = possible_winning_slots

                winning_slots = [self.wheel_segments[i] for i in self.predicted_positions]

                slot_counts = {}
                for slot in winning_slots:
                    slot_counts[slot] = slot_counts.get(slot, 0) + 1

                total_slots = len(winning_slots)
                slot_percentages = {slot: (count / total_slots) * 100 for slot, count in slot_counts.items()}

                display_text = "Possible Winning Slots: " + ', '.join([f"{slot} ({slot_percentages[slot]:.2f}%)"
                                                                        for slot in slot_percentages])
                self.status_label.config(text=display_text)

                self.draw_wheel(highlight_positions=self.predicted_positions)


    def predict(self, start_position, spin_direction, slots_passed):
        if self.trained:
            adjusted_slots_passed = slots_passed
            if spin_direction == 1 and self.cw_count > 0:
                adjusted_slots_passed += (self.avg_slots_passed_cw - slots_passed) * 0.1
            elif spin_direction == -1 and self.ccw_count > 0:
                adjusted_slots_passed += (self.avg_slots_passed_ccw - slots_passed) * 0.1

            input_data = pd.DataFrame([[start_position, spin_direction, adjusted_slots_passed]], 
                                      columns=['start_position', 'spin_direction', 'slots_passed'])
            return self.model.predict(input_data)
        return None

    def on_closing(self):
        self.save_data()
        self.root.destroy()

# Running the application
root = tk.Tk()
app = CrazyTimeApp(root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.mainloop()


import pandas as pd

class DataHandler:
    def __init__(self):
        self.data = pd.DataFrame(columns=['start_position', 'spin_direction', 'slots_passed', 'stopping_position'])
        self.load_data()

    def save_data(self):
        self.data.to_csv('crazy_time_data.csv', index=False)
        print("Data saved.")

    def load_data(self):
        try:
            self.data = pd.read_csv('crazy_time_data.csv')
            print("Data loaded.")
        except FileNotFoundError:
            print("No existing data found. Starting fresh.")

    def save_spin_result(self, start_position, spin_direction, slots_passed, stop_position):
        self.data.loc[len(self.data)] = [start_position, spin_direction, slots_passed, stop_position]

    def get_data(self):
        return self.data

from sklearn.ensemble import RandomForestClassifier

class PredictionModel:
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.trained = False
        self.train_if_ready()

    def train_if_ready(self):
        data = self.data_handler.get_data()
        if len(data) >= 10:
            X = data[['start_position', 'spin_direction', 'slots_passed']]
            y = data['stopping_position']
            self.model.fit(X, y)
            self.trained = True
            print("Model trained with current data.")

def predict(self, start_position, spin_direction, slots_passed):
    if self.trained:
        input_data = pd.DataFrame([[start_position, spin_direction, slots_passed]], 
                                  columns=['start_position', 'spin_direction', 'slots_passed'])
        prediction = self.model.predict(input_data)
        return prediction
    else:
        return None
