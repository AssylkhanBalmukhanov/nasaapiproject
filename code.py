import telebot
import pandas as pd
import datetime
import time
from rocketlc import past_launchs as pl, future_launchs as fl
from nasapy import Nasa
import requests
token = ""
bot = telebot.TeleBot(token)
nasa = Nasa(key="")
MAX_MESSAGE_LENGTH = 4000# Keyboard buttons

# Keyboard buttons
markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
markup.add("/help")
markup.add("/pic_day")
markup.add("/past_launches")
markup.add("/geomagnetic_storm")
markup.add("/astronauts")
markup.add("/future_launches")
markup.add("/milestones")
markup.add("/asteroid_feed")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Welcome to our space bot! Use button /help to see all available commands", reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = "Available commands:\n"
    help_text += "/pic_day - Request astronomy picture of a day for a specific date(from 15 june 1995 up to today)\n"
    help_text += "/past_launches - Show past SpaceX launches\n"
    help_text += "/geomagnetic_storm - Check if there is a geomagnetic storm coming\n"
    help_text += "/astronauts - Get list of current astronauts in space\n"
    help_text += "/future_launches - Show future SpaceX launches\n"
    help_text += "/milestones - Sends biggest accomplishments humanity achieved exploring space\n"
    help_text += "/asteroid_feed - View asteroids that are approaching to the earth and considered hazardous by NASA\n"
    bot.send_message(message.chat.id, help_text)

def Asteroid_feed(chat_id):
    data = nasa.asteroid_feed(start_date="2023-07-17")
    asteroids_info = ""
    for date, asteroids in data['near_earth_objects'].items():
        for asteroid in asteroids:
            name = asteroid['name']
            is_hazardous = asteroid['is_potentially_hazardous_asteroid']
            if is_hazardous:
                asteroids_info += f"Asteroid Name: {name}\n"

    if not asteroids_info:
        asteroids_info = "No potentially hazardous asteroids found."

    bot.send_message(chat_id, asteroids_info)

@bot.message_handler(commands=['asteroid_feed'])
def send_asteroid_feed(message):
    Asteroid_feed(message.chat.id)



def send_image_from_url(chat_id, url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        bot.send_photo(chat_id=chat_id, photo=url)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the image: {e}")
        bot.send_message(chat_id=chat_id, text="Sorry, but something went wrong.")

def apictureofaday(chat_id, date):
    picture = nasa.picture_of_the_day(date, hd=True)
   # print(picture['url'])
    send_image_from_url(chat_id, picture['url'])
    text_exp = ""
    text_exp+=picture['explanation']

    bot.send_message(chat_id=chat_id, text= text_exp)

@bot.message_handler(commands=['pic_day'])
def request_a_picture_of_the_day(message):
    bot.send_message(message.chat.id, "Please enter the date in the following format: YYYY-MM-DD")
    bot.register_next_step_handler(message, process_date_for_picture)

def process_date_for_picture(message):
    date = message.text.strip()
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        apictureofaday(message.chat.id, date)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid date format. Please use YYYY-MM-DD format.")

@bot.message_handler(commands=['geomagnetic_storm'])
def check_geomagnetic_storm(message):
    data = nasa.geomagnetic_storm()
    if len(data) == 0:
        text = "There is no geomagnetic storms coming!"
        #print(len(data))
    else:
        #print(len(data))
        text = str(data)
    bot.send_message(message.chat.id, text)

def get_astronauts():
    url = "http://api.open-notify.org/astros.json"
    response = requests.get(url)
    data = response.json()
    return data["people"]

@bot.message_handler(commands=['astronauts'])
def get_astronauts_in_space(message):
    astronauts = get_astronauts()
    text = ""
    for astronaut in astronauts:
        text += f"Name: {astronaut['name']}, Craft: {astronaut['craft']}\n"
    bot.send_message(message.chat.id, text)

def send_large_message(chat_id, text):
    while text:
        if len(text) < MAX_MESSAGE_LENGTH:
            bot.send_message(chat_id, text)
            return
        else:
            msg_end_idx = text.rfind('\n', 0, MAX_MESSAGE_LENGTH) 
            if msg_end_idx == -1:  
                msg_end_idx = MAX_MESSAGE_LENGTH
            bot.send_message(chat_id, text[:msg_end_idx])
            text = text[msg_end_idx:]

@bot.message_handler(commands=['past_launches'])
def send_past_space_x_launches(message):
    pls = pl()
    text = ""
    for launch in pls['rockets']:
        text += "Mission: {mission}, Date: {date}, Time: {time}, Location: {location}\n".format(
            mission=launch['mission'],
            date=launch['date_launch'],
            time=launch['time_launch'],
            location=launch['location'])
    send_large_message(message.chat.id, text)

@bot.message_handler(commands=['future_launches'])
def send_space_x_future_launches(message):
    fls = fl()
    text = ""
    for launch in fls['rockets']:
        text += "Mission: {mission}, Date: {date}, Time: {time}, Location: {location}\n".format(
            mission=launch['mission'],
            date=launch['date_launch'],
            time=launch['time_launch'],
            location=launch['location'])
    send_large_message(message.chat.id, text)

def ask_milestone():
    df = pd.read_csv('/home/assylkhan/Desktop/Immerse/space.csv')
    temp = df['date_accomplished'].tolist()
    temp2 = df['event'].tolist()
    res = ""
    for i in range(len(temp)):
        res += f"Date: {temp[i]}, Event: {temp2[i]}\n"
    return res

@bot.message_handler(commands=['milestones'])
def send_milestones(message):
    milestones_text = ask_milestone()
    bot.send_message(message.chat.id, milestones_text)

if __name__ == "__main__":
    bot.polling(none_stop=True)
