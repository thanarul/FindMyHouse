import os, time, sqlite3, smtplib
from email.message import EmailMessage
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

BASE = "https://thecannon.ca/housing/"
HEADERS = {"User-Agent": "UofG Housing Alert Bot (contact: thanusharulanantham@gmail.com)"}
RATE_SECONDS = 1.0

load_dotenv()
SMPT_HOST = os.getenv("SMTP_HOST")
SMPT_PORT = int(os.getenv("SMTP_PORT", "587"))
SMPT_USER = os.getenv("SMTP_USER")
SMPT_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMPT_USER)

# SQLITE db file 
DB = "housing_alerts.db"

# database setup 
def init_db():
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS listings
				 (id TEXT PRIMARY KEY, 
		   		 title TEXT,
		   		 price TEXT,
		   		 bedrooms TEXT,
		   		 date_posted TEXT,
		   		 url TEXT, 
		   		 raw TEXT)''')
	
	# storing each student alert subscription 
	c.execute('''CREATE TABLE IF NOT EXISTS alerts(
		   id INTEGER PRIMARY KEY AUTOINCREMENT,
		   email TEXT NOT NULL,
		   min_bedrooms INTEGER,
		   max_price INTEGER,
		   keywords TEXT)''')
	conn.commit()
	conn.close()

	# function scraper 

def fetchPage(url):
	r = requests.get(url, headers=HEADERS, timeout=20)
	r.raise_for_status()
	return r.text 

def parseListings(html):
    soup = BeautifulSoup(html, "lxml")
    cards = []

    for card in soup.select("[data-listing], .listing-card, .table-row"):
        title = card.select_one("a[href*='housing/']")
        url = urljoin(BASE, title["href"]) if title else None 
        title = title.get_text(strip=True) if title else ""
        price = (card.select_one(".price, .listing-price") or {}).get_text(strip=True) if card else ""
        beds = (card.select_one(".bedrooms, .listing-bedrooms") or {}).get_text(strip=True)
        date_posted = (card.select_one(".date, .posted, time") or {}).get_text(strip=True) 

        if url: 
            cards.append({
                "id": url,
                "title": title,
                "price": price,
                "bedrooms": beds,
                "date_posted": date_posted,
                "url": url,
                "raw": card.get_text(strip=True)
            })
    return cards

def crawlAll():
	# crawl starting from base and follow the next page links until there are no more pages

	url = BASE 
	seen = set()
	all_listings = []
	while url and url not in seen: 
		seen.add(url)
		html = fetchPage(url)
		items = parseListings(html)
		all_listings.extend(items)

		# trying to find a link to the next page 
		soup = BeautifulSoup(html, "lxml")
		next = soup.select_one("a[href*='housing/[age/']:-soup-contains('Next'), a.next")
		url = urljoin(BASE, next["href"]) if next and next.has_attr("href") else None

		time.sleep(RATE_SECONDS)
	return all_listings

def upsertListings(rows):
	# inserting new listings into the database, ignoring duplicates based on the primary key (id)
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	for r in rows:
		c.execute('''INSERT OR IGNORE INTO listings (id, title, price, bedrooms, date_posted, url, raw)
						VALUES (?, ?, ?, ?, ?, ?, ?)''',
						(r["id"], r["title"], r["price"], r["bedrooms"], r["date_posted"], r["url"], r["raw"]))
	conn.commit()
	conn.close()

def numericPrice(s):
	import re
	m = re.search(r"(\d[\d,]*)", s or "")
	return int(m.group(1).replace(",", "")) if m else None

# extracting the first number from the bedrooms 

def numBedrooms(s):
	import re 
	m = re.search(r"(\d+)", s or "")
	return int(m.group(1)) if m else None


# matching alerts 

def findNewMatches():

	# for each new student alert in the db check all listings and return matches
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	c.execute("SELECT id, title, price, bedrooms, date_posted, url, raw FROM listings")
	listings = [dict(zip(["id", "title", "price", "bedrooms","date_posted", "url", "raw"], row))
			for row in c.fetchall()]
	c.execute("SELECT id, email, min_bedrooms, max_price, keywords FROM alerts")
	alerts = c.fetchall()
	conn.close()

	messages = {}
	for aid, email, minBeds, maxPrice, keywords in alerts:
		kws = [k.strip().lower() for k in (keywords or "").split(",") if k.strip()]
		hits = []
		for L in listings:
			b = numBedrooms(L["bedrooms"]) or 0 
			p = numericPrice(L["price"]) or 10**9
			text = (L["title"] + " " + L["raw"]).lower()

			# applying the filters
			if minBeds and b < minBeds:
				continue
			if maxPrice and p > maxPrice:
				continue
			if kws and not any(k in text for k in kws):
				continue
			hits.append(L)
		
		if hits:
			messages[email] = messages.get(email, []) + hits
	return messages

def sendEmail(to, listings):
    # send an alert email with matching listings 
    msg = EmailMessage()
    msg["Subject"] = f"{len(listings)} new housing matches on thecannon.ca"
    msg["From"] = FROM_EMAIL
    msg["To"] = to

    # sample body text 
    body = []
    for it in listings:
        body.append(f"{it['title']} - {it['price']} - {it['bedrooms']} - {it['date_posted']}\n{it['url']}\n")
    msg.set_content("\n".join(body))

    with smtplib.SMTP(SMPT_HOST, SMPT_PORT) as server:
        server.starttls()
        server.login(SMPT_USER, SMPT_PASS)
        server.send_message(msg)

def run():
    init_db()
    items = crawlAll()
    upsertListings(items) 
    tosend = findNewMatches()
    for email, items in tosend.items():
        sendEmail(email, items)
        time.sleep(1.0)  # avoid spamming the SMTP server

if __name__ == "__main__":
    run()




