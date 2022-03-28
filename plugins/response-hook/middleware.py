from tyk.decorators import *
from gateway import TykGateway as tyk


@Hook
def ResponseHook(request, response, session, metadata, spec):
    tyk.log("ResponseHook is called", "info")
    tyk.log("ResponseHook: upstream returned >> {0}".format(response.status_code), "info")
    return response

