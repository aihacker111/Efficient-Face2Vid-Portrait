# coding: utf-8

"""
config dataclass used for inference
"""

import os
import requests
from dataclasses import dataclass
from typing import Literal, Tuple
from tqdm import tqdm

import torch.cuda

from .base_config import PrintableConfig, make_abs_path

# Define the URLs for the model files
MODEL_URLS = {
    'live_portrait': {
        'checkpoint_F': 'https://huggingface.co/myn0908/Live-Portrait-Models/resolve/main/appearance_feature_extractor.pth?download=true',
        'checkpoint_M': 'https://huggingface.co/myn0908/Live-Portrait-Models/resolve/main/motion_extractor.pth?download=true',
        'checkpoint_G': 'https://huggingface.co/myn0908/Live-Portrait-Models/resolve/main/spade_generator.pth?download=true',
        'checkpoint_W': 'https://huggingface.co/myn0908/Live-Portrait-Models/resolve/main/warping_module.pth?download=true',
        'checkpoint_S': 'https://huggingface.co/myn0908/Live-Portrait-Models/resolve/main/stitching_retargeting_module.pth?download=true'},
    'insight_face': {
        'landmark': 'https://huggingface.co/myn0908/Live-Portrait-Models/resolve/main/landmark.onnx?download=true'
    }

}


# Function to download a file from a URL and save it locally
def downloading(url, outf):
    if not os.path.exists(outf):
        print(f"Downloading checkpoint to {outf}")
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(outf, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, something went wrong")
        print(f"Downloaded successfully to {outf}")


# Download the models and save them in the current working directory
current_dir = os.getcwd()
model_paths = {}
for main_key, sub_dict in MODEL_URLS.items():
    dir_path = os.path.join(current_dir, 'face2vid_weights', main_key)
    os.makedirs(dir_path, exist_ok=True)
    model_paths[main_key] = {}
    for sub_key, url in sub_dict.items():
        filename = url.split('/')[-1].split('?')[0]
        save_path = os.path.join(dir_path, filename)
        downloading(url, save_path)
        model_paths[main_key][sub_key] = save_path


@dataclass(repr=False)  # use repr from PrintableConfig
class InferenceConfig(PrintableConfig):
    models_config: str = make_abs_path('./models.yaml')  # portrait animation config
    checkpoint_F: str = model_paths['live_portrait']['checkpoint_F']  # path to checkpoint
    checkpoint_M: str = model_paths['live_portrait']['checkpoint_M']  # path to checkpoint
    checkpoint_G: str = model_paths['live_portrait']['checkpoint_G']  # path to checkpoint
    checkpoint_W: str = model_paths['live_portrait']['checkpoint_W']  # path to checkpoint
    checkpoint_S: str = model_paths['live_portrait']['checkpoint_S']  # path to checkpoint

    flag_use_half_precision: bool = True  # whether to use half precision
    flag_lip_zero: bool = True  # whether let the lip to close state before animation, only take effect when flag_eye_retargeting and flag_lip_retargeting is False
    lip_zero_threshold: float = 0.03
    flag_eye_retargeting: bool = False
    flag_lip_retargeting: bool = False
    flag_stitching: bool = True  # we recommend setting it to True!
    flag_relative: bool = True  # whether to use relative motion
    flag_pasteback: bool = True  # whether to paste-back/stitch the animated face cropping from the face-cropping space to the original image space
    flag_do_crop: bool = True  # whether to crop the source portrait to the face-cropping space
    flag_do_rot: bool = True  # whether to conduct the rotation when flag_do_crop is True

    anchor_frame: int = 0  # set this value if find_best_frame is True

    input_shape: Tuple[int, int] = (256, 256)  # input shape
    output_format: Literal['mp4', 'gif'] = 'mp4'  # output video format
    output_fps: int = 30  # fps for output video
    crf: int = 15  # crf for output video

    flag_write_result: bool = True  # whether to write output video
    mask_crop = None
    flag_write_gif: bool = False
    size_gif: int = 256
    ref_max_shape: int = 1280
    ref_shape_n: int = 2

    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    device_id: int = 0
    flag_do_crop: bool = True  # whether to crop the source portrait to the face-cropping space
    flag_do_rot: bool = True  # whether to conduct the rotation when flag_do_crop is True
    # crop config
    ckpt_landmark: str = model_paths['insight_face']['landmark']
    ckpt_face: str = dir_path
    dsize: int = 512  # crop size
    scale: float = 2.3  # scale factor
    vx_ratio: float = 0  # vx ratio
    vy_ratio: float = -0.125  # vy ratio +up, -down
