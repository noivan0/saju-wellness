# 사주담 (Sajudam)

> **MVP / Alpha** — AI 사주팔자 + 감정 코칭 서비스. 20–40대 한국 여성 타겟.

---

## 🇰🇷 소개 | 🇺🇸 Overview

**[한글]**
사주팔자 기반 AI 운세 해석과 감정 코칭을 결합한 서비스입니다.
단순한 운세 풀이를 넘어, 사용자의 감정 상태를 이해하고 동양 인문학적 시각으로 위로와 방향을 제시합니다.

**[English]**
Sajudam combines traditional Korean Four Pillars (Saju) astrology with AI-powered emotional coaching.
Beyond fortune-telling, it understands the user's emotional state and provides comfort and direction through an Eastern humanistic lens.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔮 AI Saju Reading | Four Pillars analysis with personalized narrative — not template-based |
| 💬 Emotional Coaching | Sentiment-aware responses that adapt to user's emotional state |
| 🎁 Free Event Mode | Admin-managed free coaching events for community building |
| 🌏 Multilingual | Korean · Japanese · English — independent per-language builds |
| 🔒 Security | JWT HttpOnly/SameSite=Strict — CRITICAL 0 / HIGH 0 (NOVA audit certified) |
| 📊 SSE Push | Real-time streaming response via Server-Sent Events |

---

## 🧠 Design Principles

- **Maslach framework** — Emotional burnout detection patterns to tailor coaching depth
- **Eastern humanism** — Responses grounded in Korean/Chinese philosophical traditions (음양오행)
- **Dark mystique UX** — Deep indigo palette evoking cosmic, contemplative atmosphere

---

## 🛠 Tech Stack

```
Backend   FastAPI · PostgreSQL · Redis · Anthropic Claude API
Auth      JWT (HttpOnly Cookie, SameSite=Strict)
Frontend  React · SSE streaming
Infra     Docker · async architecture
Security  OWASP LLM Top 10 · CRITICAL 0 / HIGH 0 (NOVA audit certified)
```

---

## 📱 App Preview

> MVP — UI design tokens defined. Core API complete.

**Design System**
- Background: `#0F0A1E` (Deep indigo — cosmic atmosphere)
- Primary: `#8B5CF6` (Violet — mystique & wisdom)
- Accent: `#F59E0B` (Amber — Eastern warmth)
- Font: Pretendard

---

## 📌 Status

```
✅ Saju calculation engine complete
✅ AI coaching API complete
✅ Security audit passed (CRITICAL 0 / HIGH 0)
✅ Multilingual architecture designed (KO / JA / EN)
🔧 Frontend MVP in progress
⏳ Pending: .env credentials for deployment
```

---

## 🔗 Related

- [NOVA OSS](https://github.com/noivan0/NOVA) — Agent framework powering this app
- [noivan0 Portfolio](https://noivan0.github.io/noivan-portfolio/)
