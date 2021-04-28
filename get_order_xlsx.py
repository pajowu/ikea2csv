import argparse
import csv
import re
import sys
from decimal import Decimal

import requests
import requests_cache
import xlsxwriter
from bs4 import BeautifulSoup
from PIL import Image

requests_cache.install_cache('ikea')

parser = argparse.ArgumentParser()
parser.add_argument("token")
args = parser.parse_args()

HEADERS = {
    "token": args.token,
    "Consumer": "IKEAAPPI",
    "User-Agent": "IKEA App/2.23.0-4051 (iOS)",
    "Contract": "40663",
}
HOST = "https://shop.api.ingka.ikea.com"

req = requests.get(HOST + "/range/v1/de/de/purchase-history/1", headers=HEADERS)
if not req.ok:
    print("Failed to get purchase history:", req.text)
    sys.exit(1)
fieldnames = ['image', 'name', 'description', 'price', 'quantity', 'totalPrice']

workbook = xlsxwriter.Workbook('bestellungen.xlsx')
for order_num, order in enumerate(req.json()["history"]):
    print(order)
    worksheet = workbook.add_worksheet(BeautifulSoup(order['title']).text)

    for i, name in enumerate(fieldnames):
        worksheet.write(0, i, name)

    row_idx = 1
    action = order['actions']['open']

    req = requests.get(HOST + action, headers=HEADERS)

    for product in req.json()['productsSection']['products']:
        # print(product)
        totalPrice = Decimal(BeautifulSoup(product['totalPrice']).text)
        name = BeautifulSoup(product['title']).text
        description = BeautifulSoup(product['description']).text
        # print(product['quantity'])
        quantity = int(re.match(r"Anzahl: (-?\d+)", product['quantity']).group(1))
        # print(name, description, quantity, totalPrice, totalPrice/quantity)

        with open(f"{order_num}-{row_idx}.png", "wb") as f:
            img_req = requests.get(product['imageUrl'])
            f.write(img_req.content)
        if img_req.ok:
          
            with Image.open(f"{order_num}-{row_idx}.png") as img:
                width_100 = img.width
                height_100 = img.height

            img = Image.open(f"{order_num}-{row_idx}.png")
            hpercent = (100 / height_100)
            wsize = int((float(width_100)*float(hpercent)))
            img = img.resize((wsize, 100), Image.ANTIALIAS)
            img.save(f"{order_num}-{row_idx}.png") 

            dpi = 96
            dpcm = dpi

            worksheet.set_column('A:A', 15)
            worksheet.set_row(row_idx, 70)

            worksheet.insert_image(row_idx, 0, f"{order_num}-{row_idx}.png")

        for i, n in enumerate([name, description, totalPrice/quantity, quantity, totalPrice], start=1):
            worksheet.write(row_idx, i, n)

        row_idx += 1


workbook.close()
