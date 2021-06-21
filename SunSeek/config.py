from configparser import ConfigParser

def create_config():
    config = ConfigParser()
    config['Settings'] = {'Port': 8143,
                          'Max Users': 65535,
                          'Max Message Size': 1024,
                          'Private Server': 'False',
                          'Admin Password': 'None',
                          'Max Saved PMs': 15,
                          'Greeting': 'Welcome to the server'}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def get_port():
    config = ConfigParser()
    config.read('config.ini')
    return int(config['Settings']['Port'])


def get_config_data():
    config = ConfigParser()
    config.read('config.ini')
    settings = {}
    if config['Settings']['Private Server'] == 'True':
        settings['private_server'] = True
    if config['Settings']['Private Server'] == 'False':
        settings['private_server'] = False

    settings['max_pms'] = int(config['Settings']['Max Saved PMs'])
    settings['greeting'] = config['Settings']['Greeting']
    settings['max_users'] = int(config['Settings']['Max Users'])
    settings['max_msg_size'] = int(config['Settings']['Max Message Size'])

    if config['Settings']['Admin Password'] == 'None':
        settings['admin_password'] = None
    else:
        settings['admin_password'] = config['Settings']['Admin Password']
    return settings
