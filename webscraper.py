import requests 
from bs4 import BeautifulSoup	

r = requests.get("https://thecannon.ca/housing/?search=&search2=Sublet&sortby=date&viewmode=grid")

#Parsing the HTML 
soup = BeautifulSoup(r.content, 'html.parser')
print(soup.prettify())