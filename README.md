# Virgocreativo AI Voice Agent

An AI-powered business voice agent built for Virgocreativo.

## Features

- RAG-based business knowledge retrieval
- FastAPI backend
- Business lead capture
- Consultation availability checking
- Google Calendar booking
- Double-booking prevention
- Human handoff
- Guardrails for unknown questions

## Tech Stack

- Python
- FastAPI
- Sentence Transformers
- Scikit-learn
- Vapi
- Google Apps Script
- Google Calendar
- Google Sheets
- ngrok

## Architecture

Caller → Vapi → FastAPI → RAG / Business Tools → Google Calendar / Google Sheets

## Status

The backend API, RAG retrieval, lead capture, calendar availability, booking, and human handoff workflows have been tested independently.