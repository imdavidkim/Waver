# -*- coding: utf-8 -*-
import os
import shutil
from configparser import ConfigParser
from dataclasses import dataclass

TOP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TOP_DIR, os.pardir))


@dataclass
class DartConfig:
    search_key: str
    company_key: str
    search_url = 'http://dart.fss.or.kr/api/search.xml'
    company_url = 'http://dart.fss.or.kr/api/company.xml'

    def __post_init__(self):
        if self.search_key == '' or self.company_key == '':
            raise ValueError('not allow empty string')


@dataclass
class ECOSConfig:
    auth_key: str
    auth_key_validate_from: str
    auth_key_validate_to: str
    api_url = 'http://ecos.bok.or.kr/api/'

    def __post_init__(self):
        if self.auth_key == '':
            raise ValueError('not allow empty string')


@dataclass
class FREDConfig:
    api_key: str

    def __post_init__(self):
        if self.api_key == '':
            raise ValueError('not allow empty string')


@dataclass
class TelegramConfig:
    userid: str
    token: str

    def __post_init__(self):
        if self.userid == '' or self.token == '':
            raise ValueError('not allow empty string')


class ConfigSetting(object):
    config_name: str = 'config.ini'

    def __init__(self):
        self._cfg = None
        self._common = {}
        self._dart: DartConfig = None
        self._ecos: ECOSConfig = None
        self._fred: FREDConfig = None
        self._telegram: TelegramConfig = None

    def __get_config_parser(self):
        if self._cfg is None:
            self._cfg = ConfigParser()
            config_file = os.path.join(TOP_DIR, self.config_name)
            if not os.path.exists(config_file):
                shutil.copy2(config_file + '_template', config_file)
            self._cfg.read(config_file, encoding='utf-8')
        return self._cfg

    def get_common(self):
        rlt = self._common
        if self._common == {}:
            cfg = self.__get_config_parser()
            default_report = os.path.join(TOP_DIR, 'reports')
            default_chrome = os.path.join(
                ROOT_DIR, 'chromedriver_win32', 'chromedriver.exe')

            rlt['report_path'] = cfg.get('COMMON', 'REPORT_PATH',
                                         fallback=default_report)
            rlt['chromedriver'] = cfg.get(
                'COMMON', 'CHROME_PATH', fallback=default_chrome)

            rlt['agent'] = cfg.getint('COMMON', 'AGENT', fallback=2)

        return rlt

    def get_dart(self) -> DartConfig:
        if not self._dart:
            cfg = self.__get_config_parser()
            search_key = cfg.get('DART', 'SEARCH-API-KEY')
            company_key = cfg.get('DART', 'COMPANY-API-KEY')
            self._dart = DartConfig(search_key, company_key)
        return self._dart

    def get_ecos(self) -> ECOSConfig:
        if not self._ecos:
            cfg = self.__get_config_parser()
            auth_key = cfg.get('ECOS', 'AUTH-KEY')
            auth_key_valiedate_from = cfg.get('ECOS', 'AUTH-KEY-VALID-FROM')
            auth_key_valiedate_until = cfg.get('ECOS', 'AUTH-KEY-VALID-UNTIL')

            self._ecos = ECOSConfig(auth_key, auth_key_valiedate_from, auth_key_valiedate_until)

        return self._ecos

    def get_fred(self) -> FREDConfig:
        if not self._fred:
            cfg = self.__get_config_parser()
            api_key = cfg.get('FRED', 'FREDAPI_KEY')

            self._fred = FREDConfig(api_key)
        return self._fred

    def get_telegram(self) -> TelegramConfig:
        if not self._telegram:
            cfg = self.__get_config_parser()
            userid = cfg.get('Telegram', 'userid')
            token = cfg.get('Telegram', 'token')

            self._telegram = TelegramConfig(userid, token)
        return self._telegram

    @property
    def common(self) -> dict:
        return self.get_common()['common']

    @property
    def project_path(self) -> str:
        return ROOT_DIR

    @property
    def django_path(self) -> str:
        return os.path.join(ROOT_DIR, 'MainBoard')

    @property
    def django_mainboard(self) -> str:
        return os.path.join(self.django_path, 'MainBoard')

    @property
    def report_path(self) -> str:
        return self.get_common()['report_path']

    @property
    def chromedriver(self) -> str:
        return self.get_common()['chromedriver']

    # Common
    @property
    def agent(self) -> int:
        return self.get_common()['agent']

    # Sector Config
    @property
    def dart(self) -> DartConfig:
        return self.get_dart()

    @property
    def ecos(self) -> ECOSConfig:
        return self.get_ecos()

    @property
    def fred(self) -> FREDConfig:
        return self.get_fred()

    @property
    def telegram(self) -> TelegramConfig:
        return self.get_telegram()


config: ConfigSetting = ConfigSetting()

if __name__ == '__main__':
    print(config.project_path)
    print(config.report_path)
    print(config.chromedriver)
