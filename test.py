import requests
from bs4 import BeautifulSoup
from exchangelib import Credentials, Account
from exchangelib import DELEGATE
import json

main_credentials = Credentials("databasedb123@outlook.com", "Abhi@7671")
main_account = Account("databasedb123@outlook.com", credentials=main_credentials, autodiscover=True,
                       access_type=DELEGATE)
inbox = main_account.inbox
emails = inbox.filter(subject__icontains="new_york")

table_data_list = []  # List to store table data

for email in emails:
    soup = BeautifulSoup(email.body, 'html.parser')
    tables = soup.find_all('table')
    text = soup.find_all('p')
    for t in text:
        print("()()()()()()",t.text)

    for table in tables:
        table_data = []  # List to store data from each table

        # Find all rows in the table
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text().strip() for cell in cells]
            table_data.append(row_data)

        # Assuming the first row of the table contains column headers (th elements)
        if table_data:
            headers = table_data[0]
            table_data = table_data[1:]  # Remove the header row
            table_dict = [dict(zip(headers, row)) for row in table_data]  # Create dictionaries for each row

            # Append the table data for this table to the list
            table_data_list.append(table_dict)

# Convert the table data list to JSON
table_data_json = json.dumps(table_data_list, indent=4)

# Print or use the JSON data as needed
print(table_data_json)
