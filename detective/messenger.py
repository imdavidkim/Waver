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


def messeage_to_telegram(txt):
    import time
    import telegram
    my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
    chat_id = '568559695'
    bot = telegram.Bot(token=my_token)
    print(txt)
    if txt is not None and txt != '':
        bot.sendMessage(chat_id=chat_id, text=txt)
    time.sleep(3)
    my_token = '866257502:AAH3zxEzlNT-venJnI-ZacJBwrnh2nxLsNk'
    chat_id = '869289245'
    bot = telegram.Bot(token=my_token)
    print(txt)
    if txt is not None and txt != '':
        bot.sendMessage(chat_id=chat_id, text=txt)



def img_messeage_to_telegram(img_path):
    import time
    import telegram
    my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
    chat_id = '568559695'
    bot = telegram.Bot(token=my_token)
    print(img_path)
    if img_path is not None and img_path != '':
        bot.sendPhoto(chat_id=chat_id, photo=open(img_path, 'rb'))
    time.sleep(3)
    my_token = '866257502:AAH3zxEzlNT-venJnI-ZacJBwrnh2nxLsNk'
    chat_id = '869289245'
    bot = telegram.Bot(token=my_token)
    print(img_path)
    if img_path is not None and img_path != '':
        bot.sendPhoto(chat_id=chat_id, photo=open(img_path, 'rb'))
