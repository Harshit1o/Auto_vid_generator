# Video Generator Bot

An automated tool that creates videos using VEED.io's AI text-to-video generator.

## Description

This project uses Playwright to automate the video creation process on VEED.io. It generates creative prompts using OpenAI's GPT model, navigates to VEED.io, and automatically creates a video based on the prompt. The script handles the entire workflow including:

- Generating a creative prompt with OpenAI
- Navigating to VEED.io
- Entering the prompt and selecting "Voice Only" style
- Handling the video creation process
- Downloading the final video as an MP4 file

## Requirements

- Python 3.8+
- Playwright
- OpenAI Python SDK
- python-dotenv

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/video-gen-bot.git
   cd video-gen-bot
   ```

2. Install dependencies:
   ```
   pip install playwright openai python-dotenv
   playwright install
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key
   - Add your Google login credentials for VEED.io

## Usage

Run the script:
```
python new_vid_gen.py
```

The script will:
1. Generate a creative prompt
2. Launch a browser window (visible)
3. Navigate through the VEED.io interface
4. Download the finished video as `veed_video.mp4`

## Files

- `new_vid_gen.py` - The main script with improved error handling
- `vid_gen.py` - Original version of the script
- `.env` - Configuration file for API keys and credentials
- `.env.example` - Example environment configuration

## Security Note

Never commit your `.env` file to GitHub. It's included in `.gitignore` to prevent accidental exposure of your API keys and credentials.

## License

MIT