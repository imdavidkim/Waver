
import random
total_number = [i for i in range(1, 45 + 1)]


def random_pick(obj, how_many, maketype):
    print("Random pick function called...")
    global total_number
    source_number = []
    retDict = {}
    if isinstance(obj, dict):
        for key in obj.keys():
            source_number.extend(obj[key])
    elif isinstance(obj, list):
        source_number.extend(obj)
    if maketype.upper() == 'IN':
        print("Make list from source number...")
        source_number.sort()
        print("From => ")
        print(source_number)
        for r in range(1, how_many + 1):
            retDict[r] = sorted(random.sample(source_number, 6))
    elif maketype.upper() == 'OUT':
        print("Make list from out of source number...")
        source_number.sort()
        # print(source_number)
        for e in source_number:
            for idx, o in enumerate(total_number):
                if e == o: total_number.pop(idx)
            # total_number.pop(e)
        print("From => ")
        print(total_number)
        for r in range(1, how_many + 1):
            retDict[r] = sorted(random.sample(total_number, 6))
    return retDict
if __name__ == '__main__':
    games = {1: [6, 36, 38, 41, 42, 43],
             2: [1, 11, 15, 23, 24, 31]
             }
    # print(str(random_pick(games, 3, 'in')).replace("],", "]" + chr(10)))
    print(str(random_pick(games, 5, 'out')).replace("],", "]" + chr(10)))
