import asyncio
from playwright.async_api import async_playwright
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# GPT prompt generator
async def generate_prompt():
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Give me a short creative prompt for a text-to-video AI generator."}]
    )
    return response.choices[0].message.content.strip()

# Main automation function
async def run():
    prompt = await generate_prompt()
    print(f"Prompt: {prompt}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Go to VEED
        await page.goto("https://www.veed.io/tools/ai-video-generator/text-to-video", timeout=60000)
        await page.wait_for_load_state("domcontentloaded")

        # Step 2: Click on "Try AI Video Generator"
        await page.get_by_text("Try AI Video Generator").click()

        # Step 3: Wait for textbox and enter prompt
        await page.wait_for_selector("textarea")
        await page.fill("textarea", prompt)
        await page.click("button:has-text('Generate Video')")

        # Step 4: Switch presenter to "Voice Only"
        await page.wait_for_selector("text=Avatar")  # Avatar option
        await page.click("text=Avatar")
        await page.click("text=Voice Only")

        # Step 5: Click continue twice
        await page.click("text=Continue")
        await page.click("text=Continue")

        # Step 6: Wait for rendering (~1.5 mins)
        await page.wait_for_selector("text=Done", timeout=120000)
        await page.click("text=Done")

        # Step 7: Export video
        await page.wait_for_selector("text=Export Video", timeout=30000)
        await page.click("text=Export Video")

        # Step 8: Wait for rendering to complete (~1 min)
        await page.wait_for_selector("button[aria-label='Download']", timeout=60000)

        # Step 9: Download MP4
        with page.expect_download() as download_info:
            await page.click("button[aria-label='Download']")
            await page.click("text=MP4")  # Select MP4 format
        download = await download_info.value
        await download.save_as("veed_video.mp4")
        print("✅ Video downloaded as veed_video.mp4")

        await context.close()
        await browser.close()

asyncio.run(run())
