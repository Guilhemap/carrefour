# Ce script permet de contourner la protection Cloudflare d'un site web,
# de récupérer les cookies de session, puis d'utiliser Playwright pour naviguer sur le site
# et télécharger des factures au format PDF.


import asyncio
import os
import json
from pydoll.browser import Chrome
from playwright.async_api import async_playwright

async def bypass_cloudflare_and_get_cookies():
    async with Chrome() as browser:
        tab = await browser.start()
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to("https://www.carrefour.fr/mon-compte/mes-achats/en-magasin")

        print("➡️ Connecte-toi manuellement dans le navigateur visible")
        input("✅ Appuie sur Entrée une fois connecté...")

        cookies = await tab.get_cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        print("✅ Cookies sauvegardés. Fermeture de Pydoll...")

async def run_playwright_with_cookies_and_scrape():
    os.makedirs("factures", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        with open("cookies.json", "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto("https://www.carrefour.fr/mon-compte/mes-achats/en-magasin")

        print("🧭 Page chargée avec Playwright")
        input("➡️ Vérifie que tout est bien affiché. Appuie sur Entrée pour continuer...")

        buttons = await page.query_selector_all(
            "button.pl-button.receipt-list-item__button.pl-button--tone-main.pl-button--variation-tertiary"
        )
        print(f"🔍 {len(buttons)} boutons trouvés")

        for i, btn in enumerate(buttons):
            print(f"📥 Ouverture du ticket #{i+1}")

            async with page.expect_popup() as popup_info:
                await btn.click()

            new_page = await popup_info.value
            await new_page.wait_for_load_state("networkidle")

            pdf_url = new_page.url
            print(f"🔗 URL de la facture : {pdf_url}")

            # Effectue une requête directe via context.request
            try:
                response = await context.request.get(pdf_url)
                if response.ok:
                    content = await response.body()
                    filename = f"facture_{i+1}.pdf"
                    with open(os.path.join("factures", filename), "wb") as f:
                        f.write(content)
                    print(f"✅ Téléchargé : factures/{filename}")
                else:
                    print(f"❌ Erreur HTTP {response.status} sur {pdf_url}")
            except Exception as e:
                print(f"❌ Exception lors du téléchargement : {e}")

            await new_page.close()

        await browser.close()
        print("🎉 Tous les fichiers ont été téléchargés.")

async def main():
    await bypass_cloudflare_and_get_cookies()
    await run_playwright_with_cookies_and_scrape()

asyncio.run(main())
