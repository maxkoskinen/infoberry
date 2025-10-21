# Infoberry

This project turns Raspberry Pis into simple digital signage devices that can display web pages.

## What's This About?

Infoberry transforms Raspberry Pis (or really any device that can run Chromium) into display machines. Show off web pages, images, videos, or whatever you want on screens around your home, office, or tech cave.

It’s made up of two parts:

### 🍓 Client

The client runs on your Raspberry Pi and handles all the heavy lifting:

- **Displays stuff in kiosk mode** - Full-screen Chromium with no distractions
- **Rotates through your content** - URLs, images, videos, local HTML files—you name it
- **Auto-reloads** - Set refresh intervals so your content stays fresh
- **Hot-reloads config** - Edit your YAML config file and watch it update live
- **Screen rotation support** - Because sometimes monitors are mounted weird



### 🖥️ Server (Coming Soon™)

The server will eventually let you manage all your displays from one place. For now, we're keeping it simple with file-based configs. The old server got the axe during a refactor/rewrite 

## Quick Start

### 1. Installation

You can install Infoberry directly from the repository or from PyPI once published.

#### Option 1: Clone and install in editable mode

```bash
git clone https://github.com/maxkoskinen/infoberry.git
cd infoberry
pip install -e .
```

#### Option 2: Install directly via pip

```bash
pip install https://github.com/maxkoskinen/infoberry
```

Then, install Chromium for Playwright:

```bash
playwright install chromium
```

---

### 2. Configuration

Create a configuration file (for example, `client-config.yaml`) or use the provided example configuration.

---

### 3. Running the Client

Run the Infoberry client with your config:

```bash
info-berry-client -c client-config.yaml
```

The `--log-level` flag is optional.
For more options and help:

```bash
info-berry-client -h
```

---

## Content Types Supported

- **URLs** - Any web page (weather dashboards, whatever)
- **Images** - PNG, JPG, GIF—if your browser can show it, so can infoberry
- **Videos** - MP4, WebM, and friends (with autoplay and looping)
- **HTML files** - Local HTML for custom layouts

