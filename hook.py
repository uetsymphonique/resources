from plugins.resources.app.resources_api import ResourcesApi

name = "Resources"
description = 'Resources'
address = '/plugin/resources/gui'


async def enable(services):
    app = services.get('app_svc').application
    resources_api = ResourcesApi(services=services)

    app.router.add_route('GET', '/plugin/resources/export/{adversary_id}', resources_api.export_adversary)
    app.router.add_route('POST', '/plugin/resources/import', resources_api.import_adversary)
    app.router.add_route('GET', '/plugin/resources/get_adversaries', resources_api.get_adversaries)