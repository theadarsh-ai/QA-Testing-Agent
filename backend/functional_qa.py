import asyncio
from typing import Dict, Any, List
from playwright.async_api import Page, async_playwright

class FunctionalQAAgent:
    def __init__(self, url: str):
        self.url = url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.logs = []

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        self.page = await self.context.new_page()
        
        # Capture console logs
        self.page.on("console", lambda msg: self.logs.append({"type": "console", "text": msg.text}))
        
        # Navigate
        await self.page.goto(self.url, wait_until="networkidle")

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Tool to type text into an input field."""
        try:
            element = self.page.locator(selector).first
            await element.wait_for(state="visible", timeout=3000)
            await element.fill(text)
            return {"success": True, "action": f"Typed '{text}' into '{selector}'"}
        except Exception as e:
            return {"success": False, "error": f"Failed to type in '{selector}': {str(e)}"}

    async def click_element(self, selector: str) -> Dict[str, Any]:
        """Tool to click a button, link, or element."""
        try:
            element = self.page.locator(selector).first
            await element.wait_for(state="visible", timeout=3000)
            await element.click()
            await self.page.wait_for_load_state("networkidle", timeout=3000)
            return {"success": True, "action": f"Clicked '{selector}'"}
        except Exception as e:
            return {"success": False, "error": f"Failed to click '{selector}': {str(e)}"}

    async def check_element_exists(self, selector: str) -> Dict[str, Any]:
        """Tool to verify if an element exists on the page."""
        try:
            element = self.page.locator(selector).first
            is_visible = await element.is_visible(timeout=2000)
            if is_visible:
                return {"success": True, "action": f"Element '{selector}' is visible on screen."}
            else:
                return {"success": False, "error": f"Element '{selector}' was not found."}
        except Exception as e:
            return {"success": False, "error": f"Error checking '{selector}': {str(e)}"}

    async def get_page_text(self) -> str:
        """Helper to get text content for the LLM to read."""
        if not self.page:
            return ""
        try:
            return await self.page.evaluate("document.body.innerText")
        except:
            return ""

def run_functional_test(url: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Executes a sequence of functional test actions.
    actions format: [{"task": "type", "selector": "#email", "text": "test@test.com"}, ...]
    """
    async def _run():
        agent = FunctionalQAAgent(url)
        results = []
        try:
            await agent.start()
            for action in actions:
                task = action.get("task")
                if task == "type":
                    res = await agent.type_text(action["selector"], action["text"])
                elif task == "click":
                    res = await agent.click_element(action["selector"])
                elif task == "check":
                    res = await agent.check_element_exists(action["selector"])
                else:
                    res = {"success": False, "error": f"Unknown task: {task}"}
                
                results.append(res)
                if not res["success"]:
                    break # Stop on first failure
            
            final_text = await agent.get_page_text()
            return {
                "success": all(r["success"] for r in results),
                "steps": results,
                "logs": agent.logs,
            }
        finally:
            await agent.stop()

    return asyncio.run(_run())
