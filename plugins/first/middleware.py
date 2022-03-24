import base64
import json
import ssl
from urllib.parse import urlencode
from urllib.request import urlopen

from gateway import TykGateway as tyk
from tyk.decorators import *


@Hook
def AuthCheck(request, session, metadata, spec):
    auth_header = request.get_header('Authorization')
    subject_token = auth_header.split(" ")
    if len(subject_token) <= 1:
        request.object.return_overrides.response_error = "Authorization header: Invalid format"
        request.object.return_overrides.response_code = 400
        return request, session, metadata

    token = subject_token[1]
    config_data = json.loads(spec.get('config_data', {}))
    use_ping_authentication = is_ping_enabled(token, config_data.get('target_url'))
    if use_ping_authentication:
        tyk.log('Using Ping Auth', 'info')
        service_token = tyk.get_data(token)
        if not service_token:
            tyk.log('Service token not found in cache. Retrieving using API', 'info')
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
            }
            data['client_id'] = config_data['client_id']
            data['client_secret'] = config_data['client_secret']
            data['scope'] = config_data['oauth_scope']
            data['subject_token'] = token
            data = urlencode(data)
            data = data.encode('ascii')
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ping_federate_base_url = config_data['ping_federate_base_url']
            try:
                with urlopen(ping_federate_base_url + '/as/token.oauth2', data, context=ctx) as f:
                    tyk.log('Fetched service token from PingFederate', 'info')
                    response_data = json.load(f)
                    metadata["token"] = token
                    service_token = response_data.get('access_token')
                    request.add_header('Authorization', f"Bearer {service_token}")
                    tyk.store_data(token, service_token, 1800)
                    tyk.log('Stored service token in cache', 'info')
                    return request, session, metadata
            except Exception as error:
                response_body_str = error.read().decode("utf8", 'ignore')
                try:
                    response_body = json.loads(response_body_str)
                except Exception:
                    request.object.return_overrides.response_body = response_body_str
                    request.object.return_overrides.response_error = error.reason
                    request.object.return_overrides.response_code = error.status
                else:
                    request.object.return_overrides.response_body = response_body_str
                    if 'token not found, expired or invalid' in response_body.get('error_description', '').lower():
                        request.object.return_overrides.response_code = 401
                    else:
                        request.object.return_overrides.response_error = error.reason
                        request.object.return_overrides.response_code = error.status
                return request, session, metadata
        else:
            tyk.log('Found service token in cache', 'info')
            metadata["token"] = token
            request.add_header('Authorization', f"Bearer {service_token.decode('utf-8')}")
            return request, session, metadata
    else:
        tyk.log('Using Legacy Classic Platform Auth', 'info')
        metadata["token"] = token
    return request, session, metadata


def is_ping_enabled(token, target_url):
    try:
        user_data = get_jwt_data(token)
    except Exception as ex:
        tyk.log('JWT could not be decoded. Exception: ' + str(ex), 'info')
        return False
    if not user_data:
        return False
    email = user_data.get('mail')
    whitelisted_emails = tyk.get_data("whitelisted_emails")
    if not whitelisted_emails:
        tyk.log('Whitelisted emails not found in cache. Fetching using API', 'info')
        with urlopen(target_url + '/ping-enabled-emails') as f:
            response_data = json.load(f)
            whitelisted_emails = response_data.get('emails_list')
            tyk.store_data("whitelisted_emails", json.dumps(whitelisted_emails), 1800)
    else:
        tyk.log('Whitelisted emails found in cache', 'info')
        whitelisted_emails = json.loads(whitelisted_emails)
    return email in whitelisted_emails


def get_jwt_data(token):
    """
    Return decoded jwt data
    """
    jwt_parts = token.split('.')
    if len(jwt_parts) != 3:
        return None
    encoded_data = jwt_parts[1]
    decoded_data = base64.b64decode(encoded_data)
    return json.loads(decoded_data)


# 
