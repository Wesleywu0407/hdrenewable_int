import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console messages
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        
        # Capture page errors
        page.on("pageerror", lambda exc: print(f"PageError: {exc.name} {exc.message}\n{exc.stack}"))
        
        print("Opening page...")
        await page.goto("file:///home/jonathan/hdrenewable_int/dashboard_exported.html", wait_until="networkidle")
        
        await asyncio.sleep(30)  # give it time to load Pyodide
        
        await browser.close()

asyncio.run(main())
