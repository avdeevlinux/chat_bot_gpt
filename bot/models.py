from bs4 import BeautifulSoup

# Properly handle Playwright import with type-safe approach
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available, using fallback HTTP scraper (JS content missing)")
    sync_playwright = None  # Satisfy linter with explicit None assignment

MODELS = {}
user_models = {}  # Add missing user_models dictionary to fix import error

def populate_models():
    global MODELS
    MODELS.clear()
    url = "https://bothub.ru/models"

    # Simplified scraping approach using direct model name check
    html = None
    if PLAYWRIGHT_AVAILABLE and sync_playwright is not None:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Use networkidle to ensure full page load
                page.goto(url, wait_until="networkidle")
                
                # Wait for initial content to load
                page.wait_for_timeout(3000)
                
                # Click initial "Показать больше" to reveal tariff options
                show_more_btn = page.locator('button:has-text("Показать больше")')
                if show_more_btn.is_visible(timeout=2000):
                    show_more_btn.click()
                    print("Clicked initial 'Показать больше' button")
                    page.wait_for_timeout(3000)
                
                # Handle possible cookie consent banner
                cookie_accept_btn = page.locator('button:has-text("Принимаю")').or_(page.locator('button:has-text("Согласен")'))
                if cookie_accept_btn.is_visible(timeout=3000):
                    cookie_accept_btn.click()
                    print("Accepted cookies")
                    page.wait_for_timeout(1000)
                
                # Select FREE tariff first to see free models
                tariff_dropdown = page.locator('button:has-text("Тариф")')
                if tariff_dropdown.is_visible(timeout=5000):
                    # Use force click since elements might be intercepting
                    tariff_dropdown.click(force=True)
                    print("Clicked tariff dropdown")
                    page.wait_for_timeout(1000)
                    
                    # Select FREE tariff option
                    free_tariff = page.locator('div:has-text("DELUXE")').first
                    if free_tariff.is_visible(timeout=3000):
                        free_tariff.click(force=True)
                        print("Selected DELUXE tariff")
                        page.wait_for_timeout(3000)  # Wait for table update
                    else:
                        print("Warning: FREE tariff option not found")
                else:
                    print("Warning: Tariff dropdown not found")
                
                # Wait for possible dynamic content after tariff selection
                page.wait_for_timeout(5000)
                
                # Expand all models by clicking "Показать ещё" until no more
                while True:
                    # Click "Показать ещё" if visible
                    show_more_btn = page.locator('button:has-text("Показать ещё")')
                    if show_more_btn.is_visible():
                        show_more_btn.click(force=True)
                        print("Clicked 'Показать ещё' button")
                        page.wait_for_timeout(4000)  # Longer wait for loading
                    else:
                        break
                
                html = page.content()
                browser.close()
            print("Playwright scraping completed")
        except Exception as e:
            print(f"Playwright scraping error: {e}")
    
    if not html:
        # Fallback to HTTP (works only for static content)
        try:
            import httpx
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                html = resp.text
            print("Fallback HTTP scraping used")
        except Exception as e:
            print(f"HTTP fallback error: {e}")
            return

    soup = BeautifulSoup(html, "html.parser")
    
    # Simple approach: find first table (more reliable than title matching)
    table = soup.find('table')
    
    if not table:
        print("Models table not found")
        return
    
    # Process table rows - skip header
    rows = table.find_all('tr')[1:]
    
    # Find models containing 'free' in model name
    for row in rows:
        cells = row.find_all('td')
        if not cells:
            continue
            
        # Get model name from first column
        model_cell = cells[0]
        raw_model_text = model_cell.get_text(strip=True)
        model_name = raw_model_text.lower()
        print(f"Checking model: '{raw_model_text}'")
        
        # Check if model has free indicator based on URL structure
        a_tag = model_cell.find('a')
        is_free = False
        
        # First check - look for :free in URL path
        if a_tag:
            href = a_tag.get('href', '')
            print(f"  Checking URL: {href}")
            if ':free' in href or '/free/' in href:
                print(f"  Found explicit free flag in URL")
                is_free = True
        
        # Second check - look for free indicators in model name
        if not is_free:
            free_patterns = [
                'free', 'бесплат', 'freemium', '0 ₽', 'бесплатно', 'free-tier',
                '(free)', '[free]', 'free edition', 'free version'
            ]
            
            for pattern in free_patterns:
                if pattern in model_name:
                    print(f"  Found free pattern: '{pattern}' in name")
                    is_free = True
                    break
        
        # Third check - check price columns for free indicators
        if not is_free and len(cells) >= 5:
            # Check last column (DELUXE price)
            price_cell = cells[-1]
            price_text = price_cell.get_text(strip=True).lower()
            # print(f"  Checking price: '{price_text}'")
            if '0' in price_text or 'бесплат' in price_text or 'free' in price_text:
                print(f"  Found free price indicator")
                is_free = True
        
        if is_free:
            # Extract name and create proper slug format
            name = raw_model_text
            if a_tag:
                name = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                slug = href.split('/')[-1].rstrip('/')
                
                # Ensure proper slug format
                if not any(slug.endswith(suffix) for suffix in [':free', '/free', '-free']):
                    slug += ':free'
            else:
                # Fallback to text content with normalized slug
                slug = name.lower().replace(' ', '-').replace(':free', '') + ':free'
            
            # Add to MODELS dict
            MODELS[slug] = name
            # print(f"Added model: {slug} -> {name}")

    # Fallback to hardcoded models if scraping found nothing
    if not MODELS:
        print("No models scraped, using fallback list")
        fallback_models = {
            "gpt-4.1-nano:free": "GPT-4.1-Nano",
            "gpt-5-pro:free": "GPT-5-Pro",
            "gpt-4o-mini:free": "GPT-4o-Mini",
            "gemini-2.0-flash-exp:free": "Gemini-2.0-Flash-Exp",
            "hermes-3-llama-3.1-70b:free": "Hermes-3-Llama-3.1-70B",
            "qwen3-4b:free": "Qwen3-4B",
            "qwen3-235b-a22b:free": "Qwen3-235B-A22B",
            "llama-3.2-3b-instruct:free": "Llama-3.2-3B-Instruct",
            "llama-3.3-70b-instruct:free": "Llama-3.3-70B-Instruct",
            "mistral-7b-instruct:free": "Mistral-7B-Instruct",
            "deepseek-r1t-chimera:free": "DeepSeek-R1T-Chimera",
            "grok-4.1-fast:free": "Grok-4.1-Fast",
            "phi-3-mini-128k-instruct:free": "Phi-3-Mini-128K-Instruct",
            "command-r-08-2024:free": "Command-R-08-2024",
            "gemini-2.5-flash-lite:free": "Gemini-2.5-Flash-Lite"
        }
        MODELS.update(fallback_models)

populate_models()
# print("MODELS populated:", list(MODELS.keys()))
