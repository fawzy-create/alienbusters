#!/usr/bin/env python3
# simple_space_invaders.py
# A minimal Space Invaders-like game using Pygame

import sys
import random
import math
import pygame

# Configuration
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 8
ENEMY_X_SPEED = 1.0
ENEMY_DESCEND = 20
ENEMY_ROWS = 4
ENEMY_COLS = 8
ENEMY_X_PADDING = 60
ENEMY_Y_PADDING = 50
ENEMY_START_Y = 60
ENEMY_SHOOT_CHANCE = 0.002  # per frame per enemy

# Colors
BG = (10, 10, 30)
PLAYER_COLOR = (180, 220, 255)
ENEMY_COLOR = (255, 150, 150)
BULLET_COLOR = (255, 255, 100)
TEXT_COLOR = (220, 220, 220)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders - Minimal")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# Sound setup
PLAYER_UFO_SHOOT_SOUND = None
GAME_OVER_SOUND= None 
try:
    PLAYER_UFO_SHOOT_SOUND = pygame.mixer.Sound("burp.wav")
    PLAYER_UFO_SHOOT_SOUND.set_volume(0.6)
    GAME_OVER_SOUND = pygame.mixer.Sound("alphix-game-over-417465.mp3")
except Exception:
    PLAYER_UFO_SHOOT_SOUND = None

# Entities
class Player:
    def __init__(self):
        self.w = 50
        self.h = 16
        self.x = WIDTH // 2
        self.y = HEIGHT - 50
        self.speed = PLAYER_SPEED
        self.cooldown = 0

    def rect(self):
        return pygame.Rect(self.x - self.w//2, self.y - self.h//2, self.w, self.h)

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(self.w//2, min(WIDTH - self.w//2, self.x))
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, PLAYER_COLOR, r)
        # simple "gun"
        pygame.draw.rect(surf, PLAYER_COLOR, (self.x - 6, self.y - self.h//2 - 6, 12, 6))

class Bullet:
    def __init__(self, x, y, dy, owner):
        self.x = x
        self.y = y
        self.dy = dy
        self.owner = owner  # 'player' or 'enemy'
        self.radius = 4 if owner == 'player' else 6

    def update(self):
        self.y += self.dy

    def offscreen(self):
        return self.y < -10 or self.y > HEIGHT + 10

    def draw(self, surf):
        pygame.draw.circle(surf, BULLET_COLOR, (int(self.x), int(self.y)), self.radius)

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 36
        self.h = 20
        self.alive = True

    def rect(self):
        return pygame.Rect(self.x - self.w//2, self.y - self.h//2, self.w, self.h)

    def draw(self, surf):
        if not self.alive:
            return
        r = self.rect()
        pygame.draw.rect(surf, ENEMY_COLOR, r)
        # eyes
        pygame.draw.circle(surf, (20,20,40), (int(self.x - 8), int(self.y - 2)), 3)
        pygame.draw.circle(surf, (20,20,40), (int(self.x + 8), int(self.y - 2)), 3)

# Game setup
def create_enemies():
    enemies = []
    total_width = (ENEMY_COLS - 1) * ENEMY_X_PADDING
    start_x = WIDTH//2 - total_width//2
    for row in range(ENEMY_ROWS):
        for col in range(ENEMY_COLS):
            x = start_x + col * ENEMY_X_PADDING
            y = ENEMY_START_Y + row * ENEMY_Y_PADDING
            enemies.append(Enemy(x, y))
    return enemies

def draw_text(surf, txt, x, y):
    img = font.render(txt, True, TEXT_COLOR)
    surf.blit(img, (x, y))

def main():
    player = Player()
    bullets = []
    enemies = create_enemies()
    enemy_dx = ENEMY_X_SPEED
    score = 0
    level = 1
    game_over = False

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    if not game_over and player.cooldown == 0:
                        bullets.append(Bullet(player.x, player.y - player.h//2 - 8, -BULLET_SPEED, 'player'))
                        player.cooldown = 12  # frames between shots
                if event.key == pygame.K_r and game_over:
                    # restart
                    player = Player()
                    bullets = []
                    enemies = create_enemies()
                    enemy_dx = ENEMY_X_SPEED
                    score = 0
                    level = 1
                    game_over = False

        keys = pygame.key.get_pressed()
        if not game_over:
            player.update(keys)

            # Enemies movement: horizontal sweep, descend and reverse on edge
            hit_edge = False
            for e in enemies:
                if not e.alive:
                    continue
                if e.x + e.w//2 + enemy_dx > WIDTH or e.x - e.w//2 + enemy_dx < 0:
                    hit_edge = True
                    break
            if hit_edge:
                enemy_dx = -enemy_dx
                for e in enemies:
                    e.y += ENEMY_DESCEND
            else:
                for e in enemies:
                    e.x += enemy_dx

            # Enemy shooting
            for e in enemies:
                if not e.alive:
                    continue
                if random.random() < ENEMY_SHOOT_CHANCE * level:
                    bullets.append(Bullet(e.x, e.y + e.h//2 + 6, BULLET_SPEED, 'enemy'))

            # Update bullets
            for b in bullets:
                b.update()
            bullets = [b for b in bullets if not b.offscreen()]

            # Bullet collisions
            for b in bullets[:]:
                if b.owner == 'player':
                    for e in enemies:
                        if e.alive and e.rect().collidepoint(b.x, b.y):
                            e.alive = False
                            try: bullets.remove(b)
                            except ValueError: pass
                            score += 100
                            break
                else:  # enemy bullet -> player
                    if player.rect().collidepoint(b.x, b.y):
                        game_over = True

            # Check if enemies reached player
            for e in enemies:
                if e.alive and e.y + e.h//2 >= player.y - player.h:
                    game_over = True
                    break

            # Level complete?
            if all(not e.alive for e in enemies):
                level += 1
                enemies = create_enemies()
                # increase difficulty
                enemy_dx = ENEMY_X_SPEED + level * 0.2

        # Drawing
        screen.fill(BG)
        for e in enemies:
            e.draw(screen)
        player.draw(screen)
        for b in bullets:
            b.draw(screen)

        draw_text(screen, f"Score: {score}", 8, 8)
        draw_text(screen, f"Level: {level}", WIDTH - 110, 8)

        if game_over:
            draw_text(screen, "GAME OVER - Press R to restart", WIDTH//2 - 160, HEIGHT//2 - 10)

        pygame.display.flip()

if __name__ == "__main__":
    #!/usr/bin/env python3
    # simple_space_invaders_with_powerups.py
    # A minimal Space Invaders-like game using Pygame, with powerups (shield, rapid fire)


    # Configuration
    WIDTH, HEIGHT = 800, 600
    FPS = 60
    PLAYER_SPEED = 5
    BULLET_SPEED = 8
    ENEMY_X_SPEED = 1.0
    ENEMY_DESCEND = 20
    ENEMY_ROWS = 4
    ENEMY_COLS = 8
    ENEMY_X_PADDING = 60
    ENEMY_Y_PADDING = 50
    ENEMY_START_Y = 60
    ENEMY_SHOOT_CHANCE = 0.002  # per frame per enemy
    POWERUP_CHANCE_ON_KILL = 0.18
    POWERUP_FALL_SPEED = 2

    # Colors
    BG = (10, 10, 30)
    PLAYER_COLOR = (180, 220, 255)
    ENEMY_COLOR = (255, 150, 150)
    BULLET_COLOR = (255, 255, 100)
    TEXT_COLOR = (220, 220, 220)
    SHIELD_COLOR = (100, 200, 255)
    POWERUP_COLOR = {
        'shield': (100, 200, 255),
        'rapid': (255, 200, 100)
    }

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Invaders - Minimal + Powerups")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    # Entities
    class Player:
        def __init__(self):
            self.w = 50
            self.h = 16
            self.x = WIDTH // 2
            self.y = HEIGHT - 50
            self.speed = PLAYER_SPEED
            self.cooldown = 0
            # Shooting cooldown values (frames)
            self.base_cooldown = 12
            self.rapid_cooldown = 5
            self.shoot_cooldown_value = self.base_cooldown

            # Powerup state
            self.shield_active = False
            self.shield_timer = 0  # frames
            self.rapid_timer = 0  # frames

        def rect(self):
            return pygame.Rect(self.x - self.w//2, self.y - self.h//2, self.w, self.h)

        def update(self, keys):
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x -= self.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x += self.speed
            self.x = max(self.w//2, min(WIDTH - self.w//2, self.x))
            if self.cooldown > 0:
                self.cooldown -= 1

            # Powerup timers
            if self.shield_active:
                self.shield_timer -= 1
                if self.shield_timer <= 0:
                    self.shield_active = False
            if self.rapid_timer:
                self.rapid_timer -= 1
                if self.rapid_timer <= 0:
                    self.shoot_cooldown_value = self.base_cooldown

        def draw(self, surf):
            r = self.rect()
            pygame.draw.rect(surf, PLAYER_COLOR, r)
            # simple "gun"
            pygame.draw.rect(surf, PLAYER_COLOR, (self.x - 6, self.y - self.h//2 - 6, 12, 6))
            # shield visual
            if self.shield_active:
                pygame.draw.circle(surf, SHIELD_COLOR, (int(self.x), int(self.y)), max(self.w, self.h), 2)

    class Bullet:
        def __init__(self, x, y, dy, owner):
            self.x = x
            self.y = y
            self.dy = dy
            self.owner = owner  # 'player' or 'enemy'
            self.radius = 4 if owner == 'player' else 6

        def update(self):
            self.y += self.dy

        def offscreen(self):
            return self.y < -10 or self.y > HEIGHT + 10

        def draw(self, surf):
            pygame.draw.circle(surf, BULLET_COLOR, (int(self.x), int(self.y)), self.radius)

    class Enemy:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.w = 36
            self.h = 20
            self.alive = True

        def rect(self):
            return pygame.Rect(self.x - self.w//2, self.y - self.h//2, self.w, self.h)

        def draw(self, surf):
            if not self.alive:
                return
            r = self.rect()
            pygame.draw.rect(surf, ENEMY_COLOR, r)
            # eyes
            pygame.draw.circle(surf, (20,20,40), (int(self.x - 8), int(self.y - 2)), 3)
            pygame.draw.circle(surf, (20,20,40), (int(self.x + 8), int(self.y - 2)), 3)

    class Powerup:
        def __init__(self, x, y, kind):
            self.x = x
            self.y = y
            self.kind = kind  # 'shield' or 'rapid'
            self.radius = 10
            self.dy = POWERUP_FALL_SPEED
            self.alive = True

        def update(self):
            self.y += self.dy
            if self.y > HEIGHT + 20:
                self.alive = False

        def rect(self):
            return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

        def draw(self, surf):
            c = POWERUP_COLOR.get(self.kind, (200,200,200))
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.radius)
            # label
            label = 'S' if self.kind == 'shield' else 'R'
            img = font.render(label, True, (20,20,30))
            surf.blit(img, (self.x - 6, self.y - 10))

    # Game setup
    def create_enemies():
        enemies = []
        total_width = (ENEMY_COLS - 1) * ENEMY_X_PADDING
        start_x = WIDTH//2 - total_width//2
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = start_x + col * ENEMY_X_PADDING
                y = ENEMY_START_Y + row * ENEMY_Y_PADDING
                enemies.append(Enemy(x, y))
        return enemies

    def draw_text(surf, txt, x, y):
        img = font.render(txt, True, TEXT_COLOR)
        surf.blit(img, (x, y))

    def spawn_powerup_at(x, y):
        if random.random() < POWERUP_CHANCE_ON_KILL:
            kind = random.choices(['shield', 'rapid'], weights=[0.5, 0.5], k=1)[0]
            return Powerup(x, y, kind)
        return None

    def main():
        player = Player()
        bullets = []
        enemies = create_enemies()
        enemy_dx = ENEMY_X_SPEED
        score = 0
        level = 1
        game_over = False
        powerups = []

        while True:
            dt = clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        if not game_over and player.cooldown == 0:
                            bullets.append(Bullet(player.x, player.y - player.h//2 - 8, -BULLET_SPEED, 'player'))
                            player.cooldown = player.shoot_cooldown_value
                    if event.key == pygame.K_r and game_over:
                        # restart
                        player = Player()
                        bullets = []
                        enemies = create_enemies()
                        enemy_dx = ENEMY_X_SPEED
                        score = 0
                        level = 1
                        game_over = False
                        powerups = []

            keys = pygame.key.get_pressed()
            if not game_over:
                player.update(keys)

                # Enemies movement: horizontal sweep, descend and reverse on edge
                hit_edge = False
                for e in enemies:
                    if not e.alive:
                        continue
                    if e.x + e.w//2 + enemy_dx > WIDTH or e.x - e.w//2 + enemy_dx < 0:
                        hit_edge = True
                        break
                if hit_edge:
                    enemy_dx = -enemy_dx
                    for e in enemies:
                        e.y += ENEMY_DESCEND
                else:
                    for e in enemies:
                        e.x += enemy_dx

                # Enemy shooting
                for e in enemies:
                    if not e.alive:
                        continue
                    if random.random() < ENEMY_SHOOT_CHANCE * level:
                        bullets.append(Bullet(e.x, e.y + e.h//2 + 6, BULLET_SPEED, 'enemy'))

                # Update bullets
                for b in bullets:
                    b.update()
                bullets = [b for b in bullets if not b.offscreen()]

                # Update powerups
                for p in powerups:
                    p.update()
                powerups = [p for p in powerups if p.alive]

                # Bullet collisions
                for b in bullets[:]:
                    if b.owner == 'player':
                        for e in enemies:
                            if e.alive and e.rect().collidepoint(b.x, b.y):
                                e.alive = False
                                try:
                                    bullets.remove(b)
                                except ValueError:
                                    pass
                                score += 100
                                # maybe spawn a powerup
                                pu = spawn_powerup_at(e.x, e.y)
                                if pu:
                                    powerups.append(pu)
                                break
                    else:  # enemy bullet -> player
                        if player.rect().collidepoint(b.x, b.y):
                            try:
                                bullets.remove(b)
                            except ValueError:
                                pass
                            if player.shield_active:
                                # shield absorbs bullet and disables
                                player.shield_active = False
                                player.shield_timer = 0
                            else:
                                game_over = True

                # Powerup pickup
                for p in powerups[:]:
                    if player.rect().colliderect(p.rect()):
                        if p.kind == 'shield':
                            player.shield_active = True
                            player.shield_timer = FPS * 6  # 6 seconds
                        elif p.kind == 'rapid':
                            player.shoot_cooldown_value = player.rapid_cooldown
                            player.rapid_timer = FPS * 8  # 8 seconds
                        p.alive = False

                # Check if enemies reached player
                for e in enemies:
                    if e.alive and e.y + e.h//2 >= player.y - player.h:
                        game_over = True
                        break

                # Level complete?
                if all(not e.alive for e in enemies):
                    level += 1
                    enemies = create_enemies()
                    # increase difficulty
                    enemy_dx = ENEMY_X_SPEED + level * 0.2

            # Drawing
            screen.fill(BG)
            for e in enemies:
                e.draw(screen)
            player.draw(screen)
            for b in bullets:
                b.draw(screen)
            for p in powerups:
                p.draw(screen)

            draw_text(screen, f"Score: {score}", 8, 8)
            draw_text(screen, f"Level: {level}", WIDTH - 140, 8)

            # Powerup HUD
            hud_x = 8
            hud_y = 36
            if player.shield_active:
                draw_text(screen, f"Shield: {player.shield_timer//FPS}s", hud_x, hud_y)
                hud_y += 22
            if player.rapid_timer:
                draw_text(screen, f"Rapid: {player.rapid_timer//FPS}s", hud_x, hud_y)

            if game_over:
                draw_text(screen, "GAME OVER - Press R to restart", WIDTH//2 - 160, HEIGHT//2 - 10)

            pygame.display.flip()

    if __name__ == "__main__":
        # start the game with 3 lives and make level 2 easier
        def run_game_with_lives():
            player = Player()
            bullets = []
            enemies = create_enemies()
            enemy_dx = ENEMY_X_SPEED
            score = 0
            level = 1
            lives = 3
            game_over = False
            powerups = []

            while True:
                dt = clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()
                        if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                            if not game_over and player.cooldown == 0:
                                # play sound
                                PLAYER_UFO_SHOOT_SOUND.play()

                                bullets.append(Bullet(player.x, player.y - player.h//2 - 8, -BULLET_SPEED, 'player'))
                                player.cooldown = player.shoot_cooldown_value
                        if event.key == pygame.K_r and game_over:
                            # full restart
                            player = Player()
                            bullets = []
                            enemies = create_enemies()
                            enemy_dx = ENEMY_X_SPEED
                            score = 0
                            level = 1
                            lives = 3
                            game_over = False
                            powerups = []

                keys = pygame.key.get_pressed()
                if not game_over:
                    player.update(keys)

                    # Enemies movement: horizontal sweep, descend and reverse on edge
                    hit_edge = False
                    for e in enemies:
                        if not e.alive:
                            continue
                        if e.x + e.w//2 + enemy_dx > WIDTH or e.x - e.w//2 + enemy_dx < 0:
                            hit_edge = True
                            break
                    if hit_edge:
                        enemy_dx = -enemy_dx
                        for e in enemies:
                            e.y += ENEMY_DESCEND
                    else:
                        for e in enemies:
                            e.x += enemy_dx

                    # Calculate per-level enemy shooting difficulty (make level 2 easier)
                    if level == 2:
                        current_shoot_multiplier = level * 0.6  # 40% easier on level 2
                    else:
                        current_shoot_multiplier = level

                    # Enemy shooting
                    for e in enemies:
                        if not e.alive:
                            continue
                        if random.random() < ENEMY_SHOOT_CHANCE * current_shoot_multiplier:
                            bullets.append(Bullet(e.x, e.y + e.h//2 + 6, BULLET_SPEED, 'enemy'))

                    # Update bullets
                    for b in bullets:
                        b.update()
                    bullets = [b for b in bullets if not b.offscreen()]

                    # Update powerups
                    for p in powerups:
                        p.update()
                    powerups = [p for p in powerups if p.alive]

                    # Bullet collisions
                    for b in bullets[:]:
                        if b.owner == 'player':
                            for e in enemies:
                                if e.alive and e.rect().collidepoint(b.x, b.y):
                                    e.alive = False
                                    try:
                                        bullets.remove(b)
                                    except ValueError:
                                        pass
                                    score += 100
                                    # maybe spawn a powerup
                                    pu = spawn_powerup_at(e.x, e.y)
                                    if pu:
                                        powerups.append(pu)
                                    break
                        else:  # enemy bullet -> player
                            if player.rect().collidepoint(b.x, b.y):
                                try:
                                    bullets.remove(b)
                                except ValueError:
                                    pass
                                if player.shield_active:
                                    # shield absorbs bullet and disables
                                    player.shield_active = False
                                    player.shield_timer = 0
                                else:
                                    # lose a life instead of instant game over
                                    lives -= 1
                                    if lives <= 0:
                                        game_over = True
                                        GAME_OVER_SOUND.play()
                                    else:
                                        # respawn player, clear bullets and powerups to give a breather
                                        player = Player()
                                        bullets = []
                                        powerups = []
                                    break

                    # Powerup pickup
                    for p in powerups[:]:
                        if player.rect().colliderect(p.rect()):
                            if p.kind == 'shield':
                                player.shield_active = True
                                player.shield_timer = FPS * 6  # 6 seconds
                            elif p.kind == 'rapid':
                                player.shoot_cooldown_value = player.rapid_cooldown
                                player.rapid_timer = FPS * 8  # 8 seconds
                            p.alive = False

                    # Check if enemies reached player -> cost a life
                    for e in enemies:
                        if e.alive and e.y + e.h//2 >= player.y - player.h:
                            lives -= 1
                            if lives <= 0:
                                game_over = True
                            else:
                                player = Player()
                                bullets = []
                                powerups = []
                            break

                    # Level complete?
                    if all(not e.alive for e in enemies):
                        level += 1
                        enemies = create_enemies()
                        # increase difficulty, but keep level 2 easier
                        if level == 2:
                            enemy_dx = ENEMY_X_SPEED + 0.1
                        else:
                            enemy_dx = ENEMY_X_SPEED + level * 0.2

                # Drawing
                screen.fill(BG)
                for e in enemies:
                    e.draw(screen)
                player.draw(screen)
                for b in bullets:
                    b.draw(screen)
                for p in powerups:
                    p.draw(screen)

                draw_text(screen, f"Score: {score}", 8, 8)
                draw_text(screen, f"Level: {level}", WIDTH - 140, 8)
                draw_text(screen, f"Lives: {lives}", WIDTH//2 - 30, 8)

                # Powerup HUD
                hud_x = 8
                hud_y = 36
                if player.shield_active:
                    draw_text(screen, f"Shield: {player.shield_timer//FPS}s", hud_x, hud_y)
                    hud_y += 22
                if player.rapid_timer:
                    draw_text(screen, f"Rapid: {player.rapid_timer//FPS}s", hud_x, hud_y)

                if game_over:
                    draw_text(screen, "GAME OVER - Press R to restart", WIDTH//2 - 160, HEIGHT//2 - 10)

                pygame.display.flip()

        # replace the simple main() call with our lives-enabled runner
        # override the previous runner with a skins/backgrounds + UFOs variant and run it
        def run_game_with_lives():
            # Skins: each entry is a set of colors for player, enemy, bullet, bg
            SKINS = [
                {'name': 'Ocean',  'BG': (8, 10, 30),  'PLAYER_COLOR': (100, 220, 255), 'ENEMY_COLOR': (180, 220, 255), 'BULLET_COLOR': (200,255,255)},
                {'name': 'Sunset', 'BG': (30, 10, 20),  'PLAYER_COLOR': (255, 200, 120), 'ENEMY_COLOR': (255, 120, 120), 'BULLET_COLOR': (255,230,160)},
                {'name': 'Neon',   'BG': (6, 0, 20),    'PLAYER_COLOR': (120, 255, 200), 'ENEMY_COLOR': (255, 80, 200),  'BULLET_COLOR': (180,255,120)},
                {'name': 'Alien',  'BG': (4, 14, 6),    'PLAYER_COLOR': (180, 255, 140), 'ENEMY_COLOR': (120, 255, 180), 'BULLET_COLOR': (255,255,120)},
            ]
            skin_idx = 0

            # simple starfield background generator per-skin/level
            def make_stars(seed, count=80):
                rnd = random.Random(seed)
                stars = []
                for _ in range(count):
                    x = rnd.randint(0, WIDTH)
                    y = rnd.randint(0, HEIGHT)
                    r = rnd.randint(1, 3)
                    col = (rnd.randint(80, 220), rnd.randint(80, 220), rnd.randint(100, 255))
                    stars.append((x, y, r, col))
                return stars

            # override/create enemies so some are UFOs
            def create_enemies_with_ufos(level):
                enemies = []
                total_width = (ENEMY_COLS - 1) * ENEMY_X_PADDING
                start_x = WIDTH//2 - total_width//2
                for row in range(ENEMY_ROWS):
                    for col in range(ENEMY_COLS):
                        x = start_x + col * ENEMY_X_PADDING
                        y = ENEMY_START_Y + row * ENEMY_Y_PADDING
                        e = Enemy(x, y)
                        # mark some as UFOs: increase chance with level, place a few in top rows
                        ufo_chance = min(0.2 + level * 0.03, 0.45)
                        if random.random() < ufo_chance and row == 0:
                            e.is_ufo = True
                        else:
                            e.is_ufo = False
                        enemies.append(e)
                return enemies

            # patch enemy drawing to look like UFOs when flagged (we modify instance method via closure)
            def draw_enemy_variant(e, surf):
                if not e.alive:
                    return
                r = e.rect()
                if getattr(e, 'is_ufo', False):
                    # UFO look: dome with little legs
                    pygame.draw.ellipse(surf, ENEMY_COLOR, (r.x, r.y, r.w, r.h))
                    pygame.draw.rect(surf, (20,20,40), (int(e.x)-6, int(e.y)+4, 12, 4))
                    pygame.draw.circle(surf, (255,255,255), (int(e.x), int(e.y)-3), 3)
                else:
                    pygame.draw.rect(surf, ENEMY_COLOR, r)
                    pygame.draw.circle(surf, (20,20,40), (int(e.x - 8), int(e.y - 2)), 3)
                    pygame.draw.circle(surf, (20,20,40), (int(e.x + 8), int(e.y - 2)), 3)

            # We'll re-use Bullet but allow tweaking radius on creation for UFOs
            player = Player()
            bullets = []
            level = 1
            score = 0
            lives = 3
            game_over = False

            # apply initial skin
            def apply_skin(idx):
                global BG, PLAYER_COLOR, ENEMY_COLOR, BULLET_COLOR
                s = SKINS[idx % len(SKINS)]
                BG = s['BG']
                PLAYER_COLOR = s['PLAYER_COLOR']
                ENEMY_COLOR = s['ENEMY_COLOR']
                BULLET_COLOR = s['BULLET_COLOR']

            apply_skin(skin_idx)
            stars = make_stars(level)

            enemies = create_enemies_with_ufos(level)
            enemy_dx = ENEMY_X_SPEED

            while True:
                dt = clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()
                        if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                            if not game_over and player.cooldown == 0:
                                PLAYER_UFO_SHOOT_SOUND.play()
                                bullets.append(Bullet(player.x, player.y - player.h//2 - 8, -BULLET_SPEED, 'player'))
                                player.cooldown = player.shoot_cooldown_value
                        if event.key == pygame.K_r and game_over:
                            # full restart
                            player = Player()
                            bullets = []
                            enemies = create_enemies_with_ufos(1)
                            enemy_dx = ENEMY_X_SPEED
                            score = 0
                            level = 1
                            lives = 3
                            game_over = False
                            skin_idx = 0
                            apply_skin(skin_idx)
                            stars = make_stars(level)

                keys = pygame.key.get_pressed()
                if not game_over:
                    player.update(keys)

                    # Enemies movement: horizontal sweep, descend and reverse on edge
                    hit_edge = False
                    for e in enemies:
                        if not e.alive:
                            continue
                        if e.x + e.w//2 + enemy_dx > WIDTH or e.x - e.w//2 + enemy_dx < 0:
                            hit_edge = True
                            break
                    if hit_edge:
                        enemy_dx = -enemy_dx
                        for e in enemies:
                            e.y += ENEMY_DESCEND
                    else:
                        for e in enemies:
                            e.x += enemy_dx

                    # Enemy shooting (UFOs shoot slightly faster / bigger bullets)
                    # Make level 2 a bit easier as before
                    current_shoot_multiplier = level * (0.6 if level == 2 else 1.0)
                    for e in enemies:
                        if not e.alive:
                            continue
                        if random.random() < ENEMY_SHOOT_CHANCE * current_shoot_multiplier:
                            b = Bullet(e.x, e.y + e.h//2 + 6, BULLET_SPEED * (1.4 if getattr(e, 'is_ufo', False) else 1.0), 'enemy')
                            # bigger bullet if UFO
                            if getattr(e, 'is_ufo', False):
                                b.radius = 8
                            bullets.append(b)

                    # Update bullets
                    for b in bullets:
                        b.update()
                    bullets = [b for b in bullets if not b.offscreen()]

                    # Update powerups (re-use previous lists if present)
                    try:
                        powerups
                    except NameError:
                        powerups = []
                    for p in powerups:
                        p.update()
                    powerups = [p for p in powerups if p.alive]

                    # Bullet collisions
                    for b in bullets[:]:
                        if b.owner == 'player':
                            for e in enemies:
                                if e.alive and e.rect().collidepoint(b.x, b.y):
                                    e.alive = False
                                    try:
                                        bullets.remove(b)
                                    except ValueError:
                                        pass
                                    score += 100
                                    # maybe spawn a powerup
                                    try:
                                        pu = spawn_powerup_at(e.x, e.y)
                                    except NameError:
                                        pu = None
                                    if pu:
                                        powerups.append(pu)
                                    break
                        else:  # enemy bullet -> player
                            if player.rect().collidepoint(b.x, b.y):
                                try:
                                    bullets.remove(b)
                                except ValueError:
                                    pass
                                if player.shield_active:
                                    player.shield_active = False
                                    player.shield_timer = 0
                                else:
                                    lives -= 1
                                    if lives <= 0:
                                        game_over = True
                                        GAME_OVER_SOUND.play()
                                    else:
                                        # respawn player, clear bullets and powerups to give a breather
                                        player = Player()
                                        bullets = []
                                        powerups = []
                                    break

                    # Powerup pickup
                    for p in powerups[:]:
                        if player.rect().colliderect(p.rect()):
                            if p.kind == 'shield':
                                player.shield_active = True
                                player.shield_timer = FPS * 6  # 6 seconds
                            elif p.kind == 'rapid':
                                player.shoot_cooldown_value = player.rapid_cooldown
                                player.rapid_timer = FPS * 8  # 8 seconds
                            p.alive = False

                    # Check if enemies reached player -> cost a life
                    for e in enemies:
                        if e.alive and e.y + e.h//2 >= player.y - player.h:
                            lives -= 1
                            if lives <= 0:
                                game_over = True
                            else:
                                player = Player()
                                bullets = []
                                powerups = []
                            break

                    # Level complete?
                    if all(not e.alive for e in enemies):
                        level += 1
                        # change skin each level
                        skin_idx = (skin_idx + 1) % len(SKINS)
                        apply_skin(skin_idx)
                        stars = make_stars(level)
                        enemies = create_enemies_with_ufos(level)
                        # increase difficulty, but keep level 2 easier
                        if level == 2:
                            enemy_dx = ENEMY_X_SPEED + 0.1
                        else:
                            enemy_dx = ENEMY_X_SPEED + level * 0.2

                # Drawing - improved background (stars + parallax shimmer)
                screen.fill(BG)
                # draw stars
                for sx, sy, r, col in stars:
                    # small twinkling effect
                    tw = (math.sin((sx + sx + sy + pygame.time.get_ticks() * 0.004)) + 1) * 0.5
                    sc = tuple(max(0, min(255, int(c * (0.6 + 0.4 * tw)))) for c in col)
                    pygame.draw.circle(screen, sc, (sx, sy), r)

                # draw enemies with possible UFO look
                for e in enemies:
                    draw_enemy_variant(e, screen)

                # draw player (Player.draw uses global PLAYER_COLOR)
                player.draw(screen)

                # draw bullets
                for b in bullets:
                    b.draw(screen)

                # draw powerups
                for p in powerups:
                    p.draw(screen)

                # HUD
                draw_text(screen, f"Score: {score}", 8, 8)
                draw_text(screen, f"Level: {level} - Skin: {SKINS[skin_idx]['name']}", WIDTH - 280, 8)
                draw_text(screen, f"Lives: {lives}", WIDTH//2 - 30, 8)

                # Powerup HUD
                hud_x = 8
                hud_y = 36
                if player.shield_active:
                    draw_text(screen, f"Shield: {player.shield_timer//FPS}s", hud_x, hud_y)
                    hud_y += 22
                if player.rapid_timer:
                    draw_text(screen, f"Rapid: {player.rapid_timer//FPS}s", hud_x, hud_y)

                if game_over:
                    draw_text(screen, "GAME OVER - Press R to restart", WIDTH//2 - 160, HEIGHT//2 - 10)

                pygame.display.flip()

        # start the modified game
        # simple menu: Play / Quit, show highscore, toggle easier levels and force more UFOs
        def _read_highscore(path="highscore.txt"):
            try:
                with open(path, "r") as f:
                    return int(f.read().strip() or 0)
            except Exception:
                return 0

        def _menu_and_launch():
            highscore = _read_highscore()
            easier = True
            force_ufo_seed = True

            title_y = HEIGHT//2 - 110
            while True:
                clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_q, pygame.K_ESCAPE):
                            pygame.quit(); sys.exit()
                        if event.key == pygame.K_e:
                            easier = not easier
                        if event.key == pygame.K_u:
                            force_ufo_seed = not force_ufo_seed
                        if event.key == pygame.K_p:
                            # apply easier level tweaks
                            if easier:
                                # make enemies shoot less and move a bit slower / scale down difficulty growth
                                global ENEMY_SHOOT_CHANCE, ENEMY_X_SPEED
                                ENEMY_SHOOT_CHANCE = max(0.0005, ENEMY_SHOOT_CHANCE * 0.45)
                                ENEMY_X_SPEED = ENEMY_X_SPEED * 0.78
                                # also reduce level speed-up in the simplest way by lowering the multiplier variable used later
                                try:
                                    LEVEL_SPEED_EASE = 0.14
                                except Exception:
                                    LEVEL_SPEED_EASE = 0.14
                            else:
                                LEVEL_SPEED_EASE = 0.2
                            # bias UFO placement deterministically so "oben überall ufos" is more likely
                            if force_ufo_seed:
                                random.seed(123456)
                            # start the game (the in-file run_game_with_lives will use the tweaked globals / RNG)
                            run_game_with_lives()
                # draw menu
                screen.fill(BG)
                draw_text(screen, "SPACE INVADERS - MENU", WIDTH//2 - 140, title_y)
                draw_text(screen, "Press P to Play", WIDTH//2 - 90, title_y + 50)
                draw_text(screen, "Press Q or ESC to Quit", WIDTH//2 - 120, title_y + 86)
                draw_text(screen, f"Highscore: {highscore}", WIDTH//2 - 80, title_y + 130)
                draw_text(screen, f"[E]asier levels: {'ON' if easier else 'OFF'}", WIDTH//2 - 160, title_y + 170)
                draw_text(screen, f"[U] Top-row UFO bias: {'ON' if force_ufo_seed else 'OFF'}", WIDTH//2 - 160, title_y + 200)
                draw_text(screen, "Tip: After game over press R to restart.", WIDTH//2 - 210, title_y + 240)
                pygame.display.flip()

        # enable returning to menu during play with M and add simple ship-variant/strength + UFO-shooter visuals
        class _MenuRequested(Exception):
            pass

        # monkey-patch pygame.event.get to signal menu requests (press M)
        _original_event_get = pygame.event.get
        def _patched_event_get(*args, **kwargs):
            evts = _original_event_get(*args, **kwargs)
            for e in evts:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                    raise _MenuRequested()
            return evts
        pygame.event.get = _patched_event_get

        # small global to cycle ship styles / strength between runs
        SHIP_STYLE = 0

        # make new players a bit stronger and change appearance per SHIP_STYLE
        _original_player_init = Player.__init__
        def _patched_player_init(self, *a, **kw):
            _original_player_init(self, *a, **kw)
            # stronger: reduce base cooldown and enlarge hull slightly per style
            self.base_cooldown = getattr(self, 'base_cooldown', 12)
            self.base_cooldown = max(3, self.base_cooldown - SHIP_STYLE)  # stronger = less cooldown
            self.shoot_cooldown_value = self.base_cooldown
            self.w = getattr(self, 'w', 50) + SHIP_STYLE * 6
        Player.__init__ = _patched_player_init

        # vary player draw to reflect different ship styles
        _original_player_draw = Player.draw
        def _patched_player_draw(self, surf):
            # style 0 = default, 1 = triangle/nose, 2 = saucer, 3 = armored block
            if SHIP_STYLE % 4 == 0:
                _original_player_draw(self, surf)
            elif SHIP_STYLE % 4 == 1:
                # triangular hull
                pygame.draw.polygon(surf, PLAYER_COLOR, [(self.x, self.y - self.h), (self.x - self.w//2, self.y + self.h//2), (self.x + self.w//2, self.y + self.h//2)])
                pygame.draw.rect(surf, PLAYER_COLOR, (self.x - 6, self.y - self.h//2 - 8, 12, 8))
            elif SHIP_STYLE % 4 == 2:
                # saucer
                r = self.rect()
                pygame.draw.ellipse(surf, PLAYER_COLOR, (r.x - 6, r.y - 4, r.w + 12, r.h + 8))
                pygame.draw.rect(surf, PLAYER_COLOR, (self.x - 8, self.y - self.h//2 - 6, 16, 8))
            else:
                # heavy armored block
                r = self.rect()
                pygame.draw.rect(surf, PLAYER_COLOR, (r.x - 4, r.y - 6, r.w + 8, r.h + 12), 0)
                pygame.draw.rect(surf, (120,120,140), (self.x - 10, self.y - self.h//2 - 10, 20, 6))
            # shield visual if active
            if getattr(self, 'shield_active', False):
                pygame.draw.circle(surf, SHIELD_COLOR, (int(self.x), int(self.y)), max(self.w, self.h), 2)
        Player.draw = _patched_player_draw

        # draw enemies that are likely shooters as UFOs (top rows and a small random chance)
        _original_enemy_draw = Enemy.draw
        def _patched_enemy_draw(self, surf):
            if not self.alive:
                return
            # treat top-row enemies (and a few random ones) as UFO shooters visually
            if self.y <= ENEMY_START_Y + ENEMY_Y_PADDING + 6 or random.random() < 0.12:
                r = self.rect()
                # UFO dome + hull
                pygame.draw.ellipse(surf, ENEMY_COLOR, (r.x - 6, r.y - 4, r.w + 12, r.h + 8))
                pygame.draw.rect(surf, (20,20,40), (int(self.x) - 8, int(self.y) + 4, 16, 5))
                pygame.draw.circle(surf, (255,255,255), (int(self.x), int(self.y) - 4), 3)
            else:
                _original_enemy_draw(self, surf)
        Enemy.draw = _patched_enemy_draw

        # run menu/game in a loop; pressing M during play (or on game-over screen) returns to menu.
        while True:
            try:
                _menu_and_launch()
                break  # normal exit
            except _MenuRequested:
                # user requested return to menu (M). cycle ship style / strength a bit.
                SHIP_STYLE = (SHIP_STYLE + 1) % 4
                # small debounce to avoid immediately re-triggering
                pygame.time.delay(120)
                # ensure our patched event.get stays active
                pygame.event.get = _patched_event_get
                continue
                # load a sound and play it whenever the player's ship (saucer/UFO style) fires
                try:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                except Exception:
                    pass

                PLAYER_UFO_SHOOT_SOUND = None
                for _fn in ("game sound psu.m4a"):
                    try:
                        PLAYER_UFO_SHOOT_SOUND = pygame.mixer.Sound(_fn)
                        PLAYER_UFO_SHOOT_SOUND.set_volume(0.6)
                        break
                    except Exception:  
                        PLAYER_UFO_SHOOT_SOUND = None

                _original_bullet_init = Bullet.__init__
                def _patched_bullet_init(self, x, y, dy, owner):
                    _original_bullet_init(self, x, y, dy, owner)
                    try:
                        # play only for player bullets when the player's ship style is the saucer/UFO (style 2)
                        if owner == "player" and globals().get("SHIP_STYLE", 0) % 4 == 2 and PLAYER_UFO_SHOOT_SOUND:
                            PLAYER_UFO_SHOOT_SOUND.play()
                    except Exception:
                        pass

                # load mixer & sound once (put this before the menu/game loop)
                try:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                except Exception:
                    pass

                PLAYER_UFO_SHOOT_SOUND = None
                for _fn in ("game_sound_psu.wav", "game_sound_psu.ogg", "game_sound_psu.m4a"):
                    try:
                        PLAYER_UFO_SHOOT_SOUND = pygame.mixer.Sound(_fn)
                        PLAYER_UFO_SHOOT_SOUND.set_volume(0.6)
                        break
                    except Exception:
                        PLAYER_UFO_SHOOT_SOUND = None

                _original_bullet_init = Bullet.__init__
                def _patched_bullet_init(self, x, y, dy, owner):
                    _original_bullet_init(self, x, y, dy, owner)
                    try:
                        # owner is 'player' in your code; sound plays only for ship style 2 (saucer)
                        if owner == 'player' and globals().get("SHIP_STYLE", 0) % 4 == 2 and PLAYER_UFO_SHOOT_SOUND:
                            PLAYER_UFO_SHOOT_SOUND.play()
                    except Exception:
                        pass

                Bullet.__init__ = _patched_bullet_init
