# Infoberry

This project turns Raspberry Pis into simple digital signage devices that can display web pages.

It’s made up of two parts:

### 🖥️ Server

The server is where everything is managed. You can:

- Set which web pages each Pi should display
- Schedule when screens turn on or off
- Configure multiple URLs for a screen to cycle through

### 🍓 Client

The client runs on the Raspberry Pis. Each Pi:

- Polls the server regularly for settings
- Displays the assigned web pages in fullscreen
- Supports cycling between multiple pages if configured