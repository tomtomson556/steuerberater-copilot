# Main Branch Protection Policy

## Zweck

Dieses Dokument beschreibt die verbindliche Schutzregel für den Hauptbranch
`main` im Repository **steuerberater-copilot**.

## Verbindliche Regel

`main` ist der geschützte Hauptbranch.

Direkter Push auf `main` ist für Menschen und Agenten verboten. Änderungen an
`main` erfolgen ausschließlich über einen separaten Branch und Pull Request.

Fast Develop, Cursor, Codex, Copilot oder andere Agenten dürfen niemals direkt
auf `main` pushen und niemals selbst mergen. Agenten dürfen Pull Requests
vorbereiten oder erstellen, aber nicht ohne Human Review zusammenführen.

Vor einem Merge müssen die relevanten lokalen Checks grün sein. KI-Ausgaben
bleiben Entwürfe und Human Review bleibt verpflichtend.

## GitHub-Regel

Sobald die GitHub Actions CI nach dem ersten Pull Request verfügbar ist, soll
`main` zusätzlich in GitHub über Branch Protection oder ein Ruleset geschützt
werden.

Empfohlene GitHub-Regel:

- Require a pull request before merging
- Require status checks to pass before merging
- Require branch to be up to date before merging
- Block force pushes
- Block deletions
- Restrict direct pushes to `main`
- Keine Agenten als Bypass-Akteure eintragen

Die tatsächliche GitHub-Branch-Protection- oder Ruleset-Einstellung ist eine
Repository-Admin-Einstellung. Sie darf nicht durch Agenten umgangen werden. Die
Aktivierung erfolgt durch den Repository-Owner.
