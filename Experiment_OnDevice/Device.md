# Setups for LLM Processing on Device

## Description
This project focuses on running local Large Language Models (LLMs) on mobile devices and measuring their energy consumption during inference. The goal is to provide insights into the energy dissipation caused by LLM processing, helping users understand and compare energy usage on mobile hardware.

## Motivation
With advances in LLMs and AI, deploying these models locally on phones can be energy-intensive. This project aims to raise awareness of energy consumption and facilitate experiments to optimize energy efficiency during inference.

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
2. Configure your mobile device with the necessary LLM setup.
3. Edit the `config.json` file with your specific configuration.
4. Ensure USB debugging is enabled on your Android device.

## Usage
Run the experiment using the `config.json` file in `android-runner`. Follow the instructions in the configuration file to start the process and collect energy metrics.

## Additional Configuration
Any other important environment or configuration variables will be documented here.

## Contributing
Contributions are welcome! Please open issues or pull requests if you'd like to improve or extend the project.

## Contact
(Include your preferred contact information or links here)
