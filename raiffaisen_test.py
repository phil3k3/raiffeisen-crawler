import sys
from scrapy.crawler import CrawlerProcess
from raiffaisen import RaiffeisenSpider

ACCOUNT_NUMBER = 0
DATE_TO = "31.07.2015"
DATE_FROM = "26.06.2005"
TARGET_FILE = "expenses.csv"

print("Please enter bank number [0-8]: ")
bank_number = sys.stdin.readline()
print(bank_number)

print("Please enter signatory: ")
signatory = sys.stdin.readline()
print(signatory)

print("Please enter PIN: ")
pin = sys.stdin.readline()
print(pin)

process = CrawlerProcess()
process.crawl(RaiffeisenSpider, bank_number=bank_number.strip(), signatory=signatory.strip(), pin=pin.strip(),
              account_number=ACCOUNT_NUMBER, date_from=DATE_FROM, date_to=DATE_TO, target_file=TARGET_FILE)
process.start()
