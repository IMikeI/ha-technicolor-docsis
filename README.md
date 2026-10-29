# Technicolor DOCSIS fuer Home Assistant

![Technicolor DOCSIS](custom_components/technicolor_docsis/brand/icon.png)

Lokale, lesende Custom Integration fuer den **Technicolor CGA4233-EU** der
**Salzburg AG**, installierbar ueber HACS als benutzerdefiniertes Repository.
Die Einrichtung erfolgt vollstaendig in der Home-Assistant-Oberflaeche.

> **Getestet wurde ausschliesslich dieser Router im Bridge-Modus.**
> Andere Modelle, Provider, Firmwareversionen und der Router-Modus wurden
> nicht getestet. Eine Kompatibilitaet wird dafuer nicht zugesichert.

## Funktionen

- Ein Home-Assistant-Geraet fuer den Router, mit stabiler Identitaet anhand
  der Seriennummer beziehungsweise der Kabelmodem-MAC-Adresse.
- SC-QAM- und DOCSIS-3.1-Kanaele: OFDM im Downstream und OFDMA im Upstream.
- Pegel, Downstream-SNR, Kanalsynchronisierung und Modulation.
- Frequenzen, Bandbreiten, Profile und Symbolraten, soweit von der API geliefert.
- Korrigierte Fehler, nicht korrigierbare Fehler und Oktettzaehler.
- DOCSIS-Betriebsstatus, Betriebszeit, CPU-Auslastung und Speicher-Rohwerte.
- Firmware-/Hardwareinformationen und zusaetzliche Rohfelder als Attribute.
- Automatisches Erkennen neu auftauchender Kanaele, ohne die Integration neu anzulegen.
- GUI fuer Zugangsdaten, Adressaenderung, erneute Anmeldung und Abfrageintervall.
- Zahlen-Entitaet **Abfrageintervall** direkt am Geraet, dauerhaft gespeichert
  und ohne Neuladen der Integration aenderbar.
- Diagnose-Download ohne Zugangsdaten, Router-Adresse, Seriennummer oder MAC-Adresse.

Es gibt **keine** Funktionen zum Neustarten, Zuruecksetzen oder Aendern von
Router-Einstellungen. Kein Cloud-Dienst und kein laufender Browser sind erforderlich.

## Voraussetzungen

- Home Assistant **2026.2.3 oder neuer**. Automatisierte HA-Tests wurden gegen
  2026.2.3 ausgefuehrt; neuere Versionen sind damit nicht automatisch verifiziert.
- CGA4233-EU mit passenden Zugangsdaten fuer seine lokale Weboberflaeche.
- Home Assistant muss den Router selbst erreichen koennen, typischerweise unter
  `http://192.168.100.1`. Erreichbarkeit vom eigenen Notebook allein reicht nicht aus.
- HACS fuer die HACS-Installation; alternativ ist eine manuelle Installation moeglich.

## Icon und Darstellung

Das eigene Integrationssymbol wird als transparentes PNG mit 256 und 512 Pixeln
in `custom_components/technicolor_docsis/brand/` mitgeliefert. Es ist ein eigenes
Kabelmodem-Symbol und kein offizielles Technicolor- oder Salzburg-AG-Logo.
Die Vektorquelle liegt unter [docs/design/icon.svg](docs/design/icon.svg).

Home Assistant **ab 2026.3** kann diese lokalen Brand-Dateien nach Installation
und Neustart direkt fuer die Integrations- und Geraetedarstellung verwenden.
Die Integration bleibt mit 2026.2.3 verwendbar, dort jedoch ohne dieses lokale
Icon. Ein gesonderter Manifest-Eintrag oder Upload in das zentrale Brands-Repository
ist fuer die lokale Darstellung ab 2026.3 nicht erforderlich.

Die Darstellung in der HACS-/Marketplace-Liste vor der Installation haengt
von der jeweiligen Version und deren Brand-Unterstuetzung ab. Aeltere
HACS-Versionen, die nur das zentrale Brands-CDN abfragen, zeigen das lokale
Icon dort nicht automatisch. Die README enthaelt das Symbol ebenfalls.

## Schnellstart

1. Repository ueber HACS als **benutzerdefiniertes Repository**, Kategorie
   **Integration**, hinzufuegen und herunterladen.
2. Home Assistant neu starten.
3. **Einstellungen -> Geraete & Dienste -> Integration hinzufuegen** oeffnen.
4. **Technicolor DOCSIS** suchen und Router-Adresse, Benutzername und Passwort eingeben.
5. Unter **Geraete** das Geraet **Technicolor CGA4233-EU** oeffnen.

Keine YAML-Konfiguration und keine zusaetzliche Frontend-Karte sind erforderlich.

Die ausfuehrliche Anleitung mit manueller Installation, Sensorerlaeuterungen,
Fehlerbehebung und Deinstallation steht im
[Benutzerhandbuch](docs/BENUTZERHANDBUCH.md).

## Wie die Integration funktioniert

Ein asynchroner HTTP-Client verwendet dieselbe lokale JSON-API wie die
Router-Weboberflaeche. Er fordert zuerst die Login-Salts an. Falls die Firmware
Salt-Authentifizierung verwendet, bildet er den zweistufigen
PBKDF2-HMAC-SHA256-Ablauf mit jeweils 1000 Iterationen und 128 Bit Schluessellaenge
nach. Der von der Oberflaeche vorgesehene Login ohne Salt wird ebenfalls unterstuetzt.

Der Client fuehrt eine eigene Cookie-Sitzung und sendet den vom Router
geforderten CSRF- und AJAX-Header. Cookies von IP-Adressen werden explizit
akzeptiert. Bei Sitzungsablauf erfolgt einmalig eine erneute Anmeldung; dauerhaft
abgelehnte Zugangsdaten starten den Home-Assistant-Dialog zur Neuanmeldung.

**Login-Korrektur in Version 0.1.1:** Nach jeder erfolgreichen Anmeldung wird
zusaetzlich `/api/v1/session/menu` gelesen, wie in der Router-Weboberflaeche.
Dieser Schritt initialisiert die Sitzung fuer nachfolgende Datenabfragen.
Ohne ihn antwortete der getestete Router trotz erfolgreichem Login mit HTTP 500,
was in der Einrichtung als allgemeiner Verbindungsfehler angezeigt wurde.

Pro erfolgreichem Abfragezyklus werden zwei GET-Abfragen durchgefuehrt:

| API-Bereich | Inhalt |
| --- | --- |
| `/api/v1/system/...` | Modell, Identitaet, Betriebsstatus und Systemwerte |
| `/api/v1/modem/exUSTbl,exDSTbl,USTbl,DSTbl,ErrTbl` | Kanal- und Fehlerstatistiken |

Alle Sensoren teilen sich einen `DataUpdateCoordinator`. Standardmaessig erfolgt
eine Abfrage alle **120 Sekunden**, einstellbar von **60 bis 3600 Sekunden**.
Es gibt keine separate Router-Abfrage pro Sensor. Die beiden Antworten entstehen
nacheinander und sind kein atomarer Schnappschuss. Pro HTTP-Anfrage gilt ein
Timeout von 60 Sekunden; bei langsamen Antworten dauert eine Aktualisierung laenger.

Seit Version **0.1.2** kann der Benutzer das Intervall direkt ueber die
Konfigurationsentitaet **Abfrageintervall** am Router-Geraet aendern, auch ueber
ein Dashboard oder die Aktion `number.set_value`. Erlaubt sind ganze Sekunden.
Der neue Wert gilt fuer den naechsten Abfragezeitpunkt und bleibt nach einem
Neustart erhalten. Es wird dabei keine Router-Einstellung veraendert und
keine zusaetzliche Datenabfrage oder Anmeldung ausgeloest. Der Regler bleibt
bei einem voruebergehenden Router-Ausfall bedienbar.

Fehlgeschlagene Abfragen machen Sensoren nicht verfuegbar. Fehlende Messwerte
werden nicht als Null dargestellt. Kanal-IDs statt Tabellenpositionen halten
Sensoren bei einer geaenderten Kanalreihenfolge stabil. Ein anderer Router unter
derselben IP wird nicht unbemerkt als das bisherige Geraet weiterverwendet.

## Wichtige Grenzen

- Ausgelesen werden die durch die getesteten API-Endpunkte und den Benutzer
  freigegebenen Werte, nicht alle intern im Modem vorhandenen DOCSIS-Daten.
- Die separate `ErrTbl` enthaelt keine zuverlaessigen Kanal-IDs. Ihre Eintraege
  erscheinen deshalb als **Error statistics slot** mit eigener Slot-Nummer.
  Es wird **keine** ungesicherte Zuordnung zu SC-QAM-/OFDM-Kanaelen vorgenommen.
- Fehlerzaehler direkt aus `DSTbl` bleiben den dortigen Kanaelen zugeordnet.
  Diese und die separate Fehlertabelle duerfen nicht pauschal zusammengezaehlt werden.
- `Octets` sind vom Router gemeldete Zaehler, kein gemessener Durchsatz und
  kein verlaesslicher Ersatz fuer WAN-Traffic-Abrechnung.
- Das Feld `FFT` liefert auf der getesteten Firmware teilweise Modulationslisten.
  Der Wert wird unveraendert wiedergegeben, nicht als FFT-Groesse interpretiert.
- Speicherwerte bleiben mangels gesicherter API-Einheit in Routereinheiten.
- Ein DOCSIS-Status `OPERATIONAL` ist kein aktiver Test der Internet-Erreichbarkeit.
- Die interne Web-API ist nicht offiziell dokumentiert und kann sich durch
  Provider-Firmwareupdates aendern.

## Sicherheit und Datenschutz

Im Repository sind **keine echten Zugangsdaten und keine echten Geraete-IDs**
hinterlegt. Die Standardadresse und der Standardbenutzer sind nur Formularvorgaben.
Das Passwort wird erst in Home Assistant eingegeben und dort in der Config Entry
gespeichert. Home-Assistant-Konfiguration und Backups sind entsprechend zu schuetzen.

Die getestete Router-Verbindung verwendet HTTP und ist damit **nicht
transportverschluesselt**, auch wenn der Login PBKDF2 verwendet. Nur in einem
vertrauenswuerdigen lokalen Netz einsetzen, den Router nicht ins Internet
freigeben und die Zugangsdaten nicht veroeffentlichen. HTTPS wird nur bei
gueltigem Zertifikat akzeptiert; die Zertifikatspruefung wird nicht abgeschaltet.

Die Seriennummer wird lokal in der HA-Geraeteregistrierung verwendet und angezeigt.
Der Diagnose-Download schwaerzt Seriennummer und MAC-Adresse; technische Werte
koennen weiterhin Informationen ueber den Anschluss enthalten. Downloads vor
einer Veroeffentlichung pruefen.

## Teststatus

Am **29.10.2026** wurden an einem CGA4233-EU der Salzburg AG im **Bridge-Modus**
Login und lesende API-Abfragen ueber den Browser sowie zwei aufeinanderfolgende
Abfragen mit dem korrigierten Python-Client bestaetigt. Firmware:
`CGA4233EU-19.1.B39-022-E20-RMQS`, Hardware: `3.1.5`.
Dabei waren 4 SC-QAM-Downstreams, 2 OFDM-Downstreams, 4 SC-QAM-Upstreams und
1 OFDMA-Upstream sowie 6 separate Fehlerstatistik-Eintraege vorhanden.
Diese Anzahl ist ein beobachteter Zustand, keine fest eingebaute Vorgabe.

Automatisierte Tests verwenden synthetische Daten und einen lokalen HTTP-Testserver.
Sie pruefen Authentifizierung, Sitzungsablauf, Einheiten, GUI-Flows,
Geraete-/Sensoranlage, dynamische Kanaele, Diagnose-Schwaerzung und Sitzungsfreigabe.
Ein laengerfristiger Betrieb der Integration auf der produktiven
Home-Assistant-Installation ist damit noch nicht bestaetigt.

## Auf GitHub veroeffentlichen

1. Unter dem GitHub-Benutzer `IMikeI` ein Repository `ha-technicolor-docsis` anlegen.
   Fuer die uebliche HACS-Nutzung ein oeffentliches Repository verwenden.
2. Die URLs in [manifest.json](custom_components/technicolor_docsis/manifest.json)
  sind bereits auf `https://github.com/IMikeI/ha-technicolor-docsis` gesetzt.
  Bei einem anderen Repository-Namen die beiden URLs entsprechend anpassen.
3. Den **Inhalt dieses Ordners** in den Repository-Stamm hochladen. Im Stamm
   muessen unter anderem `hacs.json`, `README.md` und `custom_components/` liegen,
   nicht erst in einem zusaetzlichen Unterordner.
4. Auch `.github/workflows/validate.yml` hochladen und den GitHub-Actions-Lauf pruefen.
   Virtuelle Umgebungen, Caches und lokale Zugangsdaten niemals hochladen.
5. Nach erfolgreicher Validierung einen GitHub-Release `v0.1.2` erstellen.
6. Die echte Repository-URL in HACS als benutzerdefinierte **Integration** eintragen.

Eine Veroeffentlichung auf GitHub ist nicht automatisch eine Aufnahme in den
offiziellen HACS-Katalog. Die Nutzung als benutzerdefiniertes Repository ist
der vorgesehene erste Weg. Das Repository wurde nicht automatisch hochgeladen,
getaggt oder in HACS registriert.

## Entwicklung und Tests

Mit Python 3.14 im Repository-Stamm:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -q
```

Die HA-Tests laden die Custom Integration in einer isolierten Testinstanz und
verbinden sich nicht mit einem echten Router. Die HTTP-Client-Tests verwenden
ausschliesslich einen Testserver auf `127.0.0.1`. Der GitHub-Workflow prueft
zusaetzlich die HACS-Repository-Struktur. Eine dortige HACS-Validierung wurde
lokal nicht vorweggenommen.

API-, Daten- und Metadatenpruefungen koennen auch ohne HA-Testframework mit
installiertem `aiohttp` ausgefuehrt werden:

```sh
python -m unittest discover -s tests -v
```

Dieses Projekt ist eine unabhaengige Community-Integration und kein offizielles
Produkt von Technicolor oder Salzburg AG.
