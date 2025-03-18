import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = 'https://thecannon.ca/housing/'
driver.get(url)

time.sleep(5)

# page_source = driver.page_source

soup = BeautifulSoup(driver.page_source, 'html.parser')

driver.quit()

base_url = 'https://thecannon.ca'
listings = []

for link in soup.find_all('a', href=True):
	href = link['href']
	if href.startswith('/classified/housing/'):
		fullLink = base_url + href
		title = link.get_text(strip = True)
		if title: 
			listings.append((title, fullLink))

# printing results 
for title, link in listings:
	print(f"Title: {title}\nLink: {link}\n")
