import os

from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import time

from config import Config
import csv


app = Flask(__name__)
app.config.from_object(Config)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Optional headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
chrome_options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"  # Path to Chrome binary

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

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
    start_time = time.time()
    message_player = None
    message_h2h = None
    message_free_throws = None

    if request.method == "POST" and "first_name" in request.form:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            profile_url, player_id = search_player_and_get_id(driver, first_name, last_name)
            if player_id:
                stats_data = get_player_stats(driver, player_id)
                if stats_data:
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

    if request.method == "POST" and request.form.get("action") == "free_throws":
        try:
            filename = get_top_5_teams_by_free_throw_percentage()
            message_free_throws = f"Free throw stats exported to {filename}"
        except Exception as e:
            message_free_throws = f"An error occurred: {str(e)}"

    end_time = time.time()
    print(f"The execution took {end_time - start_time:.2f} seconds to complete.")

    return render_template(
        "index.html",
        message_player=message_player,
        message_h2h=message_h2h,
        message_free_throws=message_free_throws,
        teams=app.config["TEAM_IDS"].keys(),
    )


def get_head_to_head_data(driver, first_team_id, second_team_id, first_team, second_team):
    """
    Fetches the last 5 H2H games for first_team vs. second_team from the most recent seasons.
    Starts from 2024-25 and goes back to earlier seasons if necessary.
    """
    def fetch_team_data(team_a, team_b, season):
        """
        Fetches raw data for team_a against team_b for a given season.
        Handles cookie banners by clicking the close button if present.
        """
        url = f"https://www.nba.com/stats/team/{team_a}/boxscores-traditional?OpponentTeamID={team_b}&Season={season}"
        driver.get(url)

        table = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.Crom_table__p1iZz"))
        )
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


def get_team_free_throw_percentage(driver, team_id):
    """
    Retrieves the free throw percentages for the last 3 games for a given team.
    """
    url = f"https://www.nba.com/stats/team/{team_id}/boxscores-traditional"
    driver.get(url)
    time.sleep(5)

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.Crom_body__UYOcU tr")
    free_throw_percentages = []

    for row in rows[:3]:  # Fetch percentages for the last 3 games
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 12:  # Ensure the cell exists
                ft_percentage = cells[12].text  # Free throw percentage
                if ft_percentage != "":  # Avoid empty cells
                    free_throw_percentages.append(float(ft_percentage.strip('%')))
        except Exception as e:
            print(f"Error processing row for team {team_id}: {e}")

    return free_throw_percentages


def get_top_5_teams_by_free_throw_percentage():
    """
    Iterates over all teams, calculates their average free throw percentage for
    the last 3 games, and identifies the top 5 teams.
    """
    driver = webdriver.Chrome(service=service, options=chrome_options)
    team_results = []

    try:
        for team_name, team_id in app.config["TEAM_IDS"].items():
            if not team_id:  # Skip teams without IDs
                continue

            free_throw_percentages = get_team_free_throw_percentage(driver, team_id)
            if free_throw_percentages:
                avg_percentage = sum(free_throw_percentages) / len(free_throw_percentages)
                team_results.append({
                    "Team": team_name,
                    "Free Throw Percentages": free_throw_percentages,
                    "Average Free Throw Percentage": avg_percentage
                })
    finally:
        driver.quit()

    # Sort by average free throw percentage in descending order
    team_results.sort(key=lambda x: x["Average Free Throw Percentage"], reverse=True)

    # Export to CSV
    filename = "free_throw_percentages.csv"
    export_free_throw_percentages_to_csv(filename, team_results)

    return filename  # Return the CSV file name to indicate success


def export_free_throw_percentages_to_csv(filename, team_results):
    """
    Exports free throw percentages to a CSV file, including the top 5 teams at the end.
    """
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header for all teams
        writer.writerow(["Team", "Game 1 Free Throw %", "Game 2 Free Throw %", "Game 3 Free Throw %", "Average Free Throw %"])

        # Write data for all teams
        for team in team_results:
            row = [team["Team"]]
            row.extend(team["Free Throw Percentages"])
            row.append(f"{team['Average Free Throw Percentage']:.2f}")
            writer.writerow(row)

        # Add a blank row as a separator
        writer.writerow([])

        # Write the top 5 teams header
        writer.writerow(["Top 5 Teams by Average Free Throw Percentage"])
        writer.writerow(["Rank", "Team", "Game 1 Free Throw %", "Game 2 Free Throw %", "Game 3 Free Throw %", "Average Free Throw %"])

        # Write data for the top 5 teams
        for rank, team in enumerate(team_results[:5], start=1):
            row = [rank, team["Team"]]
            row.extend(team["Free Throw Percentages"])
            row.append(f"{team['Average Free Throw Percentage']:.2f}")
            writer.writerow(row)

    print(f"Free throw percentages exported to {filename}")


@app.route("/lior")
def lior():
    return render_template("lior.html")


@app.route("/nevo")
def nevo():
    return render_template("nevo.html")


@app.route("/raz")
def raz():
    return render_template("raz.html")


@app.route("/yoni")
def yoni():
    return render_template("yoni.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
