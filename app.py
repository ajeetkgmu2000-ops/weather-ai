
from flask import Flask, request
import requests
import joblib

model = joblib.load("weather_model.pkl")

app = Flask(__name__)

API_KEY = "f5dd45d9aa867344625dc8024cbe269a"
# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return '''
        <h1>🌦️ Weather AI</h1>
        <form action="/weather">
            <input type="text" name="city" placeholder="Enter city" required>
            <button type="submit">Get Weather</button>
        </form>
    '''

# ---------------- WEATHER PAGE ----------------
@app.route("/weather")
def weather():
    city = request.args.get("city")

    if not city:
        return "⚠️ Please enter a city"

# Weather API
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    if str(data.get("cod")) != "200":
        return f"❌ Error: {data.get('message')}"

    temp = data["main"]["temp"]
    condition = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    windspeed = data["wind"]["speed"]
    lat = data["coord"]["lat"]
    lon = data["coord"]["lon"]

    # UV Index API
    uv_url = f"https://api.openweathermap.org/data/2.5/uvi?appid={API_KEY}&lat={lat}&lon={lon}"
    uv_data = requests.get(uv_url).json()

    uv_index = uv_data.get("value", "N/A")

    # AQI API
    aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    aqi_data = requests.get(aqi_url).json()

    aqi = "N/A"
    if "list" in aqi_data:
       aqi = aqi_data["list"][0]["main"]["aqi"]

       # ---------------- ML PREDICTION ----------------
    try:
        uv_val = float(uv_index) if uv_index != "N/A" else 0
        aqi_val = aqi if aqi != "N/A" else 1

        risk = model.predict([[temp, humidity, windspeed, aqi_val, uv_val]])[0]
    except:
        risk = "N/A"

    risk_text = {
        0: "🟢 Safe",
        1: "🟡 Mild Risk",
        2: "🟠 High Risk",
        3: "🔴 Dangerous"
    }.get(risk, "Unknown")

    # AI logic
    advice = weather_advice(temp, condition, humidity, windspeed, uv_index, aqi)
    air_quality = aqi_text(aqi)

    return f"""
        <h2>🌍 Weather in {city.title()}</h2>

        p>🌡️ Temperature: {temp} °C</p>
        <p>🌤️ Condition: {condition}</p>
        <p>🌬️ Wind Speed: {windspeed} m/s</p>
        <p>💧 Humidity: {humidity}%</p>
        <p>☀️ UV Index: {uv_index}</p> 

        <hr>

        <p>🌫️ Air Quality Index: {aqi} - {air_quality}</p>

        <hr>

        <p>🧠 AI Risk Level: {risk_text}</p>

        <h3>🤖 AI Advice: {advice}</h3>

        <br>
        <a href="/">🔙 Back</a>
    """

# ---------------- AI FUNCTION ----------------
def weather_advice(temp, condition, humidity,windspeed,uv,aqi):
    advice = ""
# Temperature logic
    if temp < 15:
        advice += "It's cold 🧥 Wear a jacket,"
    elif temp < 35:
        advice += "Weather is nice 😊,"
    else:
        advice += "It's hot 🥵 Stay hydrated, "

# Condition logic
    if "rain" in condition.lower():
        advice += "Take an umbrella ☔, "
    elif  "cloud" in condition.lower():
        advice += "Cloudy skies ☁️ ,"
    elif "clear" in condition.lower():
        advice += "Clear sky 🌤️ , "

# Humidity logic
    if humidity > 80:
        advice += "Very humid 💧, "
    elif humidity < 30:
        advice += "Dry air 🌵,"

# Wind logic
    if windspeed > 8:
         advice += "Strong winds 🌬️ Be careful,"

# UV logic           
    try:          
         if uv != "N/A" and float(uv) > 7:
            advice += "High UV ☀️ Use sunscreen, "
    except:
        pass

# AQI logic (NEW)
    if aqi != "N/A":
       if aqi ==1:
        advice += "Air is clean: Good for outdoor activity,"
       elif aqi ==2:
        advice += "Air quality is fair,"
       elif aqi ==3:
        advice += "Moderate pollution: not for sensitive groups,"
       elif aqi ==4:
        advice += "Poor air quality:Avoid outdoor activity,"

    return advice


# ------------- AQI TEXT -----------
def aqi_text(aqi):
    if aqi ==1:
        return "Good 🟢"
    elif aqi == 2:
        return "Fair 🟡"
    elif aqi == 3:
        return "Moderate 🟠"
    elif aqi == 4:
        return "Poor 🔴"
    elif aqi ==5 :
        return "Very Poor ⚫"
    else:
        return "Unknown ❓"

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)