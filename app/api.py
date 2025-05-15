from flask_restful import Resource
from app.models import Startup

class StartupAPI(Resource):
    def get(self, startup_id=None):
        if startup_id:
            startup = Startup.query.get_or_404(startup_id)
            return {'id': startup.id, 'name': startup.name, 'description': startup.description, 'logo': startup.logo, 'file': startup.file}
        startups = Startup.query.all()
        return [{'id': s.id, 'name': s.name, 'description': s.description, 'logo': s.logo, 'file': s.file} for s in startups]

def register_resources(api):
    print("Adding resource StartupAPI...")
    api.add_resource(StartupAPI, '/api/startups', '/api/startups/<int:startup_id>')
    print("Resource StartupAPI added.")