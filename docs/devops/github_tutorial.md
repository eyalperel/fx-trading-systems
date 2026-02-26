# Git & GitHub – practical notes

## 1) mental model
- git = local timeline
- github = remote copy + prs/ci/reviews
- branch per change → pr → ci → merge

## 2) daily commands
git status
git add -A
git commit -m "feat: summary"
git checkout -b feature/my-change
git log --oneline -n 5

## 3) first remote push (we’ll do on day 1)
git remote add origin https://github.com/<you>/ehlers-trading-systems.git
git push -u origin main
