# Rechtliche Systemgrenzen

## Zweck und Reichweite

Dieses Dokument beschreibt interne rechtliche Systemgrenzen für den **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Es ist keine Rechtsberatung, keine vollständige juristische Bewertung und keine Aussage zur Zulässigkeit eines produktiven Einsatzes. Spätere Detailprüfungen können diese Grenzen ergänzen oder präzisieren.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Grundabgrenzung

Das System ist ein Steuer-Vorbereitungsassistent für interne Kanzlei-Prozesse.

Es ist nicht:

- ein autonomer Steuerberater
- ein steuerliches Entscheidungssystem
- ein System für individuelle Steuerberatung durch das Modell
- ein Werkzeug für steuerlich wirksame Handlungen ohne Kanzlei-Freigabe

Das System darf vorbereiten, strukturieren, dokumentieren und Review-Prozesse unterstützen. Entscheidungen, Freigaben und steuerlich wirksame Handlungen verbleiben bei der Kanzlei.

## Entwurfscharakter

Steuerlich relevante Ausgaben des Systems sind Entwürfe. Sie entfalten keine Verbindlichkeit ohne Human Review und Kanzlei-Freigabe.

Entwürfe dürfen nicht so dargestellt werden, als seien sie bereits fachlich freigegeben, abschließend bewertet oder für die externe Verwendung durch Mandanten oder Behörden bestimmt.

## Verbotene Systemhandlungen

Das System darf nicht:

- steuerlich wirksame Erklärungen ohne Kanzlei-Freigabe erstellen, freigeben oder übermitteln
- direkte produktive Schreibintegrationen in Agenda, ELSTER oder Mandantensysteme verwenden
- Bescheide eigenständig mit abschließendem Ergebnis prüfen
- Einspruchsvorbereitung mit bindendem Ergebnis durchführen
- mandantenbezogene Handlungen ohne fachliche Prüfung auslösen
- steuerlich erhebliche Entscheidungen automatisch treffen

## Daten- und Modellgrenzen im Überblick

Für Modellkontexte gelten mindestens diese Grenzen:

- keine Original-PII im Modellkontext
- keine echten vertraulichen Daten in Public-LLMs
- kein direkter Zugriff des LLM auf Datenbanken, Dateisysteme, Object Storage, Agenda, ELSTER, Audit-Logs, Token-Maps oder Secrets
- keine Umgehung des Policy- und Privacy-Gateway

Diese Grenzen gelten auch für Agenten, Werkzeuge und spätere MCP-Überlegungen.

## Verantwortlichkeit

Die fachliche Verantwortung bleibt bei der Kanzlei beziehungsweise dem Steuerberater.

Das System unterstützt Vorbereitung, Dokumentation und Review. Es ersetzt keine fachliche Prüfung, keine Kanzlei-Freigabe und keine berufsrechtlich verantwortliche Entscheidung.

## Abgrenzung zu späteren Dokumenten

Nicht Gegenstand dieses Dokuments sind:

- AI-Act-Policy
- Datenschutz-Detailpolicy
- GoBD-Detailpolicy
- Risk Classification
- Human-Review-Workflow
- Architektur-ADR
- produktive Betriebsfreigabe

Diese Themen werden, soweit erforderlich, in separaten PRs dokumentiert.

## Nicht-Zusicherungen

Dieses Dokument macht keine Zusage zur rechtlichen oder regulatorischen Einordnung des Systems.

Es sagt nicht aus, dass ein produktiver Einsatz bereits zulässig ist. Vor produktionsnaher Nutzung sind fachliche, technische, rechtliche und organisatorische Prüfungen erforderlich.
