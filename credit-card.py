# imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import imaplib, email
from bs4 import BeautifulSoup
import re
from time import sleep
import pandas as pd
import math
import yaml

# options
with open('config.yml', 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
options = webdriver.ChromeOptions()
options.add_argument("user-data-dir={}".format(config['user-data-dir']))

# driver
driver = webdriver.Chrome(executable_path='./chromedriver', options=options); sleep(5)

# login
def login():
    # function to search for a key value pair 
    def search(client, key, value): 
        result, _bytes = client.search(None, key, '"{}"'.format(value))
        return _bytes
    # login to CC
    driver.get(config['url']['login']); sleep(5) 
    driver.find_element_by_id('username').send_keys(config['cc']['member-number']); sleep(5) 
    driver.find_element_by_id('password').send_keys(config['cc']['password']); sleep(5) 
    driver.find_element_by_id('loginButton').send_keys(Keys.RETURN); sleep(10)
    if driver.current_url == config['url']['mfa']:
        driver.find_element_by_name('sendOTP').send_keys(Keys.RETURN); sleep(60)
        # login to Gmail
        client = imaplib.IMAP4_SSL('imap.gmail.com') 
        client.login(config['email']['address'], config['email']['password']) 
        _ = client.select('Inbox') 
        uids = search(client, 'FROM', config['cc']['mfa-email'])[0].split()
        _, latest_email_bytes = client.fetch(uids[-1], '(RFC822)')
        latest_email_text = str(latest_email_bytes[0][1])
        soup = BeautifulSoup(latest_email_text, 'lxml')
        pattern_1 = re.compile(r'passcode is (\d+)')
        code = pattern_1.findall(soup.find_all(text=pattern_1)[0])[0]
        # 2-factor
        driver.find_element_by_id('mfaCodeInputField').send_keys(code); sleep(5)
        driver.find_element_by_name('registerDevice').send_keys(Keys.RETURN); sleep(5)
        driver.refresh(); sleep(5)
    if driver.current_url == config['url']['home']:
        return
    else:
        print('uh-oh')
login()

# get new monthly balance
def get_new_balance():
    try:
        driver.find_element_by_xpath("//a[@aria-label='e-Statements']").send_keys(Keys.RETURN); sleep(5)
    except:
        driver.find_element_by_class_name('navbar-toggle').send_keys(Keys.RETURN); sleep(5)
        driver.find_element_by_link_text("e-Statements").click(); sleep(5)
    driver.switch_to.frame(driver.find_element_by_tag_name("iframe")); sleep(10)
    driver.find_elements_by_xpath('//input[@type="submit"]')[1].click(); sleep(5)
    table = driver.find_element_by_xpath("//table[@summary='Summary of Account Activity']")
    html = table.get_attribute('outerHTML')
    table_pd = pd.read_html(html, index_col=0)[0]
    new_balance = float(table_pd.loc['New Balance', 1])
    since_date = driver.find_element_by_xpath('//select[@name="HistoryID"]').find_elements_by_xpath('//option')[0].text.strip(); sleep(5)
    driver.get(config['url']['home']); sleep(5)
    return new_balance, since_date
new_balance, since_date = get_new_balance()

# check if monthly balance has already been paid
def is_new_balance_paid():
    driver.find_element_by_xpath('//a[@title="{}"]'.format(config['to-account'])).click(); sleep(5)
    try:
        driver.find_element_by_id('dLabeldate_range').click(); sleep(5)
    except:
        driver.maximize_window()
        driver.find_element_by_id('dLabeldate_range').click(); sleep(5)
    driver.find_element_by_xpath('//input[@type="text"]').click(); sleep(5)
    driver.find_element_by_xpath('//input[@type="text"]').send_keys(since_date); sleep(5)
    driver.find_element_by_id('date_range_go').click(); sleep(5)
    table = driver.find_element_by_xpath('//table[@class="table cardlytics_history_table"]')
    html = table.get_attribute('outerHTML')
    table_pd = pd.read_html(html)[0]
    payments = table_pd[table_pd['Description'].str.contains('PAYMENT')]
    payment_amounts = payments['Amount'].apply(lambda x: x[1:x.index('Applied') if 'Applied' in x else len(x)]).astype(float).tolist()
    driver.back(); sleep(5)
    return new_balance in payment_amounts
is_paid = is_new_balance_paid()

# if monthly balance hasn't been paid, make transfer
def move_money(from_account, to_account, amount):
    driver.find_element_by_id('transferLinkaccounts').click(); sleep(5)
    from_dropdown, to_dropdown = driver.find_elements_by_class_name('dropdown'); sleep(5)
    accounts = from_dropdown.find_elements_by_xpath('//div[starts-with(@id, "listAccountDescription")]')
    from_dropdown_accounts, to_dropdown_accounts = accounts[:3], accounts[3:]
    from_dropdown.click(); sleep(5)
    from_dropdown_account_description_2_balance = dict(zip([item.text for item in from_dropdown_accounts], [float(item.text[1:].replace(',', '')) for item in driver.find_elements_by_xpath('//span[starts-with(@id, "accountBalance")]') if item.text != '']))
    from_account_balance = from_dropdown_account_description_2_balance[from_account]
    from_account_i = list(from_dropdown_account_description_2_balance.keys()).index(from_account)
    if from_account_balance >= config['from-account-keep']+amount:
        from_dropdown_accounts[from_account_i].click(); sleep(5)
        to_dropdown.click(); sleep(5)
        to_dropdown_account_description_2_balance = dict(zip([item.text for item in to_dropdown_accounts], [float(item.text[1:].replace(',', '')) for item in driver.find_elements_by_xpath('//span[starts-with(@id, "accountBalance")]') if item.text != '']))
        to_account_i = list(to_dropdown_account_description_2_balance.keys()).index(to_account)
        to_dropdown_accounts[to_account_i].click(); sleep(5)
        try:
            driver.find_element_by_id('otherAmountRadio').click(); sleep(5)
            driver.find_element_by_id('otherAmountValue').send_keys(str(amount)); sleep(5)
        except:
            driver.find_element_by_id('amountInputField').send_keys(str(amount)); sleep(5)
        driver.find_element_by_id('makeTransfer').click(); sleep(10)
        driver.find_element_by_id('transfersConfirmationConfirmButton').click(); sleep(10)
        driver.find_element_by_id('accountsButton').click(); sleep(5)
        return True
    else:
        cursory_amount = math.ceil(config['from-account-keep'] + amount - from_account_balance)
        driver.get(config['url']['home']); sleep(5)
        success = move_money(config['pool-account'], from_account, cursory_amount)
        if success:
            return move_money(from_account, to_account, amount)
        else:
            return False
if not is_paid:
    success = move_money(config['from-account'], config['to-account'], new_balance)
    if not success:
        print('uh-oh')

# done!
driver.quit()