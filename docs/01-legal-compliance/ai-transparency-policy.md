# AI-Transparenzleitlinie

## Zweck und Reichweite

Diese interne Leitlinie beschreibt Transparenzanforderungen für KI-gestützte Vorbereitung im **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Sie ist keine Rechtsberatung und keine vollständige AI-Act-Bewertung. Sie legt Projektgrenzen für Kennzeichnung, Nachvollziehbarkeit und Kommunikation fest.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Transparenzgrundsatz

Nutzerinnen und Nutzer sollen erkennen können, wann Inhalte durch KI vorbereitet wurden.

Steuerlich relevante KI-Ausgaben bleiben **Entwürfe**. **Human Review** und Kanzlei-Freigabe bleiben vor fachlicher Verwendung erforderlich.

Das System darf nicht so wirken, als ersetze es fachliche Prüfung oder steuerliche Verantwortung.

## Kennzeichnung von KI-Ausgaben

Interne Entwürfe sind als KI-unterstützt oder systemgeneriert zu kennzeichnen.

Steuerlich relevante Outputs sind als **Entwurf** zu kennzeichnen.

Nicht zulässig ist die Darstellung als final geprüft, fachlich freigegeben, für externe Verwendung bestimmt oder als abschließende steuerliche Bewertung.

## Transparenz gegenüber Kanzlei-Nutzern

Kanzlei-Nutzerinnen und -Nutzer sollen - soweit technisch und organisatorisch umsetzbar - erkennen können:

- welche Eingaben für eine Ausgabe verwendet wurden
- welche Quellen oder Policies herangezogen wurden, soweit verfügbar
- welcher Rechtsstand oder Zeitraum relevant ist, soweit steuerliche Quellen später integriert werden
- ob **Unsicherheitsmodus** oder **Human Review** ausgelöst wurde

Diese Anforderungen gelten auf Policy-Ebene. Konkrete UI-, Logging- und Protokollierungsformen folgen in separaten PRs.

## Transparenz gegenüber Mandanten

Mandantenkommunikation mit steuerlich relevanten Inhalten erfolgt nur nach Kanzlei-Freigabe.

Automatische Mandantenberatung durch das Modell ist ausgeschlossen.

Spätere Mandantenhinweise zu KI-Unterstützung müssen durch Kanzlei- und Legal Review freigegeben werden, bevor sie extern verwendet werden.

## Grenzen

Diese Leitlinie enthält keine Aussage über den **AI Act readiness**-Vorbereitungsstand des Systems in regulatorischer Hinsicht.

Sie enthält keine Garantie regulatorischer Konformität und keine abschließende Risikoklassifizierung.

Vertrauliche Inhalte dürfen nicht in **Public-LLMs** verarbeitet werden. Das **Policy- und Privacy-Gateway** bleibt Voraussetzung für kontrollierte Modellnutzung.

## Verhältnis zu bestehenden Dokumenten

| Dokument | Bezug |
| --- | --- |
| `legal-boundaries.md` | rechtliche Systemgrenzen und Entwurfscharakter |
| `stberg-safety-policy.md` | berufsrechtliche Sicherheitsleitplanken |
| `AGENTS.md` | Agenten-Guardrails für Repository-Arbeit |
| `ai-act-readiness.md` | interne AI-Act-Readiness-Orientierung |

## Spätere Vertiefung

Detailanforderungen an UI-Kennzeichnung, Logging, Dokumentation und Mandantenhinweise folgen in separaten Pull Requests.
