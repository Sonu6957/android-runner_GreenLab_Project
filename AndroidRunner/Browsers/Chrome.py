from .Browser import Browser


class Chrome(Browser):
    def __init__(self, device=None):
        # https://stackoverflow.com/a/28151563
        if device != None and int(device.get_version()) > 12:
            super(Chrome, self).__init__('com.android.chrome', 'com.google.android.apps.chrome.IntentDispatcher')
        else:
            super(Chrome, self).__init__('com.android.chrome', 'com.google.android.apps.chrome.Main')

