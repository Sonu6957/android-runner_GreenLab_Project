from AndroidRunner.Device import Device
from AndroidRunner.Experiment import Experiment
import logging

LOGGER = logging.getLogger()

def main(device: Device, *args: tuple, **kwargs: dict):
    LOGGER.debug(args)
    LOGGER.debug(kwargs)
    
    experiment: Experiment = args[0]
    current_run = experiment.get_experiment()
    
    LOGGER.debug(device.current_activity())
    LOGGER.debug(current_run)

    print(device.current_activity())
    print(current_run)
