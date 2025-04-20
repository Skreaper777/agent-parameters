import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "1800,100"

import pygame
import sys
import time

pygame.init()

WIDTH, HEIGHT = 1600, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Симуляция агентов")

BACKGROUND_COLOR = (40, 44, 52)
BACKGROUND_COLOR_DIALOG = "#8996AF"
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 150, 255)
ORANGE = (255, 165, 0)
MYBLUE = "#153777"

SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20
SLIDER_X = 20
LIFE_Y = HEIGHT // 2 - 100
HUNGER_Y = HEIGHT // 2 - 40
MOOD_Y = HEIGHT // 2 + 20
TIRED_Y = HEIGHT // 2 + 80

THOUGHT_BOX_X = SLIDER_X + SLIDER_WIDTH + 50
THOUGHT_BOX_Y = LIFE_Y - 60
THOUGHT_BOX_WIDTH = 1100
THOUGHT_BOX_HEIGHT = 350

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
        "жизненную энергию": MYBLUE,
        "жизненной энергии": MYBLUE,
        "сытность": MYBLUE,
        "сытности": MYBLUE,
        "настроение": MYBLUE,
        "бодрость": MYBLUE
    }

    text_lower = text.lower()
    spans = []
    used = [False] * len(text)

    for phrase, color in keywords.items():
        start = 0
        phrase_lower = phrase.lower()
        while True:
            idx = text_lower.find(phrase_lower, start)
            if idx == -1:
                break
            # mark used positions
            if all(not used[i] for i in range(idx, idx + len(phrase))):
                spans.append((idx, idx + len(phrase), color))
                for i in range(idx, idx + len(phrase)):
                    used[i] = True
            start = idx + len(phrase)

    spans.sort()
    result = []
    last_idx = 0

    for start, end, color in spans:
        if last_idx < start:
            result.append((text[last_idx:start], BLACK))
        result.append((text[start:end], color))
        last_idx = end

    if last_idx < len(text):
        result.append((text[last_idx:], BLACK))

    return result


def generate_suggestion(hunger, mood, tiredness):
    text = ""
    if hunger < 100 and mood < 30 and tiredness < 30:
        text = "поднять сытность до 100, настроение и бодрость хотя бы до 30."
    elif hunger < 100 and mood < 30:
        text = "поднять сытность до 100 и настроение хотя бы до 30."
    elif hunger < 100 and tiredness < 30:
        text = "поднять сытность до 100 и бодрость хотя бы до 30."
    elif mood < 30 and tiredness < 30:
        text = "поднять настроение и бодрость хотя бы до 30."
    elif hunger == 100 and mood < 30:
        text = "улучшить настроение хотя бы до 30."
    elif hunger == 100 and tiredness < 30:
        text = "повысить бодрость хотя бы до 30."
    elif hunger < 100:
        text = "поднять сытность до 100."
    return [colorize_text(text)] if text else []


def render_colored_line(x, y, parts):
    offset_x = x
    for text, color in parts:
        surface = font.render(text, True, color)
        screen.blit(surface, (offset_x, y))
        offset_x += surface.get_width()


def get_thought_lines(energy, hunger, mood, tiredness, base_energy, applied_rules, suggestion):
    lines = [colorize_text("Фактическое значение жизненной энергии: {}".format(int(energy)))]
    lines.append(("", BLACK))
    lines.append(colorize_text("    Сейчас моя"))
    lines.append(colorize_text("    сытность: {}  настроение: {}  бодрость: {}".format(int(hunger), int(mood), int(tiredness))))
    lines.append(("", BLACK))
    lines.append(colorize_text("    По умолчанию я рассчитываю свою жизненную энергию как {} (на основе сытности).".format(int(base_energy))))

    if applied_rules:
        lines.append(colorize_text("    Однако..."))
        for rule in applied_rules:
            lines.append(colorize_text("    " + rule))
        if suggestion:
            lines.append(("", BLACK))
            lines.append(colorize_text("    Что мне делать? Надо..."))
            for part in suggestion:
                lines.append(part)
    else:
        suggestion = generate_suggestion(hunger, mood, tiredness)
        if energy < 70 or hunger < 100 or (mood >= 70 and tiredness >= 70 and hunger < 100):
            lines.append(("", BLACK))
            lines.append(colorize_text("    Я чувствую, что мог бы иметь больше жизненной энергии, если бы..."))
            for part in suggestion:
                lines.append(part)
        else:
            lines.append(colorize_text("    Никакие дополнительные ограничения не применялись."))

    return lines


running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BACKGROUND_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if HUNGER_Y <= my <= HUNGER_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                hunger = (mx - SLIDER_X) / SLIDER_WIDTH * 100
            if MOOD_Y <= my <= MOOD_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                mood = (mx - SLIDER_X) / SLIDER_WIDTH * 100
            if TIRED_Y <= my <= TIRED_Y + SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH:
                tiredness = (mx - SLIDER_X) / SLIDER_WIDTH * 100

    current_time = time.time()
    if current_time - last_life_update >= 1:
        base_energy = hunger
        applied_rules = []
        suggestion = []
        life_energy = base_energy

        if (mood >= 70 and tiredness >= 70) and life_energy < 30:
            applied_rules.append("Настроение и бодрость отличные (≥ 70), не позволяю опуститься ниже 30 — устанавливаю 30.")
            life_energy = 30
            if hunger < 100:
                suggestion = generate_suggestion(hunger, mood, tiredness)

        if (mood < 30 or tiredness < 30) and life_energy > 70:
            applied_rules.append("Настроение или бодрость плохие (< 30), не ощущаю подъёма — ограничиваю энергию сверху до 70.")
            life_energy = 70
            suggestion = generate_suggestion(hunger, mood, tiredness)

        last_life_update = current_time

    draw_slider(SLIDER_X, LIFE_Y, life_energy, "Жизненная энергия")
    draw_slider(SLIDER_X, HUNGER_Y, hunger, "Сытность")
    draw_slider(SLIDER_X, MOOD_Y, mood, "Настроение")
    draw_slider(SLIDER_X, TIRED_Y, tiredness, "Бодрость")

    pygame.draw.rect(screen, BACKGROUND_COLOR_DIALOG, (THOUGHT_BOX_X, THOUGHT_BOX_Y, THOUGHT_BOX_WIDTH, THOUGHT_BOX_HEIGHT), border_radius=8)
    thought_lines = get_thought_lines(life_energy, hunger, mood, tiredness, base_energy, applied_rules, suggestion)
    y_offset = 0
    for item in thought_lines:
        if isinstance(item, list):
            render_colored_line(THOUGHT_BOX_X + 10, THOUGHT_BOX_Y + 10 + y_offset, item)
        else:
            text_surface = font.render(item[0], True, item[1])
            screen.blit(text_surface, (THOUGHT_BOX_X + 10, THOUGHT_BOX_Y + 10 + y_offset))
        y_offset += 25

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
