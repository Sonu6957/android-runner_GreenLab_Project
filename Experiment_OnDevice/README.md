# Setups for LLM Processing on Device

## Description
This experiment focuses on running local Large Language Models (LLMs) on mobile devices using the Android-runner tool, which facilitates the deployment and execution of these models directly on Android hardware. By leveraging this tool, the project enables systematic inference operations where the energy consumption of the device is monitored in real time. This measurement is conducted using profiling tools like Perfetto and Battery Manager, which track power usage and computational load during the inference process. 

## Motivation
With advances in LLMs and AI, deploying these models locally on phones can be energy-intensive. This project aims to provide insightful data on the energy dissipation caused by LLM processing, allowing researchers and developers to better understand the trade-offs involved in running AI models locally on mobile devices. This awareness can help optimize model deployment for energy efficiency, improve device battery life, and guide future developments in mobile AI technology by comparing energy usage across different models and configurations. 

## Features
- Run LLMs locally on mobile devices
- Measure energy consumption during inference
- Utilize mobile resources efficiently
- Provide detailed metrics on energy dissipation

## Technologies Used
- Android device with USB debugging enabled
- Python tools: Android-runner, Perfetto, Battery Manager
- Languages: Shell scripting, Python

## Setup Instructions
1. Fork the repository.
2. Follow the steps and install [Android-Runner](https://github.com/S2-group/android-runner) tool and required plugin profilers i.e [Perfetto](https://github.com/S2-group/android-runner/tree/master/AndroidRunner/Plugins/perfetto) and [Battery Manager](https://github.com/S2-group/android-runner/tree/master/AndroidRunner/Plugins/batterymanager).
3. Ensure USB debugging is enabled on your Android device.
4. Create and activate Virtual Environment in your system.
    ### Following setups are to be performed in Linux System

5. Clone and Build **llama.cpp**

    - Clone the llama.cpp repository - ` git clone https://github.com/ggerganov/llama.cpp.git `
    - Navigate into the new directory - `cd llama.cpp`
    - Compile the project

        `make -j` <br>
        `cmake -B build`<br>
        `cmake --build build --config Release -j$(nproc)`
6. Download a GGUF Model <br>
        Go to [Hugging Face](https://huggingface.co/) and search for models in GGUF format and download to your system. 
7. Get Android NDK<br>
    `wget https://dl.google.com/android/repository/android-ndk-r26b-linux.zip`<br>
    `unzip android-ndk-r26b-linux.zip`
8. Build for ARM64 ( Android)
    `mkdir build-android`<br>
    `cd build-android`<br>

    `cmake .. \-DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake\-DANDROID_ABI=arm64-v8a\-DANDROID_PLATFORM=android-24\-DLLAMA_NATIVE=OFF\-DLLAMA_CUBLAS=OFF`<br>

    `make -j$(nproc)`
9. **Push llama files and model to Android Device** and give required permissions<br>
    `adb push ./bin/llama /data/local/tmp/llama`<br>
    `adb shell chmod +x /data/local/tmp/llama`<br>
    `adb push /path/to/model/your_model.gguf /data/local/tmp/`

    ### Run the Android Runner program.
    #### Prerequisites Steps <br>
        - Inside "Experiment_OnDevice" folder, Move "prompts.txt" file to your $HOME location. 
        - Select a config file as per the required model.<br>
            E.g. - For Qwen-1b select `config_Qwen.json` file.
    - Make sure your device is listed in the required config file. If not, add your device.
    - Run using ADB shell.<br>
        `python3 android-runner path\to_your\configfile.json`
10. The profilers results will be in the **output** folder whereas the output from experiment will be in the **$HOME** folder.
    






