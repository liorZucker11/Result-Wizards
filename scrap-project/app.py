import nltk
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager  # Import webdriver-manager
import re
import time
import matplotlib.pyplot as plt
import io
import base64
from config import Config
from inverted_index import build_inverted_index_from_pages
import pandas as pd
import os
import csv


app = Flask(__name__)
app.config.from_object(Config)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--headless")  # Optional: run in headless mode
chrome_options.add_argument("--disable-gpu")

# Automatically manage Chrome driver with webdriver-manager
service = Service(ChromeDriverManager().install())


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

    # Fetch the full page content
    page_content = fetch_page_content(driver)

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

    return points, rebounds, assists, game_labels, page_content


@app.route("/", methods=["GET", "POST"])
def index():
    pages_content = []

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            profile_url, player_id = search_player_and_get_id(driver, first_name, last_name)
            if player_id:
                points, rebounds, assists, game_labels, page_content = get_player_stats(driver, player_id)
                pages_content.append(page_content)

                # Build inverted index and calculate most frequent words
                inverted_index, most_common_words = build_inverted_index_from_pages(pages_content)

                # Save to CSV file
                output_dir = os.getcwd()
                common_words_file = os.path.join(output_dir, "most_common_words.csv")
                inverted_index_file = os.path.join(output_dir, "inverted_index.csv")

                # Save most common words
                with open(common_words_file, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Word", "Frequency"])
                    writer.writerows(most_common_words)

                # Save inverted index
                with open(inverted_index_file, mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Word", "Documents"])
                    for word, doc_ids in inverted_index.items():
                        writer.writerow([word, ", ".join(map(str, doc_ids))])

                print(f"CSV files saved: {common_words_file}, {inverted_index_file}")

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

                return render_template(
                    "result.html",
                    plot_data=plot_data,
                    game_labels=game_labels,
                    points=points,
                    rebounds=rebounds,
                    assists=assists,
                    zip=zip
                )

        finally:
            driver.quit()

    return render_template("index.html", teams=app.config["TEAM_IDS"].keys())


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

            if score_team1 > score_team2:
                winner = first_team
            else:
                winner = second_team

            processed_data.append({
                "Matchup": matchup,
                "Winner": winner,
                "Score": f"{first_team} {score_team1} - {second_team} {score_team2}"
            })

        # Move to the previous season
        current_season -= 1

    return processed_data

# def get_head_to_head_data(driver, first_team, second_team):
#     """
#     Navigates to the H2H URL for first_team vs. second_team (2024-25 season),
#     scrapes the table, and returns headers + row data.
#     """
#     url = f"https://www.nba.com/stats/team/{first_team}/boxscores-traditional?OpponentTeamID={second_team}&Season=2024-25"
#     driver.get(url)
#
#     time.sleep(5)
#
#     table = driver.find_element(By.CSS_SELECTOR, "table.Crom_table__p1iZz")
#
#     headers = []
#     try:
#         header_cells = table.find_elements(By.CSS_SELECTOR, "tr.Crom_headers__mzI_m")
#         header_row = [hc.text.strip() for hc in header_cells]
#         headers = header_row[0].split()
#
#         if len(headers) > 1 and headers[0] == "MATCH" and headers[1] == "UP":
#             headers = ["MATCH UP"] + headers[2:]
#     except Exception as e:
#         print("No headers found or error extracting headers:", e)
#
#     rows_data = []
#     try:
#         body_rows = table.find_elements(By.CSS_SELECTOR, "tbody.Crom_body__UYOcU tr")
#         for row in body_rows:
#             cells = row.find_elements(By.TAG_NAME, "td")
#             row_text = [c.text.strip() for c in cells]
#             rows_data.append(row_text)
#     except Exception as e:
#         print("No row data found or error extracting rows:", e)
#
#     print("Headers:", headers)
#     print("Rows data:", rows_data)
#
#     return headers, rows_data


@app.route("/headtohead", methods=["GET", "POST"])
def headtohead():
    if request.method == "POST":
        team1 = request.form.get("team1")
        team2 = request.form.get("team2")

        if team1 == team2:
            return "Please select two different teams."

        # Get the internal NBA stats IDs
        team1_id = app.config["TEAM_IDS"].get(team1)
        team2_id = app.config["TEAM_IDS"].get(team2)

        if not team1_id or not team2_id:
            return "Invalid team selection."

        driver = webdriver.Chrome(service=service, options=chrome_options)
        try:
            rows_data = get_head_to_head_data(driver, team1_id, team2_id, team1, team2)
            print(rows_data)
        finally:
            driver.quit()

        # Render a new template with the results
        return render_template(
            "head_to_head_result.html",
            team1=team1,
            team2=team2,
            games=rows_data
        )

    # GET request -> show the selection form
    return render_template("head_to_head_result.html", teams=app.config["TEAM_IDS"].keys())


if __name__ == "__main__":
    app.run(debug=True, port=4000, use_reloader=False)
