# "https://www.carrefour.fr/api/user/secured/loyalty/orders/receipts?loyaltyCardNumber=9135720000750920831&loyaltyCardType=LOYALTY"


# Ce second script réutilise la session sauvegardée pour accéder directement à la page sécurisée, ou pour faire des requêtes authentifiées à l’API.

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # ou False pour debug
    context = browser.new_context(storage_state="state.json")
    page = context.new_page()

    page.goto("https://www.carrefour.fr/mon-compte/mes-achats/en-magasin", wait_until="networkidle", timeout=60000)

    # Optionnel : affiche le contenu pour vérifier
    print("✅ Page chargée. Voici un extrait du contenu :\n")
    print(page.content()[:1000])  # affiche les 1000 premiers caractères du HTML

    # Si tu veux aussi intercepter une requête API :
    # tu peux observer les requêtes dans le DevTools, ou faire un `page.route()` / `page.on('response')`
    
    browser.close()
