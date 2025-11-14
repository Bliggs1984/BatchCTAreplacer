import os
import subprocess
import re
import math
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ffmpeg_installed():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_video_dimensions(video_path):
    try:
        cmd = f'ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=width,height -of csv=p=0 "{video_path}"'
        output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split(',')
        return int(output[0]), int(output[1])
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting video dimensions for {video_path}: {e}")
        return None, None

def calculate_aspect_ratio(width, height):
    gcd = math.gcd(width, height)
    return f"{width//gcd}:{height//gcd}"

def find_cta_video(cta_folder, cta_name, aspect_ratio):
    aspect_suffix = aspect_ratio.replace(':', 'x')
    for file in os.listdir(cta_folder):
        if file.lower().endswith(f'_{aspect_suffix}.mp4') and cta_name.lower().replace(' ', '') in file.lower().replace(' ', ''):
            return os.path.join(cta_folder, file)
    return None

def get_video_info(video_path):
    try:
        cmd = f'ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=width,height,r_frame_rate -of csv=p=0 "{video_path}"'
        output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().split(',')
        width, height, framerate = output
        return int(width), int(height), framerate
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting video info for {video_path}: {e}")
        return None, None, None

def check_nvenc_availability():
    cmd = "ffmpeg -encoders | grep nvenc"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return "nvenc" in result.stdout

def replace_end_of_video_keep_audio(input_video, cta_video, output_video, overlay_duration=4, use_gpu=False):
    duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_video}"'
    duration = float(subprocess.check_output(duration_cmd, shell=True).decode('utf-8').strip())
    
    main_width, main_height, framerate = get_video_info(input_video)
    if main_width is None:
        logging.error(f"Error processing video {input_video}, skipping...")
        return

    overlay_start = max(0, duration - overlay_duration)
    
    filter_complex = (
        f"[0:v]split=2[v1][v2];"
        f"[v1]trim=0:{overlay_start},setpts=PTS-STARTPTS[main];"
        f"[v2]trim={overlay_start},setpts=PTS-STARTPTS[base];"
        f"[1:v]trim=0:{overlay_duration},setpts=PTS-STARTPTS,scale={main_width}:{main_height}:force_original_aspect_ratio=decrease,pad={main_width}:{main_height}:(ow-iw)/2:(oh-ih)/2[cta];"
        f"[base][cta]overlay=shortest=1[overlaid];"
        f"[main][overlaid]concat=n=2:v=1:a=0[outv]"
    )
    
    if use_gpu:
        gpu_options = '-hwaccel cuda -c:v h264_nvenc -preset p4 -qp 23'
    else:
        gpu_options = '-c:v libx264 -preset medium -crf 23'

    cmd = (
        f'ffmpeg -i "{input_video}" -accurate_seek -i "{cta_video}" '
        f'-filter_complex "{filter_complex}" '
        f'-map "[outv]" -map 0:a -c:a copy '
        f'{gpu_options} '
        f'-r {framerate} '
        f'"{output_video}"'
    )
    
    logging.info(f"Executing FFmpeg command: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    logging.info(f"FFmpeg stdout: {result.stdout}")
    logging.warning(f"FFmpeg stderr: {result.stderr}")
    
    if not os.path.exists(output_video):
        logging.error(f"Error: Failed to create output video: {output_video}")
    else:
        logging.info(f"Successfully created: {output_video}")

def process_videos(main_videos, cta_base_folder, output_base_folder, overlay_duration, use_gpu, progress_callback=None):
    languages = [d for d in os.listdir(cta_base_folder) if os.path.isdir(os.path.join(cta_base_folder, d))]
    
    for main_video in main_videos:
        main_width, main_height, _ = get_video_info(main_video)
        if main_width is None:
            logging.error(f"Skipping video due to error: {main_video}")
            if progress_callback:
                progress_callback()
            continue
        main_aspect_ratio = calculate_aspect_ratio(main_width, main_height)
        
        base_name = os.path.splitext(os.path.basename(main_video))[0]
        
        for language in languages:
            lang_code = language[:2].upper()
            language_folder = os.path.join(cta_base_folder, language)
            
            ctas = [d for d in os.listdir(language_folder) if os.path.isdir(os.path.join(language_folder, d))]

            for cta_name in ctas:
                cta_code = ''.join(word[0].upper() for word in cta_name.split())
                cta_folder = os.path.join(language_folder, cta_name)
                
                cta_video = find_cta_video(cta_folder, cta_name, main_aspect_ratio)
                
                if not cta_video:
                    logging.warning(f"CTA video not found for {cta_name} with aspect ratio {main_aspect_ratio} in {cta_folder}")
                    if progress_callback:
                        progress_callback()
                    continue
                
                output_folder = os.path.join(output_base_folder, language, cta_name)
                os.makedirs(output_folder, exist_ok=True)
                
                new_filename = generate_new_filename(base_name, lang_code, cta_code, main_aspect_ratio)
                output_path = os.path.join(output_folder, new_filename)
                
                counter = 1
                while os.path.exists(output_path):
                    new_filename = f"{os.path.splitext(new_filename)[0]}_{counter}.mp4"
                    output_path = os.path.join(output_folder, new_filename)
                    counter += 1
                
                replace_end_of_video_keep_audio(main_video, cta_video, output_path, overlay_duration=overlay_duration, use_gpu=use_gpu)
                if progress_callback:
                    progress_callback()

def generate_new_filename(base_name, lang_code, cta_code, aspect_ratio):
    segments = base_name.split('_')
    
    cutoff_index = len(segments)
    length_segment = None
    for i, seg in enumerate(segments):
        if seg in ['DN', 'MN', 'SN', 'PN'] or len(seg) == 2:
            cutoff_index = i
            break
        if seg.endswith('s') and seg[:-1].isdigit():
            length_segment = seg
    
    new_segments = segments[:cutoff_index]
    
    new_segments.extend([lang_code, cta_code])
    
    if length_segment:
        new_segments.append(length_segment)
    
    if not any(seg.replace('x', ':') == aspect_ratio for seg in new_segments):
        new_segments.append(aspect_ratio.replace(':', 'x'))
    
    new_name = '_'.join(new_segments) + '.mp4'
    
    return sanitize_filename(new_name)

def sanitize_filename(filename):
    unsafe_chars = r'[<>:"/\\|?*]'
    return re.sub(unsafe_chars, '', filename)
