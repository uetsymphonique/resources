import logging
import os
import shutil
import uuid

import yaml

from app.objects.c_adversary import Adversary
from app.utility.base_service import BaseService
# from plugins.standalone.util.exception_handler import async_exception_handler

APP_ROOT = os.path.abspath(os.path.dirname(__file__))
PLUGIN_ROOT = os.path.join(APP_ROOT, '../..')
CALDERA_ROOT = os.path.join(PLUGIN_ROOT, '..')
DATA_FOLDER = os.path.join(CALDERA_ROOT, 'data')
ABILITIES_FOLDER = os.path.join(DATA_FOLDER, 'abilities')
ADVERSARIES_FOLDER = os.path.join(DATA_FOLDER, 'adversaries')

TMP_DIR = os.path.join(APP_ROOT, '../tmp')
MERGED_ABILITIES = os.path.join(TMP_DIR, 'abilities')
MERGED_ADVERSARY = os.path.join(TMP_DIR, 'adversary.yml')
UPDATED_ADVERSARY = os.path.join(TMP_DIR, 'updated_adversary.yml')


class BreakLoop(Exception): pass


class ResourcesService(BaseService):
    def __init__(self, services):
        self.services = services
        self.app_svc = services.get('app_svc')
        self.file_svc = services.get('file_svc')
        self.data_svc = services.get('data_svc')

    # #@async_exception_handler
    async def get_adversary_by_id(self, adversary_id):
        for a in await self.data_svc.locate('adversaries'):
            if a.display['adversary_id'] == adversary_id:
                return a.display
        return None

    # #@async_exception_handler
    async def get_abilities_by_adversary(self, adversary):
        abilities = [a.display for a in await self.data_svc.locate('abilities') if
                     a.display['ability_id'] in adversary["atomic_ordering"]]
        return abilities

    # #@async_exception_handler
    async def get_all_files_to_merge(self, adversary_id, abilities_folder: str, adversary_path):
        adversary = await self.get_adversary_by_id(adversary_id=adversary_id)
        # logging.info(f'Generate adversary.yml for: {adversary["name"]}')
        with open(adversary_path, 'w') as adversary_file:
            yaml.dump(adversary, adversary_file)
        abilities = await self.get_abilities_by_adversary(adversary=adversary)
        # logging.info('Dump abilities of the chosen adversary')
        for ability in abilities:
            tactic_folder = os.path.join(abilities_folder, ability["tactic"])
            os.makedirs(tactic_folder, exist_ok=True)
            yaml_file_path = os.path.join(tactic_folder, f'{ability["ability_id"]}.yml')
            if 'ability_id' in ability:
                ability["id"] = ability.pop('ability_id', None)
            abs = [ability]
            with open(yaml_file_path, 'w') as yaml_file:
                yaml.dump(abs, yaml_file)
                # logging.info(f'{ability["id"]} was dumped')

    #@async_exception_handler
    async def merge_abilities(self, abilities_folder):
        merged_abilities = []

        for root, _, files in os.walk(abilities_folder):
            for file in files:
                if file.endswith('.yml') or file.endswith('.yaml'):
                    file_path = os.path.join(root, file)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        abilities = yaml.safe_load(f)
                        if isinstance(abilities, list):
                            merged_abilities.extend(abilities)

        return merged_abilities

    @staticmethod
    #@async_exception_handler
    async def update_ids_and_atomic_ordering(adversary_data, abilities):
        adversary_data['id'] = str(uuid.uuid4())

        id_mapping = {}

        for ability in abilities:
            new_id = str(uuid.uuid4())
            id_mapping[ability['id']] = new_id
            ability['id'] = new_id

        if 'atomic_ordering' in adversary_data:
            adversary_data['atomic_ordering'] = [
                id_mapping.get(old_id, old_id) for old_id in adversary_data['atomic_ordering']
            ]

        return adversary_data, abilities

    #@async_exception_handler
    async def create_updated_adversary_file(self, adversary_file, output_file_yml, abilities):
        with open(adversary_file, 'r', encoding='utf-8') as f:
            adversary_data = yaml.safe_load(f)

        if not isinstance(adversary_data, dict):
            raise ValueError("The adversary.yml file must contain an adversary object (dictionary).")

        adversary_data['id'] = adversary_data.pop('adversary_id', None)
        adversary_data, updated_abilities = await self.update_ids_and_atomic_ordering(adversary_data, abilities)

        adversary_data['abilities'] = updated_abilities

        with open(output_file_yml, 'w', encoding='utf-8') as f:
            yaml.safe_dump(adversary_data, f, allow_unicode=True, sort_keys=False)

    #@async_exception_handler
    async def get_all_in_one_adversary_file(self, adversary_id):
        os.makedirs(TMP_DIR)
        os.makedirs(MERGED_ABILITIES)
        await self.get_all_files_to_merge(adversary_id, MERGED_ABILITIES, MERGED_ADVERSARY)
        merged_abilities = await self.merge_abilities(MERGED_ABILITIES)
        await self.create_updated_adversary_file(MERGED_ADVERSARY, UPDATED_ADVERSARY, merged_abilities)
        return UPDATED_ADVERSARY

    #@async_exception_handler
    async def remove_tmp_folder(self):
        # logging.info(f'Cleanup {TMP_DIR}')
        shutil.rmtree(TMP_DIR)

    #@async_exception_handler
    async def import_all_in_one_adversary(self, adversary):
        abilities = adversary.pop('abilities', None)
        for ability in abilities:
            tactic_folder = os.path.join(ABILITIES_FOLDER, ability["tactic"])
            os.makedirs(tactic_folder, exist_ok=True)
            yaml_file_path = os.path.join(tactic_folder, f'{ability["id"]}.yml')
            abs = [ability]
            with open(yaml_file_path, 'w') as yaml_file:
                yaml.dump(abs, yaml_file)
                # logging.info(f'{ability["id"]} was dumped')
        with open(os.path.join(ADVERSARIES_FOLDER, f'{adversary["id"]}.yml'), 'w') as ad_file:
            yaml.dump(adversary, ad_file)
            # logging.info(f'{adversary["id"]} was dumped')

        await self.data_svc.load_yaml_file(Adversary, os.path.join(ADVERSARIES_FOLDER, f'{adversary["id"]}.yml'), self.Access.RED)
