import requests
import xmltodict
import pandas as pd
import logging
import datetime
# from tqdm import tqdm

# http://stats.oecd.org/restsdmx/sdmx.ashx/GetDataStructure/ALL
# Extract OECD KeyFamily id (dataset id) and English description


def getConfig():
    import configparser
    global path, proj_path, django_path, main_path, yyyymmdd
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    proj_path = config['COMMON']['PROJECT_PATH']
    django_path = proj_path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    yyyymmdd = str(datetime.datetime.now())[:10]




def get_oecd_keyfamilies():
    # where to save
    logfile = 'logs/oecd_keyfamilies.log'
    datafile = 'OECD_keys/OECD_key_names.csv'

    # logging
    logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    logging.debug("Log started at %s", str(datetime.datetime.now()))

    # get the data structure schema with the key families (dataset ids)
    dataStructureUrl = 'http://stats.oecd.org/RESTSDMX/sdmx.ashx/GetDataStructure/ALL/'

    try:
        r = requests.get(dataStructureUrl, timeout=61)
    except requests.exceptions.ReadTimeout:
        print("Data request read timed out")
        logging.debug('Data read timed out')
    except requests.exceptions.Timeout:
        print("Data request timed out")
        logging.debug('Data request timed out')
    except requests.exceptions.HTTPError:
        print("HTTP error")
        logging.debug('HTTP error')
    except requests.exceptions.ConnectionError:
        print("Connection error")
        logging.debug('Connection error')
    else:
        if r.status_code == 200:
            keyFamIdList = []
            keyFamNameList = []
            # print(r.content)
            # soup = BeautifulSoup(r.content.decode('utf-8'), "lxml")
            # xml = soup.prettify(encoding='utf-8').replace(b'&', b'&amp;')
            # print(xml)

            # use xmltodict and traverse nested ordered dictionaries
            keyfamilies_dict = xmltodict.parse(r.text)
            keyFamilies = keyfamilies_dict['message:Structure']['message:KeyFamilies']['KeyFamily']
            # print(keyfamilies_dict)
            # print(keyfamilies_dict['message:Structure']['message:KeyFamilies'])
            for keyFamily in keyFamilies:
                keyfam_id = keyFamily['@id']
                keyFamIdList.append(keyfam_id)
                keyNames = keyFamily['Name']
                # print(keyfam_id, keyNames)
                # print(type(keyNames))
                if isinstance(keyNames, list):
                    for keyName in keyNames:
                        keyfam_lang = keyName['@xml:lang']
                        if keyfam_lang == 'en':
                            keyfam_text = keyName['#text']
                            keyFamNameList.append(keyfam_text)
                else:
                    keyfam_lang = keyNames['@xml:lang']
                    if keyfam_lang == 'en':
                        keyfam_text = keyNames['#text']
                        keyFamNameList.append(keyfam_text)
                # for keyName in keyNames:
                #     keyfam_lang = keyName['@xml:lang']
                #     if keyfam_lang == 'en':
                #         keyfam_text = keyName['#text']
                #         keyFamNameList.append(keyfam_text)
                #         # print(keyfam_id, keyfam_text)

            # create a 2D list(needed?), and a data frame. Save data frame to csv file
            # keyFamTable = [keyFamIdList, keyFamNameList]
            keyFamDF = pd.DataFrame({'KeyFamilyId': keyFamIdList, 'KeyFamilyName': keyFamNameList})
            keyFamDF.set_index('KeyFamilyId', inplace=True)
            keyFamDF.to_csv(datafile)
        else:
            print('HTTP Failed with code', r.status_code)
            logging.debug('HTTP Failed with code %d', r.status_code)

    print("completed ...")
    logging.debug("Log ended at %s", str(datetime.datetime.now()))

def get_oecd_json_dataset(dataset_id):
    # http://stats.oecd.org/sdmx-json/data/<id>/all/all
    # Get JSON datasets for all key families (dataset ids)

    # where to save or read
    logfile = 'logs/oecd_datasets.log'
    storedir = 'OECD_json_datasets/'
    keyNamesFile = 'OECD_keys/OECD_key_names.csv'

    # logging
    logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    logging.debug("Log started at %s", str(datetime.datetime.now()))

    # read in list of dataset ids
    datasourceUrl = 'http://stats.oecd.org/sdmx-json/data/'

    dataset_ids_df = pd.read_csv(keyNamesFile)
    dataset_ids = dataset_ids_df['KeyFamilyId'].tolist()
    print(dataset_ids)
    success_count = 0

    with requests.Session() as s:
        # for dataset_id in tqdm(dataset_ids):
        if dataset_id in dataset_ids:
            try:
                r = s.get(datasourceUrl + dataset_id + '/all/all', timeout=61)
            except requests.exceptions.ReadTimeout:
                print(dataset_id, ": OECD data request read timed out")
                logging.debug('%s: OECD data request read timed out', dataset_id)
            except requests.exceptions.Timeout:
                print(dataset_id, ": OECD data request timed out")
                logging.debug('%s: OECD data request timed out', dataset_id)
            except requests.exceptions.HTTPError:
                print(dataset_id, ": HTTP error")
                logging.debug('%s: HTTP error', dataset_id)
            except requests.exceptions.ConnectionError:
                print(dataset_id, ": Connection error", )
                logging.debug('%s: Connection error', dataset_id)
            else:
                if r.status_code == 200:
                    # save the json file - don't prettify to save space
                    target = storedir + dataset_id + ".json"
                    with open(target, 'w', encoding='utf-8') as f:
                        f.write(r.text)
                        success_count += 1
                else:
                    print(dataset_id, 'HTTP Failed with code', r.status_code)
                    logging.debug('%s HTTP Failed with code %d', dataset_id, r.status_code)

    print("completed ...")
    print(len(dataset_ids), " Dataset Ids")
    print(success_count, " datasets retrieved")
    logging.debug("Log ended at %s", str(datetime.datetime.now()))


def get_oecd_json_CLI_dataset():
    from detective.fnguide_collector import httpRequest
    import json

    countries = None
    time_period = None
    retDict = {}
    url = "https://stats.oecd.org:443/sdmx-json/data/DP_LIVE/G-7+KOR+OECD+USA.CLI.AMPLITUD.LTRENDIDX.M/OECD?json-lang=en&dimensionAtObservation=allDimensions&startPeriod=2005-01"
    jo = json.loads(httpRequest(url, None, 'GET', None).decode('utf-8'))

    # header
    # dataSets
    # structure
    # for key in jo['header'].keys():
    #     print(key, jo['header'][key])
    # for key in jo['structure'].keys():
    #     print(key, jo['structure'][key])
    # 국가명 : dimensions - observation - keyPosition:0 - values
    # dimensions - observation - id:TIME_PERIOD - values - id
    for d in jo['structure']['dimensions']['observation']:
        # print(d)
        if 'keyPosition' in d.keys():
            if d['keyPosition'] == 0:
                countries = [data['id'] for data in d['values']]
        else:
            if d['id'] == "TIME_PERIOD":
                time_period = [data['id'] for data in d['values']]

    # print(countries, time_period)
    for d in jo['dataSets']:
        if 'observations' in d.keys():
            for key in d['observations'].keys():
                if countries[int(key.split(":")[0])] in retDict.keys():
                    retDict[countries[int(key.split(":")[0])]][time_period[int(key.split(":")[-1])]] = \
                    d['observations'][key][0]
                else:
                    retDict[countries[int(key.split(":")[0])]] = {}
                    retDict[countries[int(key.split(":")[0])]][time_period[int(key.split(":")[-1])]] = \
                    d['observations'][key][0]
    return retDict

def make_CLI_graph():
    import matplotlib.pyplot as plt
    import os
    import datetime
    from matplotlib import font_manager, rc
    import detective.messenger as msgr
    getConfig()

    font_path = r"C:/Windows/Fonts/KoPubDotum_Pro_Light.otf"
    # 폰트 이름 얻어오기
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    # font 설정
    rc('font', family=font_name)
    src = get_oecd_json_CLI_dataset()
    try:
        # print(list(src['OECD'].keys()), list(src['OECD'].values()))
        for country in src.keys():
            retArrayDate = [datetime.datetime.strptime(date, '%Y-%m') for date in list(src[country].keys())]
            retArrayData = list(src[country].values())
            retVal = pd.core.series.Series(retArrayData, retArrayDate)
            plt.plot(retVal, label=country)
        plt.legend(loc='upper left')
        plt.xticks(rotation=45)
        plt.grid(True, axis='y', color='gray', alpha=0.5, linestyle='--')
        plt.title("OECD 경기선행지수")
        # plt.show()
        img_path = r'{}\{}\{}'.format(path, 'OECD_CLI', yyyymmdd)
        print(img_path)
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        plt.savefig(img_path + '\\result.png')
        msgr.img_messeage_to_telegram(img_path + '\\result.png')
        plt.close('all')
    except Exception as e:
        plt.close('all')



if __name__ == '__main__':
    # get_oecd_json_dataset('PRICES_CPI')
    # get_oecd_json_CLI_dataset()
    make_CLI_graph()
