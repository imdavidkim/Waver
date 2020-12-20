# -*- coding: utf-8 -*-

# 진오 =====================================================
# my_token = '781845768:AAEG55_jbdDIDlmGXWHl8Ag2aDUg-YAA8fc'
# chat_id = '84410715'
# bot = telegram.Bot(token=my_token)
# if txt is not None and txt != '':
#         bot.sendMessage(chat_id=chat_id, text=txt)
# ==========================================================
# 아부지====================================================
# my_token = '866257502:AAH3zxEzlNT-venJnI-ZacJBwrnh2nxLsNk'
# chat_id = '869289245'
# bot = telegram.Bot(token=my_token)
# if txt is not None and txt != '':
#         bot.sendMessage(chat_id=chat_id, text=txt)
# ==========================================================

# my_token = '781845768:AAEG55_jbdDIDlmGXWH18Ag2aDUg-YAA8fc'
# bot = telegram.Bot(token=my_token)
# updates = bot.getUpdates()
# for u in updates:
#     print(u.message)


def getConfig():
    from datetime import datetime
    import configparser
    global daddy, ggmsg, chart, error, chat_id_kh, chat_id_km, yyyymmdd, free, share
    config = configparser.ConfigParser()
    config.read(r'D:\Waver\detective\config.ini')
    daddy = config['TELEGRAM']['DADDY']
    ggmsg = config['TELEGRAM']['GGMSG']
    chart = config['TELEGRAM']['CHART']
    error = config['TELEGRAM']['ERROR']
    free = config['TELEGRAM']['FREECAPITAL']
    share = config['TELEGRAM']['MAJORSHAREHOLDER']
    chat_id_kh = config['TELEGRAM']['CHAT_ID_KH']
    chat_id_km = config['TELEGRAM']['CHAT_ID_KM']
    yyyymmdd = str(datetime.now())[:10]


def sendMessage(token, chatid, txt, mode=None):
    import telegram
    bot = telegram.Bot(token=token)
    print(txt)
    bot.sendMessage(chat_id=chatid, text=txt, parse_mode=mode)


def sendImage(token, chatid, img_path):
    import telegram
    bot = telegram.Bot(token=token)
    print(img_path)
    if img_path is not None and img_path != '':
        bot.sendPhoto(chat_id=chatid, photo=open(img_path, 'rb'))


def messeage_to_telegram(txt):
    import time
    getConfig()
    DEBUG = False
    print(txt)
    if txt is not None and txt != '':
        if not DEBUG:
            msg = yyyymmdd + '\n' + txt
            sendMessage(ggmsg, chat_id_kh, msg)
            time.sleep(3)
            sendMessage(daddy, chat_id_km, msg)
        else:
            msg = yyyymmdd + '\n' + txt
            sendMessage(ggmsg, chat_id_kh, msg)

def img_messeage_to_telegram(img_path, dbg=False):
    import time
    getConfig()
    DEBUG = dbg
    if img_path is not None and img_path != '':
        if not DEBUG:
            sendMessage(chart, chat_id_kh, yyyymmdd)
            sendImage(chart, chat_id_kh, img_path)
            time.sleep(3)
            sendMessage(daddy, chat_id_km, yyyymmdd)
            sendImage(daddy, chat_id_km, img_path)
        else:
            sendMessage(chart, chat_id_kh, yyyymmdd)
            sendImage(chart, chat_id_kh, img_path)

            
def free_cap_inc_message_to_telegram(txt):
    import time
    getConfig()
    DEBUG = True
    print(txt)
    if txt is not None and txt != '':
        if not DEBUG:
            sendMessage(free, chat_id_kh, txt, "HTML")
            time.sleep(3)
            sendMessage(daddy, chat_id_km, txt, "HTML")
        else:
            sendMessage(free, chat_id_kh, txt, "HTML")


def major_shareholder_message_to_telegram(txt):
    import time
    getConfig()
    DEBUG = True
    print(txt)
    if txt is not None and txt != '':
        if not DEBUG:
            msg = yyyymmdd + '\n' + txt
            sendMessage(share, chat_id_kh, msg)
            time.sleep(3)
            sendMessage(daddy, chat_id_km, msg)
        else:
            msg = yyyymmdd + '\n' + txt
            sendMessage(share, chat_id_kh, msg)


def err_messeage_to_telegram(txt):
    getConfig()
    sendMessage(error, chat_id_kh, txt)


def check_messenger_bot(token):
    import telegram
    my_token = '1267762976:AAFIwmUknc3jIP8vqH4qqmT78AYFUKs0Umw'
    bot = telegram.Bot(token=my_token)
    a = bot.getUpdates()
    for i in a:
        print(i)


# def sendMessage(token, chatid, txt):
#     import telegram
#     bot = telegram.Bot(token)
#     bot.sendMessage(chat_id=chatid, text=txt)

if __name__ == '__main__':
    chart_messenger_token = '1355279067:AAG1BdVstG8XQ6wg6QPis-Bq74huv0bHv9c'
    chat_target_id = '568559695'
    message = '20201218 FreeCapitalIncInfo'
    sendMessage(chart_messenger_token, chat_target_id, message)
    # check_messenger_bot()
