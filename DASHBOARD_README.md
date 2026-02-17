# Jablotron Volta Dashboard pro Home Assistant

Profesionální dashboard pro řízení a monitoring kotle Jablotron Volta.

## 🎯 Funkce dashboardu

Dashboard je rozdělen do **7 tabů** pro přehledné ovládání:

### 📊 **Tab 1: Přehled**
- Hlavní ovládání kotle (termostat karta)
- Přehled všech důležitých teplot
- Stav kotle a aktivní segmenty
- Grafy historie teplot

### 📈 **Tab 2: Ekvitermní křivka**
- Nastavení ekvitermní regulace (Slope, Offset, Composite Ratio)
- Zobrazení venkovních teplot (Composite, Damped)
- Gauge ukazující výslednou teplotu vody
- Tipy pro doladění nastavení

### 🔥 **Tab 3: CH1 Topný okruh**
- Kompletní nastavení topného okruhu CH1
- Teploty vody (vstup, vratná, setpoint)
- Ekvitermní parametry
- Pokročilé funkce (Optimal Start, Hysteresis)
- Doporučené nastavení pro podlahové topení s chytrými termostaty

### ⚙️ **Tab 4: Systém**
- Režim kotle
- Systémové informace (CPU, baterie, tlak)
- Topné segmenty
- Gauge pro sledování tlaku v systému

### 🚿 **Tab 5: TUV (Teplá užitková voda)**
- Aktuální a požadovaná teplota TUV
- Nastavení min/max teplot
- Graf historie
- Gauge zobrazení

### 🎛️ **Tab 6: Všechna nastavení**
- Kompletní přehled všech parametrů
- Pro pokročilé uživatele
- Varování před nesprávným nastavením

### 🔍 **Tab 7: Diagnostika**
- Všechny dostupné teploty
- Modbus a systémové informace
- Multi-graf pro ladění
- Debug informace

---

## 📥 Instalace dashboardu

### Metoda 1: Nový dashboard (doporučeno)

1. **Otevři Home Assistant**
2. Přejdi do **Settings** → **Dashboards**
3. Klikni na **+ ADD DASHBOARD** (vpravo dole)
4. Vyber **"New dashboard from scratch"**
5. Zadej název: `Jablotron Volta`
6. Klikni na ⋮ (tři tečky) → **Edit Dashboard**
7. Klikni na ⋮ znovu → **Raw configuration editor**
8. **Smaž vše** a zkopíruj celý obsah souboru `dashboard_jablotron_volta.yaml`
9. Klikni **SAVE**
10. Hotovo! 🎉

### Metoda 2: Přidat do existujícího dashboardu

1. Otevři existující dashboard
2. Klikni **Edit Dashboard** (✏️ vpravo nahoře)
3. Klikni **⋮** → **Raw configuration editor**
4. **Přidej views** z `dashboard_jablotron_volta.yaml` do sekce `views:`
5. Klikni **SAVE**

---

## 🎨 Přizpůsobení dashboardu

### Změna názvů entit

Pokud máš entity s jinými názvy, uprav je v YAML:

```yaml
# Příklad: Změna entity
- entity: sensor.outdoor_temp_composite
  name: Venkovní teplota (Composite)
```

Nahraď `sensor.outdoor_temp_composite` za tvůj skutečný název entity.

### Přidání/odebrání karet

Dashboard je modulární - můžeš snadno:
- **Odstranit karty**, které nepotřebuješ
- **Přidat nové karty** (tlačítko "+ ADD CARD" v edit módu)
- **Změnit pořadí** karet (drag & drop v edit módu)

### Změna barev/vzhledu

Home Assistant používá tvoje globální téma. Pro změnu:
- **Settings** → **Profile** → **Theme**
- Vyber z dostupných témat nebo nainstaluj vlastní

---

## 🔧 Doporučené doplňky

### Pro lepší grafy:

Nainstaluj **ApexCharts Card** (HACS):

```bash
# V HACS:
Frontend → Explore & Download Repositories → "ApexCharts Card"
```

Pak můžeš použít pokročilé grafy místo standardních `history-graph`.

### Pro energetický monitoring:

Pokud chceš sledovat spotřebu kotle:

1. Připoj **energetický měřič** (např. Shelly EM)
2. Přidej do dashboardu:

```yaml
- type: energy-distribution
  title: 💡 Spotřeba kotle
  entities:
    - entity: sensor.kotel_energy_daily
```

---

## 📱 Mobilní zobrazení

Dashboard je optimalizován i pro mobil! 

**Tipy:**
- Všechny karty jsou responzivní
- Gauge karty se automaticky přizpůsobí velikosti
- Entity karty jsou dobře čitelné i na malých displejích

---

## ❓ Nejčastější problémy

### "Entity not available"

**Problém:** Některé entity se nezobrazují.

**Řešení:**
1. Zkontroluj, že integrace `Jablotron Volta` běží
2. Ověř, že entity existují v **Developer Tools** → **States**
3. Uprav názvy entit v YAML podle skutečných názvů

### Grafy nejsou vidět

**Problém:** History grafy jsou prázdné.

**Řešení:**
1. Počkej pár minut, než se data nasbírají
2. Zkontroluj, že entity mají `state_class: measurement`
3. Restart Home Assistantu

### Dashboard se neuloží

**Problém:** Po uložení YAML se objeví chyba.

**Řešení:**
1. Zkontroluj **správné odsazení** (2 mezery, NE tabulátory!)
2. Použij YAML validator online
3. Zkontroluj, že všechny entity názvy jsou správně

---

## 🎓 Použití dashboardu

### Pro běžné použití:

→ Používej **Tab 1 (Přehled)** pro denní kontrolu  
→ Používej **Tab 2 (Ekviterm)** pro sezonní doladění

### Pro pokročilé nastavení:

→ **Tab 3 (CH1)** - kompletní nastavení topného okruhu  
→ **Tab 6 (Všechna nastavení)** - pokročilé parametry

### Pro diagnostiku problémů:

→ **Tab 7 (Diagnostika)** - všechny teploty a debug info

---

## 📚 Doporučené nastavení (tvůj systém)

Pro **podlahové topení s chytrými termostaty**:

```yaml
✅ Equitherm Slope:        0.6
✅ Equitherm Offset:       0°C
✅ Composite Ratio:        0.5
✅ Room Effect:            0%
✅ Temp Correction:        0°C
✅ Optimal Start/Stop:     OFF
✅ Hysteresis:             2-3°C
```

Všechna tato nastavení najdeš v **Tab 3 (CH1 Topný okruh)**.

---

## 🆘 Podpora

Máš otázky nebo problémy s dashboardem?

1. Zkontroluj [Issues na GitHubu](https://github.com/legendik/ha-jablotron-volta/issues)
2. Vytvoř nový issue s:
   - Screenshot problému
   - Verze Home Assistantu
   - Error log (pokud je)

---

## 📝 Licence

Tento dashboard je součástí integrace **Jablotron Volta for Home Assistant**.

---

**Vytvořeno s ❤️ pro komunitu Home Assistant**

Enjoy! 🎉
