import subprocess
import json
import asyncio
import re
import ast
from playwright.async_api import async_playwright


#TODO
# curl download all link

#TODO for best
# create loop when id input code show me thum and y/n to download



# i dont know why used async, the docs say use and i use
async def runs():
    print("hi")
    async with async_playwright() as p:
        print("run headless...")
        browser_headless = await p.chromium.launch(executable_path='../Downloads/chrome-linux64/chrome',headless = True, proxy={'server':'http://127.0.0.1:8085'})
        page_headless = await browser_headless.new_page()
        
        await page_headless.goto('https://cin.red/v/649127')
        
        await page_headless.mouse.wheel(0,1000)
        print("page title: ",await page_headless.title())
        
        
        last_scrolled_position = 0
        no_move_count = 0 
        
        while True:
            current_h = await page_headless.evaluate("window.pageYOffset + window.innerHeight")
            await page_headless.evaluate("window.scrollBy(0, 1500)")

            new_h = await page_headless.evaluate("window.pageYOffset + window.innerHeight")
            if new_h == current_h:
                no_move_count += 1
            else:
                no_move_count = 0
                print("is scrolling...", new_h)

            if no_move_count == 3:
                print("is end")
                break
            await asyncio.sleep(.2)
        
        await page_headless.screenshot(path="re.png")
        print("save screenshot 're.png'")

        await browser_headless.close()

def curl_request(url):
    
    command = ['curl', '--proxy','http://127.0.0.1:8085', url]

    result = subprocess.run(command, capture_output=True, text=True)
    
    return result.stdout

def extract_link(data):
    pattern = r'\{"t":.[^{}]*"h":....?\}?'
    
    matches = re.findall(pattern, data, re.DOTALL)
    
    return matches

def pure_link(data):
    finall = []
    for d in data:
        temp = ast.literal_eval(d.replace("}}", "}"))
        finall.append(temp.get("t"))
    return finall

def curl_dl(links):
    
    for i in links:
        command = ['curl', '--proxy','http://127.0.0.1:8085','-O', i]
        result = subprocess.run(command, capture_output=True, text=True)
        print(result)


response = curl_request('https://cin.red/v/649127')

pack = extract_link(response)

link = pure_link(pack)

print(*link, sep="\n")

asyncio.run(runs())

curl_dl(link)






