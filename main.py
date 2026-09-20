import pygame
import sys
import random
import math

pygame.init()
pygame.mixer.init()

# Спроба завантажити фонову музику
try:
    pygame.mixer.music.load("background_music.mp3")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.3)
except Exception:
    print("Попередження: Музичний файл не знайдено.")

WIDTH = 1150
HEIGHT = 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Міні Місто")
clock = pygame.time.Clock()

# Шрифти для інтерфейсу
font = pygame.font.SysFont("arial", 20)
small_font = pygame.font.SysFont("arial", 16)
big_font = pygame.font.SysFont("arial", 32, bold=True)

# Кольорова палітра
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GREEN = (180, 220, 160)
GRID = (150, 180, 140)
PANEL = (235, 235, 235)
WHITE_TEXT = (255, 255, 255)
ASPHALT = (60, 60, 65)  # Темно-сірий колір для доріг

# Ігрові параметри та ресурси
money = 5000
population = 0
happiness = 60
day = 1
city = []

# Параметри сітки міста (розширено вправо до 14 клітинок)
CELL = 75
CITY_LEFT = 30
CITY_TOP = 100
GRID_W = 14
GRID_H = 6
selected_building = None

# --- НАЛАШТУВАННЯ ЗМІНИ ДНЯ І НОЧІ ---
# Створюємо поверхню для нічного затемнення (покриває тільки ігрову сітку)
night_surf = pygame.Surface((WIDTH, 500), pygame.SRCALPHA)
night_surf.fill((10, 20, 60, 120))  # 120 — рівень темряви

# --- НАЛАШТУВАННЯ ВИПАДКОВИХ ПОДІЙ ---
current_event = None  # Назва поточної активної події
event_timer = 0  # Скільки днів подія буде відображатися

# --- НАЛАШТУВАННЯ МАШИНОК ---
CAR_COLORS = [(220, 50, 50), (50, 100, 220), (240, 200, 30), (245, 245, 245)]
cars = []


def spawn_car(start_on_screen=False):
    is_horizontal = random.choice([True, False])
    color = random.choice(CAR_COLORS)
    speed = random.choice([1.2, 1.8, 2.5])  # Випадкова швидкість

    if is_horizontal:
        row = random.randint(0, GRID_H)
        y = CITY_TOP + row * CELL - 1  # Центруємо машинку на тонкій дорозі
        x = random.randint(CITY_LEFT, CITY_LEFT + GRID_W * CELL) if start_on_screen else CITY_LEFT
        return {"x": x, "y": y, "vx": speed, "vy": 0, "w": 14, "h": 5, "color": color, "type": "hor"}
    else:
        col = random.randint(0, GRID_W)
        x = CITY_LEFT + col * CELL - 1  # Центруємо машинку на тонкій дорозі
        y = random.randint(CITY_TOP, CITY_TOP + GRID_H * CELL) if start_on_screen else CITY_TOP
        return {"x": x, "y": y, "vx": 0, "vy": speed, "w": 5, "h": 14, "color": color, "type": "ver"}


# Конфігурація характеристик будівель
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

# Шляхи до зображень будівель
IMAGES_CONFIG = {
    "house": "house.png", "apartments": "apartments.png", "shop": "shop.png",
    "factory": "factory.png", "hospital": "hospital.png", "school": "school.png",
    "park": "park.png", "power": "power.png", "fire": "fire.png", "bank": "bank.png"
}

# Автоматичне завантаження та масштабування картинок
BUILDING_IMAGES = {}
for key, filename in IMAGES_CONFIG.items():
    try:
        img = pygame.image.load(filename)
        img = pygame.transform.scale(img, (CELL - 10, CELL - 10))
        BUILDING_IMAGES[key] = img.convert_alpha()
    except Exception:
        BUILDING_IMAGES[key] = None

# Генерація кнопок нижнього інтерфейсу
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
    global money, day, happiness, population, current_event, event_timer
    has_fire_station = any(b["type"] == "fire" for b in city)

    # --- ЛОГІКА ЕНЕРГОМЕРЕЖІ ТА БЛЕКАУТУ ---
    power_plants = sum(1 for b in city if b["type"] == "power" and b["fire_days"] == 0)
    max_energy_capacity = power_plants * 6
    buildings_needing_power = sum(1 for b in city if b["type"] not in ["power", "park"])
    has_blackout = (buildings_needing_power > max_energy_capacity)

    # Базовий прибуток від будівель без пожежі
    base_income = 0
    for b in city:
        if b["fire_days"] == 0:
            building_income = BUILDINGS[b["type"]]["income"]
            # Якщо блекаут — урізаємо прибуток житлових та комерційних будівель вдвічі
            if has_blackout and b["type"] in ["house", "apartments", "shop", "factory", "bank"]:
                building_income = int(building_income * 0.5)
            base_income += building_income

    # Модифікатор прибутку від рівня щастя містян
    if happiness >= 80:
        multiplier = 1.10
    elif happiness >= 50:
        multiplier = 1.05
    elif happiness >= 25:
        multiplier = 1.00
    else:
        multiplier = 0.80

    final_income = int(base_income * multiplier)

    # Логіка розповсюдження та гасіння пожеж
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

    # Шанс виникнення нової випадкової пожежі
    if city:
        fire_chance = 0.05 if has_fire_station else 0.25
        if random.random() < fire_chance:
            not_burning = [b for b in city if b["fire_days"] == 0]
            if not_burning:
                random_b = random.choice(not_burning)
                random_b["fire_days"] = 1

    # Штрафи та бонуси від забудови міста
    if len(city) > 25:
        happiness = max(0, happiness - 1)
    parks = sum(1 for b in city if b["type"] == "park")
    if parks >= 3:
        happiness += 2

    happiness = max(0, min(100, happiness))
    money += final_income

    # ЛОГІКА ВИПАДКОВИХ ПОДІЙ
    if event_timer > 0:
        event_timer -= 1
        if event_timer == 0:
            current_event = None

    # 15% шанс на появу нової події
    if current_event is None and random.random() < 0.15:
        events = [
            {"text": "🎉 День міста! Жителі щасливі (+10% щастя, +300₴)", "money": 300, "happy": 10},
            {"text": "☀️ Спекотне літо! Усі купують морозиво та напої (+250₴)", "money": 250, "happy": 3},
            {"text": "🎪 У місто приїхав мандрівний цирк та ярмарок! (+8% щастя)", "money": 0, "happy": 8},
            {"text": "🌟 Інвестори вклали кошти в розвиток інфраструктури (+600₴)", "money": 600, "happy": 2},
            {"text": "🏆 Наше місто визнано найчистішим у регіоні! (+12% щастя)", "money": 0, "happy": 12},
            {"text": "📉 Економічна криза! Податки тимчасово впали (-400₴)", "money": -400, "happy": -5},
            {"text": "⛈️ Потужна злива підтопила вулиці та дороги (-200₴)", "money": -200, "happy": -2},
            {"text": "🦹 Кібератака на міські сервери! Банки зазнали збитків (-500₴)", "money": -500, "happy": -4},
            {"text": "🕵️ Раптова податкова інспекція знайшла порушення (-350₴)", "money": -350, "happy": 0},
            {"text": "🥶 Аномальні морози! Зросли витрати на опалення (-250₴)", "money": -250, "happy": -3},
            {"text": "🪵 Почалися масштабні ремонти, жителі незадоволені шумом (-300₴, -6% щастя)", "money": -300,
             "happy": -6},
            {"text": "🤝 Благодійний фонд провів безкоштовний концерт (+6% щастя)", "money": 0, "happy": 6}
        ]
        chosen = random.choice(events)
        current_event = chosen["text"]
        event_timer = 1
        money = max(0, money + chosen["money"])
        happiness = max(0, min(100, happiness + chosen["happy"]))

    day += 1


def draw_building(b_dict):
    building_type = b_dict["type"]
    rect = b_dict["rect"]
    fire_days = b_dict["fire_days"]

    if BUILDING_IMAGES[building_type] is not None:
        screen.blit(BUILDING_IMAGES[building_type], rect)
    else:
        # Резервне векторне малювання, якщо картинки відсутні
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
        draw_text(f"🔥 {fire_days}д", rect.x + 5, rect.y + 5, small_font, WHITE_TEXT)

    # Візуальний ефект миготіння вогню, якщо будівля горить
    if fire_days > 0:
        fire_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        alpha = 100 + int(40 * math.sin(pygame.time.get_ticks() * 0.01))
        fire_surf.fill((255, 60, 0, max(50, min(200, alpha))))
        screen.blit(fire_surf, rect.topleft)
        pygame.draw.rect(screen, (255, 0, 0), rect, 3, border_radius=5)
        draw_text(f"🔥 {fire_days}д", rect.x + 5, rect.y + 5, small_font, WHITE_TEXT)


def draw_city():
    screen.fill((205, 225, 200))
    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, 80))
    draw_text("🏙 МІНІ МІСТО", 20, 20, big_font)
    draw_text(f"💰 Гроші: {money}", 300, 25)
    draw_text(f"👥 Населення: {population}", 470, 25)
    draw_text(f"😊 Щастя: {happiness}%", 710, 25)
    draw_text(f"📅 День: {day}", 900, 25)

    # --- МАЛЮВАННЯ ТОНКИХ ДОРІГ ТА СІТКИ ---
    pygame.draw.rect(screen, ASPHALT, (CITY_LEFT, CITY_TOP, GRID_W * CELL, GRID_H * CELL))

    for row in range(GRID_H):
        for col in range(GRID_W):
            x = CITY_LEFT + col * CELL
            y = CITY_TOP + row * CELL
            # Робимо зсув 1 піксель, дороги тепер по 2 пікселі завширшки
            pygame.draw.rect(screen, GREEN, (x + 1, y + 1, CELL - 2, CELL - 2))
            pygame.draw.rect(screen, GRID, (x + 1, y + 1, CELL - 2, CELL - 2), 1)

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

    next_rect = pygame.Rect(900, 690, 220, 45)
    pygame.draw.rect(screen, (150, 210, 160), next_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 160, 110), next_rect, 2, border_radius=10)
    # Текст центруємо по новій висоті кнопки (y=702)
    draw_text("⏭ Наступний день", 935, 702, small_font)
    return next_rect


# --- ГОЛОВНИЙ ІГРОВИЙ ЦИКЛ ---
while True:
    # Спочатку розраховуємо інтерфейс і кнопку, щоб гра знала її точні координати в цьому кадрі
    next_button = draw_buttons()

    # Отримуємо поточні координати миші
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # НАДІЙНА ПЕРЕВІРКА КЛІКУ: автоматично перевіряє потрапляння в межі кнопки
            if next_button.collidepoint(mouse_x, mouse_y):
                next_day()

            # Кліки по кнопках вибору будівель
            for building_type, rect in buttons:
                if rect.collidepoint(mouse_x, mouse_y):
                    selected_building = building_type

            # Будівництво на клітинках карти міста
            if selected_building and CITY_LEFT <= mouse_x < CITY_LEFT + GRID_W * CELL and CITY_TOP <= mouse_y < CITY_TOP + GRID_H * CELL:
                col = (mouse_x - CITY_LEFT) // CELL
                row = (mouse_y - CITY_TOP) // CELL
                build(selected_building, col, row)

    # 1. Малюємо базове місто та будівлі
    draw_city()

    # 2. Малюємо індикатор дефіциту енергії під показниками
    active_power = sum(1 for b in city if b["type"] == "power" and b["fire_days"] == 0)
    needed_power = sum(1 for b in city if b["type"] not in ["power", "park"])
    power_text = f"⚡ Енергія: {active_power * 6}/{needed_power}"
    if needed_power > active_power * 6:
        draw_text(f"{power_text} (🚨 БЛЕКАУТ!)", 470, 53, small_font, (220, 50, 50))
    else:
        draw_text(f"{power_text} (Стабільно)", 470, 53, small_font, (50, 120, 50))

    # 3. Динамічне регулювання кількості машинок та їх рух
    target_cars_count = min(25, 5 + population // 15)
    if len(cars) < target_cars_count:
        cars.append(spawn_car(start_on_screen=True))
    elif len(cars) > target_cars_count:
        cars.pop()

    for car in cars:
        car["x"] += car["vx"]
        car["y"] += car["vy"]
        pygame.draw.rect(screen, car["color"], (car["x"], car["y"], car["w"], car["h"]), border_radius=1)

        # Перенесення машинок при досягненні краю сітки
        if car["type"] == "hor" and car["x"] > CITY_LEFT + GRID_W * CELL:
            car["x"] = CITY_LEFT
            car["color"] = random.choice(CAR_COLORS)
        elif car["type"] == "ver" and car["y"] > CITY_TOP + GRID_H * CELL:
            car["y"] = CITY_TOP
            car["color"] = random.choice(CAR_COLORS)

    # 4. Малюємо ніч (вмикається кожен парний день: 2, 4, 6...)
    if day % 2 == 0:
        screen.blit(night_surf, (0, 80))

    # 5. Малюємо випадкову подію
    if current_event is not None:
        pygame.draw.rect(screen, (255, 235, 150), (30, 490, 1040, 45), border_radius=5)
        pygame.draw.rect(screen, (200, 150, 50), (30, 490, 1040, 45), 2, border_radius=5)
        draw_text(f"📢 ПОДІЯ: {current_event}", 45, 502, font, BLACK)

    # 6. Малюємо сам інтерфейс панелі кнопок поверх усього міста
    # (Сама кнопка вже розрахована на початку циклу, тепер ми просто виводимо її графіку)
    draw_buttons()

    pygame.display.flip()
    clock.tick(60)
