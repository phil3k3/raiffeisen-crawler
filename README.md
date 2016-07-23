# raiffeisen-crawler
A simple [scrapy](http://scrapy.org/) spider which downloads transaction data from Raiffeisen as CSV.

Spider parameters:

* bank_number: The 0-8 bank number representing the Austrian state, with '0' representing the state of Burgenland
* signatory: Signatory (owner number) of the bank account
* pin: Bank account pin
* account_number: Number of the bank account, with '0' referring to the main account (usually sufficient
* date_from: Start date of getting transaction data
* date_to: End date of getting transaction data
* target_file: Path in the file system where the CSV containing the transactions will be saved to
