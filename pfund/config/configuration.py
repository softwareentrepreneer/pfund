import os

import yaml

from pfund.utils.utils import short_path


class Configuration:
    def __init__(self, config_path, config_name):
        self.config_path = config_path
        self.config_name = config_name
        self.configs = None
        self.reload()

    def reload(self):
        self.configs = self.read_config(self.config_name)
    
    def get_config_path(self):
        return self.config_path

    def read_config(self, config_name):
        file_path = f'{self.config_path}/{config_name}.yml'
        # short_file_path = short_path(file_path)
        if not os.path.exists(file_path):
            print(f'cannot find config {file_path}')
        else:
            with open(file_path, 'r') as f:
                return list(yaml.safe_load_all(f))

    def write_config(self, config_name, content):
        with open(f'{self.config_path}/{config_name}.yml', 'w') as f:
            f.write(yaml.dump(content))

    def load_config_section(self, section):
        try:
            return [config[section] for config in self.configs if section in config][0]
        except:
            raise Exception(f'could not find section {section} for config {self.config_name}')

    def check_if_config_exists_and_not_empty(self, config_name):
        file_path = f'{self.config_path}/{config_name}.yml'
        if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
            return True
        else:
            return False

    # REVIEW
    def load_all_and_except_config(self, config, ptype, pdt):
        '''
        handle exceptions that break the config structure, e.g. fee structure
        '''
        val = config['all']
        # try to load if theres any exception, per ptype or per pdt
        try:
            val = config['except']['ptypes'][ptype]
            val = config['except']['pdts'][pdt]
        except:
            pass
        return val