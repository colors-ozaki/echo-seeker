import pygame
import sys
import random
import math
import asyncio  # 追加

# --- 設定 ---
WIDTH, HEIGHT = 800, 600
PLAYER_SPEED = 5
JUMP_FORCE = -16
GRAVITY = 0.8

# --- 初期化 ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Echo Seeker - Night City")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 64)

# --- ゲームの状態 ---
game_state = 0 
camera_x = 0

# --- パーティクル ---
particles = [] 
def create_particles(x, y, count=5, color=(0, 200, 255)):
    for _ in range(count):
        particles.append([x, y, random.uniform(-2, 2), random.uniform(-2, 2), 20, color])

# --- 背景のビル生成 ---
building_data = []
for i in range(60): 
    b_width = random.randint(90, 160)
    b_height = random.randint(200, 520)
    b_x = i * 100 - 1000 
    windows = []
    for row in range(b_height // 25 - 1):
        for col in range(b_width // 20 - 1):
            if random.random() < 0.35:
                windows.append((col * 20 + 8, row * 25 + 10))
    building_data.append({'x': b_x, 'w': b_width, 'h': b_height, 'windows': windows})

# --- 忍者描画 ---
def draw_ninja(surface, x, y, direction, is_jumping, vel_y):
    pygame.draw.rect(surface, (10, 10, 10), (x, y, 30, 30))
    pygame.draw.rect(surface, (60, 60, 60), (x, y, 30, 30), 1)
    pygame.draw.rect(surface, (255, 200, 150), (x + 5, y + 5, 20, 8))
    eye_x = x + 8 if direction == 1 else x + 18
    pygame.draw.circle(surface, (0, 0, 0), (eye_x, y + 9), 2)
    scarf_color = (200, 0, 0)
    pygame.draw.rect(surface, scarf_color, (x + 10, y + 3, 10, 3))
    off_x = -18 if direction == 1 else 18
    off_y = 5 + (vel_y * 0.7)
    points = [(x+15, y+5), (x+15+off_x, y+off_y), (x+15+off_x*1.2, y+off_y+3)]
    pygame.draw.lines(surface, scarf_color, False, points, 3)

# --- ステージ ---
walls = [
    pygame.Rect(0, 550, 600, 50), 
    pygame.Rect(750, 450, 250, 20),
    pygame.Rect(1100, 350, 200, 20),
    pygame.Rect(1400, 480, 250, 20),
    pygame.Rect(1800, 320, 200, 20),
    pygame.Rect(2100, 200, 250, 20),
]
walls_visibility = [0.0] * len(walls)
goal_rect = pygame.Rect(2150, 150, 40, 40)

# プレイヤー変数の初期化用（グローバルを扱うために関数外に配置）
player_rect = pygame.Rect(50, 400, 30, 30)
player_vel_y = 0
is_jumping = False
player_dir = 1

def reset_player():
    global player_rect, player_vel_y, is_jumping, camera_x, walls_visibility, player_dir
    player_rect = pygame.Rect(50, 400, 30, 30)
    player_vel_y = 0
    is_jumping = False
    camera_x = 0
    player_dir = 1
    walls_visibility = [0.0] * len(walls)

def draw_background(cam_x):
    for y in range(HEIGHT):
        c = (max(10, 20-y//40), max(15, 30-y//25), max(35, 60-y//15))
        pygame.draw.line(screen, c, (0, y), (WIDTH, y))
    
    for b in building_data:
        rx = b['x'] - cam_x * 0.3
        if -b['w'] < rx < WIDTH:
            b_color = (30, 30, 45)
            b_rect = pygame.Rect(rx, HEIGHT - b['h'], b['w'], b['h'])
            pygame.draw.rect(screen, b_color, b_rect)
            pygame.draw.rect(screen, (50, 50, 70), b_rect, 1)
            for wx, wy in b['windows']:
                pygame.draw.rect(screen, (200, 200, 120), (rx + wx, (HEIGHT - b['h']) + wy, 4, 6))

# --- メインループを非同期関数にする ---
async def main():
    global game_state, camera_x, player_rect, player_vel_y, is_jumping, player_dir, walls_visibility
    
    # 音波設定
    echo_radius = 0
    echo_active = False
    echo_angle_center = 0
    ECHO_WIDTH = 55
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN and game_state == 0:
                if event.key == pygame.K_UP and not is_jumping:
                    player_vel_y = JUMP_FORCE
                    is_jumping = True
                    create_particles(player_rect.centerx, player_rect.bottom, count=3, color=(100, 100, 100))
            
            if event.type == pygame.MOUSEBUTTONDOWN and game_state == 0:
                if not echo_active:
                    echo_active = True
                    echo_radius = 0
                    mx, my = pygame.mouse.get_pos()
                    dx, dy = mx - (player_rect.centerx - camera_x), my - player_rect.centery
                    echo_angle_center = math.degrees(math.atan2(dy, dx))
                    create_particles(player_rect.centerx, player_rect.centery, count=8)

        if game_state == 0:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: 
                player_rect.x -= PLAYER_SPEED
                player_dir = -1
            if keys[pygame.K_RIGHT]: 
                player_rect.x += PLAYER_SPEED
                player_dir = 1
            
            player_vel_y += GRAVITY
            player_rect.y += player_vel_y
            
            for i, wall in enumerate(walls):
                if player_rect.colliderect(wall):
                    if player_vel_y > 0:
                        player_rect.bottom = wall.top
                        player_vel_y = 0
                        is_jumping = False
            
            if player_rect.y > HEIGHT + 100: 
                reset_player()
            
            camera_x = player_rect.x - WIDTH // 2
            
            if echo_active:
                echo_radius += 24
                if echo_radius > 850: 
                    echo_active = False

            FADE_SPEED = 3.0 
            for i, wall in enumerate(walls):
                if player_rect.colliderect(wall):
                    walls_visibility[i] = 100.0
                else:
                    dist_v = pygame.math.Vector2(wall.centerx-player_rect.centerx, wall.centery-player_rect.centery)
                    ang = math.degrees(math.atan2(dist_v.y, dist_v.x))
                    diff = (ang - echo_angle_center + 180) % 360 - 180
                    if echo_active and abs(diff) < ECHO_WIDTH//2 and abs(dist_v.length() - echo_radius) < 80:
                        walls_visibility[i] = 100.0
                    elif walls_visibility[i] > 0:
                        walls_visibility[i] -= FADE_SPEED

            if player_rect.colliderect(goal_rect): 
                game_state = 1
                
            for p in particles[:]:
                p[0] += p[2]
                p[1] += p[3]
                p[4] -= 1
                if p[4] <= 0: 
                    particles.remove(p)

        # 描画処理
        draw_background(camera_x)
        if game_state == 0:
            if echo_active:
                arc_rect = pygame.Rect(player_rect.centerx - camera_x - echo_radius, player_rect.centery - echo_radius, echo_radius*2, echo_radius*2)
                pygame.draw.arc(screen, (0, 200, 255), arc_rect, -math.radians(echo_angle_center + ECHO_WIDTH//2), -math.radians(echo_angle_center - ECHO_WIDTH//2), 3)

            for i, wall in enumerate(walls):
                if walls_visibility[i] > 0:
                    br = int(max(0, min(255, walls_visibility[i] * 2.55)))
                    pygame.draw.rect(screen, (0, br // 2, br), (wall.x - camera_x, wall.y, wall.width, wall.height))
                    pygame.draw.rect(screen, (br // 2, br, br), (wall.x - camera_x, wall.y, wall.width, wall.height), 1)

            pygame.draw.rect(screen, (200, 160, 50), (goal_rect.x - camera_x, goal_rect.y, 40, 40))
            draw_ninja(screen, player_rect.x - camera_x, player_rect.y, player_dir, is_jumping, player_vel_y)
        
        elif game_state == 1:
            text = font.render("MISSION ACCOMPLISHED", True, (255, 255, 255))
            screen.blit(text, (WIDTH//2 - 300, HEIGHT//2 - 50))

        pygame.display.flip()
        clock.tick(60)
        
        # ウェブ用：ブラウザに処理を譲る
        await asyncio.sleep(0)

# 実行
asyncio.run(main())