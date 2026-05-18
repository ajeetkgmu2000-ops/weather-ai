from urllib import response

from flask import Flask, request
import requests
import joblib

app = Flask(__name__)

model = joblib.load("weather_model.pkl")

API_KEY = "91ded49b76956e5636275a7090fb3cba"  


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return '''
    <html>
    <head>
        <title>Weather AI</title>

        <!-- 📱 Mobile Fix -->
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <!-- 🌍 Icon -->
        <link rel="icon" href="/static/icon.png" type="image/png">
        <meta name="theme-color" content="#4CAF50">
        <link rel="manifest" href="/static/manifest.json">

        <style>
            body {
                font-family: Arial;
                margin: 0;
                padding: 0;
                text-align: center;
                background: linear-gradient(135deg, #74ebd5, #9face6);
            }

            .container {
                padding: 20px;
            }

            h1 {
                font-size: 34px;
                margin-top: 30px;
            }

            input {
                width: 100%;
                max-width: 400px;
                padding: 18px;
                font-size: 18px;
                border-radius: 12px;
                border: 1px solid #ccc;
                box-sizing: border-box;
            }

            button {
                width: 100%;
                max-width: 400px;
                padding: 16px;
                font-size: 18px;
                border: none;
                border-radius: 12px;
                background: #4CAF50;
                color: white;
            }
        </style>
    </head>

    <body>

        <h1>🌦️ Weather AI</h1>

        <div class="container">
            <form action="/weather">

                <input type="text" name="city" placeholder="Enter city" required>

                <br><br>

                <button type="submit">Get Weather</button>

            </form>
        </div>

    </body>
    </html>
    '''
# ---------------- WEATHER PAGE ----------------
@app.route("/weather")
def weather():
    print("VERSION: FINAL FIX APPLIED")

    city = request.args.get("city")

    if not city:
        return "⚠️ Please enter a city"

    # -------- WEATHER API --------
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return f"❌ API failed: {response.text}"

    data = response.json()

    if str(data.get("cod")) != "200":
        return f"❌ API Error: {data.get('message')}"
    
    # -------- DATA --------
    temp = data["main"]["temp"]
    condition = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    windspeed = data["wind"]["speed"]
    lat = data["coord"]["lat"]
    lon = data["coord"]["lon"]

    # -------- UV --------
    uv_index = "Unavailable"
    try:
        uv_url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={API_KEY}"
        uv_data = requests.get(uv_url).json()

        if "value" in uv_data:
            uv_index = uv_data["value"]

    except Exception as e:
        print("UV ERROR:", e)

     
    # -------- AQI --------
    aqi = 1
    try:
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_data = requests.get(aqi_url).json()

        if "list" in aqi_data:
            aqi = aqi_data["list"][0]["main"]["aqi"]
    except:
        pass


    # -------- SAFE ML PREDICTION --------
    try:
        uv_val = float(uv_index)
    except:
        uv_val = 0.0

    try:
        aqi_val = int(aqi)
    except:
        aqi_val = 1

    temp_val = float(temp)
    humidity_val = float(humidity)
    wind_val = float(windspeed)    
    
    try:
        ml_risk = int(model.predict([[temp_val, humidity_val, wind_val, aqi_val, uv_val]])[0])
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

    if aqi_val <= 2 and uv_val < 3 and temp_val < 35:
        risk = min(risk, 1)

    risk_text = {
        0: "🟢 Safe",
        1: "🟡 Mild Risk",
        2: "🟠 High Risk",
        3: "🔴 Dangerous"
    }.get(risk, "Unknown")

    # -------- AI LOGIC --------
    advice = weather_advice(temp, condition, humidity, windspeed, uv_index, aqi)
    air_quality = aqi_text(aqi)

    # -------- COLOR LOGIC --------

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
        advice += "Strong winds 🌬️be careful, "

    # UV
    try:
        if uv != "N/A" and float(uv) > 7:
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