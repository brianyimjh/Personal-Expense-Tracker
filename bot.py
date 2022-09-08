import os
from flask import Flask, request

import telebot
from telebot import types

from gsheet import get_category_arr, insert_transaction_data
from datetime import date

TOKEN = os.getenv('TELE_API_TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda msg: msg.text != '/log_transaction')
def start(message):
    bot.send_message(message.chat.id, 'Please enter /log_transaction to log an Expense or Income transaction')

@bot.message_handler(commands=['log_transaction'])
def log_transaction(message):
    global data_to_store_list, date_index, amount_index, description_index, category_index, isExpense
    data_to_store_list = ['','','','']
    date_index = 0
    amount_index = 1
    description_index = 2
    category_index = 3
    isExpense = True

    markup = types.ReplyKeyboardMarkup()
    
    transaction_arr = ['Expense', 'Income']
    for transaction in transaction_arr:
        markup.add(types.KeyboardButton(transaction))

    user_input = bot.send_message(message.chat.id, 'Choose one:', reply_markup=markup)
    bot.register_next_step_handler(user_input, choose_category, transaction_arr)

def choose_category(message, transaction_arr):
    global isExpense
    selection = message.text

    if selection.capitalize() not in transaction_arr:
        markup = types.ReplyKeyboardMarkup()
        for transaction in transaction_arr:
            markup.add(types.KeyboardButton(transaction))
        user_input = bot.send_message(message.chat.id, 'Please select Expense or Income', reply_markup=markup)
        bot.register_next_step_handler(user_input, choose_category, transaction_arr)
    else:
        bot.send_message(message.chat.id, f'"{selection}" selected')

        if selection == 'Expense':
            isExpense = True
        elif selection == 'Income':
            isExpense = False

        category_arr = get_category_arr(isExpense)

        markup = types.ReplyKeyboardMarkup()
        for category in category_arr:
            markup.add(types.KeyboardButton(category))

        user_input = bot.send_message(message.chat.id, 'Choose one:', reply_markup=markup)
        bot.register_next_step_handler(user_input, input_amount, category_arr)

def input_amount(message, category_arr):
    global data_to_store_list, category_index
    selection = message.text
    
    if selection.title() not in category_arr:
        markup = types.ReplyKeyboardMarkup()
        for category in category_arr:
            markup.add(types.KeyboardButton(category))
        user_input = bot.send_message(message.chat.id, 'Please select one of the categories', reply_markup=markup)
        bot.register_next_step_handler(user_input, input_amount, category_arr)
    else:
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(message.chat.id, f'"{selection}" selected', reply_markup=markup)
        data_to_store_list[category_index] = selection

        user_input = bot.send_message(message.chat.id, 'Please enter an amount:')
        bot.register_next_step_handler(user_input, input_description)

def input_description(message):
    global data_to_store_list, amount_index
    amount = message.text

    try:
        data_to_store_list[amount_index] = f'{float(amount):0.2f}'

        user_input = bot.send_message(message.chat.id, 'Please enter a description:')
        bot.register_next_step_handler(user_input, confirm_description)
    except Exception as e:
        user_input = bot.send_message(message.chat.id, 'Please enter a number without the $ sign')
        bot.register_next_step_handler(user_input, input_description)

def confirm_description(message):
    description = message.text

    yes_no_arr = ['Yes', 'No']
    markup = types.ReplyKeyboardMarkup()
    for option in yes_no_arr:
        markup.add(types.KeyboardButton(option))

    user_input = bot.send_message(message.chat.id, f'Is this the description you want?\n\n"{description}"', reply_markup=markup)
    bot.register_next_step_handler(user_input, confirm_transaction, yes_no_arr, description)

def confirm_transaction(message, yes_no_arr, description):
    global data_to_store_list, description_index, date_index
    confirmation = message.text

    if confirmation not in yes_no_arr:
        markup = types.ReplyKeyboardMarkup()
        for option in yes_no_arr:
            markup.add(types.KeyboardButton(option))
        user_input = bot.send_message(message.chat.id, 'Please enter yes or no', reply_markup=markup)
        bot.register_next_step_handler(user_input, confirm_transaction, yes_no_arr, description)

    elif confirmation.capitalize() == 'No':
        markup = types.ReplyKeyboardRemove(selective=False)
        user_input = bot.send_message(message.chat.id, 'Please enter a description:', reply_markup=markup)
        bot.register_next_step_handler(user_input, confirm_description)

    else:
        data_to_store_list[description_index] = description
        data_to_store_list[date_index] = str(date.today())

        data = ''
        for i in range(len(data_to_store_list)):
            if i == date_index:
                data += f'Date: {data_to_store_list[i]}\n'
            elif i == amount_index:
                data += f'Amount: ${data_to_store_list[i]}\n'
            elif i == description_index:
                data += f'Description: {data_to_store_list[i]}\n'
            elif i == category_index:
                data += f'Category: {data_to_store_list[i]}'

        yes_no_arr = ['Yes', 'No']
        markup = types.ReplyKeyboardMarkup()
        for option in yes_no_arr:
            markup.add(types.KeyboardButton(option))

        user_input = bot.send_message(message.chat.id, f'{data}\n\nConfirm transaction?', reply_markup=markup)
        bot.register_next_step_handler(user_input, end, yes_no_arr)

def end(message, yes_no_arr):
    global data_to_store_list
    confirmation = message.text

    if confirmation not in yes_no_arr:
        markup = types.ReplyKeyboardMarkup()
        for option in yes_no_arr:
            markup.add(types.KeyboardButton(option))
        user_input = bot.send_message(message.chat.id, 'Please enter yes or no', reply_markup=markup)
        bot.register_next_step_handler(user_input, end, yes_no_arr)
    
    elif confirmation.capitalize() == 'No':
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(message.chat.id, 'Transaction not recorded\n\nPlease enter /log_transaction to log an Expense or Income transaction', reply_markup=markup)

    else:
        markup = types.ReplyKeyboardRemove(selective=False)
        try:
            insert_transaction_data(data_to_store_list, isExpense)
            bot.send_message(message.chat.id, 'Transaction recorded\n\nPlease enter /log_transaction to log another transaction', reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f'{e}', reply_markup=markup)

# Webhook Setup
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    heroku_url = 'https://personal-expenses-telegram-bot.herokuapp.com/'
    bot.set_webhook(url=heroku_url + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    # bot.polling()