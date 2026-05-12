import subprocess
import argparse
import asyncio
import re
import ast
from playwright.async_api import async_playwright


#TODO for best
# create loop when id input code show me thum and y/n to download



# i dont know why used async, the docs say use and i use
async def runs(code ,firstscreen):
    async with async_playwright() as p:
        print("run headless...")
        browser_headless = await p.chromium.launch(headless = True)
        page_headless = await browser_headless.new_page()
        
        await page_headless.goto('https://cin.red/v/'+code)

        if firstscreen:

            await asyncio.sleep(2)
            
            #await page_headless.mouse.wheel(0,100)
            print("page title: ",await page_headless.title())
            
            await page_headless.screenshot(path="re.png")
            print("save screenshot 're.png'")
            
            await browser_headless.close()

        else:
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
                await asyncio.sleep(.5)
            print("is ready for download please 10 sec wait")
            await asyncio.sleep(10)

            await browser_headless.close()

def curl_request(url):
    
    command = ['curl', url]

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
        command = ['curl','-O', i]
        result = subprocess.run(command, capture_output=True, text=True)
        print(result)





parser = argparse.ArgumentParser()
parser.add_argument("arg1", type=str, help="First argument")
parser.add_argument("arg2", type=bool, help="Second argument")
args = parser.parse_args()
response = curl_request('https://cin.red/v/'+args.arg1)

pack = extract_link(response)

link = pure_link(pack)

print(*link, sep="\n")

asyncio.run(runs(args.arg1, args.arg2))

curl_dl(link)

