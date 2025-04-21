#!/usr/bin/env python
# coding: utf-8
# agent_simulation_refactored.py

import os, sys, time
from collections import deque
from dataclasses import dataclass

import pygame

# --- Окно ----------------------------------------------------------
os.environ["SDL_VIDEO_WINDOW_POS"] = "1800,100"
WIDTH, HEIGHT = 1600, 700
SLIDER_WIDTH, SLIDER_HEIGHT = 300, 20
SLIDER_X = 20
LIFE_Y = HEIGHT // 2 - 100
HUNGER_Y = LIFE_Y + 60
MOOD_Y = HUNGER_Y + 60
TIRED_Y = MOOD_Y + 60
THOUGHT_BOX_X = SLIDER_X + SLIDER_WIDTH + 50
THOUGHT_BOX_Y = LIFE_Y - 60
THOUGHT_BOX_WIDTH, THOUGHT_BOX_HEIGHT = 1100, 350

# --- Цвета ---------------------------------------------------------
BACKGROUND_COLOR = (40, 44, 52)
BACKGROUND_COLOR_DIALOG = "#9CACC9"
GREEN = (0, 200, 0)
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
MYBLUE, MYGREEN = "#153777", "#ADFA7A"

# --- Планирование --------------------------------------------------
STATE_RANGES = {"hunger": (0, 100), "mood": (0, 100), "tiredness": (0, 100)}

@dataclass
class Action:
    name: str
    param: str
    target: int
    speed: int = 10          # единиц в секунду

def clamp(val, rng):
    """Границы 0‑100, удобная обёртка."""
    return max(rng[0], min(rng[1], val))

def build_plan(state):
    """Формируем очередь действий по приоритетам."""
    plan = deque()
    if 30 <= state["tiredness"] < 100:
        plan.append(Action("sleep", "tiredness", 100))
    if 30 <= state["mood"] < 100:
        plan.append(Action("have_fun", "mood", 100))
    if state["tiredness"] < 30:
        plan.append(Action("sleep", "tiredness", 30))
    if state["mood"] < 30:
        plan.append(Action("have_fun", "mood", 30))
    if state["hunger"] < 100:
        plan.append(Action("eat", "hunger", 100))

    return plan

def step_plan(plan, state, dt):
    """Исполняем первое действие в очереди."""
    if not plan:
        return
    act = plan[0]
    cur = state[act.param]
    if cur >= act.target:           # цель достигнута
        plan.popleft()
        return
    state[act.param] = clamp(cur + act.speed * dt, STATE_RANGES[act.param])

def thoughts_from_plan(plan):
    if not plan:
        return ["pass  # цели достигнуты"]
    return [
        f"{idx+1}. {a.name}()  # пока {a.param} < {a.target}"
        for idx, a in enumerate(plan)
    ]

# --- Вспомогательные функции отображения ---------------------------
def colorize_text(text, font):
    """Подсвечиваем параметры в строке."""
    keywords = {
        "Жизненную Энергию": MYGREEN,
        "Жизненной Энергии": MYGREEN,
        "Сытность": MYBLUE,
        "Настроение": MYBLUE,
        "Бодрость": MYBLUE
    }
    spans, used = [], [False]*len(text)
    lower = text.lower()
    for phrase, col in keywords.items():
        start, ph_low = 0, phrase.lower()
        while True:
            idx = lower.find(ph_low, start)
            if idx == -1:
                break
            if all(not used[i] for i in range(idx, idx+len(phrase))):
                spans.append((idx, idx+len(phrase), col))
                for i in range(idx, idx+len(phrase)):
                    used[i] = True
            start = idx + len(phrase)
    spans.sort()
    parts, last = [], 0
    for s, e, col in spans:
        if last < s:
            parts.append((text[last:s], BLACK))
        parts.append((text[s:e], col))
        last = e
    if last < len(text):
        parts.append((text[last:], BLACK))
    return parts

def draw_slider(screen, font, x, y, value, name):
    pygame.draw.rect(screen, BACKGROUND_COLOR_DIALOG, (x, y, SLIDER_WIDTH, SLIDER_HEIGHT))
    pygame.draw.rect(screen, GREEN, (x, y, int(SLIDER_WIDTH*value/100), SLIDER_HEIGHT))
    screen.blit(font.render(f"{name}: {int(value)}", True, WHITE), (x, y-25))

def render_colored_line(screen, font, x, y, parts):
    off = x
    for txt, col in parts:
        surf = font.render(txt, True, col)
        screen.blit(surf, (off, y))
        off += surf.get_width()

# --- Основная функция ----------------------------------------------
def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Симуляция агента ― refactored")
    font = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()

    # Начальное состояние
    state = {"hunger": 100, "mood": 100, "tiredness": 100}
    life_energy, base_energy = 100, 100
    applied_rules, plan = [], build_plan(state)
    last_life_update = time.time()
    running = True

    while running:
        dt = clock.tick(60)/1000.0     # секунд за кадр
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION) and pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if HUNGER_Y <= my <= HUNGER_Y+SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X+SLIDER_WIDTH:
                    state["hunger"] = (mx-SLIDER_X)/SLIDER_WIDTH*100
                if MOOD_Y <= my <= MOOD_Y+SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X+SLIDER_WIDTH:
                    state["mood"] = (mx-SLIDER_X)/SLIDER_WIDTH*100
                if TIRED_Y <= my <= TIRED_Y+SLIDER_HEIGHT and SLIDER_X <= mx <= SLIDER_X+SLIDER_WIDTH:
                    state["tiredness"] = (mx-SLIDER_X)/SLIDER_WIDTH*100

        # --- Исполнение плана --------------------------------------
        step_plan(plan, state, dt)
        if not plan:
            plan = build_plan(state)

        # --- Жизненная энергия раз в секунду -----------------------
        now = time.time()
        if now - last_life_update >= 1:
            base_energy = state["hunger"]
            life_energy = base_energy
            applied_rules.clear()

            if state["mood"] >= 70 and state["tiredness"] >= 70 and life_energy < 30:
                applied_rules.append("≥70 по настроению и бодрости → не даю упасть ниже 30. [2.1]")
                life_energy = 30
            if (state["mood"] < 30 or state["tiredness"] < 30) and life_energy > 70:
                applied_rules.append("<30 по одному из параметров → режу потолок до 70. [2.2]")
                life_energy = 70
            last_life_update = now

        # --- Отрисовка --------------------------------------------
        screen.fill(BACKGROUND_COLOR)
        draw_slider(screen, font, SLIDER_X, LIFE_Y, life_energy, "Жизненная энергия")
        draw_slider(screen, font, SLIDER_X, HUNGER_Y, state["hunger"], "Сытность")
        draw_slider(screen, font, SLIDER_X, MOOD_Y,   state["mood"],   "Настроение")
        draw_slider(screen, font, SLIDER_X, TIRED_Y,  state["tiredness"], "Бодрость")

        pygame.draw.rect(screen, BACKGROUND_COLOR_DIALOG,
                         (THOUGHT_BOX_X, THOUGHT_BOX_Y, THOUGHT_BOX_WIDTH, THOUGHT_BOX_HEIGHT),
                         border_radius=8)

        lines = []
        lines.append(colorize_text(f"Фактическая Жизненная Энергия: {int(life_energy)}", font))
        lines.append(colorize_text(f"Сытность: {int(state['hunger'])}  Настроение: {int(state['mood'])}  Бодрость: {int(state['tiredness'])}", font))
        lines.append(colorize_text(f"Базовое значение (по сытности): {int(base_energy)}", font))
        if applied_rules:
            lines.append(colorize_text("Сработали правила:", font))
            for r in applied_rules:
                lines.append(colorize_text("  "+r, font))
        lines.append(colorize_text("План действий:", font))
        for ln in thoughts_from_plan(plan):
            lines.append(colorize_text("   "+ln, font))

        y = 0
        for part in lines:
            render_colored_line(screen, font, THOUGHT_BOX_X+10, THOUGHT_BOX_Y+10+y, part)
            y += 25

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# --- Точка входа ---------------------------------------------------
if __name__ == "__main__":
    run()
