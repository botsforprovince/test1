import sys
import os
import time
import json
import threading

import tkinter
from tkinter.filedialog import askopenfilename
from tkinter import messagebox

import pyautogui

import autorization
import network_utils
import logs_read
from pyautogui import screenshot
import keyboard
import telebot
from functions import *
from logs_read import *
from settings import *
import winsound
import py_win_keyboard_layout


if not check_keyboard_layout():
    py_win_keyboard_layout.change_foreground_window_keyboard_layout(0x04090409)
    print('Ошибка распознавания клавиатуры. Перезагрузка.')
    restart_program()


# Загрузка настроек программы в переменную
settings = load_settings()

if not settings.get('user_login'):
    settings['user_login'] = None

if not settings.get('auto_autorization'):
    settings['auto_autorization'] = False

if settings.get('user_password'):
    save_password = settings['user_password']
else:
    save_password = None

try:
    user_data = autorization.start_autorization(settings['user_login'], settings['auto_autorization'], save_password)
    user_login, settings['user_login'] = user_data[0], user_data[0]
    user_password = user_data[1]
    auto_autorization, settings['auto_autorization'] = user_data[2], user_data[2]
    if auto_autorization:
        settings['user_password'] = user_password
    user_serial = user_data[3]
    save_settings(settings)
except:
    sys.exit()



province_file = settings.get('province_file') # Путь до MTA Province
if not province_file:
    tkinter.Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    province_file = askopenfilename(
        title="Выберите файл Multi Theft Auto.exe",
        filetypes=(("Executable Files", "*.exe"),),
        initialdir="C:/Games/MTA Province/MTA",
        initialfile="Multi Theft Auto.exe"
    )
    settings['province_file'] = province_file # Записать путь к MTA Province в настройки


token = '6324636732:AAHkK2U98V4f2BXJAyTpq4zzLnKRwWPD0Ow'
bot = telebot.TeleBot(token)
Mouse = Mouse()
Key = Keys()
program = True
is_program_running = False


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    print(message.chat.id)
    send_message_tg('Привет, это бот для управления BFP')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "Привет":
        send_message_tg("Привет, чем я могу тебе помочь?")
    elif message.text == "/help":
        send_message_tg("Напиши привет")
    elif message.text == "/startstop":
        start_stop_program()
    elif message.text == "/close":
        time.sleep(1)
        close_program()
    else:
        send_message_tg("Я тебя не понимаю. Напиши /help или /startstop")


def send_message_tg(message):
    try:
        bot.send_message(tg_chat_id, message)
    except:
        send_message_tg(message)


def start_stop_program():
    global is_program_running
    if not is_program_running:
        print("Bot start")
        is_program_running = True
        send_message_tg("Bot ON")
        winsound.Beep(600, 1000)
    else:
        print("Bot stop")
        is_program_running = False
        Key.all_keyUp()
        send_message_tg("Bot OFF")
        winsound.Beep(600, 400)
        time.sleep(0.2)
        winsound.Beep(600, 400)


def close_program():
    print('Завершение...')
    global program
    program = False
    print('Циклы отключены.')
    send_message_tg("Bot CLOSE")
    bot.stop_polling()
    print('Поток telegram_bot завершен.')


def check_pressed_keyboards_keys():
    while program:
        if keyboard.is_pressed('p'):  # if key 'q' is pressed
            print('You Pressed P Key!')
            start_stop_program()
            time.sleep(1)
        elif keyboard.is_pressed('q'):  # if key 'q' is pressed
            print('You Pressed Q Key!')
            close_program()
            time.sleep(2)
        elif keyboard.is_pressed('r'):  # if key 'q' is pressed
            print('You Pressed R Key!')
            restart_program()
        else:
            time.sleep(500 / 1000)
    exit()


def isGameActive():
    while program:
        # monitor_settings = functions.getMonitorSettings()
        app_window = pyautogui.getWindowsWithTitle('MTA: Province')[0]
        is_active = app_window.isActive
        if is_active:
            return True
        else:
            return False


def read_chat(line_count=1, province_file=province_file):
    if line_count == 1:
        return classify_string(read_log_file(province_file))

    else:
        lines = []
        chat_lines = read_log_file(province_file, line_count) # возвращает массив ['text1', 'text2', ...]
        for line in range(line_count):
            lines.append(classify_string(chat_lines[line]))
        return lines


def regular_chat_check():
    pass


thr_key = threading.Thread(target=check_pressed_keyboards_keys, args=(), name='thr-1')
thr_key.start()

# bot.polling(none_stop=True, interval=0)
thr_tg = threading.Thread(target=bot.polling, kwargs={'interval': 1}, name='thr-tgbot')
thr_tg.start()
# chat_timestamp = classify_string(read_log_file()[0])['timestamp']


global xcen, ycen, xres, yres, xrat, yrat


def setGameMonitor(width, height):
    global xcen, ycen, xres, yres, xrat, yrat
    xcen = width / 2
    ycen = height / 2
    xres = 1440 / width
    yres = 900 / height
    xrat = ((1440 / 900) / (width / height)) / (width / 1440)
    yrat = ((1440 / 900) / (width / height)) / (height / 900)


def control_doors():
    last_timestamp = read_chat()['timestamp']
    while program:
        try:
            if not IfPixelSearchRange([255, 255, 0], 50,
                                      xcen_map - int(25 // xres), ycen_map - int(25 // yres),
                                      xcen_map + int(5 // xres), ycen_map + int(25 // yres)):
                print('Ошибка, остановки нет. Продолжение маршрута.')
                Key.all_keyUp()
                return 'Err-1'
        except:
            print('Ого! Ошибка в блоке control_doors -> IfPixelSearch()\nМы постараемся ее исправить!')
            pass

        is_doors = read_chat()
        if not is_doors['timestamp'] == last_timestamp:
            last_timestamp = is_doors['timestamp']

            if is_doors['message'] == 'Откройте двери и подождите пассажиров.':
                time.sleep(0.5)
                Key.all_keyUp()
                Key.press('2')
                print('Двери трамвая открыты.')

            elif is_doors['message'] == 'Закройте двери и продолжайте маршрут.':
                time.sleep(0.5)
                Key.all_keyUp()
                Key.press('2')
                print('Двери трамвая закрыты.')
                time.sleep(1)
                return 'Ok'


def is_delayed_stop():
    if IfPixelSearchRange([135, 225, 182], 0,
                          xcen_map - int(25 // xres),
                          ycen_map - int(15 // yres),
                          xcen_map - int(10 // xres),
                          ycen_map + int(10 // yres)
                          ):
        print('Следующая остановка на развороте.')
        send_message_tg("Bot: Следующая остановка на развороте.\n.")
        return True
    else:
        return False


# Загрузка настроек из файла
tg_chat_id = 5193596301

# координаты карты 1440x900 - 22,697 - 208,881
# центр 115, 789

setGameMonitor(1440, 900)
# Координаты карты
x0_map = int(22 // xres)
x_map = int(208 // xres)
xcen_map = int(115 // xres)
y0_map = int(697 // yres)
y_map = int(881 // yres)
ycen_map = int(789 // yres)

# Координаты для торможения
x0_brake = int(105 // xres)
x_brake = int(124 // xres)
y0_brake = int(774 // yres)
y_brake = int(800 // yres)

# Координаты для остановки
x0_speedometer = int(1348 // xres)
x_speedometer = int(1383 // xres)
y0_speedometer = int(811 // yres)
y_speedometer = int(878 // yres)

print('Программа готова к работе и ждет начала маршрута.')
Key.all_keyUp()
is_First_Station = True
route_status = 0
station_number = 0
error_count = 0
delay_stop = False
train_lights = False

while program:
    if is_program_running:
        if IfPixelSearchRange([255, 255, 0], 50, x0_map, y0_map, x_map, y_map):
            if route_status == 0:
                error_count += 1
                time.sleep(1)
                if error_count >= 3:
                    route_status = 1
                    error_count = 0
                    print('Программа начала прохождение маршрута.')
                continue
        else:
            if route_status == 0:
                time.sleep(1)
                continue
            else:
                error_count += 1
                Key.all_keyUp()
                time.sleep(1)
                if error_count >= 30:
                    print('Произошла ошибка, программа на протяжении 30 секунд не видит желтый маркер.')
                    start_stop_program()
                    error_count = 0
                else:
                    time.sleep(1)
                    continue

        if not train_lights:
            Key.double_press('l')
            route_status = 1
            station_number = 1
            train_lights = True

        if IfPixelSearchRange([255, 255, 0], 50, x0_brake, y0_brake, x_brake, y_brake):
            # print('Торможение...')
            if is_First_Station:
                Key.all_keyUp()
                time.sleep(0.5)
                is_First_Station = False
            if delay_stop:
                time.sleep(4)
            Key.keyUp('w')
            Key.keyDown('s')
            if IfPixelSearch([47, 43, 42], x0_speedometer, y0_speedometer,
                             x_speedometer, y_speedometer):  # когда скорость меньше 10км/ч
                print('Остановка...')
                Key.keyDown('w')
                control_doors()  # открытие/закрытие дверей
                delay_stop = is_delayed_stop()
        else:
            Key.keyDown('w')
    else:
        time.sleep(1)
print('Главный процесс завершен.')
