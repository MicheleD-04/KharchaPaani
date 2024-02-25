from __future__ import print_function
from googleapiclient.discovery import build 
from google.oauth2 import service_account
import time

SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file('finalkey.json', scopes=SCOPES)

spreadsheet_service = build('sheets', 'v4', credentials=credentials)

prev_row_count = 11

import google.generativeai as genai
genai.configure(api_key='AIzaSyBZiRgrm3cnh6LG6n4sJQUOU9uyr8N588w')
model = genai.GenerativeModel('gemini-pro')

import pymongo

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://db:UDb7KayB6eTqLMcd@hackathon.a83vwgw.mongodb.net/?retryWrites=true&w=majority")
db = client["hackathon"]
transactions_db = db["transactions"]
contacts_db = db["contacts"]
labels_db = db["labels"]

import Levenshtein

def search_similar_document(collection, query):
    similar_document = None
    max_similarity_score = 0

    # Iterate through all documents in the collection
    for document in collection.find():
        # Calculate similarity score for each field in the document
        similarity_score = 0
        for field in document:
            # Calculate similarity score using Levenshtein distance
            if Levenshtein.ratio(str(document[field]), str(query)) > similarity_score:
                similarity_score = Levenshtein.ratio(str(document[field]), str(query))

        # Update max_similarity_score and similar_document if the current document has higher similarity
        if similarity_score > max_similarity_score:
            max_similarity_score = similarity_score
            similar_document = document

    return similar_document, max_similarity_score

import re

pattern = r'Rs\.(\d+\.\d+)'

from discordwebhook import Discord

discord = Discord(url="https://discord.com/api/webhooks/1211062401919877170/qiNjK4nHLF0cXwgJ5Gv9FJUpGfNT_J2jdOAeEHQ7LZOpUW54y0EsjGJOrE-NWRmZnpgt")

discord_prev_count = 11

while True:
    result = spreadsheet_service.spreadsheets().values().get(
        spreadsheetId='1PAPxgUWwhMOar79lgIH4nsNG3mNX1EWdvLQLZ_ioFCs',
        range='Sheet1'
    ).execute()

    # Calculate the current row count (excluding header)
    current_row_count = len(result.get('values', [])) - 1

    # Check if a new row has been added
    if current_row_count > prev_row_count:
        
        print("|INFO| New SMS Received!")
        row = result.get('values', [])[-1]
        
        prev_row_count = current_row_count
        
        response = model.generate_content(f"Reply with Yes or No, does this message indicate a debit transaction: {row[-1]}")
        print("|INFO| Is message regarding a transaction: ", response.text)
        if response.text.lower() == "yes":
            response = model.generate_content(f"Answer in one word, is this payment to a person or a business: {row[-1]}")
            print("|INFO| Transaction type: ", response.text)
            if response.text.lower() == "person":
                
                response = model.generate_content(f"Reply with 'Number:' or 'Name:' and 'Amount: ', extract the number paid to or the first name of the person paid to along with the amount paid: {row[-1]}")
                #print(response.text)
                
                main_parts = response.text.split("\n")[0]
                query = main_parts.split(":")[1]
                similar_document, similarity_score = search_similar_document(contacts_db, query)
                
                match = re.search(pattern, response.text)
                amount = match.group(1)
                print("SIMILARITY SCORE - ", similarity_score)
                if similarity_score > 0.5:
                    data = {"Date & Time": row[0], "Amount": amount, "Paid to": similar_document['Name']}
                    transactions_db.insert_one(data)
                    print(f"|INFO| New transaction logged: {amount} sent to {similar_document['Name']}")
                    
                else:
                    print("|ACTION REQUIRED| Discord message sent")
                    discord.post(content=f"We're not sure who you just paid! Please enter what you paid for:")
                    
                    while True:
                        print("|INFO| Waiting for reply")
                        discord_result = spreadsheet_service.spreadsheets().values().get(spreadsheetId='11TzQ1e9W6olmlv8HnPvUiZlRXsTWyQt2W3HLCcIUKi8',range='Sheet1').execute()
                        discord_current_count = len(discord_result.get('values', []))
                        if discord_current_count > discord_prev_count+2:
                            discord_row = discord_result.get('values', [])[-1]
                            print(discord_row)
                            discord_prev_count = discord_current_count
                            discord_paid_to = discord_row[0]
                            print("|INFO| Discord message received")
                            break
                        else:
                            pass
                        time.sleep(10)
                    
                    data = {"Date & Time": row[0], "Amount": amount, "Paid to": discord_paid_to}
                    transactions_db.insert_one(data)
                    print(f"|INFO| New transaction logged: {amount} sent to {discord_paid_to}")
            
            else:
                
                response = model.generate_content(f"Reply as follows: 'Amount: , Business:', extract the amount paid and business paid to: {row[-1]}")
                match = re.search(pattern, response.text)
                amount = match.group(1)
                business = response.text.split("Business: ")[-1]
                data = {"Date & Time": row[0], "Amount": amount, "Paid to": business}
                transactions_db.insert_one(data)
                print(f"|INFO| New transaction logged: {amount} sent to {business}")
        
        else:
            pass
    
    time.sleep(5)
