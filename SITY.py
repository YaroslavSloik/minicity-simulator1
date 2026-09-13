import pygame
import sys
import random
import math

pygame.init()
pygame.mixer.init()

try:
    pygame.mixer.music.load("background_music.mp3")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.3)
except Exception:
    print("Попередження: Музичний файл не знайдено.")

WIDTH = 1100
HEIGHT = 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Міні Місто")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 20)
small_font = pygame.font.SysFont("arial", 16)
big_font = pygame.font.SysFont("arial", 32, bold=True)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GREEN = (180, 220, 160)
GRID = (150, 180, 140)
PANEL = (235, 235, 235)
ROAD = (120, 120, 120)

money = 5000
population = 0
happiness = 60
day = 1
city = []

CELL = 75
CITY_LEFT = 30
CITY_TOP = 100
GRID_W = 12
GRID_H = 6
selected_building = None

BUILDINGS = {
    "house": {"name": "🏠 Будинок", "price": 200, "income": 20, "population": 5, "happiness": 0,
              "color": (210, 170, 120)},
    "apartments": {"name": "🏢 Багатоповерхівка", "price": 700, "income": 80, "population": 25, "happiness": -1,
                   "color": (160, 170, 190)},
    "shop": {"name": "🏪 Магазин", "price": 500, "income": 100, "population": 0, "happiness": 2,
             "color": (220, 150, 190)},
    "factory": {"name": "🏭 Фабрика", "price": 1200, "income": 250, "population": 0, "happiness": -7,
                "color": (100, 100, 110)},
    "hospital": {"name": "🏥 Лікарня", "price": 1500, "income": -50, "population": 0, "happiness": 10,
                 "color": (240, 240, 240)},
    "school": {"name": "🏫 Школа", "price": 1000, "income": -30, "population": 0, "happiness": 8,
               "color": (230, 190, 90)},
    "park": {"name": "🌳 Парк", "price": 400, "income": 0, "population": 0, "happiness": 12, "color": (90, 180, 90)},
    "power": {"name": "⚡ Електростанція", "price": 1300, "income": 150, "population": 0, "happiness": -5,
              "color": (240, 180, 70)},
    "fire": {"name": "🚒 Пожежна частина", "price": 900, "income": -20, "population": 0, "happiness": 6,
             "color": (220, 70, 60)},
    "bank": {"name": "🏦 Банк", "price": 2000, "income": 400, "population": 0, "happiness": 3, "color": (120, 170, 210)}
}

IMAGES_CONFIG = {
    "house": "house.png",
    "apartments": "apartments.png",
    "shop": "shop.png",
    "factory": "factory.png",
    "hospital": "hospital.png",
    "school": "school.png",
    "park": "park.png",
    "power": "power.png",
    "fire": "fire.png",
    "bank": "bank.png"
}

BUILDING_IMAGES = {}
for key, filename in IMAGES_CONFIG.items():
    try:
        img = pygame.image.load(filename)
        img = pygame.transform.scale(img, (CELL - 10, CELL - 10))
        BUILDING_IMAGES[key] = img.convert_alpha()
    except Exception:
        BUILDING_IMAGES[key] = None

buttons = []
building_keys = list(BUILDINGS.keys())
button_y = 575
for i, key in enumerate(building_keys):
    x = 20 + (i % 5) * 215
    y = button_y + (i // 5) * 55
    rect = pygame.Rect(x, y, 200, 45)
    buttons.append((key, rect))


def draw_text(text, x, y, used_font=font, color=BLACK):
    image = used_font.render(text, True, color)
    screen.blit(image, (x, y))


def cell_free(col, row):
    x = CITY_LEFT + col * CELL
    y = CITY_TOP + row * CELL
    for b in city:
        if b["rect"].x == x + 5 and b["rect"].y == y + 5:
            return False
    return True


def build(building_type, col, row):
    global money, population, happiness
    data = BUILDINGS[building_type]
    if money < data["price"] or not cell_free(col, row):
        return
    x = CITY_LEFT + col * CELL
    y = CITY_TOP + row * CELL
    rect = pygame.Rect(x + 5, y + 5, CELL - 10, CELL - 10)
    city.append({"type": building_type, "rect": rect, "fire_days": 0})
    money -= data["price"]
    population += data["population"]
    happiness = max(0, min(100, happiness + data["happiness"]))


def next_day():
    global money, day, happiness, population
    has_fire_station = any(b["type"] == "fire" for b in city)

    # 1. Базовий прибуток від будівель без пожежі
    base_income = 0
    for b in city:
        if b["fire_days"] == 0:
            base_income += BUILDINGS[b["type"]]["income"]

    # 2. Модифікатор прибутку від рівня щастя
    if happiness >= 80:
        multiplier = 1.10
    elif happiness >= 50:
        multiplier = 1.05
    elif happiness >= 25:
        multiplier = 1.00
    else:
        multiplier = 0.80

    final_income = int(base_income * multiplier)

    # 3. Логіка пожеж
    survived_city = []
    for b in city:
        if b["fire_days"] > 0:
            if has_fire_station:
                b["fire_days"] = 0
                survived_city.append(b)
            else:
                b["fire_days"] += 1
                if b["fire_days"] < 3:
                    survived_city.append(b)
                else:
                    population -= BUILDINGS[b["type"]]["population"]
                    happiness = max(0, happiness - 5)
        else:
            survived_city.append(b)

    city[:] = survived_city

    # 4. Шанс нової пожежі
    if city:
        fire_chance = 0.05 if has_fire_station else 0.25
        if random.random() < fire_chance:
            not_burning = [b for b in city if b["fire_days"] == 0]
            if not_burning:
                random_b = random.choice(not_burning)
                random_b["fire_days"] = 1

    # 5. Штрафи та бонуси від забудови
    if len(city) > 25:
        max(0, happiness - 1)
    parks = sum(1 for b in city if b["type"] == "park")
    if parks >= 3:
        happiness += 2

    happiness = max(0, min(100, happiness))
    money += final_income
    day += 1


def draw_building(b_dict):
    building_type = b_dict["type"]
    rect = b_dict["rect"]
    fire_days = b_dict["fire_days"]

    if BUILDING_IMAGES[building_type] is not None:
        screen.blit(BUILDING_IMAGES[building_type], rect)
    else:
        data = BUILDINGS[building_type]
        color = data["color"]
        pygame.draw.rect(screen, color, rect, border_radius=5)
        if building_type == "house":
            pygame.draw.polygon(screen, (170, 70, 70),
                                [(rect.left, rect.top + 20), (rect.centerx, rect.top - 5), (rect.right, rect.top + 20)])
            pygame.draw.rect(screen, (80, 160, 220), (rect.centerx - 12, rect.centery, 24, 20))
        elif building_type == "apartments":
            for i in range(3):
                for j in range(2):
                    pygame.draw.rect(screen, (90, 150, 210), (rect.x + 10 + j * 25, rect.y + 10 + i * 18, 15, 10))
        elif building_type == "shop":
            pygame.draw.rect(screen, (220, 70, 90), (rect.x, rect.y, rect.width, 15))
            pygame.draw.rect(screen, (80, 160, 220), (rect.centerx - 18, rect.centery - 5, 36, 25))
        elif building_type == "factory":
            pygame.draw.rect(screen, (70, 70, 70), (rect.x + 20, rect.y - 10, 12, 30))
            pygame.draw.rect(screen, (70, 70, 70), (rect.x + 45, rect.y - 20, 12, 40))
        elif building_type == "hospital":
            pygame.draw.rect(screen, (220, 50, 50), (rect.centerx - 7, rect.y + 12, 14, 35))
            pygame.draw.rect(screen, (220, 50, 50), (rect.centerx - 17, rect.y + 22, 35, 14))
        elif building_type == "school":
            pygame.draw.rect(screen, (235, 200, 120), rect)
            pygame.draw.rect(screen, (180, 100, 70), (rect.x - 3, rect.y - 5, rect.width + 6, 10))
            for i in range(3):
                pygame.draw.rect(screen, (80, 160, 220), (rect.x + 8 + i * 20, rect.y + 22, 14, 15))
            pygame.draw.rect(screen, (90, 80, 70), (rect.centerx - 10, rect.y + 45, 20, 25))
            pygame.draw.rect(screen, (245, 245, 245), (rect.x + 10, rect.y + 5, rect.width - 20, 13))
        elif building_type == "park":
            pygame.draw.circle(screen, (40, 140, 50), (rect.x + 20, rect.y + 25), 13)
            pygame.draw.circle(screen, (40, 140, 50), (rect.x + 50, rect.y + 35), 15)
            pygame.draw.circle(screen, (40, 140, 50), (rect.x + 35, rect.y + 55), 14)
        elif building_type == "power":
            pygame.draw.polygon(screen, (255, 230, 70),
                                [(rect.centerx + 5, rect.y + 5), (rect.centerx - 8, rect.y + 35),
                                 (rect.centerx + 3, rect.y + 35), (rect.centerx - 5, rect.y + 65),
                                 (rect.centerx + 18, rect.y + 25), (rect.centerx + 5, rect.y + 25)])
        elif building_type == "fire":
            pygame.draw.circle(screen, (255, 180, 30), (rect.centerx, rect.centery), 18)
        elif building_type == "bank":
            pygame.draw.polygon(screen, (230, 230, 230),
                                [(rect.left + 5, rect.y + 20), (rect.centerx, rect.y), (rect.right - 5, rect.y + 20)])
            for i in range(3):
                pygame.draw.rect(screen, (230, 230, 230), (rect.x + 12 + i * 20, rect.y + 30, 10, 30))

    if fire_days > 0:
        fire_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        alpha = 100 + int(40 * math.sin(pygame.time.get_ticks() * 0.01))
        fire_surf.fill((255, 60, 0, max(50, min(200, alpha))))
        screen.blit(fire_surf, rect.topleft)
        pygame.draw.rect(screen, (255, 0, 0), rect, 3, border_radius=5)
        draw_text(f"🔥 {fire_days}д", rect.x + 5, rect.y + 5, small_font, WHITE)


def draw_city():
    screen.fill((205, 225, 200))
    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, 80))
    draw_text("🏙 МІНІ МІСТО", 20, 20, big_font)
    draw_text(f"💰 Гроші: {money}", 300, 25)
    draw_text(f"👥 Населення: {population}", 470, 25)
    draw_text(f"😊 Щастя: {happiness}%", 710, 25)
    draw_text(f"📅 День: {day}", 900, 25)

    for row in range(GRID_H):
        for col in range(GRID_W):
            x = CITY_LEFT + col * CELL
            y = CITY_TOP + row * CELL
            pygame.draw.rect(screen, GREEN, (x, y, CELL - 2, CELL - 2))
            pygame.draw.rect(screen, GRID, (x, y, CELL - 2, CELL - 2), 1)

    for b in city:
        draw_building(b)


def draw_buttons():
    pygame.draw.rect(screen, PANEL, (0, 560, WIDTH, 190))
    for building_type, rect in buttons:
        active = (selected_building == building_type)
        color = (180, 220, 255) if active else (220, 220, 220)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, (130, 130, 130), rect, 2, border_radius=8)
        data = BUILDINGS[building_type]
        draw_text(f"{data['name']} — {data['price']}₴", rect.x + 8, rect.y + 12, small_font)

    next_rect = pygame.Rect(850, 665, 220, 55)
    pygame.draw.rect(screen, (150, 210, 160), next_rect, border_radius=10)
    draw_text("⏭ Наступний день", 885, 682, small_font)
    return next_rect


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            for building_type, rect in buttons:
                if rect.collidepoint(mouse_x, mouse_y):
                    selected_building = building_type
            if 850 <= mouse_x <= 1070 and 665 <= mouse_y <= 720:
                next_day()
            if selected_building and CITY_LEFT <= mouse_x < CITY_LEFT + GRID_W * CELL and CITY_TOP <= mouse_y < CITY_TOP + GRID_H * CELL:
                col = (mouse_x - CITY_LEFT) // CELL
                row = (mouse_y - CITY_TOP) // CELL
                build(selected_building, col, row)

    draw_city()
    next_button = draw_buttons()
    pygame.display.flip()
    clock.tick(60)
