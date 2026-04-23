import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

data = pd.DataFrame({
    "temp": [5, 15, 25, 35, 42, 30, 18, 10],
    "humidity": [20, 40, 60, 70, 80, 90, 50, 30],
    "windspeed": [2, 3, 5, 7, 10, 6, 4, 2],
    "aqi": [1, 2, 2, 3, 4, 3, 2, 1],
    "uv": [2, 3, 5, 7, 9, 6, 4, 2],
    "risk": [0, 0, 1, 2, 3, 2, 1, 0]
})

X = data[["temp", "humidity", "windspeed", "aqi", "uv"]]
y = data["risk"]

model = DecisionTreeClassifier()
model.fit(X, y)

joblib.dump(model, "weather_model.pkl")

print("MODEL CREATED SUCCESSFULLY")