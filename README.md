# Flask Webhook Server with OpenAI LLM Integration (Techstax Assignment)

This repository contains a lightweight Flask server that handles incoming POST webhooks — typically triggered by GitHub Actions — and processes the payload using OpenAI’s GPT-3.5 model via API.

It is designed to work alongside the action-repo, which sends webhooks on every push and every pull request merge to the main branch. The server generates smart summaries or changelog-style messages using LLM prompting.
