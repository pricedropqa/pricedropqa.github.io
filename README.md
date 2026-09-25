# PriceDrop QA – സെറ്റപ്പ് ഗൈഡ് (Setup Guide)

## ഫോൾഡറിലെ ഫയലുകൾ
| ഫയൽ | എന്താണ് |
|---|---|
| `index.html` | ആപ്പ് മുഴുവൻ ഈ ഒരൊറ്റ ഫയലിലാണ് |
| `data.csv` | സാമ്പിൾ വിലകൾ (കടകളുടെ പേരുകൾ ഡെമോ മാത്രം) |
| `manifest.json` | ഫോണിൽ ആപ്പായി ഇൻസ്റ്റാൾ ചെയ്യാനുള്ള വിവരങ്ങൾ |
| `sw.js` | ഓഫ്‌ലൈനായും വേഗത്തിലും തുറക്കാൻ |
| `icons/` | ആപ്പ് ഐക്കൺ (Canva-യിൽ സ്വന്തമായി ഉണ്ടാക്കി ഇതേ പേരിൽ മാറ്റാം) |

---

## സ്റ്റെപ്പ് 1: Google Sheet ഉണ്ടാക്കുക (ഡാറ്റ)
1. sheets.google.com തുറന്ന് പുതിയ ഷീറ്റ് ഉണ്ടാക്കുക. പേര്: `PriceDrop Data`.
2. **File → Import → Upload** ചെയ്ത് `data.csv` തിരഞ്ഞെടുക്കുക → "Replace current sheet".
3. ഇനി മുതൽ വിലകൾ ഈ ഷീറ്റിൽ മാറ്റിയാൽ മതി. ഓരോ വരിയും = **ഒരു കടയിലെ ഒരു മോഡൽ**.

### കോളങ്ങൾ (column names മാറ്റരുത്)
| കോളം | ഉദാഹരണം | കുറിപ്പ് |
|---|---|---|
| type | Phone | Phone / Tablet / Watch / Earbuds / Accessory |
| tier | Flagship | Flagship / Mid-Range / Budget / Low End |
| brand | Samsung | |
| model | Galaxy A56 | ഒരേ മോഡൽ എല്ലാ കടകളിലും **ഒരേ സ്പെല്ലിംഗിൽ** എഴുതണം |
| storage | 256GB | |
| shop | കടയുടെ പേര് | |
| area | Al Sadd | |
| price | 1399 | അക്കം മാത്രം |
| old_price | 1699 | ഓപ്ഷണൽ, ഡിസ്കൗണ്ട് % ഇതിൽ നിന്ന് കണക്കാക്കും |
| offer | Free cover | ഓപ്ഷണൽ |
| in_stock | Yes / No | |
| whatsapp | 974XXXXXXXX | കൺട്രി കോഡ് 974 ഉൾപ്പെടെ, + ഇല്ലാതെ |
| phone | 974XXXXXXXX | |
| map_url | Google Maps ലിങ്ക് | Maps-ൽ കട തുറന്ന് Share → Copy link |
| updated | 2026-09-25 | വില അവസാനം ചെക്ക് ചെയ്ത തീയതി |

## സ്റ്റെപ്പ് 2: ഷീറ്റ് പബ്ലിഷ് ചെയ്യുക
1. ഷീറ്റിൽ **File → Share → Publish to web**.
2. "Entire document" എന്നതിന് പകരം നിങ്ങളുടെ ഷീറ്റ് ടാബ് തിരഞ്ഞെടുക്കുക, ഫോർമാറ്റ് **Comma-separated values (.csv)**.
3. **Publish** അമർത്തി കിട്ടുന്ന ലിങ്ക് കോപ്പി ചെയ്യുക.
4. `index.html` ഒരു എഡിറ്ററിൽ (VS Code / Notepad) തുറന്ന് ഈ വരി കണ്ടെത്തുക:
   ```
   const SHEET_CSV_URL = "";
   ```
   ലിങ്ക് ഉള്ളിൽ പേസ്റ്റ് ചെയ്യുക:
   ```
   const SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/....../pub?output=csv";
   ```
5. സേവ് ചെയ്യുക. ⚠️ പബ്ലിഷ് ചെയ്ത ഷീറ്റ് ആർക്കും കാണാം. അതിൽ രഹസ്യ വിവരങ്ങൾ വെക്കരുത്.

> ഷീറ്റിൽ മാറ്റം വരുത്തിയാൽ വെബ്സൈറ്റിൽ വരാൻ Google-ന് ഏകദേശം 5 മിനിറ്റ് എടുക്കും.

## സ്റ്റെപ്പ് 3: GitHub Pages-ൽ ഫ്രീ ആയി ഹോസ്റ്റ് ചെയ്യുക
1. github.com-ൽ ഫ്രീ അക്കൗണ്ട് ഉണ്ടാക്കുക. യൂസർനെയിം ഉദാ: `pricedropqa`.
2. മുകളിൽ **+ → New repository**. പേര്: `pricedropqa`. **Public** തിരഞ്ഞെടുത്ത് Create.
3. **"uploading an existing file"** ലിങ്കിൽ ക്ലിക്ക് ചെയ്ത് ഈ ഫോൾഡറിലെ എല്ലാ ഫയലുകളും `icons` ഫോൾഡറും ഡ്രാഗ് ചെയ്ത് ഇടുക → **Commit changes**.
4. **Settings → Pages** → Source: "Deploy from a branch" → Branch: `main`, ഫോൾഡർ `/ (root)` → **Save**.
5. 1–2 മിനിറ്റിനുള്ളിൽ ലിങ്ക് റെഡി: `https://pricedropqa.github.io/pricedropqa/`

(Netlify വേണമെങ്കിൽ: app.netlify.com/drop തുറന്ന് ഫോൾഡർ മുഴുവൻ ഡ്രാഗ് ചെയ്താൽ മതി.)

## സ്റ്റെപ്പ് 4: ഫോണിൽ ആപ്പായി ഇൻസ്റ്റാൾ ചെയ്യുക
- **Android (Chrome):** ലിങ്ക് തുറക്കുക → മുകളിലെ "Install app" ബട്ടൺ, അല്ലെങ്കിൽ ⋮ മെനു → *Add to Home screen*.
- **iPhone (Safari):** ലിങ്ക് തുറക്കുക → Share ബട്ടൺ → *Add to Home Screen*.

---

## മാറ്റങ്ങൾ വരുത്താൻ
- **പുതിയ കാറ്റഗറി / ഡിവൈസ് ടൈപ്പ്:** `index.html`-ലെ `TIERS`, `TYPES` ലിസ്റ്റുകളിൽ ചേർക്കുക.
- **നിറങ്ങൾ:** `index.html`-ന്റെ മുകളിലെ `--brand`, `--accent`.
- **പേര് മാറ്റാൻ (TechFinder ആക്കണമെങ്കിൽ):** `index.html`, `manifest.json` എന്നിവയിൽ "PriceDrop" എന്ന് തിരഞ്ഞ് മാറ്റുക.
- **index.html മാറ്റി വീണ്ടും അപ്‌ലോഡ് ചെയ്യുമ്പോൾ:** `sw.js`-ലെ `pricedrop-v1` എന്നത് `pricedrop-v2` ആക്കുക. എങ്കിലേ ഫോണുകളിൽ പുതിയ വേർഷൻ വരൂ.

## അടുത്ത പടികൾ (പിന്നീട്)
- **Google Analytics (ഫ്രീ):** എത്ര പേർ വരുന്നു, ഏത് കടയ്ക്ക് എത്ര WhatsApp/Call ടാപ്പ് കിട്ടി എന്നിവ അറിയാൻ. ആപ്പിൽ ഈ ട്രാക്കിംഗ് (`trackLead`) ഇതിനകം തയ്യാറാണ്. Analytics കോഡ് ചേർത്താൽ മതി. കടകളെ പെയ്ഡ് പ്ലാനിലേക്ക് മാറ്റാൻ ഈ കണക്കുകളാണ് പ്രധാനം.
- **കടകൾക്ക് സ്വയം വില അപ്ഡേറ്റ് ചെയ്യാൻ:** ഒരു Google Form ഉണ്ടാക്കി അതിന്റെ മറുപടികൾ ഇതേ ഷീറ്റിലേക്ക് വരുത്താം.
- **സ്വന്തം ഡൊമെയ്ൻ (.qa):** ബിസിനസ് ലൈസൻസ് എടുത്ത ശേഷം GitHub Pages → Custom domain-ൽ ചേർക്കാം.

---

## Version 2 – പുതിയ കോളങ്ങൾ (ഓപ്ഷണൽ)
Google Sheet-ൽ `updated` കോളത്തിന് ശേഷം ഈ 7 കോളങ്ങൾ ചേർക്കുക (പേര് കൃത്യമായി ഇങ്ങനെ തന്നെ):

| കോളം | ഉദാഹരണം | കുറിപ്പ് |
|---|---|---|
| image | images/galaxy-s25-ultra.jpg | ഫോണിന്റെ ചിത്രം. GitHub-ലെ `images` ഫോൾഡറിലെ ഫയൽ, അല്ലെങ്കിൽ ഒരു https ലിങ്ക്. ഒഴിഞ്ഞു കിടന്നാൽ ബ്രാൻഡ് നിറത്തിലുള്ള ചിത്രം തനിയെ വരും |
| ram | 12GB | |
| display | 6.9" AMOLED 120Hz | |
| camera | 200MP main | |
| battery | 5000mAh | |
| chipset | Snapdragon 8 Elite | |
| youtube | https://youtu.be/... | നിങ്ങളുടെ റിവ്യൂ വീഡിയോ – ഫോൺ പേജിൽ ചുവന്ന ബട്ടൺ ആയി വരും |

**ഒരു ഫോണിന് ഒരു വരിയിൽ മാത്രം** ഇവ പൂരിപ്പിച്ചാൽ മതി. ആ ഫോണിന്റെ എല്ലാ കടകൾക്കും അത് ബാധകമാകും.

### ചിത്രങ്ങൾ ചേർക്കാൻ
1. ചിത്രങ്ങൾ ചതുരാകൃതിയിൽ (ഉദാ: 800×800), വെള്ള/സുതാര്യ ബാക്ക്ഗ്രൗണ്ടിൽ, `.jpg`/`.png`/`.webp` ആയി സേവ് ചെയ്യുക. പേരിൽ സ്പേസ് വേണ്ട: `galaxy-s25-ultra.jpg`.
2. GitHub-ൽ **Add file → Upload files** → ചിത്രങ്ങൾ ഒരു `images` ഫോൾഡറിലാക്കി ആ ഫോൾഡർ ഡ്രാഗ് ചെയ്യുക → Commit.
3. ഷീറ്റിലെ `image` കോളത്തിൽ `images/galaxy-s25-ultra.jpg` എന്ന് എഴുതുക.

### index.html-ലെ മറ്റ് സെറ്റിംഗുകൾ
- `OWNER_WHATSAPP` – നിങ്ങളുടെ WhatsApp നമ്പർ (974XXXXXXXX) ഇട്ടാൽ "Shop owner? List your prices for free" ബാനറും ലിങ്കും വരും.
- `BANNERS` – ഹോം സ്ക്രീനിലെ ബാനറുകൾ. പിന്നീട് ഈ സ്ഥലം ബ്രാൻഡുകൾക്ക് പരസ്യമായി വിൽക്കാം.
- `TYPES` – പുതിയ ടാബ് ചേർക്കാൻ ഒരു വരി: `{key:"Laptop", icon:"💻", en:"Laptops", ar:"لابتوب"}`
