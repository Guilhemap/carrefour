from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # interface visible
    context = browser.new_context()
    page = context.new_page()

    # Aller sur la page login ou directement sur les achats (ce qui redirigera vers le login)
    page.goto("https://www.carrefour.fr/mon-compte/mes-achats/en-magasin")

    input("➡️ Connecte-toi manuellement avec XXX / YYY puis appuie sur Entrée pour continuer...")

    # Sauvegarde de l’état (cookies + localStorage + sessionStorage)
    context.storage_state(path="state.json")
    print("✅ Session sauvegardée dans 'state.json'")

    browser.close()
