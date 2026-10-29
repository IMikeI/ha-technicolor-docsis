# Technicolor DOCSIS für Home Assistant

![Technicolor DOCSIS](custom_components/technicolor_docsis/brand/icon.png)

Eine lokale, rein lesende Custom Integration für den **Technicolor CGA4233-EU** der **Salzburg AG**. Du installierst sie über HACS als benutzerdefiniertes Repository und richtest sie komplett in der Home-Assistant-Oberfläche ein.

> **Getestet wurde ausschließlich dieser Router im Bridge-Modus.**
> Andere Modelle, Provider, Firmwareversionen und den Router-Modus habe ich nicht getestet. Ob es dort läuft, kann ich deshalb nicht zusichern.

## Funktionen

- SC-QAM- und DOCSIS-3.1-Kanäle: OFDM im Downstream, OFDMA im Upstream.
- Pegel, Downstream-SNR, Kanalsynchronisierung und Modulation.
- Frequenzen, Bandbreiten, Profile und Symbolraten, soweit die API sie liefert.
- Korrigierte und nicht korrigierbare Fehler sowie Oktettzähler.
- DOCSIS-Betriebsstatus, Betriebszeit, CPU-Auslastung und Speicher-Rohwerte.
- Firmware- und Hardwareinfos plus zusätzliche Rohfelder als Attribute.
- Neu auftauchende Kanäle werden automatisch erkannt, du musst die Integration nicht neu anlegen.
- GUI für Zugangsdaten, Adressänderung, erneute Anmeldung und Abfrageintervall.
- Zahlen-Entität **Abfrageintervall** direkt am Gerät. Sie wird dauerhaft gespeichert und lässt sich ohne Neuladen der Integration ändern.
- Diagnose-Download ohne Zugangsdaten, Router-Adresse, Seriennummer oder MAC-Adresse.

Es gibt **keine** Funktionen zum Neustarten, Zurücksetzen oder Ändern von Router-Einstellungen. Du brauchst weder einen Cloud-Dienst noch einen laufenden Browser.

## Voraussetzungen

- Home Assistant **2026.2.3 oder neuer**. Die automatisierten Tests liefen gegen 2026.2.3, neuere Versionen sind damit nicht automatisch geprüft.
- Ein CGA4233-EU mit passenden Zugangsdaten für die lokale Weboberfläche.
- Home Assistant muss den Router selbst erreichen können, normalerweise unter `http://192.168.100.1`. Dass dein Notebook ihn erreicht, reicht nicht.
- HACS für die HACS-Installation. Alternativ geht auch eine manuelle Installation.

## Schnellstart

1. Repository über HACS als **benutzerdefiniertes Repository** mit der Kategorie **Integration** hinzufügen und herunterladen.
2. Home Assistant neu starten.
3. **Einstellungen -> Geräte & Dienste -> Integration hinzufügen** öffnen.
4. **Technicolor DOCSIS** suchen und Router-Adresse, Benutzername und Passwort eingeben.
5. Unter **Geräte** das Gerät **Technicolor CGA4233-EU** öffnen.

Du brauchst keine YAML-Konfiguration und keine zusätzliche Frontend-Karte.

Die ausführliche Anleitung mit manueller Installation, Sensorerklärungen, Fehlerbehebung und Deinstallation findest du im [Benutzerhandbuch](docs/BENUTZERHANDBUCH.md).

## So funktioniert die Integration

Ein asynchroner HTTP-Client nutzt dieselbe lokale JSON-API wie die Weboberfläche des Routers. Zuerst fragt er die Login-Salts ab. Verwendet die Firmware Salt-Authentifizierung, bildet er den zweistufigen PBKDF2-HMAC-SHA256-Ablauf nach, jeweils mit 1000 Iterationen und 128 Bit Schlüssellänge. Auch der Login ohne Salt, den die Oberfläche vorsieht, wird unterstützt.

Der Client führt eine eigene Cookie-Sitzung und sendet den CSRF- und AJAX-Header, den der Router verlangt. Cookies von IP-Adressen werden ausdrücklich akzeptiert. Läuft die Sitzung ab, meldet er sich einmal automatisch neu an. Lehnt der Router die Zugangsdaten dauerhaft ab, startet Home Assistant den Dialog zur Neuanmeldung.

**Login-Korrektur in Version 0.1.1:** Nach jeder erfolgreichen Anmeldung wird zusätzlich `/api/v1/session/menu` gelesen, genau wie in der Weboberfläche. Dadurch wird die Sitzung für die folgenden Datenabfragen initialisiert. Ohne diesen Schritt antwortete der getestete Router trotz erfolgreichem Login mit HTTP 500. In der Einrichtung sah das dann wie ein allgemeiner Verbindungsfehler aus.

Pro erfolgreichem Abfragezyklus gibt es zwei GET-Abfragen:

| API-Bereich | Inhalt |
| --- | --- |
| `/api/v1/system/...` | Modell, Identität, Betriebsstatus und Systemwerte |
| `/api/v1/modem/exUSTbl,exDSTbl,USTbl,DSTbl,ErrTbl` | Kanal- und Fehlerstatistiken |

Alle Sensoren teilen sich einen `DataUpdateCoordinator`. Standardmäßig wird alle **120 Sekunden** abgefragt, einstellbar von **60 bis 3600 Sekunden**. Pro Sensor gibt es keine eigene Router-Abfrage. Die beiden Antworten kommen nacheinander und sind kein atomarer Schnappschuss. Pro HTTP-Anfrage gilt ein Timeout von 60 Sekunden, bei langsamen Antworten dauert eine Aktualisierung also entsprechend länger.

Seit Version **0.1.2** kannst du das Intervall direkt über die Konfigurationsentität **Abfrageintervall** am Router-Gerät ändern, auch per Dashboard oder über die Aktion `number.set_value`. Erlaubt sind ganze Sekunden. Der neue Wert gilt ab dem nächsten Abfragezeitpunkt und bleibt nach einem Neustart erhalten. Dabei ändert sich keine Router-Einstellung, und es wird keine zusätzliche Abfrage oder Anmeldung ausgelöst. Der Regler bleibt auch bei einem vorübergehenden Router-Ausfall bedienbar.

Schlägt eine Abfrage fehl, werden die Sensoren trotzdem nicht „nicht verfügbar“. Fehlende Messwerte erscheinen nicht als Null. Die Sensoren arbeiten mit Kanal-IDs statt Tabellenpositionen und bleiben deshalb stabil, wenn sich die Kanalreihenfolge ändert. Ein anderer Router unter derselben IP wird nicht unbemerkt als das bisherige Gerät weiterverwendet.

Dieses Projekt ist eine unabhängige Community-Integration und kein offizielles Produkt von Technicolor oder der Salzburg AG.
