import os
import zipfile


def getConfig():
    import configparser
    global path, django_path, main_path
    config = configparser.ConfigParser()
    config.read('../detective/config.ini')
    path = config['COMMON']['REPORT_PATH']
    proj_path = config['COMMON']['PROJECT_PATH']
    django_path = proj_path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


if __name__ == '__main__':
    getConfig()
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            print(dir)
        for file in files:
            print(file)
    # zipf = zipfile.ZipFile('Python.zip', 'w', zipfile.ZIP_DEFLATED)
    # zipdir(path, zipf)
    # zipf.close()
