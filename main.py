import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "1800,100"  # X=1600, Y=100 — правый край большого экрана

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
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Настройки бегунков
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20
SLIDER_X = 20
LIFE_Y = HEIGHT // 2 - 100
HUNGER_Y = HEIGHT // 2 - 40
MOOD_Y = HEIGHT // 2 + 20
TIRED_Y = HEIGHT // 2 + 80

# Настройки области мыслей агента
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
suggestion = ""
last_life_update = time.time()

font = pygame.font.SysFont(None, 24)


def draw_slider(x, y, value, name):
    pygame.draw.rect(screen, GRAY, (x, y, SLIDER_WIDTH, SLIDER_HEIGHT))
    fill_width = int(SLIDER_WIDTH * (value / 100))
    pygame.draw.rect(screen, GREEN, (x, y, fill_width, SLIDER_HEIGHT))
    label = font.render(f"{name}: {int(value)}", True, WHITE)
    screen.blit(label, (x, y - 25))


def get_thought(energy, hunger, mood, tiredness, base_energy, applied_rules, suggestion):
    lines = [f"Фактическое значение жизненной энергии: {int(energy)}"]
    lines.append("")
    lines.append(f"    Сейчас моя сытность составляет {int(hunger)}, настроение — {int(mood)}, усталость — {int(tiredness)}.")
    lines.append("")
    lines.append(f"    По умолчанию я рассчитываю свою жизненную энергию как {int(base_energy)} (на основе сытности).")

    if applied_rules:
        lines.append("    Однако...")
        for rule in applied_rules:
            lines.append("    " + rule)
        if suggestion:
            lines.append("")
            lines.append("    Что мне делать? Надо...")
            lines.append("    " + suggestion)
    else:
        if energy < 70 or hunger < 70:
            lines.append("")
            lines.append("    Я чувствую, что мог бы иметь больше энергии, если бы...")
            if hunger < 70 and mood < 70 and tiredness < 70:
                lines.append("    ...поднял сытность до 100, настроение и бодрость хотя бы до 70.")
            elif hunger < 70 and mood < 70:
                lines.append("    ...поднял сытность до 100 и настроение хотя бы до 70.")
            elif hunger < 70 and tiredness < 70:
                lines.append("    ...поднял сытность до 100 и бодрость хотя бы до 70.")
            elif mood < 70 and tiredness < 70:
                lines.append("    ...поднял настроение и бодрость хотя бы до 70.")
            elif hunger < 100:
                lines.append("    ...поднял сытность до 100.")
            elif mood < 70:
                lines.append("    ...улучшил настроение хотя бы до 70.")
            elif tiredness < 70:
                lines.append("    ...восстановил силы и снизил усталость хотя бы до 70.")
        else:
            lines.append("    Никакие дополнительные ограничения не применялись.")

    return "\n".join(lines)


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

    # Обновление жизненной энергии каждую 1 секунду
    current_time = time.time()
    if current_time - last_life_update >= 1:
        base_energy = hunger
        applied_rules = []
        suggestion = ""
        life_energy = base_energy

        if (mood >= 70 and tiredness >= 70) and life_energy < 30:
            applied_rules.append("Настроение и бодрость отличные (≥ 70), не позволяю опуститься ниже 30 — устанавливаю 30.")
            life_energy = 30
            if hunger < 70:
                suggestion = "повысить сытность до 100, чтобы жизненная энергия могла достичь 100."

        if (mood < 30 or tiredness < 30) and life_energy > 70:
            applied_rules.append("Настроение или бодрость плохие (< 30), не ощущаю подъёма — ограничиваю энергию сверху до 70.")
            life_energy = 70
            if mood < 30 and tiredness < 30 and hunger < 70:
                suggestion = "поднять сытность до 100, настроение и бодрость хотя бы до 70."
            elif mood < 30 and tiredness < 30:
                suggestion = "поднять и настроение, и бодрость хотя бы до 70."
            elif mood < 30 and hunger < 70:
                suggestion = "поднять сытность до 100 и настроение хотя бы до 70."
            elif tiredness < 30 and hunger < 70:
                suggestion = "поднять сытность до 100 и бодрость хотя бы до 70."
            elif mood < 30:
                suggestion = "улучшить настроение хотя бы до 70."
            elif tiredness < 30:
                suggestion = "восстановить силы и снизить усталость хотя бы до 70."
            elif hunger < 100:
                suggestion = "повысить сытность до 100."

        last_life_update = current_time

    draw_slider(SLIDER_X, LIFE_Y, life_energy, "Жизненная энергия")
    draw_slider(SLIDER_X, HUNGER_Y, hunger, "Сытность")
    draw_slider(SLIDER_X, MOOD_Y, mood, "Настроение")
    draw_slider(SLIDER_X, TIRED_Y, tiredness, "Усталость")

    # Область мыслей агента
    pygame.draw.rect(screen, GRAY, (THOUGHT_BOX_X, THOUGHT_BOX_Y, THOUGHT_BOX_WIDTH, THOUGHT_BOX_HEIGHT), border_radius=8)
    thought = get_thought(life_energy, hunger, mood, tiredness, base_energy, applied_rules, suggestion)
    thought_lines = thought.split("\n")
    for i, line in enumerate(thought_lines):
        text_surface = font.render(line, True, BLACK)
        screen.blit(text_surface, (THOUGHT_BOX_X + 10, THOUGHT_BOX_Y + 10 + i * 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
