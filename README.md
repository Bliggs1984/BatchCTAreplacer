# Batch Video CTA Processor

## Project Overview

This project is a Python script that provides a graphical user interface (GUI) for batch processing videos. It's designed to replace the end of a main video with a Call-to-Action (CTA) video. The application leverages the powerful `ffmpeg` command-line tool for all video manipulation tasks, and its GUI is built using Python's built-in `tkinter` library.

The script intelligently handles multiple languages and CTA variations. It automatically selects the correct CTA video based on the main video's aspect ratio and the dynamically discovered language and CTA type from your folder structure. For faster processing, it also supports optional GPU acceleration using NVIDIA's NVENC.

## Features

*   **Batch Video Processing:** Process multiple main videos efficiently.
*   **Dynamic CTA Integration:** Seamlessly replace video endings with custom CTA videos.
*   **Aspect Ratio Matching:** Automatically selects the correct CTA video based on the main video's aspect ratio.
*   **Multi-Language Support:** Organizes and processes videos based on language-specific CTA folders.
*   **Dynamic Discovery:** Languages and CTA types are discovered directly from your folder structure, eliminating the need for manual configuration files.
*   **GPU Acceleration:** Optional support for NVIDIA NVENC for faster video encoding.
*   **User-Friendly GUI:** Intuitive interface built with `tkinter` for easy operation.
*   **FFmpeg Pre-check:** Verifies `ffmpeg` installation at startup to prevent runtime errors.
*   **Safer FFmpeg Usage:** FFmpeg and ffprobe invocations use list-style subprocess arguments (no `shell=True`) and correctly place input-level vs output-level options to avoid parsing errors.

## Prerequisites

*   **Python 3.x:** Ensure you have a compatible version of Python installed.
*   **FFmpeg:** A complete, cross-platform solution to record, convert, and stream audio and video. It must be installed and accessible from your system's PATH. The application includes a startup check for `ffmpeg` and will display an error if it's not found.

### Installing FFmpeg (if not already installed)

If you encounter an error stating that `ffprobe` or `ffmpeg` is not recognized, you need to install FFmpeg and add it to your system's PATH.

**Using Winget (Recommended for Windows):**

1.  Open PowerShell as Administrator.
2.  Run the following command to install FFmpeg:
    ```bash
    winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    ```
3.  The `winget` installer should automatically add FFmpeg to your system's PATH. If not, you may need to manually add the `bin` directory of the FFmpeg installation to your PATH environment variable. A typical installation path for `winget` might be similar to `C:\Users\<YourUsername>\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_<some_hash>\ffmpeg-<version>-full_build\bin`.

**Manual Installation (Windows):**

1.  **Download FFmpeg:**
    *   Visit [gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
    *   Download `ffmpeg-release-essentials.7z`.
2.  **Extract the Files:**
    *   Extract the contents of the `.7z` file to a location like `C:\ffmpeg`.
3.  **Add FFmpeg to System PATH:**
    *   Press `Windows + X` and select "System," or search for "Environment Variables" and select "Edit the system environment variables."
    *   Click "Environment Variables."
    *   Under "System variables," select `Path` and click "Edit."
    *   Click "New" and add the path to the `bin` folder (e.g., `C:\ffmpeg\bin`).
    *   Click "OK" on all dialogs.
4.  **Verify Installation:**
    *   Open a **new** Command Prompt window.
    *   Type `ffmpeg -version`. If successful, you'll see version information.

## Usage

1.  **Prepare your CTA Videos:**
    Organize your CTA videos in a specific directory structure within your designated CTA folder:
    ```
    CTAS/
    ├── English/
    │   ├── Download Now/
    │   │   └── Download Now_16x9.mp4
    │   └── Play Now/
    │       └── Play Now_16x9.mp4
    ├── Spanish/
    │   ├── Download Now/
    │   │   └── Download Now_16x9.mp4
    │   └── Play Now/
    │       └── Play Now_16x9.mp4
    └── ...
    ```
    The script will dynamically discover languages (e.g., "English", "Spanish") and CTA types (e.g., "Download Now", "Play Now") from this structure. CTA video filenames should follow the format `{cta_name}_{aspect_ratio}.mp4` (e.g., `Download Now_16x9.mp4`).

2.  **Run the Application:**
    Execute the following command in your terminal:
    ```bash
    python main.py
    ```
    This will launch the GUI application.

3.  **Select Folders and Videos:**
    *   **Main Videos:** Click "Select Main Videos" and choose the video files you want to process.
    *   **CTA Folder:** Click "Select CTA Folder" and select the root directory where your language and CTA folders are organized (e.g., `CTAS/`).
    *   **Output Folder:** Click "Select Output Folder" and choose where you want the processed videos to be saved.
    *   **CTA Duration:** Enter the duration in seconds for the CTA video to be overlaid at the end of the main video.
    *   **Use GPU Acceleration:** Check this box if you have an NVIDIA GPU and want to use NVENC for faster encoding.

4.  **Process Videos:**
    Click the "Process Videos" button to start the batch processing. A progress window will appear, showing the status of the operation.

## Development Conventions

*   **Video File Naming:** CTA videos should be named in the format `{cta_name}_{aspect_ratio}.mp4` (e.g., `Download Now_16x9.mp4`).
*   **Directory Structure:** The application dynamically discovers languages and CTA types. The expected structure for CTA videos is `CTAS/<Language>/<CTA Type>/<CTA Video>`.
*   **Code Style:** The code follows standard Python conventions (PEP 8).

Notes for contributors / maintainers:
- FFmpeg command construction: build argument lists (e.g., `['ffmpeg','-i', input, ...]`) instead of shell strings to avoid quoting/escaping bugs and security issues.
- Input-level options (like `-hwaccel cuda`) must appear before the `-i` they apply to; encoder options (like `-c:v h264_nvenc`) belong with the output options.
- NVENC detection: `video_processor.check_nvenc_availability()` checks `ffmpeg -encoders` output for `nvenc` (no shell `grep`), which is more cross-platform.
- Settings: the GUI persists last-used CTA folder, Output folder, CTA duration, and GPU checkbox state to `settings.json` located next to `main.py`.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open-source and available under the [MIT License](LICENSE).
