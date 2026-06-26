# Main Branch Protection Policy

## Zweck

Dieses Dokument beschreibt die verbindliche Schutzregel fuer den Hauptbranch
`main` im Repository **steuerberater-copilot**.

## Verbindliche Regel

`main` ist der geschuetzte Hauptbranch.

Direkter Push auf `main` ist fuer Menschen und Agenten verboten. Aenderungen an
`main` erfolgen ausschliesslich ueber einen separaten Branch und Pull Request.

Fast Develop, Cursor, Codex, Copilot oder andere Agenten duerfen niemals direkt
auf `main` pushen und niemals selbst mergen. Agenten duerfen Pull Requests
vorbereiten oder erstellen, aber nicht ohne Human Review zusammenfuehren.

Vor einem Merge muessen die relevanten lokalen Checks gruen sein. KI-Ausgaben
bleiben Entwuerfe und Human Review bleibt verpflichtend.

## GitHub-Regel

Sobald die GitHub Actions CI nach dem ersten Pull Request verfuegbar ist, soll
`main` zusaetzlich in GitHub ueber Branch Protection oder ein Ruleset geschuetzt
werden.

Empfohlene GitHub-Regel:

- Require a pull request before merging
- Require status checks to pass before merging
- Require branch to be up to date before merging
- Block force pushes
- Block deletions
- Restrict direct pushes to `main`
- Keine Agenten als Bypass-Akteure eintragen

Die tatsaechliche GitHub-Branch-Protection- oder Ruleset-Einstellung ist eine
Repository-Admin-Einstellung. Sie darf nicht durch Agenten umgangen werden. Die
Aktivierung erfolgt durch den Repository-Owner.
