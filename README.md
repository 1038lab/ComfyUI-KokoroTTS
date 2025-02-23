# ComfyUI-KokoroTTS

ComfyUI-KokoroTTS is a powerful text-to-speech node for ComfyUI. It leverages the Kokoro TTS framework to convert text into natural-sounding speech, supporting multiple languages and voices. The node is easy to integrate and customize, making it perfect for various applications.

## Features

### Kokoro TTS Node
- **Multiple languages and voices support**
- **Adjustable speech rate and volume**
- **High-quality voice synthesis**
- **All voices are setting in Languages.json**

## Installation

### Method 1: Install via ComfyUI-Manager
Search for `ComfyUI-KokoroTTS` in ComfyUI-Manager and install.
Then install dependencies:
```bash
./ComfyUI/python_embeded/python -m pip install -r requirements.txt
```

### Method 2: Manual Clone Installation
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/1038lab/ComfyUI-KokoroTTS.git

cd ComfyUI-KokoroTTS
./ComfyUI/python_embeded/python -m pip install -r requirements.txt
```
### manually download models
```bash
https://huggingface.co/1038lab/KokoroTTS/tree/main
```
download and save save all files to `TTS/KokoroTTS`

### more languages support:
By default, only English is supported. To add more languages, edit `Languages.json` to add more languages support. remove `#` language name in the json file. restart ComfyUI.

## Usage Examples

### Basic Usage
```python
from KokoroTTS import KokoroTTS

tts = KokoroTTS()
audio_output = tts.tts("Hello, world!", voice="default_voice")
```

### Using in ComfyUI Workflow
1. Add Kokoro TTS node to workflow
2. Input text and select voice
3. Adjust speed and volume (optional)
4. Connect to Save Audio node for export

## Available Voices

Available voices can be loaded using the `load_voices` method. See config.json for detailed voice list.

## Requirements
- Python packages (see requirements.txt)
- CUDA compatible GPU (optional, for faster processing)

## License
GNU GPLv3

## Credits
- Kokoro TTS Framework
