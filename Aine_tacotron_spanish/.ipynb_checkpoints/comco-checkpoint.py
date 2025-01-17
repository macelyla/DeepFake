import pandas as pd
import os
# Define the root path
root_path = "/srv/storage/idmctal@storage1.nancy.grid5000.fr/2023/m2/adrelingyte/data/spanish/cml_tts_dataset_spanish_v0.1"

# Set the output path based on your specific configuration
output_path = os.path.join(root_path)
path='/home/mcelylatorre/workspace/tmp'
# Path to your "train.csv" file
train_csv_path = os.path.join(root_path, "train.csv")

column_names = ['wav_filename','wav_filesize','transcript','transcript_wav2vec','levenshtein','duration','num_words','client_id', 'path']

df = pd.read_csv('/srv/storage/idmctal@storage1.nancy.grid5000.fr/2023/m2/adrelingyte/data/spanish/cml_tts_dataset_spanish_v0.1/train.csv', delimiter='|')
df.columns = column_names



# Load the "train.csv" file into a DataFrame
# Construct full paths to the audio files using the "wav_filename" column
df['full_audio_path'] = df['wav_filename'].apply(lambda x: os.path.join(root_path, x))


import os
from trainer import Trainer, TrainerArgs
from TTS.config import BaseAudioConfig, BaseDatasetConfig
from TTS.tts.configs.fast_speech_config import FastSpeechConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.forward_tts import ForwardTTS
from TTS.tts.utils.speakers import SpeakerManager
from TTS.tts.utils.text.tokenizer import TTSTokenizer
from TTS.utils.audio import AudioProcessor
from TTS.tts.models.tacotron2 import Tacotron2
import torch

print(torch.cuda.is_available())
USE_CUDA = torch.cuda.is_available()

# GlowTTSConfig: all model related values for training, validating and testing.
from TTS.tts.configs.tacotron2_config import Tacotron2Config

output_path = "/srv/storage/idmctal@storage1.nancy.grid5000.fr/2023/m2/adrelingyte/data/spanish/cml_tts_dataset_spanish_v0.1"

if not os.path.exists(output_path):
    os.makedirs(output_path)
    

# Create a BaseDatasetConfig object
dataset_config = BaseDatasetConfig(formatter="custom_formatter", meta_file_train="train.csv", path=os.path.join(output_path))

# Load the dataset using your custom formatter
train_samples, eval_samples = load_tts_samples([dataset_config], eval_split=True)

audio_config = BaseAudioConfig(
    sample_rate=24000,
    do_trim_silence=True,
    trim_db=23.0,
    signal_norm=False,
    mel_fmin=0.0,
    mel_fmax=8000,
    spec_gain=1.0,
    log_func="np.log",
    ref_level_db=20,
    preemphasis=0.0,
)

# Configure your Tacotron2 model
config = Tacotron2Config(
    batch_size=32,
    eval_batch_size=16,
    num_loader_workers=4,
    num_eval_loader_workers=4,
    precompute_num_workers=4,
    run_eval=True,
    test_delay_epochs=-1,
    epochs=100,
    use_phonemes=True,
    phonemizer="gruut",
    phoneme_language="es-es",
    phoneme_cache_path=os.path.join(path, "phoneme_cache2"),
    print_step=25,
    print_eval=False,
    mixed_precision=True,
    output_path=path,
    datasets=[dataset_config],
    use_speaker_embedding=True,
    min_text_len=0,
    max_text_len=500,
    min_audio_len=100000,  # Adjust this value based on your requirements
    max_audio_len=400000,  # Adjust this value based on your requirements
)

config.audio.fft_size = 2048
config.audio.win_length = 1200
config.audio.hop_length = 256
config.audio.num_mels = 80

ap = AudioProcessor.init_from_config(audio_config)

# Initialize the TTSTokenizer
tokenizer, config = TTSTokenizer.init_from_config(config)


speaker_manager = SpeakerManager()
speaker_manager.set_ids_from_data(train_samples + eval_samples, parse_key="speaker_name")
config.num_speakers = speaker_manager.num_speakers

model = Tacotron2(config, ap, tokenizer, speaker_manager=speaker_manager)

trainer = Trainer(
    TrainerArgs(), config, output_path, model=model, train_samples=train_samples, eval_samples=eval_samples
)

trainer.fit()