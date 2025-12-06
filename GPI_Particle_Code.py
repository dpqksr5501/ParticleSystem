import pygame
import random
import math

# --- 기본 설정 및 상수 ---
WIDTH, HEIGHT = 1300, 850
FPS = 60

# 물리 상수
WIND_POWER = 0.5
FRICTION = 0.99
REPULSION_POWER = 5.0
BOUNCE_FACTOR = -0.7 
OBSTACLE_FRICTION = 0.99 # 장애물 마찰력 (이동형 장애물이 멈추도록)

# 색상 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
GRAY = (150, 150, 150)      # 고정형 장애물 색상
ORANGE = (255, 165, 0)      # 이동형 장애물 색상

# --- 파티클 생성기 ---
class SpawnPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.timer = 0
        self.spawn_rate = 1 

    def update(self, particle_system):
        self.timer += 1
        if self.timer >= self.spawn_rate:
            particle_system.add_particles(self.x, self.y, count=1)
            self.timer = 0

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.radius + 3, 1)

# --- 장애물 사각형 클래스 ---
class Obstacle:
    def __init__(self, x, y, size=40, is_static=True):
        self.rect = pygame.Rect(x - size//2, y - size//2, size, size)
        self.is_static = is_static
        
        # 물리 속성
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
        self.vel_x = 0.0
        self.vel_y = 0.0
        
        if is_static:
            self.mass = float('inf')
            self.inv_mass = 0.0
            self.color = GRAY
        else:
            self.mass = 200.0 
            self.inv_mass = 1.0 / self.mass
            self.color = ORANGE

    def update(self):
        if not self.is_static:
            # 마찰력 적용
            self.vel_x *= OBSTACLE_FRICTION
            self.vel_y *= OBSTACLE_FRICTION
            
            # 위치 업데이트
            self.pos_x += self.vel_x
            self.pos_y += self.vel_y
            
            # Rect 위치 동기화
            self.rect.centerx = int(self.pos_x)
            self.rect.centery = int(self.pos_y)
            
            # 화면 경계 충돌
            if self.rect.left < 0:
                self.vel_x *= -1
                self.pos_x = self.rect.width // 2
            elif self.rect.right > WIDTH:
                self.vel_x *= -1
                self.pos_x = WIDTH - self.rect.width // 2
                
            if self.rect.top < 0:
                self.vel_y *= -1
                self.pos_y = self.rect.height // 2
            elif self.rect.bottom > HEIGHT:
                self.vel_y *= -1
                self.pos_y = HEIGHT - self.rect.height // 2

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 1)

# --- 파티클 클래스 ---
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = random.uniform(-2, 2)
        self.vel_y = random.uniform(-2, 2)
        self.acc_x = 0
        self.acc_y = 0
        self.radius = random.randint(3, 5)
        self.lifetime = 300
        self.color = [random.randint(50, 100), random.randint(100, 200), random.randint(200, 255)]
        
        self.mass = self.radius * 2
        self.inv_mass = 1.0 / self.mass

    def apply_force(self, force_x, force_y):
        self.acc_x += force_x * self.inv_mass 
        self.acc_y += force_y * self.inv_mass

    def apply_repulsion(self, target_x, target_y):
        dx = self.x - target_x
        dy = self.y - target_y
        distance = math.sqrt(dx**2 + dy**2)
        if distance < 1: distance = 1
        force = REPULSION_POWER * 10 / distance 
        self.apply_force((dx / distance) * force, (dy / distance) * force)

    def resolve_collision(self, obstacle):
        closest_x = max(obstacle.rect.left, min(self.x, obstacle.rect.right))
        closest_y = max(obstacle.rect.top, min(self.y, obstacle.rect.bottom))

        dist_x = self.x - closest_x
        dist_y = self.y - closest_y
        distance_squared = (dist_x ** 2) + (dist_y ** 2)

        if distance_squared < (self.radius ** 2):
            distance = math.sqrt(distance_squared)
            if distance == 0: return

            normal_x = dist_x / distance
            normal_y = dist_y / distance
            
            overlap = self.radius - distance
            self.x += normal_x * overlap
            self.y += normal_y * overlap
            
            rel_vel_x = self.vel_x - obstacle.vel_x
            rel_vel_y = self.vel_y - obstacle.vel_y
            
            vel_along_normal = (rel_vel_x * normal_x) + (rel_vel_y * normal_y)
            
            if vel_along_normal > 0: return 

            restitution = 0.7 
            j = -(1 + restitution) * vel_along_normal
            j /= (self.inv_mass + obstacle.inv_mass)
            
            impulse_x = j * normal_x
            impulse_y = j * normal_y
            
            self.vel_x += impulse_x * self.inv_mass
            self.vel_y += impulse_y * self.inv_mass
            
            obstacle.vel_x -= impulse_x * obstacle.inv_mass
            obstacle.vel_y -= impulse_y * obstacle.inv_mass

    def update(self):
        self.vel_x += self.acc_x
        self.vel_y += self.acc_y
        self.vel_x *= FRICTION
        self.vel_y *= FRICTION
        
        self.x += self.vel_x
        self.y += self.vel_y
        
        self.acc_x = 0
        self.acc_y = 0
        self.lifetime -= 1.0

    def draw(self, screen):
        if self.lifetime > 0:
            particle_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            alpha = int(min(self.lifetime, 255))
            
            speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
            
            r = max(0, min(255, self.color[0] + int(speed * 30)))
            g = max(0, min(255, self.color[1] - int(speed * 10)))
            b = max(0, min(255, self.color[2] - int(speed * 10)))
            
            pygame.draw.circle(particle_surf, (r, g, b, alpha), (self.radius, self.radius), self.radius)
            screen.blit(particle_surf, (int(self.x) - self.radius, int(self.y) - self.radius))

# --- 물리 엔진 관리자 ---
class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.spawners = []
        self.obstacles = []

    def add_particles(self, x, y, count=1):
        for _ in range(count):
            self.particles.append(Particle(x, y))

    def add_spawner(self, x, y):
        self.spawners.append(SpawnPoint(x, y))

    def clear_spawners(self):
        self.spawners.clear()

    def add_obstacle(self, x, y, is_static):
        self.obstacles.append(Obstacle(x, y, is_static=is_static))

    # 장애물 제거 함수
    def clear_obstacles(self):
        self.obstacles.clear()

    # 장애물 간 충돌 처리
    def resolve_obstacle_collisions(self):
        n = len(self.obstacles)
        for i in range(n):
            for j in range(i + 1, n):
                obs1 = self.obstacles[i]
                obs2 = self.obstacles[j]
                
                # 둘 다 고정이면 충돌 처리 불필요
                if obs1.is_static and obs2.is_static:
                    continue

                # AABB 충돌 감지
                if obs1.rect.colliderect(obs2.rect):
                    # 충돌 깊이 및 법선 계산
                    dx = obs1.pos_x - obs2.pos_x
                    dy = obs1.pos_y - obs2.pos_y
                    
                    # 겹친 정도 계산
                    w_half_sum = (obs1.rect.width + obs2.rect.width) / 2
                    h_half_sum = (obs1.rect.height + obs2.rect.height) / 2
                    
                    overlap_x = w_half_sum - abs(dx)
                    overlap_y = h_half_sum - abs(dy)

                    if overlap_x <= 0 or overlap_y <= 0: continue # 실제로는 안 겹침

                    # 법선 결정: 겹침이 더 적은 축을 법선으로 사용
                    normal_x, normal_y = 0, 0
                    penetration = 0

                    if overlap_x < overlap_y:
                        normal_x = 1 if dx > 0 else -1
                        penetration = overlap_x
                    else:
                        normal_y = 1 if dy > 0 else -1
                        penetration = overlap_y

                    # 위치 보정 (겹침 해결)
                    total_inv_mass = obs1.inv_mass + obs2.inv_mass
                    if total_inv_mass == 0: continue
                    
                    move_per_inv_mass = penetration / total_inv_mass
                    
                    if not obs1.is_static:
                        obs1.pos_x += normal_x * move_per_inv_mass * obs1.inv_mass
                        obs1.pos_y += normal_y * move_per_inv_mass * obs1.inv_mass
                    if not obs2.is_static:
                        obs2.pos_x -= normal_x * move_per_inv_mass * obs2.inv_mass
                        obs2.pos_y -= normal_y * move_per_inv_mass * obs2.inv_mass

                    # 충격량(Impulse) 적용
                    rel_vel_x = obs1.vel_x - obs2.vel_x
                    rel_vel_y = obs1.vel_y - obs2.vel_y
                    
                    vel_along_normal = rel_vel_x * normal_x + rel_vel_y * normal_y
                    
                    if vel_along_normal > 0: continue # 이미 멀어지는 중

                    restitution = 0.5 # 상자끼리의 반발 계수
                    j = -(1 + restitution) * vel_along_normal
                    j /= total_inv_mass
                    
                    impulse_x = j * normal_x
                    impulse_y = j * normal_y
                    
                    if not obs1.is_static:
                        obs1.vel_x += impulse_x * obs1.inv_mass
                        obs1.vel_y += impulse_y * obs1.inv_mass
                    if not obs2.is_static:
                        obs2.vel_x -= impulse_x * obs2.inv_mass
                        obs2.vel_y -= impulse_y * obs2.inv_mass

    def update(self, wind_x, wind_y, repulse_pos=None):
        for spawner in self.spawners:
            spawner.update(self)
        
        for obs in self.obstacles:
            obs.update()

        # 장애물끼리의 충돌 처리 실행
        self.resolve_obstacle_collisions()

        self.particles = [p for p in self.particles if p.lifetime > 0]
        
        for p in self.particles:
            p.apply_force(wind_x, wind_y)
            if repulse_pos:
                p.apply_repulsion(repulse_pos[0], repulse_pos[1])
            
            p.update()
            
            for obs in self.obstacles:
                p.resolve_collision(obs)

    def draw(self, screen):
        for obs in self.obstacles:
            obs.draw(screen)
        for spawner in self.spawners:
            spawner.draw(screen)
        for p in self.particles:
            p.draw(screen)

# --- 메인 실행 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Particle Physics Engine: Impulse & Dynamics")
    clock = pygame.time.Clock()
    system = ParticleSystem()
    running = True

    while running:
        screen.fill(BLACK)
        repulse_pos = None
        
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        is_ctrl = mods & pygame.KMOD_LCTRL
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    system.clear_spawners()
                
                if event.key == pygame.K_r:
                    mx, my = pygame.mouse.get_pos()
                    system.add_obstacle(mx, my, is_static=True)
                
                if event.key == pygame.K_t:
                    mx, my = pygame.mouse.get_pos()
                    system.add_obstacle(mx, my, is_static=False)
                
                # M 키: 모든 장애물 제거
                if event.key == pygame.K_m:
                    system.clear_obstacles()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if is_ctrl: 
                        system.add_spawner(mx, my)
                    else: 
                        system.add_particles(mx, my, count=5)

        mouse_buttons = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()
        
        if mouse_buttons[0] and not is_ctrl:
            system.add_particles(mx, my, count=2)
        if mouse_buttons[2]:
            repulse_pos = (mx, my)
            pygame.draw.circle(screen, CYAN, (mx, my), 20, 1)

        wind_x, wind_y = 0, 0
        if keys[pygame.K_LEFT]: wind_x -= WIND_POWER
        if keys[pygame.K_RIGHT]: wind_x += WIND_POWER
        if keys[pygame.K_UP]: wind_y -= WIND_POWER
        if keys[pygame.K_DOWN]: wind_y += WIND_POWER

        system.update(wind_x, wind_y, repulse_pos)
        system.draw(screen)
        
        # UI
        font = pygame.font.SysFont(None, 24)
        msg = f"Particles: {len(system.particles)} | Spawners: {len(system.spawners)} | Obstacles: {len(system.obstacles)}"
        help_msg = "L-Click: Particle Spawn | R-Click: Repulsion | LShift: Clear Spawners | M: Clear Boxes"
        help_msg_2 = "R: Static Box | T: Dynamic Box | Ctrl+Click: Spawner | UP/DOWN/LEFT/RIGHT : Wind" 

        # 출력
        screen.blit(font.render(msg, True, WHITE), (10, 10))
        screen.blit(font.render(help_msg, True, CYAN), (10, 35))
        screen.blit(font.render(help_msg_2, True, CYAN), (10, 60))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

main()