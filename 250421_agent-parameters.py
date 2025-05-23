import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "1800,100"

import pygame
import sys
import time

# Инициализация Pygame
pygame.init()

# Параметры экрана
WIDTH, HEIGHT = 1600, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Симуляция агентов")

# Цвета
BACKGROUND_COLOR = (40, 44, 52)
BACKGROUND_COLOR_DIALOG = "#9CACC9"
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MYBLUE = "#153777"
MYGREEN = "#ADFA7A"

# Настройки ползунков
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20
SLIDER_X = 20
LIFE_Y = HEIGHT // 2 - 100
HUNGER_Y = HEIGHT // 2 - 40
MOOD_Y = HEIGHT // 2 + 20
TIRED_Y = HEIGHT // 2 + 80

# Область мыслей
THOUGHT_BOX_X = SLIDER_X + SLIDER_WIDTH + 50
THOUGHT_BOX_Y = LIFE_Y - 60
THOUGHT_BOX_WIDTH = 1100
THOUGHT_BOX_HEIGHT = 350

# Начальные значения
life_energy = 100
hunger = 100
mood = 100
tiredness = 100
base_energy = hunger
applied_rules = []
suggestion = []
last_life_update = time.time()

font = pygame.font.SysFont(None, 24)

def draw_slider(x, y, value, name):
    pygame.draw.rect(screen, BACKGROUND_COLOR_DIALOG, (x, y, SLIDER_WIDTH, SLIDER_HEIGHT))
    fill_width = int(SLIDER_WIDTH * (value / 100))
    pygame.draw.rect(screen, GREEN, (x, y, fill_width, SLIDER_HEIGHT))
    label = font.render(f"{name}: {int(value)}", True, WHITE)
    screen.blit(label, (x, y - 25))

def colorize_text(text):
    keywords = {
        "Жизненную Энергию": MYGREEN,
        "Жизненной Энергии": MYGREEN,
        "Сытность": MYBLUE,
        "Сытности": MYBLUE,
        "Настроение": MYBLUE,
        "Бодрость": MYBLUE
    }

    lines = text.split('\n')
    all_colored = []

    for line in lines:
        text_lower = line.lower()
        spans = []
        used = [False] * len(line)

        for phrase, color in keywords.items():
            start = 0
            phrase_lower = phrase.lower()
            while True:
                idx = text_lower.find(phrase_lower, start)
                if idx == -1:
                    break
                if all(not used[i] for i in range(idx, idx + len(phrase))):
                    spans.append((idx, idx + len(phrase), color))
                    for i in range(idx, idx + len(phrase)):
                        used[i] = True
                start = idx + len(phrase)

        spans.sort()
        result = []
        last_idx = 0

        for start_idx, end_idx, color in spans:
            if last_idx < start_idx:
                result.append((line[last_idx:start_idx], BLACK))
            result.append((line[start_idx:end_idx], color))
            last_idx = end_idx

        if last_idx < len(line):
            result.append((line[last_idx:], BLACK))

        all_colored.append(result)

    return all_colored

def generate_suggestion(hunger, mood, tiredness):
    text = ""
    if hunger < 100 and mood < 30 and tiredness < 30:
        text = ("    поднять Сытность до 100, Настроение и Бодрость хотя бы до 30.\n"
                "     Потому что если Настроение и Бодрость будут меньше 30,\n"
                "    то значение Жизненной Энергии не поднимается выше 70.[1.1]")
    elif hunger < 100 and mood < 30:
        text = ("    поднять Сытность до 100 и Настроение хотя бы до 30.\n"
                "       Потому что если Настроение будет меньше 30,\n"
                "       то значение Жизненной Энергии не поднимается выше 70.[1.2]")
    elif hunger < 100 and tiredness < 30:
        text = ("    поднять Сытность до 100 и Бодрость хотя бы до 30. \n"
                "        Потому что если Бодрость будет меньше 30,\n"
                "     то значение Жизненной Энергии не поднимается выше 70.[1.3]")
    elif mood < 30 and tiredness < 30:
        text = "    поднять Настроение и Бодрость хотя бы до 30. [1.4]"
    elif hunger == 100 and mood < 30:
        text = "    улучшить Настроение хотя бы до 30. [1.6]"
    elif hunger == 100 and tiredness < 30:
        text = "    повысить Бодрость хотя бы до 30. [1.7]"
    elif hunger < 100:
        text = "    поднять Сытность до 100. [1.5]"

    result = colorize_text(text)
    return result if result else []

def render_colored_line(x, y, parts):
    offset_x = x
    for txt, col in parts:
        surf = font.render(txt, True, col)
        screen.blit(surf, (offset_x, y))
        offset_x += surf.get_width()

def get_thought_lines(energy, hunger, mood, tiredness, base_energy, applied_rules, suggestion):
    lines = []
    # Фактическое значение энергии
    lines.append(colorize_text(f"Фактическое значение Жизненной Энергии: {int(energy)}"))
    lines.append([("", BLACK)])

    # Текущие параметры
    lines.append(colorize_text("    Сейчас моя"))
    lines.append(colorize_text(f"    Сытность: {int(hunger)}  Настроение: {int(mood)}  Бодрость: {int(tiredness)}"))
    lines.append([("", BLACK)])

    # Базовый расчёт
    lines.append(colorize_text(f"    По умолчанию я рассчитываю свою Жизненную Энергию как {int(base_energy)} (на основе Сытности)."))

    # Правила и предложения
    if applied_rules:
        lines.append(colorize_text("    Однако..."))
        for rule in applied_rules:
            lines.append(colorize_text("    " + rule))
        if suggestion:
            lines.append([("", BLACK)])
            lines.append(colorize_text("    Что мне делать? Надо..."))
            # **Вставляем каждый совет целиком**
            for part in suggestion:
                lines.append(part)
    else:
        suggestion = generate_suggestion(hunger, mood, tiredness)
        if energy < 70 or hunger < 100 or (mood >= 70 and tiredness >= 70 and hunger < 100):
            lines.append([("", BLACK)])
            lines.append(colorize_text("    Я чувствую, что мог бы иметь больше Жизненной Энергии, если бы я попробовал:"))
            for part in suggestion:
                # **Тоже вставляем целиком**
                lines.append(part)
        else:
            lines.append(colorize_text("    Никакие дополнительные ограничения не применялись."))

    # flatten colorize_text -> list of lists
    flat = []
    for item in lines:
        if isinstance(item, list) and all(isinstance(el, tuple) for el in item):
            flat.append(item)
        else:
            # если это результат colorize_text (список списков), разворачиваем
            flat.extend(item)
    return flat

# Основной цикл
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BACKGROUND_COLOR)

    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        elif evt.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION) and pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if HUNGER_Y <= my <= HUNGER_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                hunger = (mx - SLIDER_X) / SLIDER_WIDTH * 100
            if MOOD_Y <= my <= MOOD_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                mood = (mx - SLIDER_X) / SLIDER_WIDTH * 100
            if TIRED_Y <= my <= TIRED_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                tiredness = (mx - SLIDER_X) / SLIDER_WIDTH * 100

    # Обновляем энергию раз в секунду
    now = time.time()
    if now - last_life_update >= 1:
        base_energy = hunger
        applied_rules = []
        suggestion = []
        life_energy = base_energy

        if (mood >= 70 and tiredness >= 70) and life_energy < 30:
            applied_rules.append("Настроение и Бодрость отличные (≥ 70), не позволяю опуститься Жизненной Энергии ниже 30 — устанавливаю 30. [2.1]")
            life_energy = 30
            if hunger < 100:
                suggestion = generate_suggestion(hunger, mood, tiredness)

        if (mood < 30 or tiredness < 30) and life_energy > 70:
            applied_rules.append("Настроение или Бодрость плохие (< 30), не ощущаю подъёма — ограничиваю Жизненную Энергию сверху до 70. [2.2]")
            life_energy = 70
            suggestion = generate_suggestion(hunger, mood, tiredness)

        last_life_update = now

    # Рисуем ползунки
    draw_slider(SLIDER_X, LIFE_Y, life_energy, "Жизненная энергия")
    draw_slider(SLIDER_X, HUNGER_Y, hunger, "Сытность")
    draw_slider(SLIDER_X, MOOD_Y, mood, "Настроение")
    draw_slider(SLIDER_X, TIRED_Y, tiredness, "Бодрость")

    # Рисуем область мыслей
    pygame.draw.rect(screen, BACKGROUND_COLOR_DIALOG,
                     (THOUGHT_BOX_X, THOUGHT_BOX_Y, THOUGHT_BOX_WIDTH, THOUGHT_BOX_HEIGHT),
                     border_radius=8)

    lines = get_thought_lines(life_energy, hunger, mood, tiredness, base_energy, applied_rules, suggestion)
    y_off = 0
    for parts in lines:
        render_colored_line(THOUGHT_BOX_X + 10, THOUGHT_BOX_Y + 10 + y_off, parts)
        y_off += 25

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
