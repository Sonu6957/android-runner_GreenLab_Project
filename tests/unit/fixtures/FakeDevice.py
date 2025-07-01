# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class FakeDevice(object):
    def __init__(self, device_id):
        self.id = device_id
    
    @staticmethod
    def current_activity():
        return {"type": "standard", "name": 'fake.activity'}

    def logcat_regex(self, regex):
        return regex

    def launch_activity(self, package, activity, action='', data_uri='', from_scratch=False, force_stop=False):
        print(("{},{},{},{},{}".format(package, activity, action, data_uri, from_scratch, force_stop)))
