# PrintMonitor

A web-based monitoring dashboard for the **FlashForge Adventurer 4** 3D printer.

PrintMonitor allows you to monitor your printer's status, temperatures, progress, and live camera feed from a computer or smartphone connected to the same local network.

## Features

- **Automatic printer discovery** — finds the printer on the local network without requiring a manually configured IP address.
- **Live camera stream** — displays the printer's camera feed directly in the dashboard.
- **Multi-device camera streaming** — shares a single connection to the printer's camera between multiple clients.
- **Printer telemetry** — retrieves temperature, machine status, and printing information.
- **Automatic reconnection** — attempts to reconnect when the printer becomes unavailable.
- **Local network access** — open the dashboard from a phone, tablet, or computer.
- **Responsive web interface** — designed for convenient monitoring across devices.

## Android App

PrintMonitor also includes an Android APK that provides a dedicated browser-based app experience for the monitoring dashboard.

The APK is available in the repository's **[Releases](../../releases)** section.

The app acts as a lightweight browser wrapper for the web interface, allowing you to access PrintMonitor more conveniently from an Android device connected to the same local network.

## Tech Stack

### Backend
- Python
- FastAPI
- Uvicorn
- Socket communication
- MJPEG streaming

### Frontend
- React
- TypeScript
- Vite
- CSS

## Architecture

```text
                 FlashForge Adventurer 4
                    /             \
          Control interface     Camera
             Port 8899         Port 8080
                  \               /
                   \             /
                    Python Backend
                       FastAPI
                         |
                  Local Network API
                         |
                  React Frontend
                    /         \
               Computer     Smartphone
```

The backend communicates with the printer, retrieves telemetry, and maintains a shared camera connection. Multiple frontend clients can receive the same video stream without opening separate connections to the printer.

## Requirements

- Windows 10/11
- Python 3
- Node.js and npm
- FlashForge Adventurer 4
- Computer and printer connected to the same local network

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/PrintMonitor.git
cd PrintMonitor
```

### 2. Install backend dependencies

```bash
cd backend
py -m pip install fastapi uvicorn
```

### 3. Install frontend dependencies

Open another terminal:

```bash
cd frontend
npm install
```

## Running

Start the backend:

```bash
cd backend
py -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Open the dashboard:

```text
http://localhost:5173
```

To access it from another device on the same network, use your computer's local IP address:

```text
http://YOUR_COMPUTER_IP:5173
```

Make sure Windows Firewall allows connections to ports `5173` and `8000`.

## API Endpoints

| Endpoint | Description |
|---|---|
| `/api/health` | Backend health check |
| `/api/status` | Printer
