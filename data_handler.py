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

