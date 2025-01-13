from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Initialize the WebDriver with the correct Service object
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Example of a website to scrape
page_url = "https://webscraper.io/test-sites/e-commerce/static/computers/laptops?page=1"
driver.get(page_url)

# Extracting elements
titles = driver.find_elements(By.CLASS_NAME, "title")
prices = driver.find_elements(By.CLASS_NAME, "price")
descriptions = driver.find_elements(By.CLASS_NAME, "description")
ratings = driver.find_elements(By.CLASS_NAME, "ratings")

# Storing the scraped data
element_list = []
for i in range(len(titles)):
    element_list.append([titles[i].text, prices[i].text, descriptions[i].text, ratings[i].text])

print(element_list)

# Closing the driver
driver.quit()
