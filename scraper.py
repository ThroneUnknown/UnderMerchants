import requests
from bs4 import BeautifulSoup
import json

TARGET = "underrail.json"  # Data destination
TABLE_EXCEPTIONS = ["Booth"]  # Cause problems for data tables
SPECIAL_EXCEPTIONS = ["Moe"]  # Special inventory is broken
FULL_EXCEPTIONS = ["Rude Rob"]  # Missing Parameters

def scrape():
    # Scrape vendor list
    URL = "https://www.stygiansoftware.com/wiki/index.php?title=Merchants"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find(id="mw-content-text").find("table", class_="sortable").tbody
    table.find("tr").extract()  # Remove header

    # Targeted data
    names = []
    locations = []
    categories = []
    selling = []
    buying = []
    special = []
    money = []
    currencies = []
    merchant_URLs = []

    # Find merchants and locations from data table
    for row in table.find_all("tr"):
        if row.find("td").text in FULL_EXCEPTIONS:
            continue
        names.append(row.find_all("td")[0].text)
        locations.append(row.find_all("td")[1].text)
        categories.append(row.find_all("td")[2].text)
        merchant_URLs.append(row.find("td").a["href"])

    print("Merchant overviews complete")

    for i in range(len(names)):
        print(f"{int(i / len(names) * 100)}% | {i}/{len(names)} | {names[i]}                    ", end="\r")

        merchant_page = requests.get("https://www.stygiansoftware.com" + merchant_URLs[i])
        merchant_soup = BeautifulSoup(merchant_page.content, "html.parser")
        
        store_table = merchant_soup.find(id="mw-content-text").find_all("table", class_="wikitable")[-1].tbody.find_all("tr")
        
        # EXCEPTIONS: Some characters have tables after their trading one on the page
        if names[i] in TABLE_EXCEPTIONS:
            store_table = merchant_soup.find(id="mw-content-text").find_all("table", class_="wikitable")[0].tbody.find_all("tr")
        
        selling.append([store_table[1].find_all("td")[0].find("ul").find_all("li")[i].text for i in range(len(store_table[1].find_all("td")[0].find("ul").find_all("li")))])
        buying.append([store_table[1].find_all("td")[1].find("ul").find_all("li")[i].text for i in range(len(store_table[1].find_all("td")[1].find("ul").find_all("li")))])
        
        if store_table[3].find("td").find("ul").find("li").text == "None":
            currencies.append([])
            money.append([])
        else:
            cashes = [store_table[3].find("td").find("ul").find_all("li")[i].text for i in range(len(store_table[3].find("td").find("ul").find_all("li")))]
            currencies.append([x[x.index(" "):] for x in cashes])
            money.append([int(x.split(" ")[0]) for x in cashes])
        
        # Special merchandise
        if len(store_table) > 4 and names[i] not in SPECIAL_EXCEPTIONS:
            special.append([store_table[5].find("td").find("ul").find_all("li")[i].text for i in range(len(store_table[5].find("td").find("ul").find_all("li")))])
        else:
            special.append([])

    print(f"Finished, {len(names)} merchants processed        ")

    # Convert data to JSON
    full_data = json.dumps([{"NAME": names[i], "LOCATION": locations[i], "CATEGORY": categories[i][:-1], "SELLING": selling[i], "BUYING": buying[i], "SPECIAL": special[i], "MONEY": money[i], "CURRENCIES": currencies[i]} for i in range(len(names))], indent=4)

    with open(TARGET, "w") as file:
        file.writelines(full_data)