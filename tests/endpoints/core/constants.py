import enum


class RequestMethods(str, enum.Enum):
    get = "GET"
    post = "POST"
    delete = "DELETE"
    put = "PUT"


class ApiRoutes(str, enum.Enum):
    templates = "v1/templates"
