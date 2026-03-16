import asyncio
from typing import Dict, Any, List
from playwright.async_api import async_playwright

async def run_axe_core(url: str) -> Dict[str, Any]:
    """
    Runs Axe-core accessibility auditing on the given URL via Playwright.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle")
            
            # Inject axe-core
            await page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.0/axe.min.js")
            
            # Run axe
            results = await page.evaluate("async () => await axe.run({ runOnly: ['wcag2a', 'wcag2aa'] })")
            
            violations = []
            for violation in results.get("violations", []):
                for node in violation.get("nodes", []):
                    violations.append({
                        "id": violation["id"],
                        "impact": violation["impact"],
                        "description": violation["description"],
                        "help": violation["help"],
                        "helpUrl": violation["helpUrl"],
                        "html": node.get("html", ""),
                        "target": node.get("target", [])
                    })
                    
            return {
                "success": True,
                "url": url,
                "violation_count": len(violations),
                "violations": violations
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()

def run_dom_accessibility(url: str) -> Dict[str, Any]:
    return asyncio.run(run_axe_core(url))
