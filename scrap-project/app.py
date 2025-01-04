from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
from config import Config
#from inverted_index import build_inverted_index_from_pages
import csv


app = Flask(__name__)
app.config.from_object(Config)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--headless")  # Optional: run in headless mode

service = Service(ChromeDriverManager().install())
page_texts = []


def extract_visible_text(driver):
    """
    Extracts visible text from the current page source.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    texts = soup.stripped_strings
    return " ".join(texts)


def export_to_csv(filename, headers, rows):
    """
    Exports data to a CSV file.
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Data has been exported to {filename}")


def fetch_page_content(driver):
    """
    Fetch the full HTML content of the current page.
    """
    return driver.page_source


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
    stats_data = []

    for row in rows[:10]:  # Fetch stats for the last 10 games
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 16:
                game_info = cells[0].text  # Game information
                pts = cells[3].text  # Points
                reb = cells[15].text  # Rebounds
                ast = cells[16].text  # Assists

                stats_data.append([game_info, int(pts), int(reb), int(ast)])
        except Exception as e:
            print(f"Error processing row: {e}")

    # Calculate averages
    if stats_data:
        avg_points = sum(row[1] for row in stats_data) / len(stats_data)
        avg_rebounds = sum(row[2] for row in stats_data) / len(stats_data)
        avg_assists = sum(row[3] for row in stats_data) / len(stats_data)
    else:
        avg_points = avg_rebounds = avg_assists = 0

    # Append averages as the last row
    stats_data.append(["Averages", round(avg_points, 2), round(avg_rebounds, 2), round(avg_assists, 2)])

    return stats_data


@app.route("/", methods=["GET", "POST"])
def index():
    message_player = None
    message_h2h = None

    if request.method == "POST" and "first_name" in request.form:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            profile_url, player_id = search_player_and_get_id(driver, first_name, last_name)
            if player_id:
                stats_data = get_player_stats(driver, player_id)
                if stats_data:
                    # Export to CSV
                    filename = f"{first_name}_{last_name}_stats.csv"
                    headers = ["Game", "Points", "Rebounds", "Assists"]
                    export_to_csv(filename, headers, stats_data)

                    message_player = f"Player stats exported to {filename}"
                else:
                    message_player = "No stats data found for the player."
        finally:
            driver.quit()

    if request.method == "POST" and "team1" in request.form:
        team1 = request.form.get("team1")
        team2 = request.form.get("team2")

        if team1 == team2:
            message_h2h = "Please select two different teams."
        else:
            team1_id = app.config["TEAM_IDS"].get(team1)
            team2_id = app.config["TEAM_IDS"].get(team2)

            if not team1_id or not team2_id:
                message_h2h = "Invalid team selection."
            else:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                try:
                    rows_data = get_head_to_head_data(driver, team1_id, team2_id, team1, team2)
                finally:
                    driver.quit()

                if rows_data:
                    filename = f"{team1}_vs_{team2}_H2H.csv"
                    headers = ["Matchup", "Winner", "Score"]
                    rows = [[data["Matchup"], data["Winner"], data["Score"]] for data in rows_data]

                    export_to_csv(filename, headers, rows)

                    message_h2h = f"Head-to-Head data exported to {filename}"
                else:
                    message_h2h = "No head-to-head data found for the selected teams."

    return render_template("index.html", message_player=message_player, message_h2h=message_h2h, teams=app.config["TEAM_IDS"].keys())


def get_head_to_head_data(driver, first_team_id, second_team_id, first_team, second_team):
    """
    Fetches the last 5 H2H games for first_team vs. second_team from the most recent seasons.
    Starts from 2024-25 and goes back to earlier seasons if necessary.
    """
    def fetch_team_data(team_a, team_b, season):
        """
        Fetches raw data for team_a against team_b for a given season.
        """
        url = f"https://www.nba.com/stats/team/{team_a}/boxscores-traditional?OpponentTeamID={team_b}&Season={season}"
        driver.get(url)
        time.sleep(5)

        table = driver.find_element(By.CSS_SELECTOR, "table.Crom_table__p1iZz")
        rows_data = []

        try:
            body_rows = table.find_elements(By.CSS_SELECTOR, "tbody.Crom_body__UYOcU tr")
            for row in body_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = [cell.text.strip() for cell in cells]
                rows_data.append(row_data)
        except Exception as e:
            print("Error extracting row data:", e)

        return rows_data

    # Define starting season and initialize processed data
    current_season = 2024
    max_games = 5
    processed_data = []

    while len(processed_data) < max_games and current_season >= 2000:  # Limit to seasons starting from 2000
        season_str = f"{current_season}-{str(current_season + 1)[-2:]}"

        # Fetch data for first_team vs. second_team
        rows_data1 = fetch_team_data(first_team_id, second_team_id, season_str)
        # Fetch data for second_team vs. first_team (reverse matchup)
        rows_data2 = fetch_team_data(second_team_id, first_team_id, season_str)

        # Combine and process data for the season
        for row1, row2 in zip(rows_data1, rows_data2):
            if len(processed_data) >= max_games:
                break

            matchup = row1[0]  # Date and matchup string
            score_team1 = int(row1[3])  # Points for first_team
            score_team2 = int(row2[3])  # Points for second_team

            winner = first_team if score_team1 > score_team2 else second_team

            processed_data.append({
                "Matchup": matchup,
                "Winner": winner,
                "Score": f"{first_team} {score_team1} - {second_team} {score_team2}"
            })

        # Move to the previous season
        current_season -= 1

    return processed_data


if __name__ == "__main__":
    app.run(debug=True, port=4000, use_reloader=False)
