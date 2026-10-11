# Uzhavan Express Telegram Availability Bot

Checks the upcoming Thursday and Friday journeys and sends one Telegram message.

## Configured journeys
- Thursday outbound: train 16866, Kumbakonam (KMU) -> Chennai Egmore (MS)
- Friday return: train 16865, Chennai Egmore (MS) -> Kumbakonam (KMU)
- Defaults: class SL, quota GN

**Before relying on alerts, verify the train numbers/directions, class and quota with RailRadar/IRCTC.** Compare API results against the official booking site, especially if the API response indicates a database source.

## Run locally
1. Install Python 3.9+.
2. Create and activate a virtual environment: `python -m venv .venv`
3. Install packages: `pip install -r requirements.txt`
4. Set environment variables `RAILRADAR_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`.
5. Run `python train_alert.py`.

Never hardcode secrets in the Python file or commit them. If an old Telegram token was exposed, revoke it in BotFather and use a new one.

## GitHub Actions setup
1. Upload this folder to a private GitHub repository.
2. Go to **Settings -> Secrets and variables -> Actions**.
3. Add repository secrets `RAILRADAR_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`.
4. Add repository variable `RAILRADAR_MONTHLY_LIMIT` using the actual quota shown in your RailRadar account. The script's fallback is 1000, but provider limits can differ.
5. Ensure workflow permissions allow contents read/write.
6. Run the workflow manually from **Actions** to test. The recurring schedule is Monday at 09:00 IST.

GitHub scheduled workflows may start late during busy periods.

## Usage counter
`usage.json` counts this bot's calls and resets by India-local calendar month. GitHub Actions commits counter changes to the repository. This is only a local estimate; it excludes API calls made elsewhere and is not the provider's authoritative usage balance. If a network failure occurs, provider-side usage may be uncertain.

Telegram Bot API messaging is free; RailRadar quota and rate limits depend on the provider plan.
