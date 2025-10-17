from AndroidRunner.Device import Device
import time

def main(device, *args: tuple, **kwargs: dict):
    device.shell('am start -n "com.example.batterymanager_utility/com.example.batterymanager_utility.MainActivity" -a android.intent.action.MAIN -c android.intent.category.LAUNCHER')
    time.sleep(2)

    
    
    