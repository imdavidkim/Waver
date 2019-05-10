import logging

DEFAULT_FORMAT = '%(asctime)s - %(levelname)-7s - %(filename)s,%(lineno)d - %(message)s'
FORMAT = DEFAULT_FORMAT


def set_format(logger_name='detective', format=None, formatter=logging.Formatter):
    format = format if format else FORMAT
    _logger = logging.getLogger(logger_name)

    if _logger.handlers == []:
        h = logging.StreamHandler()
        h.setFormatter(formatter(format))
        _logger.addHandler(h)
    else:
        handler = _logger.handlers[-1]
        handler.setFormatter(formatter(format))


def get_logger(logger_name='detective'):
    if logging.root.handlers:
        # extract format for code: logging.basicConfig(format=FORMAT)
        logging.root.handlers[0].flush()
        # don't use root logger
        # logging.root.handlers = []
    _logger = logging.getLogger(logger_name)

    return _logger


def get_logger2(logger_name='detective', level=None, format=None, filename=None):
    global FORMAT
    if logging.root.handlers:
        # extract format for code: logging.basicConfig(format=FORMAT)
        root_fmt = logging.root.handlers[0].formatter._fmt
        if root_fmt != logging.BASIC_FORMAT:
            FORMAT = root_fmt
        logging.root.handlers[0].flush()
        # don't use root logger
        # logging.root.handlers = []
    if format:
        FORMAT = format
    format = format if format else FORMAT

    _logger = logging.getLogger(logger_name)
    if level:
        _logger.setLevel(level)
    if _logger.handlers:
        _logger.handlers = []
    if filename:
        h = logging.FileHandler(filename, 'a')
    else:
        h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(format))
    _logger.addHandler(h)
    _logger.propagate = False
    return _logger


handler = None
logger = get_logger()

if __name__ == '__main__':
    class MultiLineFormatter(logging.Formatter):
        def format(self, record):
            str = logging.Formatter.format(self, record)
            header, footer = str.split(record.message)
            str = str.replace('\n', '\n' + header)
            return str


    get_logger().warning('\n'.join(['ddfdsafdsa', 'fdsafdsa', 'fdsafdsa']))
    get_logger().info('ddd')
    get_logger().warning('\n'.join(['ddfdsafdsa', 'fdsafdsa', 'fdsafdsa']))
    set_format('detective', '%(asctime)s - %(filename)s,%(lineno)d %(message)s', MultiLineFormatter)
    get_logger().warning('\n'.join(['ddfdsafdsa', 'fdsafdsa', 'fdsafdsa']))
    get_logger().warning('\n'.join(['ddfdsafdsa', 'fdsafdsa', 'fdsafdsa']))
    set_format('detective', '- %(filename)s,%(lineno)d %(message)s', MultiLineFormatter)
    get_logger().warning('\n'.join(['ddfdsafdsa', 'fdsafdsa', 'fdsafdsa']))
