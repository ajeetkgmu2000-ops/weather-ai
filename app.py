from urllib import response

from flask import Flask, request
import requests
import joblib

app = Flask(__name__)

model = joblib.load("weather_model.pkl")

API_KEY = "b140148be18b4d3092f124116261705"  


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return '''
    <h1 style="text-align:center; font-size:42px;">
        🌦️ Weather AI
    </h1>
    <div style="text-align:center;">
        <form action="/weather">
            <input type="text" name="city" placeholder="Enter city" required>
            <button type="submit">Get Weather</button>
        </form>
    </div>
    '''


# ---------------- WEATHER PAGE ----------------
@app.route("/weather")
def weather():
    city = request.args.get("city")

    if not city:
        return "⚠️ Please enter a city"


    # -------- WEATHER API --------
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=yes"
    response = requests.get(url)

    if response.status_code != 200:
     return "❌ API request failed"

    data = response.json()
    
    # -------- DATA --------
    temp = data["current"]["temp_c"]
    condition = data["current"]["condition"]["text"]
    humidity = data["current"]["humidity"]
    windspeed = data["current"]["wind_kph"] / 3.6

    # -------- UV --------
    uv_index = data["current"]["uv"]
    if uv_index is None:
        uv_index = "Unavailable"
     
    # -------- AQI --------
    aqi = 1
    try:
        pm25 = data["current"]["air_quality"]["pm2_5"]

        if pm25 <= 12:
            aqi = 1
        elif pm25 <= 35:
            aqi = 2
        elif pm25 <= 55:
            aqi = 3
        elif pm25 <= 150:
            aqi = 4
        else:
            aqi = 5
    except:
        aqi = 1

    # -------- SAFE ML PREDICTION --------
    try:
        uv_val = float(uv_index)
    except:
        uv_val = 0.0

    try:
        aqi_val = int(aqi) 
    except:
        aqi_val = 1

    try:
        temp_val = float(temp)
        humidity_val = float(humidity)
        wind_val = float(windspeed)
    except:
        return "❌ invalid weather data"
    try:
        ml_risk = model.predict([[temp_val, humidity_val, wind_val, aqi_val, uv_val]])[0]
        ml_risk = int(ml_risk) 
    except:
        ml_risk = 0
    
     # -------- FINAL RISK --------
    risk = ml_risk

    if aqi_val >= 4:
        risk = 3

    if aqi_val == 3:
        risk = max(risk, 2)

    if uv_val >= 9:
        risk = max(risk, 2)

    if temp_val > 40:
        risk = max(risk, 2)

    if humidity_val < 20 and temp_val > 38:
        risk = max(risk, 1)

    # -------- TEXT --------
    risk_text = {
        0: "🟢 Safe",
        1: "🟡 Mild Risk",
        2: "🟠 High Risk",
        3: "🔴 Dangerous"
    }.get(risk, "Unknown")

    air_quality = aqi_text(aqi)
    advice = weather_advice(temp, condition, humidity, windspeed, uv_index, aqi)
    
    # -------- COLORS --------
    if risk == 0:
        risk_color = "#4CAF50"
    elif risk == 1:
        risk_color = "#FFC107"
    elif risk == 2:
        risk_color = "#FF9800"
    else:
        risk_color = "#F44336"

    if aqi_val <= 2:
        aqi_color = "#4CAF50"
    elif aqi_val == 3:
        aqi_color = "#FF9800"
    else:
        aqi_color = "#F44336"

    if uv_val < 3:
        uv_color = "#4CAF50"
    elif uv_val < 7:
        uv_color = "#FFC107"
    else:
        uv_color = "#9C27B0"
    
    

    # -------- HTML --------
    return f"""
<html>
<head>
    <title>Weather AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
    font-family:Arial;
    margin:0;
    padding:0;
    background: linear-gradient(135deg, #74ebd5, #9face6);
    text-align:center;
">

<h1 style="padding:20px;">🌦️ Weather AI</h1>


<div style="
    background:white;
    padding:20px;
    border-radius:15px;
    width:90%;
    max-width:420px;
    margin:auto;
    box-shadow:0 8px 20px rgba(0,0,0,0.2);
">

    <h2>🌍 {city.title()}</h2>

    <div style="text-align:left; line-height:1.6;">
         🌡️ Temperature: {temp} °C <br>
         🌤️ Condition: {condition} <br>
         🌬️ Wind Speed: {windspeed} m/s <br>
         💧 Humidity: {humidity}% <br>
    </div>

    <br>  

    <!-- UV BLOCK -->
    <div style="
        background:{uv_color};
        color:white;
        padding:10px;
        border-radius:10px;
        margin-bottom:10px;
    ">
        ☀️ UV Index: {uv_index}
    </div>

    <!-- AQI BLOCK -->
    <div style="
        background:{aqi_color};
        color:white;
        padding:10px;
        border-radius:10px;
        margin-bottom:10px;
    ">
        🌫️ AQI: {aqi} - {air_quality}
    </div>

    <!-- RISK BLOCK -->
    <div style="
        background:{risk_color};
        color:white;
        padding:12px;
        border-radius:10px;
        font-weight:bold;
        margin-bottom:15px;
    ">   

        🧠 AI Risk Level: {risk_text} 
    </div>   

    <!-- ADVICE -->
    <div style="
        background:#f5f5f5;
        padding:10px;
        border-radius:10px;
        text-align:left;
    ">
        🤖 {advice}
    </div>

    <br>
    <a href="/">🔙 Back</a>

  </div>  

  </body>
  </html>
  """

# ---------------- AI FUNCTION ----------------
def weather_advice(temp, condition, humidity, windspeed, uv, aqi):
    advice = ""

    # Temperature
    if temp < 20:
        advice += "It's cold 🧥 Wear a jacket, "
    elif temp < 35:
        advice += "Weather is nice 😊, "
    else:
        advice += "It's hot 🥵 Stay hydrated, "

    # Condition
    if "rain" in condition.lower():
        advice += "Take an umbrella ☔, "
    elif "cloud" in condition.lower():
        advice += "Cloudy skies ☁️, "
    elif "clear" in condition.lower():
        advice += "Clear sky 🌤️, "

    # Humidity
    if humidity > 80:
        advice += "Very humid 💧, "
    elif humidity < 30:
        advice += "Dry air 🌵, "

    # Wind
    if windspeed > 8:
        advice += "Strong winds 🌬️ Be careful, "

    # UV
    try:
     if float(uv) > 7:
        advice += "High UV ☀️ Use sunscreen, "
    except:
     pass

    # -------- YOUR AQI LOGIC (UNCHANGED) --------
    if aqi != "N/A":
        if aqi == 1:
            advice += "Air is clean: Good for outdoor activity, "
        elif aqi == 2:
            advice += "Air quality is fair, "
        elif aqi == 3:
            advice += "Moderate pollution: not for sensitive groups, "
        elif aqi == 4:
            advice += "Poor air quality: Avoid outdoor activity, "

    return advice

# ---------------- AQI TEXT ----------------
def aqi_text(aqi):
    if aqi == 1:
        return "Good 🟢"
    elif aqi == 2:
        return "Fair 🟡"
    elif aqi == 3:
        return "Moderate 🟠"
    elif aqi == 4:
        return "Poor 🔴"
    elif aqi == 5:
        return "Very Poor ⚫"
    else:
        return "Unknown ❓"

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)