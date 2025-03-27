import requests
from bs4 import BeautifulSoup

# page = requests.get('https://thecannon.ca/housing/')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}

page = requests.get('https://thecannon.ca/housing/', headers=headers)

soup = BeautifulSoup(page.content, 'html.parser')

page_listings = soup.find_all("a")

print(page_listings)