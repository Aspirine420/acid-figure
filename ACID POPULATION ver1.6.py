import pygame
import random
import math
import numpy as np

# --- ДИНАМИЧЕСКАЯ ПАЛИТРА ---
def get_random_neon():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

C1, C2 = get_random_neon(), get_random_neon()
while math.dist(C1, C2) < 130: C2 = get_random_neon()

Z1, Z2 = [max(1, int(x/18)) for x in C1], [max(1, int(x/18)) for x in C2]
TRACE_COLOR = (40, 45, 50) 

WIDTH, HEIGHT = 1450, 850
SIM_WIDTH = 1050
FPS = 60
PANEL_X = SIM_WIDTH + 15

COLORS = {
    'circle': {'unit': C1, 'zone': Z1, 'name': "КРУГИ"},
    'triangle': {'unit': C2, 'zone': Z2, 'name': "ТРЕУГОЛЬНИКИ"},
    'grid': (20, 20, 30), 'ui_bg': (5, 5, 10),
    'score_res': (255, 255, 0), 'weapon_res': (0, 255, 255),
    'energy_res': (0, 100, 255), 'repair_res': (255, 50, 50),
    'sniper_res': (200, 0, 255), 'veteran': (255, 255, 255)
}

class Brain:
    def __init__(self, weights=None):
        if weights: self.w1, self.w2 = weights
        else:
            self.w1, self.w2 = np.random.randn(12, 11) * 0.5, np.random.randn(2, 12) * 0.5
        self.out = np.zeros(2)

    def forward(self, x):
        self.layer1 = np.tanh(np.dot(self.w1, x))
        self.out = np.tanh(np.dot(self.w2, self.layer1))
        return self.out

    def mutate(self):
        f = random.uniform(0.05, 0.15)
        return Brain([self.w1 + np.random.randn(12, 11) * f, self.w2 + np.random.randn(2, 12) * f])

class Creature:
    def __init__(self, x, y, team, is_boss=False, brain=None):
        self.x, self.y, self.team = float(x), float(y), team
        self.is_boss = is_boss
        self.hp = 1200.0 if is_boss else 120.0
        self.max_hp, self.energy = self.hp, 150.0
        self.brain = brain if brain else Brain()
        self.angle = random.uniform(0, 6.28)
        self.ammo, self.frags, self.flags_captured = (250 if is_boss else 15), 0, 0
        self.weapon_type = "МЕГА-ДРОБОВИК" if is_boss else "Слаб.Пистолет"
        self.has_flag, self.kb_x, self.kb_y = False, 0.0, 0.0
        self.role = "ЛИДЕР" if is_boss else random.choice(["АТАКА", "ЗАЩИТА", "СНАБЖЕНИЕ"])
        self.target_pos = [float(x), float(y)]
        self.born_tick, self.is_veteran, self.age = 0, False, 0
        self.thought_process = "Анализ..."

    def think(self, enemies, flags, bases, resources, dom, current_tick):
        self.age = (current_tick - self.born_tick) // 60
        if self.age >= 120: self.is_veteran = True
        
        en_rel_x, en_rel_y, d_en = 1.0, 1.0, 2000.0
        if enemies:
            best_en = min(enemies, key=lambda e: math.hypot(self.x - e.x, self.y - e.y))
            d_en = math.hypot(best_en.x - self.x, best_en.y - self.y)
            if d_en > 0: en_rel_x, en_rel_y = (best_en.x - self.x)/400, (best_en.y - self.y)/400

        enemy_team = 'triangle' if self.team == 'circle' else 'circle'
        tx, ty = bases[enemy_team]
        if self.has_flag: tx, ty = bases[self.team]
        elif self.role == "ЛИДЕР": tx, ty = flags[enemy_team]
        elif (self.role == "СНАБЖЕНИЕ" or self.energy < 60) and resources:
            best_r = min(resources, key=lambda r: math.hypot(self.x - r[0], self.y - r[1]))
            tx, ty = best_r[0], best_r[1]

        self.target_pos = [float(tx), float(ty)]
        
        if self.energy < 40: self.thought_process = "ГОЛОД: Ищу еду"
        elif self.has_flag: self.thought_process = "НЕСУ ФЛАГ!"
        elif d_en < 300: self.thought_process = f"БОЙ: {self.weapon_type}"
        else: self.thought_process = f"ЦЕЛЬ: {self.role}"

        role_val = {"АТАКА": 0.1, "ЗАЩИТА": 0.5, "СНАБЖЕНИЕ": 0.9, "ЛИДЕР": 0.0}[self.role]
        inputs = np.array([en_rel_x, en_rel_y, (tx-self.x)/400, (ty-self.y)/400, self.hp/self.max_hp, 
                           self.energy/150, self.ammo/30, dom, math.sin(self.angle), math.cos(self.angle), role_val])
        
        out = self.brain.forward(inputs)
        self.angle += out[0] * 0.18
        speed = (out[1] + 1) * 0.5 * (2.1 if self.is_boss else 2.6) * (0.3 + 0.7*(self.energy/150))
        
        self.energy -= (0.007 if self.is_boss else 0.01) + speed * 0.04
        self.x += math.cos(self.angle)*speed + self.kb_x
        self.y += math.sin(self.angle)*speed + self.kb_y
        self.kb_x *= 0.8; self.kb_y *= 0.8
        self.x, self.y = np.clip(self.x, 30, SIM_WIDTH-30), np.clip(self.y, 30, HEIGHT-30)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock, font = pygame.time.Clock(), pygame.font.SysFont("Consolas", 14, bold=True)
    small_font = pygame.font.SysFont("Consolas", 11, bold=True)
    
    creatures, bullets, respawn_queue = [], [], []
    res_scores, res_weapons, res_energy, res_repair, res_sniper = [], [], [], [], []
    stats = {'circle': {'score': 0, 'flags': 0, 'res': 0}, 'triangle': {'score': 0, 'flags': 0, 'res': 0}}
    bases = {'circle': (100, HEIGHT//2), 'triangle': (SIM_WIDTH-100, HEIGHT//2)}
    flags = {'circle': list(bases['circle']), 'triangle': list(bases['triangle'])}
    flag_holders, selected, tick, last_event = {'circle': None, 'triangle': None}, None, 0, "СИСТЕМА ЗАПУЩЕНА"

    def spawn(t, b=None, is_boss=False):
        c = Creature(bases[t][0], bases[t][1] + random.randint(-100,100), t, is_boss, b)
        c.born_tick = tick; creatures.append(c)

    for _ in range(40): res_scores.append([random.randint(150, SIM_WIDTH-150), random.randint(50, HEIGHT-50)])
    for t in ['circle', 'triangle']:
        spawn(t, is_boss=True)
        for _ in range(10): spawn(t)

    while True:
        tick += 1
        pygame.draw.rect(screen, COLORS['circle']['zone'], (0, 0, SIM_WIDTH//2, HEIGHT))
        pygame.draw.rect(screen, COLORS['triangle']['zone'], (SIM_WIDTH//2, 0, SIM_WIDTH//2, HEIGHT))
        for i in range(0, SIM_WIDTH+1, 50): pygame.draw.line(screen, COLORS['grid'], (i,0), (i,HEIGHT), 1)
        for i in range(0, HEIGHT+1, 50): pygame.draw.line(screen, COLORS['grid'], (0,i), (SIM_WIDTH,i), 1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); return
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                selected = next((c for c in creatures if math.hypot(c.x-mx, c.y-my)<35), None)

        for r in respawn_queue[:]:
            r['timer'] -= 1
            if r['timer'] <= 0: spawn(r['team'], r['brain'], r['is_boss']); respawn_queue.remove(r)

        if tick % 80 == 0:
            res_scores.append([random.randint(150, SIM_WIDTH-150), random.randint(50, HEIGHT-50)])
            if tick % 300 == 0: res_weapons.append([random.randint(100, SIM_WIDTH-100), random.randint(50, HEIGHT-50)])
            if tick % 450 == 0: res_sniper.append([random.randint(100, SIM_WIDTH-100), random.randint(50, HEIGHT-50)])
            if tick % 200 == 0: res_energy.append([random.randint(100, SIM_WIDTH-100), random.randint(50, HEIGHT-50)])
            if tick % 400 == 0: res_repair.append([random.randint(100, SIM_WIDTH-100), random.randint(50, HEIGHT-50)])

        for r in res_scores: pygame.draw.circle(screen, COLORS['score_res'], r, 5)
        for r in res_weapons: pygame.draw.rect(screen, COLORS['weapon_res'], (r[0]-6, r[1]-6, 12, 12), 2)
        for r in res_sniper: pygame.draw.polygon(screen, COLORS['sniper_res'], [(r[0], r[1]-9), (r[0]-8, r[1]+7), (r[0]+8, r[1]+7)], 2)
        for r in res_energy: pygame.draw.circle(screen, COLORS['energy_res'], r, 4)
        for r in res_repair: pygame.draw.rect(screen, COLORS['repair_res'], (r[0]-3, r[1]-8, 6, 16)); pygame.draw.rect(screen, COLORS['repair_res'], (r[0]-8, r[1]-3, 16, 6))

        for t in ['circle', 'triangle']:
            pygame.draw.circle(screen, COLORS[t]['unit'], bases[t], 65, 1)
            if flag_holders[t]: flags[t] = [flag_holders[t].x, flag_holders[t].y]
            else: flags[t] = list(bases[t])
            fx, fy = int(flags[t][0]), int(flags[t][1])
            pygame.draw.rect(screen, COLORS[t]['unit'], (fx-8, fy-25, 16, 12))
            pygame.draw.line(screen, (255,255,255), (fx-8, fy-25), (fx-8, fy), 2)

        circs, tris = [c for c in creatures if c.team == 'circle'], [c for c in creatures if c.team == 'triangle']
        dom = (stats['circle']['score'] - stats['triangle']['score']) / (stats['circle']['score'] + stats['triangle']['score'] + 1)

        for c in creatures[:]:
            enemies = tris if c.team == 'circle' else circs
            all_res = res_scores + res_weapons + res_sniper + res_energy + res_repair
            c.think(enemies, flags, bases, all_res, dom if c.team == 'circle' else -dom, tick)
            
            # --- ЛИНИИ ВЗГЛЯДА ПРЯМО ДО ЦЕЛИ ---
            # Прозрачная линия до цели (куда юнит ХОЧЕТ попасть)
            pygame.draw.line(screen, (TRACE_COLOR), (c.x, c.y), (c.target_pos[0], c.target_pos[1]), 1)
            # Яркая линия взгляда (куда юнит СМОТРИТ в данный момент)
            v_len = 55 if c.is_boss else 30
            pygame.draw.line(screen, (200,200,200), (c.x, c.y), (c.x + math.cos(c.angle)*v_len, c.y + math.sin(c.angle)*v_len), 2)

            if c.is_veteran: pygame.draw.circle(screen, COLORS['veteran'], (int(c.x), int(c.y)), int(38 if c.is_boss else 18), 1)
            screen.blit(small_font.render(f"{c.age}s", 1, (255,255,255)), (c.x - 10, c.y - (55 if c.is_boss else 35)))
            screen.blit(small_font.render(c.thought_process, 1, (200,200,200)), (c.x - 30, c.y + (40 if c.is_boss else 25)))

            for r in res_scores[:]:
                if math.hypot(c.x-r[0], c.y-r[1]) < 35: stats[c.team]['score'] += 5; res_scores.remove(r); c.energy = min(200, c.energy+50)
            for r in res_energy[:]:
                if math.hypot(c.x-r[0], c.y-r[1]) < 35: c.energy = 200; res_energy.remove(r)
            for r in res_weapons[:]:
                if math.hypot(c.x-r[0], c.y-r[1]) < 35: c.weapon_type = "Дробовик"; c.ammo += 25; res_weapons.remove(r)
            for r in res_sniper[:]:
                if math.hypot(c.x-r[0], c.y-r[1]) < 35: c.weapon_type = "Снайпер"; c.ammo += 12; res_sniper.remove(r)
            for r in res_repair[:]:
                if math.hypot(c.x-r[0], c.y-r[1]) < 35: c.hp = min(c.max_hp, c.hp+150 if c.is_boss else 70); res_repair.remove(r)

            et = 'triangle' if c.team == 'circle' else 'circle'
            if not c.has_flag and not flag_holders[et] and math.hypot(c.x-flags[et][0], c.y-flags[et][1]) < 45:
                c.has_flag = True; flag_holders[et] = c; last_event = f"ФЛАГ {et.upper()} УКРАДЕН"
            if c.has_flag and math.hypot(c.x-bases[c.team][0], c.y-bases[c.team][1]) < 65:
                c.has_flag = False; flag_holders[et] = None; stats[c.team]['score'] += 100; stats[c.team]['flags'] += 1; last_event = f"ФЛАГ {c.team.upper()} ДОМА"

            if c.ammo > 0 and tick % 45 == 0 and enemies:
                target = min(enemies, key=lambda e: math.hypot(c.x-e.x, c.y-e.y))
                if math.hypot(c.x-target.x, c.y-target.y) < (700 if c.weapon_type == "Снайпер" else 400):
                    a = math.atan2(target.y-c.y, target.x-c.x); c.ammo -= 1
                    dmg = (12 if "Пистолет" in c.weapon_type else (100 if c.weapon_type == "Снайпер" else 35)) * (1.5 if c.is_veteran else 1.0)
                    spd = 30 if c.weapon_type == "Снайпер" else 15
                    if c.is_boss: offs = [-0.4, -0.2, 0, 0.2, 0.4]
                    elif c.weapon_type == "Дробовик": offs = [-0.2, 0, 0.2]
                    else: offs = [0]
                    for off in offs: bullets.append({'x':c.x, 'y':c.y, 'vx':math.cos(a+off)*spd, 'vy':math.sin(a+off)*spd, 'team':c.team, 'life':55, 'dmg': dmg})

            sz, clr = (32 if c.is_boss else 12), COLORS[c.team]['unit']
            if c == selected: pygame.draw.circle(screen, (255,255,255), (int(c.x), int(c.y)), sz+15, 1)
            if c.team=='circle': pygame.draw.circle(screen, clr, (int(c.x), int(c.y)), sz, 0 if c.energy > 40 else 2)
            else: pygame.draw.polygon(screen, clr, [(c.x, c.y-sz), (c.x-sz, c.y+sz), (c.x+sz, c.y+sz)], 0 if c.energy > 40 else 2)
            pygame.draw.rect(screen, (0,255,100), (c.x-sz, c.y-sz-12, int(sz*2*(c.hp/c.max_hp)), 5))
            if c.hp <= 0 or c.energy <= 0:
                respawn_queue.append({'team': c.team, 'brain': c.brain.mutate(), 'is_boss': c.is_boss, 'timer': 3600})
                creatures.remove(c)

        for b in bullets[:]:
            b['x'] += b['vx']; b['y'] += b['vy']; b['life'] -= 1
            pygame.draw.circle(screen, (255,255,255), (int(b['x']), int(b['y'])), 2)
            for c in creatures:
                if c.team != b['team'] and math.hypot(b['x']-c.x, b['y']-c.y) < (34 if c.is_boss else 15):
                    c.hp -= b['dmg']; b['life'] = 0; c.kb_x, c.kb_y = b['vx']*0.1, b['vy']*0.1
            if b['life'] <= 0: bullets.remove(b)

        # ИНТЕРФЕЙС
        pygame.draw.rect(screen, COLORS['ui_bg'], (SIM_WIDTH, 0, WIDTH-SIM_WIDTH, HEIGHT))
        y = 20
        screen.blit(font.render(f"СЧЕТ: {stats['circle']['score']} - {stats['triangle']['score']}", 1, (255,255,255)), (PANEL_X, y))
        y += 20
        screen.blit(font.render(f"ФЛАГИ: {stats['circle']['flags']} | {stats['triangle']['flags']}  В ОЧЕРЕДИ: {len([r for r in respawn_queue if r['team']=='circle'])}/{len([r for r in respawn_queue if r['team']=='triangle'])}", 1, (100,100,100)), (PANEL_X, y))
        
        if selected and selected in creatures:
            y += 40
            screen.blit(font.render(f"ОБЪЕКТ: {COLORS[selected.team]['name']} {'(БОСС)' if selected.is_boss else ''}", 1, COLORS[selected.team]['unit']), (PANEL_X, y))
            screen.blit(font.render(f"МЫСЛИ: {selected.thought_process}", 1, (0, 255, 255)), (PANEL_X, y+18))
            screen.blit(font.render(f"ИНВЕНТАРЬ: {selected.weapon_type} | ЖИЗНЬ: {selected.age}с", 1, (255, 255, 0)), (PANEL_X, y+36))
            y_net = y + 80
            in_labels = ["Враг X", "Враг Y", "Цель X", "Цель Y", "HP", "Энергия", "Пули", "Домин.", "Sin", "Cos", "Роль"]
            for i, txt in enumerate(in_labels):
                screen.blit(font.render(txt, 1, (80,80,80)), (PANEL_X, y_net+i*28))
                for j in range(12):
                    w = selected.brain.w1[j][i]
                    color = (0, 255, 100) if w > 0 else (255, 50, 50)
                    pygame.draw.line(screen, color, (PANEL_X+90, y_net+i*28+7), (PANEL_X+210, y_net+j*23+7), 1)
            for i, txt in enumerate(["ПОВОРОТ", "СКОРОСТЬ"]):
                screen.blit(font.render(txt, 1, (150,150,150)), (PANEL_X+225, y_net+110+i*70))

        ym = HEIGHT - 180
        pygame.draw.rect(screen, (5, 5, 15), (PANEL_X, ym, 380, 160))
        screen.blit(font.render(f"> {last_event}", 1, (0, 255, 100)), (PANEL_X+10, ym+40))
        dom_w = 340
        pygame.draw.rect(screen, COLORS['triangle']['unit'], (PANEL_X+20, ym+80, dom_w, 10))
        pygame.draw.rect(screen, COLORS['circle']['unit'], (PANEL_X+20, ym+80, int(dom_w*(0.5+dom*0.5)), 10))
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
