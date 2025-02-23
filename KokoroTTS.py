import os
import torch
import json
from kokoro import KPipeline
import folder_paths
import requests
from huggingface_hub import hf_hub_download

KOKORO_MODEL_DIR = os.path.join("TTS", "KokoroTTS")
folder_paths.add_model_folder_path("kokoro", os.path.join(folder_paths.models_dir, KOKORO_MODEL_DIR))

AVAILABLE_FILES = {
    "model": {
        "repo_id": "1038lab/KokoroTTS",
        "files": {
            "kokoro-v1_0.pth": "kokoro-v1_0.pth",
            "config.json": "config.json"
        }
    },
    "voices": {
        "repo_id": "1038lab/KokoroTTS",
        "path": "voices"
    }
}

class BaseModelLoader:
    def __init__(self):
        self.pipeline = None
        self.base_cache_dir = os.path.join(folder_paths.models_dir, KOKORO_MODEL_DIR)
        
    def check_model_cache(self):
        if not os.path.exists(self.base_cache_dir):
            return False, "Model directory not found"
        
        missing_files = []
        for filename in AVAILABLE_FILES["model"]["files"].keys():
            if not os.path.exists(os.path.join(self.base_cache_dir, AVAILABLE_FILES["model"]["files"][filename])):
                missing_files.append(filename)
        
        if missing_files:
            return False, f"Missing model files: {', '.join(missing_files)}"
            
        return True, "Model cache verified"
    
    def download_model(self):
        try:
            os.makedirs(self.base_cache_dir, exist_ok=True)
            print(f"Downloading Kokoro model files...")
            
            for filename, save_name in AVAILABLE_FILES["model"]["files"].items():
                print(f"Downloading {filename}...")
                hf_hub_download(
                    repo_id=AVAILABLE_FILES["model"]["repo_id"],
                    filename=filename,
                    local_dir=self.base_cache_dir,
                    local_dir_use_symlinks=False
                )
                    
            return True, "Model files downloaded successfully"
            
        except Exception as e:
            return False, f"Error downloading model files: {str(e)}"

    def ensure_voice(self, voice):
        voice_dir = os.path.join(self.base_cache_dir, "voices")
        os.makedirs(voice_dir, exist_ok=True)
        
        voice_file = f"{voice}.pt"
        voice_path = os.path.join(voice_dir, voice_file)
        
        if not os.path.exists(voice_path):
            try:
                print(f"Downloading voice: {voice_file}")
                hf_hub_download(
                    repo_id=AVAILABLE_FILES["voices"]["repo_id"],
                    filename=f"{AVAILABLE_FILES['voices']['path']}/{voice_file}",
                    local_dir=self.base_cache_dir,
                    local_dir_use_symlinks=False
                )
            except Exception as e:
                print(f"Failed to download {voice_file}: {str(e)}")
                if os.path.exists(voice_path):
                    os.remove(voice_path)
                raise ValueError(f"Failed to download voice file: {voice_file}")
        
        return voice_path

class KokoroTTS(BaseModelLoader):
    def __init__(self):
        super().__init__()

    @staticmethod
    def load_voices():
        """Load available voices for Kokoro TTS."""
        config_path = os.path.join(os.path.dirname(__file__), "Languages.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        voices = list(config["kokorotts_voices"].keys())
        voice_names = config["kokorotts_voices"]
        
        # 构建语言代码映射
        lang_codes = {}
        for code, prefixes in config["kokorotts_lang_codes"].items():
            for prefix in prefixes:
                for voice_id in voices:
                    if voice_id.startswith(prefix):
                        lang_codes[voice_id] = code
        
        return (voices, voice_names, lang_codes)

    DEFAULT_VOICES, VOICE_NAMES, VOICE_LANG_CODES = load_voices.__func__()

    @classmethod
    def INPUT_TYPES(s):
        voice_ids = s.DEFAULT_VOICES
        voice_names = [s.VOICE_NAMES[v] for v in voice_ids]
        
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "placeholder": "Enter text to convert to speech"}),
                "voice": (voice_names, { 
                    "default": voice_names[0],
                    "tooltip": "Select a voice style"
                }),
            },
            "optional": {
                "speed": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.1, "tooltip": "Speech rate (0.5 to 2.0)"}),
                "volume": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.1, "tooltip": "Audio volume"})
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "tts"
    CATEGORY = "🧪AILab/🔊Audio"

    def load_model(self):
        if self.pipeline is None:
            cache_status, message = self.check_model_cache()
            if not cache_status:
                print(f"Cache check: {message}")
                print("Downloading required model files...")
                download_status, download_message = self.download_model()
                if not download_status:
                    raise ValueError(download_message)
                print("Model files downloaded successfully")

    def get_pipeline(self, voice):
        lang_code = self.VOICE_LANG_CODES[voice]
        
        try:
            if lang_code == 'j':
                import misaki
            elif lang_code == 'z':
                import misaki
                import ordered_set
            elif lang_code in ['e', 'f', 'h', 'i', 'p']:  # European languages
                import subprocess
                subprocess.run(['espeak-ng', '--version'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
        except (ImportError, FileNotFoundError) as e:
            lang_names = {
                'e': 'Spanish', 'f': 'French', 'h': 'Hindi',
                'i': 'Italian', 'j': 'Japanese', 'p': 'Portuguese',
                'z': 'Chinese'
            }
            
            if lang_code in ['j', 'z'] and isinstance(e, ImportError):
                raise ImportError(
                    f"\n=== {lang_names[lang_code]} Voice Support Required ===\n"
                    f"To use {lang_names[lang_code]} voices, please:\n"
                    "1. Open requirements.txt in your ComfyUI folder\n"
                    "2. Remove the '#' in front of the required packages\n"
                    "3. Run: pip install -r requirements.txt\n"
                    "4. Restart ComfyUI\n"
                    "================================"
                )

            elif lang_code in ['e', 'f', 'h', 'i', 'p']:
                print(f"\nWarning: espeak-ng not installed. Some words might not be pronounced correctly.")
                print("To install espeak-ng:")
                print("- Windows: Download from https://github.com/espeak-ng/espeak-ng/releases")
                print("- Linux: sudo apt-get install espeak-ng")
                print("- MacOS: brew install espeak\n")

        try:
            if self.pipeline is None or getattr(self.pipeline, 'lang_code', None) != lang_code:
                self.pipeline = KPipeline(lang_code=lang_code)
        except Exception as e:
            print(f"Error creating pipeline for language {lang_code}: {str(e)}")
            raise

        return self.pipeline

    def tts(self, text, voice, speed=1.0, volume=1.0):
        """Convert text to speech using Kokoro model."""
        if not text.strip():
            raise ValueError("Text cannot be empty")
            
        try:
            # 从显示名称获取对应的voice_id
            voice_id = next(k for k, v in self.VOICE_NAMES.items() if v == voice)
            
            self.load_model()
            pipeline = self.get_pipeline(voice_id)
            self.ensure_voice(voice_id)
            
            generator = pipeline(
                text.strip(),
                voice=voice_id,  # 使用voice_id而不是显示名称
                speed=speed,
                split_pattern=r'\n+'
            )
            
            audio_segments = []
            for _, _, audio_data in generator:
                if torch.is_tensor(audio_data):
                    audio_data = audio_data.numpy()
                audio_segments.append(torch.from_numpy(audio_data).float())
            
            if audio_segments:
                waveform = torch.cat(audio_segments, dim=0)
                if len(waveform.shape) == 1:
                    waveform = waveform.unsqueeze(0)
                
                waveform = waveform / (waveform.abs().max() + 1e-6) * volume
                
                audio_output = {
                    "waveform": waveform.unsqueeze(0),
                    "sample_rate": 24000
                }
                
                return (audio_output,)
            
            raise Exception("No audio generated")
            
        except Exception as e:
            print(f"Kokoro TTS Error: {str(e)}")
            empty_waveform = torch.zeros((1, 1, 16000))
            return ({"waveform": empty_waveform, "sample_rate": 16000},)

NODE_CLASS_MAPPINGS = {
    "KokoroTTS": KokoroTTS
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KokoroTTS": "Kokoro TTS 🔊"
}
