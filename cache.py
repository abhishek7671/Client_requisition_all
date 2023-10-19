from cachetools import TTLCache
from exchangelib import Credentials, Account, Message, DELEGATE, HTMLBody
from bs4 import BeautifulSoup


cache = TTLCache(maxsize=100, ttl=150)


def get_email_thread_data(subject):
    if subject in cache:
        return cache[subject]
    else:
        email_thread_data = fetch_email_thread_data(subject)
        cache[subject] = email_thread_data
        return email_thread_data

def fetch_email_thread_data(subject):
    main_credentials = Credentials("rammouri123@outlook.com", "Abhi@7671")
    main_account = Account("rammouri123@outlook.com", credentials=main_credentials, autodiscover=True,
                           access_type=DELEGATE)
    inbox = main_account.inbox
    emails = inbox.filter(subject__icontains=subject)
    email_thread_data = []

    for email in emails:
        formatted_timestamp = email.datetime_sent.date()
        clean_subject = email.subject.strip()
        while clean_subject.startswith("Re:"):
            clean_subject = clean_subject[3:].strip()
        table_data_list = []
        text_data = ''
        soup = BeautifulSoup(email.body, 'html.parser')
        tables = soup.find_all('table')
        texts = soup.find_all('p')

        for text in texts:
            text_data = text.text

        for table in tables:
            table_data = []
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text().strip() for cell in cells]
                table_data.append(row_data)
            if table_data:
                headers = table_data[0]
                table_data = table_data[1:]
                table_data_list = [dict(zip(headers, row)) for row in table_data]

        # table_data_json = json.dumps(table_data_list, indent=4)

        thread_data = {
            "subject": clean_subject,
            "sender": email.sender.email_address,
            "recipients": [to.email_address for to in email.to_recipients],
            "receiver": email.receiver.email_address if hasattr(email, 'receiver') else "",
            "cc": [cc.email_address for cc in email.cc_recipients] if email.cc_recipients else [],
            "timestamp": formatted_timestamp,
            "time": email.datetime_sent.strftime("%H:%M:%S %p"),
            "text": text_data,
            "table": table_data_list,
            "has_attachments": bool(email.attachments),
        }
        if email.attachments:
            attachments = []
            for attachment in email.attachments:
                attachment_info = {
                    "filename": attachment.name,
                    "content_type": attachment.content_type,
                    "size": attachment.size,
                }
                attachments.append(attachment_info)
            thread_data["attachments"] = attachments
        email_thread_data.append(thread_data)
    return email_thread_data
