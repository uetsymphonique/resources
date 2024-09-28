import logging
from app.service.auth_svc import for_all_public_methods, check_authorization
import yaml
from aiohttp import web

from plugins.resources.app.resources_svc import ResourcesService

@for_all_public_methods(check_authorization)
class ResourcesApi:
    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')
        self.log = logging.getLogger('resources_api')
        self.resources_svc = ResourcesService(services=services)

    async def export_adversary(self, request):
        adversary_id = request.match_info.get("adversary_id")
        with open(await self.resources_svc.get_all_in_one_adversary_file(adversary_id), 'r') as yaml_in:
            yaml_object = yaml.safe_load(yaml_in)
            await self.resources_svc.remove_tmp_folder()
            return web.json_response(yaml_object)

    async def import_adversary(self, request):
        await self.resources_svc.import_all_in_one_adversary(await request.json())
        return web.json_response(dict(msg="success"))

    async def get_adversaries(self, request):
        adversaries = sorted([a.display for a in await self.data_svc.locate('adversaries')],
                             key=lambda a: a['name'])
        return web.json_response(dict(adversaries=[dict(
            adversary_id=a["adversary_id"], name=a["name"]) for a in adversaries
        ]))
