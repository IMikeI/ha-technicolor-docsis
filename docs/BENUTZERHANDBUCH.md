# Benutzerhandbuch: Technicolor DOCSIS

## 1. Zweck und getestete Umgebung

Die Integration macht die DOCSIS-Kanal- und Systemwerte eines Technicolor
CGA4233-EU in Home Assistant verfuegbar. Dadurch lassen sich Pegel,
Signalqualitaet, Synchronisierung und Fehlerzaehler beobachten und historisch
vergleichen. Sie nimmt keine Aenderungen an der Kabelverbindung vor.

> **Getestet wurde ausschliesslich der Technicolor CGA4233-EU der Salzburg AG
> im Bridge-Modus.** Andere Modelle, Provider, Firmwareversionen und der
> Router-Modus wurden nicht getestet. Nicht allein fuer diese Integration
> den Betriebsmodus des Routers umstellen.

Vorausgesetzt wird Home Assistant ab 2026.2.3. Automatisierte Tests wurden mit
2026.2.3 ausgefuehrt. Live bestaetigt wurden die lokale Router-API und wiederholte
Abfragen mit dem korrigierten Python-Client; ein
Langzeitbetrieb der fertigen Integration auf einer produktiven HA-Installation
steht noch aus.

## 2. Netzwerk pruefen

Der Router ist im getesteten Bridge-Betrieb unter `http://192.168.100.1`
erreichbar. Home Assistant muss diese Adresse aus seinem eigenen Netzwerk
erreichen koennen, einschliesslich Container- oder VM-Netzwerk.

Wenn Home Assistant hinter einer eigenen Firewall oder einem weiteren Router
steht, kann eine passende Route zum Kabelmodem erforderlich sein. Die dafuer
notwendigen Einstellungen haengen vom Netzwerk ab; die Integration aendert
keine Routen oder Firewallregeln.

Es werden keine Portfreigaben ins Internet benoetigt. Verwende die
Zugangsdaten der lokalen Router-Weboberflaeche, nicht das Kundenportal-Passwort.

## 3. Installation ueber HACS

Voraussetzung ist ein auf GitHub veroeffentlichtes Repository mit der
Integration. Die Schritte fuer den Upload stehen in der
[Projektbeschreibung](../README.md#auf-github-veroeffentlichen).

1. Home Assistant oeffnen und **HACS** aufrufen.
2. Im HACS-Menue **Benutzerdefinierte Repositories / Custom repositories** oeffnen.
3. Die GitHub-URL des veroeffentlichten Repositorys eintragen.
4. Als Kategorie **Integration** auswaehlen und das Repository hinzufuegen.
5. **Technicolor DOCSIS (CGA4233-EU)** suchen, oeffnen und herunterladen.
6. Home Assistant vollstaendig neu starten, nicht nur den Browser aktualisieren.

Die genauen HACS-Menuebezeichnungen koennen je nach HACS-Version abweichen.
HACS installiert die Dateien; das Router-Geraet wird erst durch die folgende
Einrichtung angelegt.

## 4. Alternative: manuelle Installation

1. Im Home-Assistant-Konfigurationsverzeichnis den Ordner `custom_components`
   verwenden oder anlegen.
2. Aus diesem Repository den gesamten Ordner
   `custom_components/technicolor_docsis` dort ablegen.
3. Home Assistant neu starten.

Die resultierende Struktur muss so aussehen:

```text
/config/
  custom_components/
    technicolor_docsis/
      __init__.py
      api.py
      binary_sensor.py
      brand/
        icon.png
        icon@2x.png
      config_flow.py
      const.py
      coordinator.py
      data.py
      diagnostics.py
      entity.py
      manifest.json
      number.py
      sensor.py
      strings.json
      translations/
        de.json
        en.json
```

`/config` bezeichnet hier das HA-Konfigurationsverzeichnis; sein tatsaechlicher
Pfad haengt von der Installationsart ab. Es ist keine Aenderung an
`configuration.yaml` erforderlich.

### Integrationssymbol

Der Ordner `brand` muss mitinstalliert werden. Home Assistant ab **2026.3**
verwendet die darin enthaltenen transparenten PNGs automatisch. Die normale
Version hat 256 Pixel, die hochaufloesende Version 512 Pixel. Die Vektorquelle
und der freigegebene Entwurf befinden sich nur zur Bearbeitung unter `docs/design`
im Repository; dieser Dokumentationsordner muss nicht nach HA kopiert werden.

Nach einer Aktualisierung Home Assistant neu starten und gegebenenfalls den
Browser-Cache aktualisieren. Auf HA 2026.2.3 funktioniert die Integration
weiterhin, das lokale Integrationssymbol wird dort aber noch nicht unterstuetzt.
Die HACS-/Marketplace-Anzeige vor Installation haengt von der jeweiligen
Version ab. Aeltere HACS-Versionen, die nur das zentrale Brands-CDN abfragen,
erhalten ein lokal mitgeliefertes Icon dort nicht automatisch.

## 5. Router ueber die GUI einrichten

Die benoetigten Eingaben:

| Feld | Eingabe |
| --- | --- |
| Router-Adresse | Normalerweise `http://192.168.100.1` |
| Benutzername | Benutzer der Router-Weboberflaeche, im getesteten Fall `user` |
| Passwort | Dein aktuelles Router-Passwort |

1. **Einstellungen -> Geraete & Dienste** oeffnen.
2. **Integration hinzufuegen** waehlen.
3. Nach **Technicolor DOCSIS** suchen.
4. Die oben beschriebenen Felder ausfuellen.
5. Bestaetigen und die Verbindungspruefung abwarten. Die Router-API kann langsam antworten.
6. Nach erfolgreicher Einrichtung den Eintrag **Technicolor DOCSIS CGA4233-EU** oeffnen.
7. Unter dessen Geraeten **Technicolor CGA4233-EU** aufrufen.

Die Adresse **ohne** `/#/login`, `/#/status/docsis_signal` oder andere Pfade
eingeben. Zugangsdaten nicht in die URL schreiben.

Die Integration legt ein Router-Geraet an. Die Kanaele erscheinen als
Entitaeten dieses Geraets, nicht als einzelne physische Geraete.

## 6. Welche Sensoren gibt es?

Die genaue Anzahl ergibt sich aus der Router-Antwort. Es werden nur Felder als
Messsensoren angelegt, die in der jeweiligen Kanaltabelle vorhanden sind.
Nicht jeder Kanaltyp hat dieselben Felder.

| Gruppe | Bedeutung |
| --- | --- |
| Downstream SC-QAM | Klassische Empfangskanaele aus `DSTbl` |
| Downstream OFDM | DOCSIS-3.1-Empfangskanaele aus `exDSTbl` |
| Upstream SC-QAM | Klassische Sendekanaele aus `USTbl` |
| Upstream OFDMA | DOCSIS-3.1-Sendekanaele aus `exUSTbl` |
| Error statistics slot | Separate Fehlerstatistik aus `ErrTbl`; keine zugesicherte Kanalzuordnung |

Die englischen Gruppenbezeichnungen bleiben auch bei deutscher Oberflaeche
erhalten. Der anschliessende Messwertname wird uebersetzt. Die Nummer hinter
einer Kanalgruppe ist die vom Router gelieferte Kanal-ID; bei Fehlerstatistiken
ist es dagegen die Tabellen-Slot-ID.

### Pegel und Signalqualitaet

- **Pegel:** Empfangs- beziehungsweise Sendepegel des Kanals in `dBmV`.
- **SNR:** Vom Router gemeldeter Downstream-Signal-Rausch-Abstand in `dB`.
- **Kanalsynchronisierung:** An bei `Locked`, aus bei anderen gemeldeten Zustaenden.
- **Modulation:** Zum Beispiel `256-QAM` oder `64-qam`, so wie vom Router gemeldet.
- **FFT / Modulation (Routerwert):** Unveraendertes `FFT`-Feld. Bei der getesteten
  Firmware kann hier eine Liste von Modulationen stehen, keine FFT-Groesse.

Grenzwerte sind von Kanaltyp und Provider abhaengig. Die Integration vergibt
keine pauschale Bewertung wie gut/schlecht und stellt keine Leitungsdiagnose.

### Frequenzen und Kanalparameter

Frequenz, Startfrequenz, PLC-Frequenz, Mittenfrequenz und Bandbreite werden,
soweit verfuegbar, in MHz angezeigt. Eine Symbolrate wird in Baud (`Bd`)
angegeben. OFDMA-Symbolraten, die die Firmware nicht liefert, werden nicht
erfunden. Kanaltyp und Profil werden als Routerwerte dargestellt.

### Fehler und Oktette

- **Korrigierte Fehler:** Vom Router gemeldeter korrigierter Fehlerzaehler.
- **Nicht korrigierbare Fehler:** Vom Router gemeldeter nicht korrigierbarer Zaehler.
- **Oktette:** Ein Oktett entspricht einem Byte. Die Zahlen werden ohne
  Interpretation als Durchsatz uebernommen.

Die Fehlerdaten direkt eines SC-QAM-Downstreams und die Daten der separaten
`ErrTbl` stammen aus unterschiedlichen API-Feldern und koennen voneinander
abweichen. `ErrTbl` enthaelt keine verlaessliche Kanal-ID. Daher werden deren
Eintraege ausdruecklich **nicht** anhand der Reihenfolge einem Kanal zugeordnet.
Fehler-Slots koennen nach einem Neustart oder einer Neukonfiguration eine andere
Bedeutung haben. Nicht zur kanalgenauen Langzeitanalyse verwenden und nicht
pauschal mit den Kanalzaehlern addieren.

Die Zaehler werden in HA als `total_increasing` behandelt. Ein Rueckgang kann
als Zaehlerneustart interpretiert werden. Router-Neustarts, Ueberlaeufe oder
Firmware-Eigenheiten koennen Statistiken beeinflussen. Die Integration setzt
keine Zaehler zurueck.

### System und Geraetedaten

- **DOCSIS-Status:** Rohzustand, beispielsweise `OPERATIONAL`.
- **DOCSIS-Verbindung:** An, wenn der DOCSIS-Status `OPERATIONAL` ist. Kein Ping,
  kein Speedtest und keine Pruefung externer Internetziele.
- **Betriebszeit:** Router-Laufzeit in Sekunden; HA kann diese umgerechnet darstellen.
- **CPU-Auslastung:** Der von der Firmware gemeldete Prozentwert.
- **Speicher gesamt/frei:** Rohwerte in Routereinheiten, ohne unbestaetigte Byte-Umrechnung.

Modell, Hersteller, Seriennummer sowie Firmware- und Hardwareversion stehen
in den Geraeteinformationen. Weitere Systemwerte wie Bootloader-Version,
Firmware-Buildzeit und Prozessortakt finden sich als Attribute des
**DOCSIS-Status**-Sensors. Die Integration vergibt fuer diese Rohattribute
keine ungesicherten Einheiten. Die Attribute der Kanalsynchronisierung enthalten
die vom Kanal gelieferten Rohfelder, einschliesslich seiner internen Indizes.

## 7. Optionale Sensoren aktivieren

Weniger haeufig benoetigte Felder sind anfangs deaktiviert: Frequenzen,
Bandbreiten, Symbolraten, Profile, Kanaltypen, Oktettzaehler und Speicher-Rohwerte.
Sie sind bereits in der Entitaetsregistrierung angelegt.

1. Das Router-Geraet unter **Einstellungen -> Geraete & Dienste -> Geraete** oeffnen.
2. Die Entitaetsliste oeffnen und bei Bedarf deaktivierte Entitaeten einblenden.
3. Den gewuenschten Sensor oeffnen und in dessen Einstellungen aktivieren.
4. Warten, bis HA die Entitaet aktiviert beziehungsweise die Integration neu laedt.

Neue Kanal-IDs werden bei erfolgreichen Aktualisierungen automatisch erkannt.
Verschwindet ein bekannter Kanal, bleiben seine Entitaeten erhalten und werden
nicht verfuegbar. Sie koennen nach einer geaenderten Kanalbelegung bei Bedarf
in HA deaktiviert oder, soweit HA dies zulaesst, entfernt werden.

## 8. Einstellungen spaeter aendern

### Abfrageintervall

Ab Version **0.1.2** gibt es direkt am Router-Geraet eine Zahlen-Entitaet:

1. **Einstellungen -> Geraete & Dienste -> Geraete -> Technicolor CGA4233-EU** oeffnen.
2. Unter den Konfigurationsentitaeten **Abfrageintervall** auswaehlen.
3. Einen ganzzahligen Wert von **60 bis 3600 Sekunden** eingeben und bestaetigen.

Standard sind **120 Sekunden**. Der Regler passt den naechsten Abfragezeitpunkt
direkt an, ohne die Integration neu zu laden. Der Wert wird dauerhaft gespeichert
und bleibt nach einem Neustart erhalten. Dabei wird nur die HA-Abfrageeinstellung
veraendert, keine Einstellung im Router. Auch waehrend eines voruebergehenden
Router-Ausfalls kann das Intervall angepasst werden.

Die Zahlen-Entitaet kann ausserdem zu einem Dashboard hinzugefuegt oder mit
der HA-Aktion `number.set_value` geaendert werden. Die genaue Entitaets-ID ist
in den Einstellungen dieser Entitaet sichtbar und kann vom Benutzer geaendert werden.

Alternativ bleibt **Konfigurieren / Optionen** beim Integrationseintrag
verfuegbar. Dieser Dialog speichert denselben Wert und laedt die Integration
anschliessend neu; danach zeigt die Zahlen-Entitaet den neuen Wert an.

Kuerzere Intervalle belasten die Router-Verwaltungsoberflaeche staerker. Eine
API-Antwort kann mehrere Sekunden dauern; es gibt keine Echtzeitgarantie.

### Adresse oder Zugangsdaten

Im Menue des Integrationseintrags **Neu konfigurieren / Reconfigure** waehlen.
Adresse und Benutzername pruefen und das Passwort erneut eingeben. Die Daten
muessen weiterhin zum selben physischen Router gehoeren. Ein ausgetauschter
Router wird als neue Integration hinzugefuegt.

Bei dauerhaft abgelehnten Zugangsdaten zeigt Home Assistant automatisch eine
Meldung zur erneuten Anmeldung. Bei einem normalen Sitzungsablauf meldet sich
die Integration selbst erneut an.

## 9. Verlauf und Dashboards

Die Sensoren sind normale HA-Entitaeten und koennen ueber den visuellen
Dashboard-Editor zu vorhandenen Entitaets-, Kachel- oder Verlaufskarten
hinzugefuegt werden. Eine separate Custom Card ist nicht erforderlich.

Verlaufsdaten setzen voraus, dass die betreffenden Entitaeten vom Recorder
erfasst werden. Deaktivierte oder vom Recorder ausgeschlossene Sensoren haben
keinen automatisch nachtraeglich aufgefuellten Verlauf. Fuer Pegel und SNR
sind zeitliche Trends haeufig hilfreicher als einzelne Momentaufnahmen.

## 10. Fehlerbehebung

| Problem | Pruefung |
| --- | --- |
| Integration fehlt in der Suche | HA nach Installation neu starten; Ordnerstruktur pruefen; Browser neu laden |
| Integrationssymbol fehlt | HA ab 2026.3 und mitinstallierten `brand`-Ordner pruefen; HA neu starten und Browser-Cache aktualisieren; HACS-Listenansicht ist versionsabhaengig |
| Verbindung fehlgeschlagen | Router-Adresse, Route aus dem HA-Netz, Firewall, Modell und Firmware pruefen |
| Login klappt im Browser, Integration meldet Verbindungsfehler | Mindestens Version 0.1.1 verwenden: Sie initialisiert nach dem Login die Sitzung ueber `/session/menu` und behebt den dadurch verursachten HTTP-500-Fehler |
| Anmeldung abgelehnt | Zugangsdaten zuerst in der lokalen Router-Oberflaeche pruefen; keine Kundenportal-Zugangsdaten verwenden |
| Bereits eingerichtet | Vorhandenen Integrationseintrag verwenden; dieselbe Seriennummer kann nicht zweimal angelegt werden |
| Anderer Router erkannt | Bei Geraetetausch eine neue Integration hinzufuegen statt bestehende Statistiken umzudeuten |
| Sensor ist unbekannt | Firmware liefert keinen gueltigen Wert, beispielsweise `NA`; es wird bewusst keine Null erfunden |
| Sensor ist nicht verfuegbar | Abfrage fehlgeschlagen oder Kanal nicht mehr vorhanden; naechsten Zyklus und Protokoll pruefen |
| Fehler-Slot passt nicht zum Kanal | Slots haben keine gesicherte Kanalzuordnung; nicht anhand der Reihenfolge zuordnen |
| Ein Sensor fehlt | Deaktivierte Entitaeten einblenden; ausserdem liefert nicht jeder Kanaltyp jedes Feld |
| Stoerung nach Firmwareupdate | Web-API kann sich geaendert haben; Firmwarestand und redigierte Diagnosedaten fuer die Fehlermeldung notieren |
| HTTPS funktioniert nicht | HTTPS-Unterstuetzung, Adresse und gueltige Zertifikatskette pruefen; getesteter Zugriff war HTTP |

Die HA-Protokolle sind unter **Einstellungen -> System -> Protokolle** erreichbar.
Die Integration zeigt beim Ausfall keine veralteten Messwerte als aktuelle
Gueltigwerte an, sondern markiert ihre Entitaeten als nicht verfuegbar.

Fuer eine Fehlermeldung den Integrationseintrag oeffnen und im Menue
**Diagnosedaten herunterladen** waehlen. Adresse, Zugangsdaten, Seriennummer
und MAC-Adresse sind nicht im Diagnose-Download enthalten beziehungsweise
werden geschwaerzt. Den Inhalt trotzdem vor einer Veroeffentlichung pruefen.

## 11. Sicherheit

Der getestete HTTP-Zugriff ist nicht verschluesselt. Nur im vertrauenswuerdigen
LAN verwenden und keine Internet-Portfreigabe fuer die Router-Verwaltung einrichten.
Eine gehashte Login-Antwort ersetzt keine Transportverschluesselung.

Das Router-Passwort wird von HA in der Integrationskonfiguration gespeichert.
Konfigurationsdateien und Backups schuetzen. Echte Passwoerter niemals in
GitHub-Issues, Screenshots oder Repository-Dateien einfuegen.

Es werden nur die Login-Anfragen als POST gesendet; alle Messwertabfragen sind
GET-Anfragen. Es gibt keine Steuerbefehle, keinen automatischen Neustart und
keine Aenderung von Provider-, WLAN- oder Bridge-Einstellungen. Eine separate
Sitzung wird verwendet; moegliche firmwareseitige Beschraenkungen paralleler
Web-Anmeldungen wurden nicht im Langzeitbetrieb getestet.

## 12. Aktualisieren und entfernen

**Aktualisieren:** In HACS die neue Version installieren und Home Assistant
neu starten. Vorher ein HA-Backup anlegen und Aenderungshinweise lesen.
Bei manueller Installation den Integrationsordner durch die neue Version
ersetzen und HA neu starten.

**Entfernen:** Zuerst den Integrationseintrag unter **Geraete & Dienste**
loeschen. Anschliessend die Integration ueber HACS entfernen beziehungsweise
den manuell installierten Ordner entfernen und HA neu starten. Der Router wird
dabei nicht zurueckgesetzt oder anderweitig veraendert. Bereits aufgezeichnete
Historie unterliegt weiterhin den Recorder-Aufbewahrungsregeln von HA.
