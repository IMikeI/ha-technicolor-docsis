# Technicolor DOCSIS fuer Home Assistant

![Technicolor DOCSIS](custom_components/technicolor_docsis/brand/icon.png)

Lokale, lesende Custom Integration für den **Technicolor CGA4233-EU** der
**Salzburg AG**, installierbar über HACS als benutzerdefiniertes Repository.
Die Einrichtung erfolgt vollstaendig in der Home-Assistant-Oberflaeche.

> **Getestet wurde ausschliesslich dieser Router im Bridge-Modus.**
> Andere Modelle, Provider, Firmwareversionen und der Router-Modus wurden
> nicht getestet. Eine Kompatibilitaet wird dafuer nicht zugesichert.

## Funktionen

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
  2026.2.3 ausgeführt; neuere Versionen sind damit nicht automatisch verifiziert.
- CGA4233-EU mit passenden Zugangsdaten fuer seine lokale Weboberflaeche.
- Home Assistant muss den Router selbst erreichen koennen, typischerweise unter
  `http://192.168.100.1`. Erreichbarkeit vom eigenen Notebook allein reicht nicht aus.
- HACS fuer die HACS-Installation; alternativ ist eine manuelle Installation moeglich.

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
Konfigurationsentitaet **Abfrageintervall** am Router-Geraet ändern, auch ueber
ein Dashboard oder die Aktion `number.set_value`. Erlaubt sind ganze Sekunden.
Der neue Wert gilt fuer den naechsten Abfragezeitpunkt und bleibt nach einem
Neustart erhalten. Es wird dabei keine Router-Einstellung veraendert und
keine zusaetzliche Datenabfrage oder Anmeldung ausgeloest. Der Regler bleibt
bei einem voruebergehenden Router-Ausfall bedienbar.

Fehlgeschlagene Abfragen machen Sensoren nicht verfuegbar. Fehlende Messwerte
werden nicht als Null dargestellt. Kanal-IDs statt Tabellenpositionen halten
Sensoren bei einer geaenderten Kanalreihenfolge stabil. Ein anderer Router unter
derselben IP wird nicht unbemerkt als das bisherige Geraet weiterverwendet.

Dieses Projekt ist eine unabhaengige Community-Integration und kein offizielles
Produkt von Technicolor oder Salzburg AG.
