import queue
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from urllib.request import urlopen

from printer import get_status, find_printer


app = FastAPI(title="PrintMonitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Общий видеопоток камеры
CAMERA_CONTENT_TYPE = (
    "multipart/x-mixed-replace;boundary=boundarydonotcross"
)

subscribers = set()
subscribers_lock = threading.Lock()
camera_thread = None


def broadcast(data):
    with subscribers_lock:
        clients = list(subscribers)

    for client in clients:
        try:
            client.put_nowait(data)

        except queue.Full:
            try:
                client.get_nowait()
            except queue.Empty:
                pass

            try:
                client.put_nowait(data)
            except queue.Full:
                pass


def camera_worker():
    print("Camera worker started.")

    while True:
        ip = find_printer()

        if not ip:
            print("Camera: printer not found. Retrying...")
            time.sleep(3)
            continue

        camera_url = f"http://{ip}:8080/?action=stream"

        try:
            print(f"Connecting to camera: {ip}")

            with urlopen(camera_url, timeout=8) as camera:
                print("Camera connected.")

                while True:
                    chunk = camera.read1(8192)

                    if not chunk:
                        raise ConnectionError(
                            "Camera stream closed."
                        )

                    broadcast(chunk)

        except Exception as error:
            print(f"Camera connection lost: {error}")

            find_printer(force=True)

            time.sleep(2)


def subscribe_camera():
    global camera_thread

    client_queue = queue.Queue(maxsize=30)

    with subscribers_lock:
        subscribers.add(client_queue)

        if (
            camera_thread is None
            or not camera_thread.is_alive()
        ):
            camera_thread = threading.Thread(
                target=camera_worker,
                daemon=True
            )

            camera_thread.start()

    return client_queue


def camera_generator(client_queue):
    try:
        while True:
            try:
                chunk = client_queue.get(timeout=30)
                yield chunk

            except queue.Empty:
                continue

    finally:
        with subscribers_lock:
            subscribers.discard(client_queue)


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "application": "PrintMonitor"
    }


@app.get("/api/status")
def printer_status():
    return get_status()


@app.get("/api/camera/stream")
def camera_stream():
    client_queue = subscribe_camera()

    return StreamingResponse(
        camera_generator(client_queue),
        headers={
            "Content-Type": CAMERA_CONTENT_TYPE,
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
