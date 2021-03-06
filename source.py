# IMPORTING LIBRARIES
import requests
from bs4 import BeautifulSoup as bfs
import datetime 
import gspread
import time
from twilio.rest import Client
import os
import schedule

# GOOGLE SHEETS API AUTHENTICATION
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
                "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

gc = gspread.service_account(filename='credentials.json',scopes=scope)  # for heroku directory 

# USER-AGENT
# Using a googlebot user agent as most websites allow googlebot to scrape their websites
google_bot = {'User-Agent':'MMozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)','referer':'https://www.google.com/'}


# OPENING UP REQUIRED GOOGLE SHEETS
dfu = gc.open("URLs").sheet1
dfa = gc.open("Amazon").sheet1
dff = gc.open("Flipkart").sheet1


# TWILIO API AUTHENTICATION
account_sid = os.environ['twilio_sid'] 
auth_token = os.environ['twilio_access_token'] 
client = Client(account_sid, auth_token)



def reminder():
	remind_msg = client.messages.create(from_='whatsapp:+14155238886',  
		                                body="Please remember to send 'join opportunity-simple' after every 72 hours and 'ok' to this message",      
		                                to='whatsapp:+917000263689')


# CONTINUE FURTHER ONLY IF THERE ARE ANY ITEMS IN OUR LIST
def scraping():
	# FORMATTING DATES FOR CONVINIENCE
	today = datetime.date.today()
	today_slash = f"{today.day}/{today.month}/{today.year}"


	if len(dfu.col_values(1))>1:
		#SEPERATING URLS OF AMAZON & FLIPKART
		item_urls = list(zip(dfu.col_values(1)[1:],dfu.col_values(2)[1:]))
		amazon_urls = {item:url for item,url in item_urls if 'amazon' in url}
		flipkart_urls = {item:url for item,url in item_urls if 'flipkart' in url}

		# AMAZON PRICE SCRAPING & STORING

		# CONTINUE FURTHER IF THERE ARE ANY AMAZON PRODUCTS IN OUT LIST 
		if len(amazon_urls)!=0: 
			price_list = [today_slash]        										# ADDING TODAYS DATE
			
			# PRICE SCRAPING
			for Item in amazon_urls:
				res = requests.get(amazon_urls[Item],headers=google_bot)
				soup = bfs(res.text,'lxml')
				
				try:
					price = soup.select('#priceblock_ourprice')[0].text[2:]
					price = float(price.replace(',',''))
				
				except IndexError:
					price_return = soup.select('#priceblock_dealprice')
					
					if len(price_return)!=0:
				        	price = price_return[0].text[2:]
				        	price = float(price.replace(',',''))
					else:
						price = 'Currently Unavailable'
						
				finally:
					price_list.append(price)
				time.sleep(5)

			# UPDATE THE CURRENT DB
			dfa.append_row(values=price_list,insert_data_option='INSERT_ROWS')


		# FLIPKART PRICE SCRAPING & STORING

		# CONTINUE FURTHER IF THERE ARE ANY FLIPKART PRODUCTS IN OUT LIST 
		if len(flipkart_urls)!=0:
			price_list = [today_slash]                                        	# ADDING TODAYS DATE
			
			# PRICE SCRAPING
			for Item in flipkart_urls:
				res = requests.get(flipkart_urls[Item],headers=google_bot)
				soup = bfs(res.text,'lxml')
				
				try:
					price = soup.select('._1vC4OE._3qQ9m1')[0].text[1:]
					price = float(price.replace(',',''))
				except:
					price = 'Currently Unavailable'
				
				finally:
					price_list.append(price)
				time.sleep(5)



			# UPDATE THE CURRENT DB
			dff.append_row(values=price_list,insert_data_option='INSERT_ROWS')




# SENDING MESSAGE IF PRICE DROPS

# CHECKING PRICE DROPS FOR AMAZON PRODUCTS
def messaging():
	if len(dfa.col_values(1))>2:
		yes = len(dfa.col_values(1))-1
		tod = yes + 1  
		total_items = len(dfa.row_values(1)[1:])
		for item in range(2,total_items+2):
			yes_value = dfa.cell(yes,item).value
			tod_value = dfa.cell(tod,item).value
			item_name = dfa.cell(1,item).value
			if yes_value.isdigit() and tod_value.isdigit():
				if int(tod_value)<int(yes_value):
					message = client.messages.create( 
			                              from_='whatsapp:+14155238886',  
			                              body=f"Your {item_name} code is {tod_value}",      
			                              to='whatsapp:+917000263689')

	# CHECKING PRICE DROPS DOR FLIPKART PRODUCTS
	if len(dff.col_values(1))>2:
		yes = len(dff.col_values(1))-1
		tod = yes + 1	
		total_items = len(dff.row_values(1)[1:])
		for item in range(2,total_items+2):
			yes_value = dff.cell(yes,item).value
			tod_value = dff.cell(tod,item).value
			item_name = dff.cell(1,item).value
			if yes_value.isdigit() and tod_value.isdigit():
				if int(tod_value)<int(yes_value):
					message = client.messages.create( 
			                              from_='whatsapp:+14155238886',  
			                              body=f"Your {item_name} code is {tod_value}",      
			                              to='whatsapp:+917000263689')


# SCHEDLING THE JOB TO RUN AFTER EVERY 24 HRS
schedule.every(24).hours.do(scraping)
schedule.every(24).hours.do(messaging)
schedule.every(23.8).hours.do(reminder)

while True:
	schedule.run_pending()
