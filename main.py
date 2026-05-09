import subprocess
import json
import asyncio
from playwright.async_api import async_playwright


# i dont know why used async, the docs say use and i use
async def runs():
    print("hi")
    async with async_playwright() as p:
        print("run headless...")
        browser_headless = await p.chromium.launch(executable_path='../Downloads/chrome-linux64/chrome',headless = True, proxy={'server':'http://127.0.0.1:8085'})
        page_headless = await browser_headless.new_page()
        
        await page_headless.goto('https://cin.red/')
        
        await page_headless.mouse.wheel(0,1000)
        print("page title: ",await age_headless.title())
        
        await page_headless.screenshot(path="re.png")
        print("save screenshot 're.png'")
        
        await browser_headless.close()

def curl_request(url):
    
    command = ['curl', '--proxy','http://127.0.0.1:8085', url]

    result = subprocess.run(command, capture_output=True, text=True)
    
    return result.stdout

response = curl_request('https://cin.red/v/236851')

asyncio.run(runs())
print(response)
