"""Shared response-gateway and draft text markers for the offline MVP."""

RESPONSE_DRAFT_VISIBILITY_MARKERS = ("entwurf", "draft")
RESPONSE_HUMAN_REVIEW_VISIBILITY_MARKERS = ("human review", "pruefung")
PRODUCTIVE_TRANSMISSION_MARKER = "produktive uebermittlung"
PRODUCTIVE_TRANSMISSION_NEGATION_MARKER = "keine produktive uebermittlung"
TAX_ADVICE_MARKER = "steuerberatung"
TAX_ADVICE_NEGATION_MARKER = "keine steuerberatung"

DRAFT_REVIEW_DISCLAIMER = (
    "Entwurf: fachliche Pruefung durch die Kanzlei erforderlich."
)
NO_TAX_ADVICE_OR_PRODUCTIVE_TRANSMISSION_DISCLAIMER = (
    "Keine Steuerberatung, keine Berechnung und keine produktive Uebermittlung."
)

HUMAN_REVIEW_GATE_TITLE_PREFIX = "Offline-MVP Human Review Gate fuer"
OFFLINE_DRAFT_TITLE_PREFIX = "Offline-MVP Entwurf fuer"
HUMAN_REVIEW_GATE_STOPPED_SUMMARY = (
    "Human Review Gate: automatische Offline-Mock-Fortsetzung gestoppt."
)
NO_AUTOMATIC_COMMUNICATION_BEFORE_HUMAN_REVIEW_NOTE = (
    "Keine automatische Rueckfragenkommunikation oder fachliche "
    "Inhaltsausgabe vor Human Review."
)
NO_DATEV_ELSTER_TRANSFER_NOTE = "keine Agenda-, DATEV- oder ELSTER-Uebertragung."
MANUAL_HANDOFF_DRAFT_NOTE = (
    "Nur manueller Handoff-Entwurf; keine Agenda-, DATEV- oder ELSTER-Uebertragung."
)
REVIEW_BEFORE_USE_NOTE = (
    "Vor jeder fachlichen Nutzung sind Gateway- und Kanzlei-Review zu pruefen."
)
REVIEW_HANDOFF_ARTIFACT_NOTICE = (
    "Draft-/Review-Artefakt fuer den Offline-MVP. Nicht final."
)
REVIEW_HANDOFF_NO_EXTERNAL_ACTION_NOTICE = (
    "Dieses Markdown nutzt nur vorhandene Offline-MVP-Workflowdaten. "
    "Es erzeugt keine fachliche Freigabe und fuehrt keine externe Aktion aus."
)
REVIEW_HANDOFF_CLOSING_NOTE = (
    "Fachliche Nutzung, Weitergabe oder Uebernahme in nachgelagerte "
    "Arbeitsprozesse erfordert menschliche Pruefung und Freigabe."
)
