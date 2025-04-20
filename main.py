import pygame
import sys
import time

# Инициализация Pygame
pygame.init()

# Параметры экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Симуляция агентов")

# Цвета
BACKGROUND_COLOR = (40, 44, 52)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Настройки бегунков
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20
SLIDER_X = (WIDTH - SLIDER_WIDTH) // 2 - 100
LIFE_Y = HEIGHT // 2 - 40
HUNGER_Y = HEIGHT // 2 + 40

# Начальные значения
life_energy = 100
hunger = 100
last_life_update = time.time()

font = pygame.font.SysFont(None, 24)


def draw_slider(x, y, value, name):
    # Контур бегунка
    pygame.draw.rect(screen, GRAY, (x, y, SLIDER_WIDTH, SLIDER_HEIGHT))
    # Заполненная часть
    fill_width = int(SLIDER_WIDTH * (value / 100))
    pygame.draw.rect(screen, GREEN, (x, y, fill_width, SLIDER_HEIGHT))
    # Текст
    label = font.render(f"{name}: {int(value)}", True, WHITE)
    screen.blit(label, (x, y - 25))


def get_thought(energy):
    if energy < 30:
        return "Я скоро умру"
    elif 30 <= energy < 50:
        return "Мне очень плохо. Надо что-то делать."
    elif 50 <= energy < 70:
        return "Чувствую скоро станет плохо. Надо что-то делать."
    elif 80 <= energy <= 100:
        return "Мне очень хорошо. Мне ничего не надо"
    else:
        return ""

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BACKGROUND_COLOR)

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if HUNGER_Y <= my <= HUNGER_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                hunger = (mx - SLIDER_X) / SLIDER_WIDTH * 100

    # Обновление жизненной энергии каждые 5 секунд
    current_time = time.time()
    if current_time - last_life_update >= 5:
        life_energy = hunger
        last_life_update = current_time

    # Отрисовка бегунков
    draw_slider(SLIDER_X, LIFE_Y, life_energy, "Жизненная энергия")
    draw_slider(SLIDER_X, HUNGER_Y, hunger, "Сытность")

    # Область мыслей агента
    pygame.draw.rect(screen, GRAY, (SLIDER_X + SLIDER_WIDTH + 50, LIFE_Y - 30, 280, 120), border_radius=8)
    thought = get_thought(life_energy)
    thought_lines = thought.split("\n")
    for i, line in enumerate(thought_lines):
        text_surface = font.render(line, True, BLACK)
        screen.blit(text_surface, (SLIDER_X + SLIDER_WIDTH + 60, LIFE_Y - 10 + i * 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
