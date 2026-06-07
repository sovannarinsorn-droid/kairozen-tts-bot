# 🔊 Kairozen Bot

Telegram bot ពហុមុខងារ: TTS ខ្មែរ + ស្វែងរកចម្រៀង + ដោនវីដេអូ

## ✨ Features
| មុខងារ | ការពិពណ៌នា |
|--------|------------|
| 🔊 TTS | បំប្លែងអក្សរជាសម្លេងខ្មែរ (Piseth/Sreymom) |
| 🎵 ស្វែងរក | រកចម្រៀងតាមចំណងជើង → ដោន MP3/MP4 |
| 📥 ដោន | ដោនពី YouTube/TikTok/Facebook តាម link |

## 🎙️ Voices
- `km-KH-PisethNeural` — ប្រុស
- `km-KH-SreymomNeural` — ស្រី

## 🚀 Setup នៅ Termux

```bash
pkg install ffmpeg python
pip install -r requirements.txt

cp .env.example .env
nano .env   # បំពេញ BOT_TOKEN

python bot.py
```

## ⚠️ Note
- ffmpeg ត្រូវការសម្រាប់ convert MP3
- Video ដោនបានត្រឹម 50MB (Telegram limit)
- `.env` ការពារដោយ `.gitignore`
