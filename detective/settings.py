# -*- coding: utf-8 -*-
import os
import shutil
from configparser import ConfigParser
from dataclasses import dataclass

TOP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TOP_DIR, os.pardir))


@dataclass(eq=False, frozen=True)
class DartConfig:
    search_key: str
    company_key: str
    search_url = 'http://dart.fss.or.kr/api/search.xml'
    company_url = 'http://dart.fss.or.kr/api/company.xml'

    def __post_init__(self):
        if self.search_key == '' or self.company_key == '':
            raise ValueError('not allow empty string')


@dataclass(eq=False, frozen=True)
class ECOSConfig:
    auth_key: str
    auth_key_validate_from: str
    auth_key_validate_to: str
    api_url = 'http://ecos.bok.or.kr/api/'

    def __post_init__(self):
        if self.auth_key == '':
            raise ValueError('not allow empty string')


@dataclass(eq=False, frozen=True)
class FREDConfig:
    api_key: str

    def __post_init__(self):
        if self.api_key == '':
            raise ValueError('not allow empty string')


@dataclass(eq=False, frozen=True)
class TelegramConfig:
    userid: str
    token: str

    def __post_init__(self):
        if self.userid == '' or self.token == '':
            raise ValueError('not allow empty string')


class ConfigSetting(object):
    _config_name: str = 'config.ini'

    def __init__(self):
        self._cfg = None
        self._common = {}
        self._dart: DartConfig = self._init_dart()
        self._ecos: ECOSConfig = self._init_ecos()
        self._fred: FREDConfig = self._init_fred()
        self._telegram: TelegramConfig = self._init_telegram()

    def _get_config_parser(self):
        if self._cfg is None:
            self._cfg = ConfigParser()
            config_file = os.path.join(TOP_DIR, self._config_name)
            if not os.path.exists(config_file):
                shutil.copy2(config_file + '_template', config_file)
            self._cfg.read(config_file, encoding='utf-8')
        return self._cfg

    def get_common(self):
        rlt = self._common
        if self._common == {}:
            import logging
            from detective.common.log import DEFAULT_FORMAT, logger, handler
            cfg = self._get_config_parser()
            default_report = os.path.join(TOP_DIR, 'reports')
            default_chrome = os.path.join(
                ROOT_DIR, 'chromedriver_win32', 'chromedriver.exe')

            rlt['report_path'] = cfg.get('COMMON', 'REPORT_PATH',
                                         fallback=default_report)
            rlt['chromedriver'] = cfg.get(
                'COMMON', 'CHROME_PATH', fallback=default_chrome)

            rlt['agent'] = cfg.getint('COMMON', 'AGENT', fallback=2)

            log_level = cfg.get('COMMON', 'log_level', fallback='INFO')
            log_format = cfg.get('COMMON', 'log_format', fallback=DEFAULT_FORMAT)

            logger.setLevel(getattr(logging, log_level))
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(handler)
            logger.propagate = False

        return rlt

    def _init_dart(self) -> DartConfig:
        cfg = self._get_config_parser()
        search_key = cfg.get('DART', 'SEARCH-API-KEY')
        company_key = cfg.get('DART', 'COMPANY-API-KEY')
        return DartConfig(search_key, company_key)

    def _init_ecos(self) -> ECOSConfig:
        cfg = self._get_config_parser()
        auth_key = cfg.get('ECOS', 'AUTH-KEY')
        auth_key_valiedate_from = cfg.get('ECOS', 'AUTH-KEY-VALID-FROM')
        auth_key_valiedate_until = cfg.get('ECOS', 'AUTH-KEY-VALID-UNTIL')

        return ECOSConfig(auth_key, auth_key_valiedate_from, auth_key_valiedate_until)

    def _init_fred(self) -> FREDConfig:
        cfg = self._get_config_parser()
        api_key = cfg.get('FRED', 'FREDAPI_KEY')

        return FREDConfig(api_key)

    def _init_telegram(self) -> TelegramConfig:
        cfg = self._get_config_parser()
        userid = cfg.get('Telegram', 'userid')
        token = cfg.get('Telegram', 'token')

        return TelegramConfig(userid, token)

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
        return self._dart

    @property
    def ecos(self) -> ECOSConfig:
        return self._ecos

    @property
    def fred(self) -> FREDConfig:
        return self._fred

    @property
    def telegram(self) -> TelegramConfig:
        return self._telegram


config: ConfigSetting = ConfigSetting()

if __name__ == '__main__':
    print(config.project_path)
    print(config.report_path)
    print(config.chromedriver)
