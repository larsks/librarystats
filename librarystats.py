from __future__ import print_function

import csv
from imapclient import IMAPClient

import credentials

FIELDS = (
    'AUTHOR',
    'TITLE',
    'CALL NO',
    'BARCODE',
    'SOURCE',
    'DATE CHECKED OUT',
    'DATE DUE',
)

gmail = IMAPClient('imap.gmail.com', ssl=True, use_uid=True)
gmail.login(credentials.username, credentials.password)
gmail.select_folder('[Gmail]/All Mail')

res = gmail.search(
    ['X-GM-RAW',
     'items due in 2 days after:2016/12/31 from:minlib.net']
)

books = []
messages = gmail.fetch(res, ['BODY[TEXT]'])

# Email from the library contains two columns. This
# loop de-columnizes the messages and discards extraneous header
# text.
for msgid in res:
    msg = messages[msgid]
    body = msg[b'BODY[TEXT]'].decode('utf-8')

    found = False
    col1_all = []
    col2_all = []

    for line in body.splitlines():
        line = line.strip()
        if not found:
            if not line.startswith('AUTHOR:'):
                continue
            found = True

        col1 = line[:37]
        col2 = line[37:]
        col1_all.append(col1)
        col2_all.append(col2)

    book = []
    in_book = False
    for line in col1_all + col2_all:
        if line.startswith('AUTHOR'):
            if book:
                books.append(book)
                book = []

            in_book = True

        if in_book:
            if not line:
                in_book = False
                continue

            book.append(line)

    if book:
        books.append(book)

# Now we iterate over the extracted lines and transform them
# into dictionaries.
records = []
for book in books:
    record = dict(zip(FIELDS, book))

    for k, v in record.items():
        try:
            if v.split(': ')[0] in FIELDS:
                record[k] = v.split(': ')[1].strip()
        except IndexError:
            pass

    record['SOURCE'], record['DATE DUE'] = record['SOURCE'].split(' DUE: ')

    records.append(record)

# And finally write out a CSV file.
with open('books.csv', 'w') as fd:
    writer = csv.DictWriter(fd, FIELDS)
    writer.writeheader()
    writer.writerows(records)
