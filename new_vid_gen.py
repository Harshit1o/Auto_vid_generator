import asyncio
from playwright.async_api import async_playwright
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get credentials from environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# GPT prompt generator
async def generate_prompt():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Give me a short creative prompt for a text-to-video AI generator."}]
    )
    return response.choices[0].message.content.strip()

# Helper function for more resilient element waiting and clicking
async def wait_and_click(page, selector, timeout=30000, retry_count=3):
    for attempt in range(retry_count):
        try:
            await page.wait_for_selector(selector, state="visible", timeout=timeout)
            await page.click(selector)
            print(f"✅ Successfully clicked: {selector}")
            return True
        except Exception as e:
            if attempt < retry_count - 1:
                print(f"⚠️ Attempt {attempt+1} failed for {selector}: {str(e)}. Retrying...")
                await asyncio.sleep(2)  # Small delay before retry
            else:
                print(f"❌ All attempts failed for {selector}: {str(e)}")
                return False
    return False

# Main automation function
async def run():
    prompt = await generate_prompt()
    print(f"Prompt: {prompt}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Go to VEED
        try:
            await page.goto("https://www.veed.io/ai-text-to-video", timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            print("✅ Loaded VEED.io")
        except Exception as e:
            print(f"❌ Error loading page: {str(e)}")
            return
            
        # Step 3: Wait for textbox and enter prompt
        try:
            await page.wait_for_selector("textarea", timeout=30000)
            await page.fill("textarea", prompt)
            await wait_and_click(page, "button:has-text('Generate Video')")
        except Exception as e:
            print(f"❌ Error entering prompt: {str(e)}")
            return

        # Step 4: Wait for options to appear (with retry mechanism)
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                # Wait for Voice Only option
                await page.wait_for_selector("text='Voice Only'", timeout=15000)
                await page.click("text='Voice Only'")
                print("✅ Selected Voice Only")
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"⚠️ Attempt {attempt+1} failed to find Voice Only option: {str(e)}. Retrying...")
                    await asyncio.sleep(3)  # Give more time before retry
                else:
                    print(f"❌ Failed to find Voice Only option after {max_attempts} attempts")
                    # Try to continue anyway
        
        # Step 5: Click first "Continue" button
        if not await wait_and_click(page, "text='Continue'"):
            print("⚠️ Trying alternative method for first Continue button")
            continue_buttons = await page.query_selector_all("button")
            clicked = False
            for button in continue_buttons:
                button_text = await button.text_content()
                if "Continue" in button_text:
                    await button.click()
                    print("✅ Found and clicked Continue button (alternative method)")
                    clicked = True
                    break
            if not clicked:
                print("❌ Could not find any Continue button")
                return

        # Step 6: Wait a bit before looking for the second "Continue" button
        await asyncio.sleep(5)  # Give time for the UI to update
        
        # Handle the second "Continue" button
        if not await wait_and_click(page, "text='Continue'", timeout=20000):
            print("⚠️ Trying alternative method for second Continue button")
            continue_buttons = await page.query_selector_all("button")
            clicked = False
            for button in continue_buttons:
                button_text = await button.text_content()
                if "Continue" in button_text:
                    await button.click()
                    print("✅ Found and clicked Continue button (alternative method)")
                    clicked = True
                    break
            if not clicked:
                print("⚠️ Could not find second Continue button, trying to proceed anyway")

        # Step X: Accept Terms and Conditions if prompt appears
        try:
            await page.wait_for_selector("text=Accept and Continue", timeout=100000)
            await page.click("text=Accept and Continue")
            print("✅ Accepted terms and conditions.")
        except:
            print("ℹ️ Terms popup didn't appear, continuing...")

        # Step Y: Wait for processing to complete and click the 'Done' button
        try:
            # Wait longer for the Done button to appear
            await page.wait_for_selector("text=Done", timeout=10000) 
            await page.click("text=Done")
            print("✅ Clicked 'Done'")
        except Exception as e:
            print(f"❌ Error finding Done button: {str(e)}")
            # Try alternative selectors
            try:
                done_buttons = await page.query_selector_all("button")
                for button in done_buttons:
                    button_text = await button.text_content()
                    if "Done" in button_text:
                        await button.click()
                        print("✅ Found and clicked Done button (alternative method)")
                        break
            except Exception as inner_e:
                print(f"❌ Alternative approach for Done button failed: {str(inner_e)}")

        # Step 9: Export video
        if not await wait_and_click(page, "text=Export Video", timeout=30000):
            print("❌ Could not click Export Video button")
            return

        # Sign in step
        try:
            await page.wait_for_selector("text='Log in'", timeout=10000)
            await page.click("text='Log in'")
            
            async with page.expect_popup() as popup_info:
                await page.click("text='Sign in with Google'")
            google_popup = await popup_info.value
            await google_popup.wait_for_load_state()

            # Fill Google login fields (if not already logged in)
            await google_popup.fill("input[type='email']", EMAIL)
            await google_popup.click("button:has-text('Next')")

            # Password entry
            await google_popup.wait_for_selector("input[type='password']", timeout=10000)
            await google_popup.fill("input[type='password']", PASSWORD)
            await google_popup.click("button:has-text('Next')")
            print("✅ Completed Google sign-in")
        except Exception as e:
            print(f"⚠️ Sign-in process issue: {str(e)}")
            print("Continuing with the process assuming already logged in")

        # Step 10: Wait for rendering to complete (~1 min)
        try:
            await page.wait_for_selector("button[aria-label='Download']", timeout=120000)  # 2 minutes
            print("✅ Download button is now visible")
        except Exception as e:
            print(f"❌ Error waiting for download button: {str(e)}")
            return

        # Step 11: Download MP4
        try:
            with page.expect_download() as download_info:
                await page.click("button[aria-label='Download']")
                await page.click("text=MP4")  # Select MP4 format
            download = await download_info.value
            await download.save_as("veed_video.mp4")
            print("✅ Video downloaded as veed_video.mp4")
        except Exception as e:
            print(f"❌ Error downloading video: {str(e)}")

        await context.close()
        await browser.close()

asyncio.run(run())
