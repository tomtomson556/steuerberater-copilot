# Glossar

Kurze, projektinterne Begriffsdefinitionen. Keine Rechtsauslegung.

| Begriff | Definition |
| --- | --- |
| **Agenda-Handoff** | Übergabe vorbereiteter Daten an die Kanzleisoftware Agenda über Export, Staging oder manuelle Übernahme - ohne direkte produktive Schreibintegration. |
| **Audit-Log** | Manipulationssichere oder revisionssichere Protokollierung von relevanten Systemereignissen zur Nachvollziehbarkeit; kein direkter Modellzugriff. |
| **Detokenisierung** | Rückführung pseudonymisierter Platzhalter in lesbare Werte außerhalb des Modellkontexts, typischerweise im Policy- und Privacy-Gateway oder im Kanzlei-Workspace. |
| **Entwurf** | Vom System erzeugtes Vorbereitungsmaterial ohne steuerliche Wirksamkeit; erfordert Human Review vor fachlicher Verwendung. |
| **Human Review** | Pflichtprüfung durch qualifizierte Kanzleimitarbeiter oder Steuerberater vor Weiterverwendung steuerlich relevanter Ergebnisse. |
| **Kanzlei-Workspace** | Interner Arbeitsbereich der Kanzlei für Prüfung, Freigabe und Bearbeitung von Entwürfen. |
| **Mandantenportal** | Mandantenseitiger Zugang zur strukturierten Daten- und Unterlagenübermittlung, soweit von der Kanzlei freigegeben. |
| **MCP-Service** | Begrenzter, kontrollierter Dienst im Model Context Protocol; stellt Werkzeuge bereit, ohne dem Modell offene Systemrechte zu geben. |
| **Original-PII** | Unmittelbar identifizierende personenbezogene Daten in Originalform; dürfen nicht in den Modellkontext gelangen. |
| **Policy- und Privacy-Gateway** | Kontrollschicht vor dem Modell: Filterung, Pseudonymisierung, Freigabeentscheidungen und Rückführung von Token. |
| **Public-LLM** | Öffentlich oder cloudbasiert betriebenes Sprachmodell außerhalb einer isolierten Kanzlei-Umgebung; nicht für vertrauliche Inhalte vorgesehen. |
| **Quelle** | Referenzierbare fachliche Grundlage (Norm, Verwaltungsanweisung, Kommentar o. Ä.) mit Rechtsstand und Zeitraum. |
| **Roter Fall** | Vorgang oder Inhalt mit erhöhtem Risiko, der zusätzliche Prüfung, Eskalation oder Freigabe erfordert; kein automatischer Durchlauf. |
| **Steuer-Vorbereitungsassistent** | Alternative Bezeichnung für das Projekt; betont die Vorbereitungsfunktion ohne Entscheidungsautorität. |
| **Steuerberater-Copilot** | Projektname; KI-gestütztes Vorbereitungssystem für deutsche Steuerkanzleien - kein autonomer Steuerberater. |
| **Temporal RAG** | Retrieval-Augmented Generation mit zeitlicher Einordnung von Quellen und Rechtsständen. |
| **Token-Map** | Zuordnungstabelle zwischen Pseudonymen (Token) und Originalwerten; liegt außerhalb des Modellkontexts und ist nicht für das LLM zugänglich. |
| **Unsicherheitsmodus** | Betriebszustand, in dem das System bei unzureichender Evidenz oder unklarer Einordnung keine inhaltliche Ausgabe erzwingt, sondern Rückfragen oder Eskalation auslöst. |
| **WORM** | Write Once, Read Many - Speicherprinzip zur unveränderlichen Ablage; relevant für revisionssichere Archivierung. |
