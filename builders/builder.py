from hashlib import md5
from urllib import urlencode


class PostFieldsBuilder:
    def __init__(self):
        self.fields = {}

    def with_view_state(self, view_state):
        self.fields.update({"javax.faces.ViewState": "e1s"+view_state})
        return self

    def with_identity(self, key_value):
        self.fields.update({key_value: key_value})
        return self

    def with_custom(self, key, value):
        self.fields.update({key: value})
        return self

    def with_empty(self, key):
        self.fields.update({key: ''})
        return self

    def build(self):
        return urlencode(self.fields)


class LoginPostFieldsBuilder(PostFieldsBuilder):
    def __init__(self):
        PostFieldsBuilder.__init__(self)
        self.fields.update({'loginform': 'loginform'})

    def with_login_mandate(self, login_mandate):
        self.fields.update({"loginform:LOGINMAND": login_mandate})
        return self

    def with_signatory(self, signatory):
        self.fields.update({"loginform:LOGINVFNR": signatory})
        return self


class PinLoginPostFieldsBuilder(PostFieldsBuilder):
    def __init__(self):
        PostFieldsBuilder.__init__(self)
        self.fields.update({'loginpinform': 'loginpinform'})

    def with_login_pin(self, login_pin):
        md5_hash = md5()
        md5_hash.update(login_pin)
        self.fields.update({"loginpinform:LOGINPIN": md5_hash.hexdigest()})
        self.fields.update({"loginpinform:PIN": "*****"})
        return self