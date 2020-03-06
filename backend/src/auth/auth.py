import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'new-coffee-shop.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffeeshop'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    if 'Authorization' not in request.headers:
        raise AuthError({
                            'code': 'unauthorized',
                            'description': 'Token not valid.'
                        }, 401)
    # get the header from the request
    auth_header = request.headers['Authorization']
    # raise an AuthError if no header is present
    if not auth_header:
        raise AuthError('Authorization header is missing', 401)

    # split bearer and the token
    header_parts = auth_header.split(' ')

    # raise an AuthError if the header is malformed
    if len(header_parts) != 2:
        raise AuthError('Invalid Header - 2 parts not detected', 401)
    elif header_parts[0].lower() != 'bearer':
        raise AuthError('Invalid Header - Must start with bearer', 401)
    #return the token part of the header
    return header_parts[1]

'''
@implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload
'''
def check_permissions(permission, payload):
    # raise an AuthError if permissions are not included in the payload
    if 'permissions' not in payload:
        raise AuthError({
                            'code': 'invalid_claims',
                            'description': 'Permissions not included in JWT.'
                        }, 400)

    # raise an AuthError if the requested permission string is not in the payload permissions array
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True

'''
@implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)
'''
def verify_decode_jwt(token):

    # verify the token using Auth0 /.well-known/jwks.json
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    json_web_key = json.loads(jsonurl.read())

    # get the data in the header
    unverified_header = jwt.get_unverified_header(token)

    #choose our key
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError('Invalid Header - Kid not in header', 401)

    for key in json_web_key['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    # verify key, decode the payload from the token, return the decoded payload
    if rsa_key:
        try:
            payload = jwt.decode(token,
                                 rsa_key,
                                 algorithms=ALGORITHMS,
                                 audience=API_AUDIENCE,
                                 issuer=f'https://{AUTH0_DOMAIN}/')

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError('Token Expired', 401)

        except jwt.JWTClaimsError:
            raise AuthError('Invalid Claims', 401)

        except Exception:
            raise AuthError('Invalid Header - Exception Found', 400)

    raise AuthError('Invalid Header - Unable to decode jwt', 400)


'''
@implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()  #get the token
            try:
                payload = verify_decode_jwt(token)  #decode the jwt
            except:
                raise AuthError('Token not valid', 401)

            #validate claims and check the requested permission
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
