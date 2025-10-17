from AndroidRunner.Device import Device
import os
from datetime import datetime
from pathlib import Path

# noinspection PyUnusedLocal
def main(device: Device, *args: tuple, **kwargs: dict):
    print("Inside After Experiment file")
    output_path = os.getcwd()
    target_dir = os.path.join(output_path, 'Experiment_Output')
    data_file_path = os.path.join(target_dir, f"run_data_0.csv")
    p = Path(data_file_path)
    if not p.is_file():
            print(f"Error: File not found at '{target_dir}'")
            return
    timestamp = datetime.now().strftime("_%Y%m_%H%M%S")
    new_filename = f"{p.stem}{timestamp}{p.suffix}"
    new_path = p.with_name(new_filename)
    p.rename(new_path)
