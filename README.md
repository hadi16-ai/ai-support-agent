# 🤖 AI Support Triage Agent

🚀 Built in 24 hours during HackerRank Orchestrate Hackathon  

An AI-powered system that classifies support tickets, decides whether to escalate or respond, and generates contextual replies across multiple domains.

---

## 🧠 Problem

Customer support teams handle thousands of tickets daily.  
Manually triaging them is slow, inconsistent, and error-prone.

This project automates:
- Ticket classification
- Decision making (Reply vs Escalate)
- Response generation

---

## ⚙️ Features

- Multi-domain support (HackerRank, Claude, Visa)
- Intelligent routing (Escalate vs Reply)
- Context-aware response generation
- Structured CSV-based pipeline

---

## 🏗️ How It Works

1. Input → Support tickets (CSV)
2. Classification → Identify domain
3. Decision → Escalate or reply
4. Response → Generated using LLM
5. Output → Stored in CSV format

---

## 📊 Sample Output

| ticket_id | domain | action   | response                     |
|----------|--------|----------|------------------------------|
| 101      | Claude | Replied  | Please try resetting...      |
| 102      | Visa   | Escalated| Requires manual verification |

> Full outputs available in `support_issues/` and `support_tickets/`

---

## ⚙️ Tech Stack

- Python  
- Claude API (via OpenRouter)  
- Prompt Engineering  
- CSV Processing  

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
python code/main.py
