import asyncio
import urllib.parse
from typing import Dict, Any, List
from playwright.async_api import async_playwright

SECURITY_PAYLOADS = {
    "xss": ["<script>alert(1)</script>", "\"-prompt(8)-\""],
    "sqli": ["' OR 1=1--", "admin' --"],
}

async def run_security_fuzz(url: str) -> Dict[str, Any]:
    """
    Very basic security fuzzer. It looks for input fields on a given URL and 
    attempts to send common payloads to check for unhandled exceptions or reflections.
    """
    issues = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. URL Parameter Fuzzing
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed.query)
            if query:
                for key in query.keys():
                    for p_type, payloads in SECURITY_PAYLOADS.items():
                        test_query = query.copy()
                        test_query[key] = payloads[0]
                        test_url = parsed._replace(query=urllib.parse.urlencode(test_query, doseq=True)).geturl()
                        
                        response = await page.goto(test_url, wait_until="networkidle")
                        if response and response.status >= 500:
                            issues.append({
                                "type": f"potential_{p_type}",
                                "severity": "critical",
                                "description": f"HTTP {response.status} when injecting payload into URL parameter '{key}'",
                                "url": url
                            })
            else:
                await page.goto(url, wait_until="networkidle")

            # 2. Basic Input Field Fuzzing
            inputs = await page.locator("input[type='text'], input[type='email'], input[type='search'], textarea").all()
            for index, input_el in enumerate(inputs[:3]): # Test up to 3 inputs to save time
                is_visible = await input_el.is_visible()
                if not is_visible: continue
                
                try:
                    name_attr = await input_el.get_attribute("name") or f"input_{index}"
                    
                    # Test SQLi payload
                    await input_el.fill(SECURITY_PAYLOADS["sqli"][0])
                    # We don't submit to avoid trashing real DBs, but 
                    # a full implementation would submit and check response.
                    
                    issues.append({
                        "type": "input_found",
                        "severity": "info",
                        "description": f"Found input field '{name_attr}'. Ready for deeper penetration testing.",
                        "url": url
                    })
                except Exception:
                    continue

            return {
                "success": True,
                "url": url,
                "security_issues": issues
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()

def run_security_scan(url: str) -> Dict[str, Any]:
    return asyncio.run(run_security_fuzz(url))
