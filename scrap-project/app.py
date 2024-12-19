from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import re
import time
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Selenium setup
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service(r"C:\Users\Yoni\Downloads\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe")


def search_player_and_get_id(driver, first_name, last_name):
    url = "https://www.nba.com/players"
    driver.get(url)
    time.sleep(3)

    search_bar = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search Players']")
    search_bar.clear()
    search_bar.send_keys(f"{first_name} {last_name}")
    search_bar.send_keys(Keys.RETURN)
    time.sleep(3)

    try:
        player_link = driver.find_element(By.CSS_SELECTOR, "a.RosterRow_playerLink__qw1vG")
        relative_url = player_link.get_attribute("href")
        base_url = "https://www.nba.com"
        profile_url = base_url + relative_url if relative_url.startswith("/") else relative_url

        match = re.search(r"player/(\d+)/", profile_url)
        if match:
            player_id = match.group(1)
            return profile_url, player_id
    except Exception as e:
        print(f"Player not found: {e}")
        return None, None


def get_player_stats(driver, player_id):
    url = f"https://www.nba.com/stats/player/{player_id}/boxscores-traditional"
    driver.get(url)
    time.sleep(5)

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.Crom_body__UYOcU tr")
    points, rebounds, assists, game_labels = [], [], [], []

    for row in rows[:10]:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 16:
                game_info = cells[0].text
                pts = cells[3].text
                reb = cells[15].text
                ast = cells[16].text

                points.append(int(pts))
                rebounds.append(int(reb))
                assists.append(int(ast))
                game_labels.append(game_info)
        except Exception as e:
            print(f"Error processing row: {e}")

    return points, rebounds, assists, game_labels


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            profile_url, player_id = search_player_and_get_id(driver, first_name, last_name)
            if player_id:
                points, rebounds, assists, game_labels = get_player_stats(driver, player_id)

                # Create plot
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(game_labels, points, marker='o', label="Points", alpha=0.7)
                ax.plot(game_labels, rebounds, marker='s', label="Rebounds", alpha=0.7)
                ax.plot(game_labels, assists, marker='^', label="Assists", alpha=0.7)
                ax.legend()
                ax.set_title(f"Last 10 Games Stats")
                ax.set_xlabel("Games")
                ax.set_ylabel("Stats")
                plt.xticks(rotation=45)

                # Save plot to a string
                buf = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format="png")
                buf.seek(0)
                plot_data = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()

                return render_template("result.html", plot_data=plot_data, game_labels=game_labels, points=points, rebounds=rebounds, assists=assists, zip=zip)

        finally:
            driver.quit()

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
