import time,datetime
from selenium import webdriver #Open the Parser
from selenium.webdriver.common.by import By #Finding the element
from selenium.webdriver.common.keys import Keys #Enter key
from selenium.webdriver.support.select import Select #Combobox Selection
from selenium.webdriver.chrome.options import Options   # Hide Chrome Parser
import mplfinance as mpf
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path


global Serial, result
Serial = ['2330', '2762']
result = []
Error = 0
url = 'https://www.twse.com.tw/zh/trading/historical/stock-day.html'

def getting_data(Year, Month, Serial):
    chrome_options = Options()                              
    chrome_options.add_argument('--headless')               
    driver = webdriver.Chrome()
    driver = webdriver.Chrome(chrome_options) 
    driver.get(url) # Go to TWSE Website
    
    time.sleep(3)
    Stock_name = driver.find_element(By.NAME, "stockNo")
    selectA = driver.find_element(By.NAME, "yy")
    selectB = driver.find_element(By.NAME, "mm")
    select = Select(selectA)
    
    select.select_by_value(Year)
    time.sleep(2)
    
    select = Select(selectB)
    select.select_by_value(Month)
    time.sleep(2)
    
    Stock_name.send_keys(Serial)
    
    button = driver.find_element(By.CSS_SELECTOR, "#form > div > div.groups > div.submit > button")
    button.send_keys(Keys.ENTER)
    
    time.sleep(2)
    try:
        #Getting the data we want
        data = driver.find_element(By.XPATH, """//*[@id="reports"]/div[2]/div[2]/table/tbody""").text
        temp = ""
        for i in data:
            if i != " " and i != "\n":
                temp += i
            else:
                result.append(temp)
                temp = ""
        result.append(temp)

    except:
        pass
#Plotting the candle figure     
def Plot_Candlestickchart(Ser, filename):
    global result
    num = len(result) // 9
    data = [[0] * 6 for _ in range(num)]
    for i, j in enumerate(result):
        if i % 9 == 0:
            j = str( int(j[0:3]) + 1911)+ '-' + j[4:6] + '-' + j[7:9]
            data[i // 9][i % 9] = j
        elif i % 9 == 1:
            j = int(j.replace(',', ''))
            j /= 1000
            data[i // 9][i % 9] = j
        elif i % 9 in [3, 4, 5, 6]:
            data[i // 9][i % 9 - 1] = float(j.replace(',', ''))
    data_plot = pd.DataFrame(data, columns=['Date','Volume', 'Open', 'High', 'Low', 'Close'])
    data_plot.index = pd.DatetimeIndex(data_plot['Date'])
    mpf.plot(data_plot, type='candle', style='yahoo', mav=(5, 10), \
title = Ser + '\'s candle figure', volume = True,
ylabel_lower = 'Shares', savefig = filename)

#Judging the stock what status is
def strategy(ma_5, ma_10, ma_30, ending):
    if ma_5 > ma_10 and ma_10 > ma_30:
        status = 'entry_long'
    elif (ending - ma_5) > 0.05:
        status = 'wait_short'
    elif ma_5 < ma_10 and ma_10 < ma_30:
        status = 'entry_short'
    else:
        status = 'wait_long'
    return status

#Sending email with text and image
def email_sending(message, filename):
    content = MIMEMultipart()  #create MIMEMultipart object
    content["subject"] = "Stock Reminder Test"  #subject of the mail
    content["from"] = "example@gmail.com"  #sender
    content["to"] = "example@gmail.com" #receiver
    content.attach(MIMEText(message))  #sending text
    content.attach(MIMEImage(Path(filename).read_bytes()))  #sending image
    
    with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:  # settinging SMTP server
        try:
            smtp.ehlo()  #SMTP server certified
            smtp.starttls()  #Encrypted transmissions
#https://github.com/Yorkxe/Stock-Reminder/blob/c28381270b302ce798ff33dcce970c8afcdd5cf7/Setting%20for%20sending%20mail%20with%20Python/Setting.md
            smtp.login("example@gmail.com", "password")  #login sender's gmail
            smtp.send_message(content)  #sending mail
            print("Complete!")
        except Exception as e:
            print("Error message: ", e)

for Ser in Serial:
    t = time.localtime()
    #getting the price from the last two month ans this month
    if t.tm_mon < 3:
        for i in range(12 + t.tm_mon - 2, 13, 1):    
            getting_data(str(t.tm_year - 1), str(i), Ser)
        for i in range(1, t.tm_mon + 1, 1):    
            getting_data(str(t.tm_year), str(i), Ser)
    else:
        for i in range(t.tm_mon - 2, t.tm_mon + 1, 1):    
            getting_data(str(t.tm_year), str(i), Ser)
    #If the stock didn't exist or the data from the stock is too few, the program will sending an 404 image.
    if len(result) // 9 > 40:
        num = len(result) // 9
        box = [3, 4, 5]
        ending = float( result[9 * num - 3] )
        ma_5 = sum( [float(result[9 * i - 3]) for i in range(num, num - 5, -1)] ) / 5
        ma_10 = sum( [float(result[9 * i - 3]) for i in range(num, num - 10, -1)] ) / 10
        ma_30 = sum( [float(result[9 * i - 3]) for i in range(num, num - 30, -1)] ) / 30
        now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
        filename = str( now.date() ) + '-' + Ser + '.jpg'
        Plot_Candlestickchart(Ser, filename)
        status = strategy(ma_5, ma_10, ma_30, ending)
        message = "The status for " + Ser + " is " + status
        email_sending(message, filename)
    else:
        message = "The data for " + Ser + " is not found or the serial didn't exist."
        filename = '404.jpg'
        email_sending(message, filename)
    
    result = []
