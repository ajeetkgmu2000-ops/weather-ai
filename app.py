from flask import Flask, request
import requests
import joblib

app = Flask(__name__)

model = joblib.load("weather_model.pkl")

API_KEY = "f5dd45d9aa867344625dc8024cbe269a"


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
    print("VERSION: FINAL FIX APPLIED")

    city = request.args.get("city")

    if not city:
        return "⚠️ Please enter a city"

    # -------- WEATHER API --------
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return "❌ API request failed (Check API/internet)"

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
    uv_index = "N/A"
    try:
        uv_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid={API_KEY}"
        uv_data = requests.get(uv_url).json()
        uv_index = uv_data.get("current", {}).get("uvi", "N/A")
    except:
        pass

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
    
    print("RAW AQI:", aqi, type(aqi))
    print("AQI_VAL:", aqi_val, type(aqi_val))
    # -------- SAFETY OVERRIDE --------
    # Always start from ML
    try:
      risk = int(ml_risk)
    except:
      risk = 0
    
    # 🔥 FORCE RULES (ALL independent — NO elif)

     # AQI highest priority
    if aqi_val >= 4:
     risk = 3

     # Moderate AQI
    if aqi_val == 3:
     risk = max(risk, 2)

     # UV risk
    if uv_val >= 9:
     risk = max(risk, 2)

     # Heat risk
    if temp_val > 40:
     risk = max(risk, 2)

     # Dry heat
    if humidity_val < 20 and temp_val > 38:
     risk = max(risk, 1)

    print("DEBUG → AQI:", aqi_val, "UV:", uv_val, "TEMP:", temp_val, "ML:", ml_risk, "FINAL:", risk)
     
    

    

    risk_text = {
        0: "🟢 Safe",
        1: "🟡 Mild Risk",
        2: "🟠 High Risk",
        3: "🔴 Dangerous"
    }.get(risk, "Unknown")

    # -------- AI LOGIC --------
    advice = weather_advice(temp, condition, humidity, windspeed, uv_index, aqi)
    air_quality = aqi_text(aqi)

    # -------- HTML --------
    return f"""
    <html>
    <head>
        <title>Weather AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family:Arial; background:#f2f6ff; text-align:center;">

        <h1>🌦️ Weather AI</h1>

        <div style="background:white; padding:20px; border-radius:10px; width:90%; max-width:400px; margin:auto;">
            <h2>🌍 {city.title()}</h2>


              🌡️ Temperature: {temp} °C <br>
              🌤️ Condition: {condition} <br>
              🌬️ Wind Speed: {windspeed} m/s <br>
              💧 Humidity: {humidity}% <br>
              ☀️ UV Index: {uv_index} <br>
              🌫️ Air Quality Index: {aqi} - {air_quality} <br><br>

              <b>🧠 AI Risk Level: {risk_text} <br><br>

              🤖 AI Advice: {advice} 
               <br><br>

              <a href="/">🔙 Back</a>
            </div>

    </body>
    </html>
    """


# ---------------- AI FUNCTION ----------------
def weather_advice(temp, condition, humidity, windspeed, uv, aqi):
    advice = ""

    # Temperature
    if temp < 15:
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


