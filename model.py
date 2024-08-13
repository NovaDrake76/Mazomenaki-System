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
            prediction = self.model.predict([[start_position, spin_direction, slots_passed]])
            return prediction
        else:
            return None

