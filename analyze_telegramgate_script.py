import classifier as spanish_sentiment_analysis
from spellchecker import SpellChecker

#---------------------------------------------------------------------------------

from tika import parser

pdf_path = "./dataset/telegram_gate.pdf"
raw = parser.from_file(pdf_path)
pdf_content = raw['content']

#---------------------------------------------------------------------------------

pdf_content = pdf_content.strip("\n")

#---------------------------------------------------------------------------------

import re

# Remove "Telegram Web"
pdf_content = pdf_content.replace("Telegram Web", "")

# Remove the date "1/20/2019"
pdf_content = pdf_content.replace("1/20/2019", "")

# Remove the telegram URL which appears at the end of every page
# Create a regular expression to match different variations of the link which differ by extra empty spaces
regex = re.compile(r'https( )*:(\/|1)(\/|1)web( )*\.telegram( )*\.org\/#\/im\?p=s1209505337( )*_( )*15413785455230905639')

# Remove strings that match the regex
pdf_content = re.sub(regex, "", pdf_content)

#---------------------------------------------------------------------------------

# Create regex for matching timestamps
regex = re.compile(r'[0-9][0-9]?:[0-9][0-9]( )?:[0-9][0-9]( )?(A|P)M')

# Remove timestamps
pdf_content = re.sub(regex, "", pdf_content)

#---------------------------------------------------------------------------------

# Create a list of sentences from document
pdf_lines = pdf_content.split("\n")

# Remove empty string elements

regex = re.compile(r'^( )*$')
pdf_lines = [line for line in pdf_lines if not regex.match(line)]

#---------------------------------------------------------------------------------

# Get admin chat members by keeping unique lines which contain the word 'admin'
admin_chat_members = set(line.strip() for line in pdf_lines if ' admin ' in line)

#---------------------------------------------------------------------------------

# Clean the admin chat members list by removing ' admin' and any text after

admin_chat_members_cleaned = set()

for element in admin_chat_members:
    
    index = element.find(' admin') # locate where in the line is the string ' admin' 
    
    admin_chat_members_cleaned.add(element[:index])
    
admin_chat_members = admin_chat_members_cleaned

#---------------------------------------------------------------------------------

# Remove the elements in admin_chat_members which contain the text 'gif', they are repeated

admin_chat_members = [member for member in admin_chat_members if not('gif' in member)]

#---------------------------------------------------------------------------------

# Two elements in the admin_chat_members list seem to be typos (Tika misread them), remove them

admin_chat_members.remove("R Russello") # assuming it's 'R Rosello' read incorrectly by Tika
admin_chat_members.remove("Fdo") # assuming it's 'F do' read incorrectly by Tika

#---------------------------------------------------------------------------------

# Replace typos: 'Fdo' with 'F do' and 'R Russello' with 'R Rosello'

pdf_lines_fixed = []

for line in pdf_lines:
    
    new_line = line
    
    if 'R Russello' in line:
        new_line = line.replace('R Russello', 'R Rosello')
        
    if 'Fdo' in line:
        new_line = line.replace('Fdo', 'F do')
        
    pdf_lines_fixed.append(new_line)
        
pdf_lines = pdf_lines_fixed

#---------------------------------------------------------------------------------

# Make a consolidated chat members list

nonadmin_chat_members = [
    "Raul Maldonado",
    "Anthony O. Maceira Zayas",
    "Ricardo Llerandi",
    "LuisG"
]

all_chat_members = admin_chat_members + nonadmin_chat_members

#---------------------------------------------------------------------------------

# Create admin member accronyms

user_acronyms = set()

for chat_member in all_chat_members:
    
    names = chat_member.split(" ")
    names = names[:2] # user accronyms in the PDF have a maximum of 2 letters
    
    acronym = ""
    for name in names:
        acronym += name[0].upper()
    
    user_acronyms.add(acronym)
    
#---------------------------------------------------------------------------------

# Build regular expression for identifying text containing only an accronym and spaces

regular_exp = ""

for acronym in user_acronyms:
    
    regular_exp += acronym + "|"
    
regular_exp = regular_exp[:len(regular_exp)-1]

regex = re.compile(r'^( )*({regular_exp})( )*$'.format(regular_exp=regular_exp))

# Remove accronyms from pdf_lines
pdf_lines = [line for line in pdf_lines if not regex.match(line)]

#---------------------------------------------------------------------------------

# Store the conversation in the list conversation, which will be 
# a list of dictionaries where the dictionary will contain the keys 
# 'chat_member' and 'message'
    
page_number_regex = re.compile(r'( )*[0-9][0-9]?[0-9]?\/889( )*')

# Build date regex
# date example: Friday, November 30, 2018 
weekday = '(Moday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
month = '(January|February|March|April|May|June|July|August|September|October|November|December)'
day = '[0-9]?[0-9]'
year = '20[1-2][0-9]'
date_regex = re.compile(r'{weekday}, {month} {day}, {year}'.format(weekday=weekday, 
                                                                   month=month,
                                                                   day=day,
                                                                   year=year))
page_number = 1
date = None
    
conversation = []

current_chat_member = None # which chat member is the current author

new = False # is the detected chat member new (different from previous)?

for line in pdf_lines:
    
    if page_number_regex.match(line):
        page_number += 1
        continue
        
    if date_regex.match(line):
        date = line.strip()
        continue
    
    for chat_member in all_chat_members:
        if chat_member in line:
            # don't add chat member element to conversation
            current_chat_member = chat_member
            new = True
            break
            
    if new:
        new = False
        continue # skip to next iteration
       
    if (current_chat_member != None) and not(current_chat_member in line):
        conversation.append({
            "chat_member": current_chat_member,
            "message": line,
            "page_number": page_number,
            "date": date
        })
        
#---------------------------------------------------------------------------------

# Create abridged Telegramgate

#---------------------------------------------------------------------------------

# Randomly generate colors per chat member for bar chart

import random

def random_color(): # returns a random color in hexadecimal
    color = "%06x" % random.randint(0, 0xFFFFFF) 
    return color

# randomly generate colors per user
chat_member_colors = {member:random_color() for member in all_chat_members}
        
#---------------------------------------------------------------------------------

# Get messages per user

messages_per_user = {user:0 for user in all_chat_members}

for message in conversation:
    
    messages_per_user[message['chat_member']] += 1

#---------------------------------------------------------------------------------
    
# Draw bar chart which represents messages per user, and save to '"barchart.png"
    
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt

users = list(messages_per_user.keys())
y_pos = np.arange(len(users))
number_of_lines = list(messages_per_user.values())

fig, ax = plt.subplots()   
barlist = ax.barh(y_pos, number_of_lines, align='center', alpha=0.5)

# color the bars
for i,user_color in enumerate(chat_member_colors.items()):
    user = user_color[0]
    color = user_color[1]
    barlist[i].set_color('#'+color)

plt.yticks(y_pos, users)
plt.xlabel('Number of Lines per Chat Member')
plt.title('Messaging Frequency Per User')

for i, v in enumerate(number_of_lines):
    ax.text(v + 4, i, " "+str(v), color='grey', fontweight='bold',va='center')
    
fig.savefig("barchart.png", bbox_inches = "tight")

#---------------------------------------------------------------------------------

# Create abridged Telegramgate PDF from created HTML

import pdfkit

html_content = "<html><body><h1>Telegramgate: Abridged</h1>"

page = 1

html_content += '<p>page {page} </br></p>'.format(page=page)

for msg in conversation:
    
    user = msg['chat_member']
    message = msg['message']
    
    if msg["page_number"] > page:
        page += 1
        html_content += '<p></br>page {page}</p>'.format(page=page)
        
    color = chat_member_colors[user]
    
    html_content += '<p><font color="{color}"><b>{user}</b></font>: {message}</p>'.format(color=color,user=user,message=message)
    
html_content += "</body></html>"

filename = "telegramgate_abridged"
html_filename = filename + '.html'

f = open(html_filename,"w")
f.write(html_content)
f.close()

pdf_filename = filename + '.pdf'

pdfkit.from_file(html_filename, pdf_filename)