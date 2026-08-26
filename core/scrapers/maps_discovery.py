from re import search
import time
from playwright.sync_api import sync_playwright
from core.schemas import DiscoveredBusiness

def discover_businesses(niche: str, location: str, batch_size: int = 5, delay: float = 1.5) -> list[DiscoveredBusiness]:
    query=f"{niche} in {location}"
    results: list[DiscoveredBusiness]=[]

    with sync_playwright() as p:
        browser=p.chromium.launch(headless=False)
        page=browser.new_page()

        search_url=f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        page.goto(search_url,timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # the results of the google maps
        results_panel=page.locator('div[role="feed"]')

        # scroll a few times to load more cards into DOM
    
        for _ in range(4):
            results_panel.evaluate("(el) => el.scrollBy(0,1500)")
            page.wait_for_timeout(1500)
        

        # each business results is an <a> card inside the feed
        cards=page.locator('div[role="feed"] > div > div > a').all()

        for card in cards[:batch_size]:
            try:
                card.click()
                page.wait_for_timeout(1500)

                name=card.get_attribute("aria-label")
                card.click()
                page.wait_for_timeout(2500)
                rating=_safe_rating(page)
                phone=_safe_phone(page)
                website=_safe_website(page)


                if not name:
                    continue

                business = DiscoveredBusiness(
                    business_name=name,
                    rating=rating,
                    phone_number=phone,
                    website_url=website,
                    niche=niche,
                    location=location,
                )

                results.append(business)

            except Exception as e:
                print(f"Skipped one card due to error : {e}")
        
        browser.close()

    return results

def _safe_text(page,selector: str) -> str | None:
    try:
        el=page.locator(selector).first
        return el.inner_text().strip()

    except Exception:
        return None

def _safe_rating(page) -> float | None:
    try:
        text=page.locator('span[aria-label*="stars"]').first
        return float(text)
    except Exception:
        return None

def _safe_phone(page) -> str | None:
    try:
        el=page.locator('button[data-item-id^="phone"]').first
        label=el.get_attribute("aria-label")
        if label:
            return label.replace("Phone:", "").strip()
        return None
    except Exception:
        return None

def _safe_website(page) -> str | None:
    try:
        el=page.locator('a[data-item-id="authority"]').first
        return el.get_attribute("href")
    except Exception:
        return None

if __name__ == "__main__":
    businesses=discover_businesses("restaurants","Banglore",batch_size=3)
    for b in businesses:
        print(b)




    