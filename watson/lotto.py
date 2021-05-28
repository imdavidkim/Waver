
import random
import logging, os
from datetime import datetime

logfile = 'detector'
if not os.path.exists('./logs'):
    os.makedirs('./logs')
now = datetime.now().strftime("%Y%m%d%H%M%S")

logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

streamHandler = logging.StreamHandler()
fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.setLevel(level=logging.INFO)

total_number = [i for i in range(1, 45 + 1)]


def random_pick(obj, how_many, maketype):
    print("Random pick function called...")
    global total_number
    source_number = []
    result_number = []
    retDict = {}
    if isinstance(obj, dict):
        for key in obj.keys():
            source_number.extend(obj[key])
    elif isinstance(obj, list):
        source_number.extend(obj)
    if maketype.upper() == 'IN':
        logger.info("Make list from source number...")
        sn = list(set(source_number))
        sn.sort()
        logger.info("From => ")
        logger.info(sn)
        for r in range(1, how_many + 1):
            retDict[r] = sorted(random.sample(sn, 6))
    elif maketype.upper() == 'OUT':
        logger.info("Make list from out of source number...")
        source_number.sort()
        # print(source_number)
        for e in source_number:
            for idx, o in enumerate(total_number):
                if e == o: total_number.pop(idx)
            # total_number.pop(e)
        logger.info("From {} => ".format(len(total_number)))
        logger.info(total_number)
        for r in range(1, how_many + 1):
            retDict[r] = sorted(random.sample(total_number, 6))
    if isinstance(retDict, dict):
        for key in retDict.keys():
            result_number.extend(retDict[key])
    elif isinstance(retDict, list):
        result_number.extend(retDict)
    result_number = list(set(result_number))
    result_number.sort()
    logger.info("Result {} => ".format(len(result_number)))
    logger.info(result_number)
    return len(result_number), retDict


if __name__ == '__main__':

    # range_info = ["in", 3, 8]
    range_info = ["out", 5, 18]
    games = {1: [6, 7, 17, 21, 29, 41],
             2: [3, 4, 24, 30, 34, 39]
             }  # 3: [9, 17, 24, 28, 38, 40]
    res_num, ret_dict = random_pick(games, range_info[1], range_info[0])
    while res_num > range_info[2]:
        res_num, ret_dict = random_pick(games, range_info[1], range_info[0])
    logger.info(str(ret_dict).replace("],", "]" + chr(10)))  # 8

