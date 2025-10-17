import subprocess
import time
import os
import json
import sys
import pty
from AndroidRunner.Device import Device
import csv
import random

metadata = {}


# Function to read prompts from text file
def load_prompts_from_file(filepath):  
    with open(filepath, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f if line.strip()]
    return prompts

def main(device: Device, *args: tuple, **kwargs: dict):
    output_path = os.getcwd()
    prompt_file_path = os.path.join(os.path.dirname(output_path), 'promptfile.txt')
    prompts = load_prompts_from_file(prompt_file_path)

    current_run_data = kwargs.get("current_run")
    run_id = current_run_data.get("runId")

    # --- Setup Parameters ---
    binary = "/data/local/tmp/llama-cli"
    model_file = "/data/local/tmp/Llama.gguf" 
    model_short_name = "Llama-1b" 

    # Randomly select a prompt
    prompt = random.choice(prompts)
    prompt_words = len(prompt.split()) 
    
    prompt_size_category = "big" if prompt_words > 50 else "small"

    input_size_kb = len(prompt.encode("utf-8")) / 1024.0

    
    adb_command_str = (
        f"cd /data/local/tmp && "
        f"LD_LIBRARY_PATH=/data/local/tmp {binary} "
        f"-m {model_file} -c 2048 -no-cnv --n-predict 800 "
        f"--prompt '{prompt}' "
        f"&& echo RUN_DONE"
    )


    full_host_command = ["adb", "shell", adb_command_str]

    print("Running command:\n", " ".join(full_host_command))
    print("\n--- Model Output (Real-time Stream) ---\n")

    start_time = time.time()
    output_text_lines = []

 
    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(full_host_command, stdout=slave_fd, stderr=slave_fd, close_fds=True)
    os.close(slave_fd)

    with os.fdopen(master_fd, 'rb', 0) as master_pty:
        while True:
            if process.poll() is not None:
                try:
                    remaining_output = master_pty.read()
                    if remaining_output:
                        output_chunk = remaining_output.decode('utf-8', errors='ignore')
                        sys.stdout.write(output_chunk)
                        output_text_lines.append(output_chunk)
                except OSError:
                    pass
                break

            try:
                output_chunk = os.read(master_fd, 1024)
            except OSError:
                break

            if output_chunk:
                output_str = output_chunk.decode('utf-8', errors='ignore')
                sys.stdout.write(output_str)
                sys.stdout.flush()
                output_text_lines.append(output_str)
                if "RUN_DONE" in output_str:
                    break
            time.sleep(0.01)
    process.wait()
   

    end_time = time.time()
    execution_time_sec = end_time - start_time
    print("\n\n--- End of Stream ---")

    stdout_full = "".join(output_text_lines)
    if "RUN_DONE" in stdout_full:
        output_text = stdout_full.split("RUN_DONE")[0].strip()
    else:
        output_text = stdout_full.strip()

    return_code = process.returncode
    output_size_kb = len(output_text.encode("utf-8")) / 1024.0

    print(f"\nProcess exited with code {return_code}")
    print(f"Input size: {input_size_kb:.6f} KB, Prompt size: {prompt_words} words, Execution Time: {execution_time_sec:.2f}s, Output size: {output_size_kb:.2f} KB")



    run_data = {
        "run Id": run_id,
        "execution_time_sec": execution_time_sec,
        "input_size_kb": input_size_kb,
        "output_size_kb": output_size_kb,
        "prompt_size": prompt_size_category,
        "model": model_short_name,
        "api": "no",
        "mobile": "yes"
    }
    
    target_dir = os.path.join(output_path, 'Experiment_Output')
    os.makedirs(target_dir, exist_ok=True)

    
    data_file_path = os.path.join(target_dir, f"run_data_0.csv")

    fieldnames = list(run_data.keys())

    write_header = not os.path.exists(data_file_path)

    with open(data_file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(run_data)

    print("Run Data CSV Path: - " + data_file_path)
