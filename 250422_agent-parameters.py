"""agent_simulation.py – v2.0
Исправлены клики по кнопкам и расширена модель правил.

Файл **rules.json** теперь поддерживает три способа задания условий:

1. Простейшие однопараметровые пороги (старый формат) ─ ключи `lt` / `lte` / `gt` / `gte`
   ```json
   { "param": "tiredness", "lt": 30, "action": "sleep", "target": 30 }
   ```
2. Диапазоны через `gte`+`lt` (ответ на *Вопрос 2*)
   ```json
   { "param": "tiredness", "gte": 30, "lt": 100, "action": "sleep", "target": 100 }
   ```
3. Сложная логика на Python‑выражениях — поле `when` ( *Вопрос 3* )
   ```json
   { "when": "(mood < 30 or tiredness < 30) and hunger < 100", "action": "eat", "param": "hunger", "target": 100 }
   ```
   В выражении доступны переменные: `hunger`, `mood`, `tiredness`, `life_energy`.

Измени порядок элементов — изменится приоритет.
"""

import json, os, sys, time
from collections import deque
from dataclasses import dataclass
from enum import Enum
import pygame

RULES_FILE = "rules.json"

# ───────── UI ─────────
WIDTH, HEIGHT = 1600, 760
SLIDER_W, SLIDER_H = 300, 20
SLIDER_X = 20
LIFE_Y      = HEIGHT // 2 - 130
HUNGER_Y    = LIFE_Y + 60
MOOD_Y      = HUNGER_Y + 60
TIRED_Y     = MOOD_Y + 60
THOUGHT_X, THOUGHT_Y = SLIDER_X + SLIDER_W + 50, LIFE_Y - 60
THOUGHT_W, THOUGHT_H = 1100, 420
BTN_ACT   = pygame.Rect(SLIDER_X, TIRED_Y + 90, 140, 40)
BTN_PAUSE = pygame.Rect(SLIDER_X + 160, TIRED_Y + 90, 140, 40)

BACKGROUND = (40, 44, 52)
DIALOG_BG  = "#9CACC9"
GREEN = (0, 200, 0)
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
MYBLUE, MYGREEN = "#153777", "#ADFA7A"

# ───────── State / Actions ─────────
RANGES = {"hunger":(0,100), "mood":(0,100), "tiredness":(0,100)}

@dataclass
class Action:
    name: str
    param: str
    target: int
    speed: int = 20

class SimMode(Enum):
    IDLE=0; RUNNING=1; PAUSED=2

# ───────── Helpers ─────────
clamp = lambda v,r: max(r[0], min(r[1], v))

param_ru = {"hunger":"Сытность", "mood":"Настроение", "tiredness":"Бодрость"}
action_ru= {"sleep":"Поспать","have_fun":"Развлечься","eat":"Поесть"}

# ───────── Rule Engine ─────────
class RuleEngine:
    def __init__(self):
        self._mtime=0; self.rules=[]; self.reload()
    def reload(self):
        try:
            m=os.path.getmtime(RULES_FILE)
            if m!=self._mtime:
                with open(RULES_FILE,encoding='utf-8') as f:
                    self.rules=json.load(f)
                self._mtime=m
        except FileNotFoundError:
            self.rules=[]
    def _eval_expr(self, expr, state):
        try:
            return bool(eval(expr, {}, state))
        except Exception:
            return False
    def _simple_cond(self, rule, state):
        v=state[rule['param']]
        if 'lt' in rule and not v < rule['lt']: return False
        if 'lte'in rule and not v <=rule['lte']:return False
        if 'gt' in rule and not v > rule['gt']: return False
        if 'gte'in rule and not v >=rule['gte']:return False
        return True
    def condition_met(self, rule, state):
        if 'when' in rule:
            return self._eval_expr(rule['when'], state)
        return self._simple_cond(rule, state)
    def build_plan(self, state):
        plan=deque()
        for r in self.rules:
            if self.condition_met(r,state):
                plan.append(Action(r.get('action','noop'), r.get('param','hunger'), r.get('target',100), r.get('speed',20)))
        return plan

# ───────── Drawing ─────────

def draw_slider(scr,font,x,y,val,name):
    pygame.draw.rect(scr,DIALOG_BG,(x,y,SLIDER_W,SLIDER_H))
    pygame.draw.rect(scr,GREEN,(x,y,int(SLIDER_W*val/100),SLIDER_H))
    scr.blit(font.render(f"{name}: {int(val)}",True,WHITE),(x,y-25))

def draw_btn(scr,font,rect,text,active=True):
    col=(70,140,70) if active else (90,90,90)
    pygame.draw.rect(scr,col,rect,border_radius=6)
    lbl=font.render(text,True,WHITE)
    scr.blit(lbl,(rect.x+(rect.width-lbl.get_width())//2, rect.y+8))

def colorize(text):
    kw={"Жизненную Энергию":MYGREEN,"Жизненной Энергии":MYGREEN,"Сытность":MYBLUE,"Настроение":MYBLUE,"Бодрость":MYBLUE}
    parts,last=[],0; lower=text.lower()
    for k,c in kw.items():
        idx=lower.find(k.lower());
        if idx>=0:
            if last<idx: parts.append((text[last:idx],BLACK))
            parts.append((text[idx:idx+len(k)],c)); last=idx+len(k)
    if last<len(text): parts.append((text[last:],BLACK))
    return parts or [(text,BLACK)]

def render_line(scr,font,x,y,parts):
    off=x
    for t,c in parts:
        s=font.render(t,True,c); scr.blit(s,(off,y)); off+=s.get_width()

# ───────── Main loop ─────────

def main():
    pygame.init(); scr=pygame.display.set_mode((WIDTH,HEIGHT)); pygame.display.set_caption('Agent Sim 2.0')
    font=pygame.font.SysFont(None,24); clock=pygame.time.Clock()

    state=dict(hunger=100,mood=100,tiredness=100)
    life_energy=base_energy=100; applied_rules=[]
    engine=RuleEngine(); plan=engine.build_plan(state); mode=SimMode.IDLE
    last_energy=time.time()

    def update_sliders(mx,my):
        if HUNGER_Y<=my<=HUNGER_Y+SLIDER_H and SLIDER_X<=mx<=SLIDER_X+SLIDER_W:
            state['hunger']=(mx-SLIDER_X)/SLIDER_W*100
        if MOOD_Y<=my<=MOOD_Y+SLIDER_H and SLIDER_X<=mx<=SLIDER_X+SLIDER_W:
            state['mood']=(mx-SLIDER_X)/SLIDER_W*100
        if TIRED_Y<=my<=TIRED_Y+SLIDER_H and SLIDER_X<=mx<=SLIDER_X+SLIDER_W:
            state['tiredness']=(mx-SLIDER_X)/SLIDER_W*100

    running=True
    while running:
        dt=clock.tick(60)/1000.0
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                running=False
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if BTN_ACT.collidepoint(e.pos):
                    if mode==SimMode.IDLE: mode=SimMode.RUNNING
                    elif mode==SimMode.RUNNING: engine.reload(); plan=engine.build_plan(state)
                elif BTN_PAUSE.collidepoint(e.pos):
                    if mode==SimMode.RUNNING: mode=SimMode.PAUSED
                    elif mode==SimMode.PAUSED: mode=SimMode.RUNNING
                else:
                    update_sliders(*e.pos)
            elif e.type==pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                update_sliders(*e.pos)

        engine.reload()
        # execute plan
        if mode==SimMode.RUNNING and plan:
            act=plan[0]; cur=state[act.param]
            if cur>=act.target:
                plan.popleft()
            else:
                state[act.param]=clamp(cur+act.speed*dt,RANGES[act.param])
        if mode==SimMode.RUNNING and not plan:
            mode=SimMode.IDLE; plan=engine.build_plan(state)
        if mode==SimMode.IDLE:
            plan=engine.build_plan(state)
        # life energy
        if time.time()-last_energy>=1:
            base_energy=state['hunger']; life_energy=base_energy; applied_rules.clear()
            if state['mood']>=70 and state['tiredness']>=70 and life_energy<30:
                applied_rules.append('≥70 по настроению и бодрости → не даю упасть ниже 30 [2.1]'); life_energy=30
            if (state['mood']<30 or state['tiredness']<30) and life_energy>70:
                applied_rules.append('<30 по одному из параметров → потолок 70 [2.2]'); life_energy=70
            last_energy=time.time()
        # ─ render ─
        scr.fill(BACKGROUND)
        draw_slider(scr,font,SLIDER_X,LIFE_Y,life_energy,'Жизненная энергия')
        draw_slider(scr,font,SLIDER_X,HUNGER_Y,state['hunger'],'Сытность')
        draw_slider(scr,font,SLIDER_X,MOOD_Y,state['mood'],'Настроение')
        draw_slider(scr,font,SLIDER_X,TIRED_Y,state['tiredness'],'Бодрость')
        draw_btn(scr,font,BTN_ACT,'Действовать',mode==SimMode.IDLE)
        draw_btn(scr,font,BTN_PAUSE,'Пауза' if mode==SimMode.RUNNING else 'Продолжить',mode!=SimMode.IDLE)
        pygame.draw.rect(scr,DIALOG_BG,(THOUGHT_X,THOUGHT_Y,THOUGHT_W,THOUGHT_H),border_radius=8)
        lines=[colorize(f'Фактическая Жизненная Энергия: {int(life_energy)}'),
               colorize(f'Сытность: {int(state["hunger"])}  Настроение: {int(state["mood"])}  Бодрость: {int(state["tiredness"])}')]
        if applied_rules:
            lines.append(colorize('Сработали правила:'))
            lines.extend(colorize('  '+r) for r in applied_rules)
        lines.append(colorize('План действий:'))
        if plan:
            for i,a in enumerate(plan,1):
                lines.append(colorize(f'  {i}. {action_ru.get(a.name,a.name)} – пока {param_ru[a.param]} < {a.target}'))
        else:
            lines.append(colorize('  нет задач – pass'))
        y=0
        for part in lines:
            render_line(scr,font,THOUGHT_X+10,THOUGHT_Y+10+y,part); y+=25
        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__=='__main__':
    main()
