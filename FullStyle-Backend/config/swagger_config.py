import yaml
import os

def get_swagger_config():
    """
    Cargar y devolver la configuración de Swagger desde el archivo YAML
    """
    dirname = os.path.dirname(__file__)
    swagger_path = os.path.join(dirname, '..', 'swagger', 'swagger.yaml')
    
    with open(swagger_path, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)

def get_apidocs():
    """
    Endpoint para devolver la configuración de Swagger en formato JSON
    """
    return get_swagger_config()
