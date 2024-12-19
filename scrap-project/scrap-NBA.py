from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import re
import time
import matplotlib.pyplot as plt

chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Path to ChromeDriver
service = Service(r"C:\Users\Yoni\Downloads\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)


def search_player_and_get_id(first_name, last_name):
    """Search for the player using the search bar and return their profile URL and ID."""
    url = "https://www.nba.com/players"
    driver.get(url)
    time.sleep(3)  # Allow page to load

    # Locate the search bar and enter the player's name
    search_bar = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search Players']")
    search_bar.clear()
    search_bar.send_keys(f"{first_name} {last_name}")
    search_bar.send_keys(Keys.RETURN)
    time.sleep(3)  # Allow search results to load

    # Locate the player's profile link in the search results
    try:
        player_link = driver.find_element(By.CSS_SELECTOR, "a.RosterRow_playerLink__qw1vG")
        relative_url = player_link.get_attribute("href")

        base_url = "https://www.nba.com"
        profile_url = base_url + relative_url if relative_url.startswith("/") else relative_url

        # Extract the player ID from the profile URL
        match = re.search(r"player/(\d+)/", profile_url)
        if match:
            player_id = match.group(1)
            return profile_url, player_id
    except Exception as e:
        print(f"Player not found: {e}")
        return None, None


def get_player_stats(player_id, player_name):
    """Fetch last 10 games' stats for a player."""
    url = f"https://www.nba.com/stats/player/{player_id}/boxscores-traditional"
    print(f"Fetching stats for {player_name} from {url}")
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Scrape game stats
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.Crom_body__UYOcU tr")
    print(f"Found {len(rows)} game rows.")

    points = []
    rebounds = []
    assists = []
    game_labels = []

    for i, row in enumerate(rows[:10]):  # Limit to the last 10 games
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 16:  # Ensure sufficient data in the row
                game_info = cells[0].text
                pts = cells[3].text  # PTS
                reb = cells[15].text  # REB
                ast = cells[16].text  # AST

                game_labels.append(game_info)
                points.append(int(pts))
                rebounds.append(int(reb))
                assists.append(int(ast))
        except Exception as e:
            print(f"Error processing row {i}: {e}")

    if points and rebounds and assists:
        average_points = sum(points) / len(points)
        average_rebounds = sum(rebounds) / len(rebounds)
        average_assists = sum(assists) / len(assists)

        print(f"Points from the last 10 games: {points}")
        print(f"Rebounds from the last 10 games: {rebounds}")
        print(f"Assists from the last 10 games: {assists}")
        print(f"Average points: {average_points:.2f}")
        print(f"Average rebounds: {average_rebounds:.2f}")
        print(f"Average assists: {average_assists:.2f}")

        plt.figure(figsize=(12, 8))

        plt.plot(game_labels, points, marker='o', label='Points', alpha=0.7)
        plt.plot(game_labels, rebounds, marker='s', label='Rebounds', alpha=0.7)
        plt.plot(game_labels, assists, marker='^', label='Assists', alpha=0.7)

        plt.axhline(y=average_points, color='red', linestyle='--', label=f'Avg Points: {average_points:.2f}')
        plt.axhline(y=average_rebounds, color='green', linestyle='--', label=f'Avg Rebounds: {average_rebounds:.2f}')
        plt.axhline(y=average_assists, color='blue', linestyle='--', label=f'Avg Assists: {average_assists:.2f}')

        plt.title(f"{player_name.title()} - Stats in Last 10 Games")
        plt.xlabel("Games")
        plt.ylabel("Stats")
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    else:
        print("No sufficient data found.")


try:
    # User Input
    first_name = "deni"
    last_name = "avdija"

    profile_url, player_id = search_player_and_get_id(first_name, last_name)
    if player_id:
        print(f"Player Profile URL: {profile_url}")
        print(f"Player ID: {player_id}")

        get_player_stats(player_id, f"{first_name} {last_name}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()
