import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import sys
import subprocess

def auto_install(packages):
    """Checks and install imports."""
    for package, import_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"[Bootstrapping] Module {package} not found. Installing...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--break-system-packages"
                ])
                print(f"[Bootstrapping] {package} successfully installed!")
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                except Exception as e:
                    print(f"Critical error while installing {package}: {e}")
                    sys.exit(1)

REQUIRED_PACKAGES = {
    "pygame": "pygame",
    "requests": "requests",
    "Pillow": "PIL"
}

auto_install(REQUIRED_PACKAGES)

import socket
import threading
import pygame
import requests
import io
import sys
from PIL import Image
import time
ZOOM = 15

print("The script is the recipient of data from the Traccar Suckless mobile application.")
print("The script can be run anywhere, the main thing is that there are imports.")
print("mouse button 4: zoom in, mouse button 5: zoom out, space: synchro with center")

try:
    user_input = input("Enter UDP port [default 8080]: ").strip()
    if user_input == "":
        UDP_PORT = 8080
    else:
        UDP_PORT = int(user_input)
except ValueError:
    print("Incorrect port! Trying default port...")
    UDP_PORT = 8080
except KeyboardInterrupt:
    print("\nLaunch stopped.")
    sys.exit(0)

print(f"[system] Launching {UDP_PORT}...")


coords_received = False
lock = threading.Lock()

def udp_receiver():
    global current_lat, current_lon, coords_received
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            text = data.decode('utf-8')
            parts = text.split(',')
            if len(parts) == 2:
                with lock:
                    current_lat = float(parts[0])
                    current_lon = float(parts[1])
                    coords_received = True
                print(f"[UDP] Updated: {current_lat}, {current_lon}")
        except Exception as e:
            print(f"Error UDP: {e}")

threading.Thread(target=udp_receiver, daemon=True).start()

import math

current_lat = None
current_lon = None
coords_received = False

def latlon_to_tile(lat, lon, ZOOM):
    lat_rad = math.radians(lat)
    n = 2.0 ** ZOOM
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return int(xtile), int(ytile)

def download_map_tile(lat, lon, ZOOM, width=600, height=600):
    if ZOOM == None:
        ZOOM = 15
    print("[OSM] Assembling tiles from CartoDB (OpenStreetMap)...")
    
    xtile_cent, ytile_cent = latlon_to_tile(lat, lon, ZOOM)
    
    grid_size = 3
    stitch_surface = pygame.Surface((grid_size * 256, grid_size * 256))
    stitch_surface.fill((30, 30, 30))
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    start_x = xtile_cent - 1
    start_y = ytile_cent - 1
    
    tiles_loaded = 0
    
    for i in range(grid_size):
        for j in range(grid_size):
            x = int(start_x + i)
            y = int(start_y + j)
            
            url = f"https://basemaps.cartocdn.com/rastertiles/voyager/{ZOOM}/{x}/{y}.png"
            
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200 and b"PNG" in res.content[:10]:
                    pil_img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                    raw_data = pil_img.tobytes()
                    tile_img = pygame.image.fromstring(raw_data, pil_img.size, "RGBA")
                    stitch_surface.blit(tile_img, (i * 256, j * 256))
                    tiles_loaded += 1
                else:
                    print(f"[OSM] Server returned HTTP {res.status_code} for tile {x},{y}")
            except Exception as e:
                print(f"[OSM] Internet ({url}) error on tile {x},{y}: {e}")

    if tiles_loaded == 0:
        print("[OSM] Failed downloading tailes. Enabling offline mode.")
        for r in range(40, stitch_surface.get_width() // 2, 40):
            pygame.draw.circle(stitch_surface, (50, 70, 50), (stitch_surface.get_width()//2, stitch_surface.get_height()//2), r, 1)

    final_surface = pygame.Surface((width, height))
    n = 2.0 ** ZOOM
    x_exact = (lon + 180.0) / 360.0 * n
    y_exact = (1.0 - math.log(math.tan(math.radians(lat)) + (1.0 / math.cos(math.radians(lat)))) / math.pi) / 2.0 * n
    
    pixel_x = int((x_exact - start_x) * 256)
    pixel_y = int((y_exact - start_y) * 256)
    
    crop_x = pixel_x - (width // 2)
    crop_y = pixel_y - (height // 2)
    
    final_surface.blit(stitch_surface, (0, 0), (crop_x, crop_y, width, height))
    return final_surface

pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Traccar Suckless Map")
clock = pygame.time.Clock()

map_image = None
center_lat, center_lon = current_lat, current_lon

print("Awaiting coordinates from phone to build map...")

running = True
smooth_lat, smooth_lon = None, None
ALPHA = 0.15
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: 
                if ZOOM < 19:
                    ZOOM += 1
                    map_image = None
                    print(f"Zoom in.. {ZOOM}")
            elif event.button == 5: 
                if ZOOM > 1:
                    ZOOM -= 1
                    map_image = None
                    print(f"Zoom out.. {ZOOM}")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: 
                with lock:
                    if coords_received:
                        center_lat, center_lon = current_lat, current_lon
                        map_image = None
                        print("[system] center synchronized")

    with lock:
        lat, lon = current_lat, current_lon
        ready = coords_received

    if ready:
        if smooth_lat is None:
            smooth_lat, smooth_lon = lat, lon
        else:
            smooth_lat = smooth_lat * (1 - ALPHA) + lat * ALPHA
            smooth_lon = smooth_lon * (1 - ALPHA) + lon * ALPHA

        if map_image is None:
            center_lat, center_lon = lat, lon
            map_image = download_map_tile(center_lat, center_lon, ZOOM)

    screen.fill((30, 30, 30))

    if map_image:
        screen.blit(map_image, (0, 0))
        
        n = 2.0 ** ZOOM
        
        def lon_to_x(ln): return (ln + 180.0) / 360.0 * n * 256
        def lat_to_y(lt): return (1.0 - math.log(math.tan(math.radians(lt)) + (1.0 / math.cos(math.radians(lt)))) / math.pi) / 2.0 * n * 256
        
        dx = lon_to_x(smooth_lon) - lon_to_x(center_lon)
        dy = lat_to_y(smooth_lat) - lat_to_y(center_lat)
        
        marker_x = int(WIDTH / 2 + dx)
        marker_y = int(HEIGHT / 2 + dy)
        
        if 0 <= marker_x <= WIDTH and 0 <= marker_y <= HEIGHT:
            pygame.draw.circle(screen, (255, 255, 255), (marker_x, marker_y), 10)
            pygame.draw.circle(screen, (0, 150, 255), (marker_x, marker_y), 7)
        else:
            pygame.draw.circle(screen, (40, 60, 40), (WIDTH // 2, HEIGHT // 2), 150, 2)
            pygame.draw.circle(screen, (40, 60, 40), (WIDTH // 2, HEIGHT // 2), 80, 1)
            if int(time.time() * 2) % 2 == 0:
                pygame.draw.circle(screen, (0, 255, 0), (WIDTH // 2, HEIGHT // 2), 8)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()