import pygame
import numpy as np
import sys
import itertools
import random

# --- parametry symulacji ---
N = 10
speeds = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
angles_deg = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
gravity_y = -9.8
bounciness = 0.95
air_resistance = 0.025
kick_force = 10.0
kick_force_min = 0.0
kick_force_max = 30.0

# --- inicjalizacja pygame ---
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Balls Simulation with RK4 solver")
clock = pygame.time.Clock()

# --- skalowanie fizyki do ekranu ---
sim_min_width = 20.0
c_scale = min(width, height) / sim_min_width
sim_width = width / c_scale
sim_height = height / c_scale

def cX(x): return int(x * c_scale)
def cY(y): return int(height - y * c_scale)

# --- inicjalizacja kulek ---
balls = []
for i in range(N):
    speed = speeds[i] if i < len(speeds) else speeds[-1]
    angle_deg_i = angles_deg[i] if i < len(angles_deg) else angles_deg[-1]
    angle_rad = np.radians(angle_deg_i)
    balls.append({
        'radius': 0.3,
        'mass': 1.0,
        'pos': {'x': 0.2, 'y': 0.2},
        'vel': {
            'x': speed * np.cos(angle_rad),
            'y': speed * np.sin(angle_rad)
        },
        'color': (
            np.random.randint(50, 255),
            np.random.randint(50, 255),
            np.random.randint(50, 255)
        )
    })

gravity = {'x': 0.0, 'y': gravity_y}
time_step = 1.0 / 60.0

# --- domek ---
cx = sim_width / 2
house_width = 8
house_height = 5
roof_height = 2.5
y1 = 0.0
y2 = y1 + house_height
x1, x2 = cx - house_width/2, cx + house_width/2

house_segments = [
    ((x1, y1), (x1, y2)), ((x2, y1), (x2, y2)), ((x1, y1), (x2, y1)),
    ((x1, y2), (cx, y2 + roof_height)), ((cx, y2 + roof_height), (x2, y2)),
    ((cx - 1.0, y1), (cx - 1.0, y1 + 2.5)), ((cx + 1.0, y1), (cx + 1.0, y1 + 2.5)),
    ((cx - 1.0, y1 + 2.5), (cx + 1.0, y1 + 2.5)),
    ((cx - 2.0, y1 + 3.0), (cx - 2.0, y1 + 4.0)), ((cx - 1.0, y1 + 3.0), (cx - 1.0, y1 + 4.0)),
    ((cx - 2.0, y1 + 3.0), (cx - 1.0, y1 + 3.0)), ((cx - 2.0, y1 + 4.0), (cx - 1.0, y1 + 4.0)),
]

# --- funkcje pomocnicze ---
def reflect(vx, vy, x1, y1, x2, y2, bounciness):
    lx, ly = x2 - x1, y2 - y1
    nx, ny = -ly, lx
    norm = np.sqrt(nx**2 + ny**2)
    nx /= norm
    ny /= norm
    dot = vx * nx + vy * ny
    vx_new = vx - 2 * dot * nx
    vy_new = vy - 2 * dot * ny
    return vx_new * bounciness, vy_new * bounciness

def collide_balls(b1, b2):
    dx = b2['pos']['x'] - b1['pos']['x']
    dy = b2['pos']['y'] - b1['pos']['y']
    dist = np.hypot(dx, dy)
    min_dist = b1['radius'] + b2['radius']
    if dist == 0 or dist >= min_dist:
        return

    nx = dx / dist
    ny = dy / dist
    overlap = (min_dist - dist) / 2
    b1['pos']['x'] -= nx * overlap
    b1['pos']['y'] -= ny * overlap
    b2['pos']['x'] += nx * overlap
    b2['pos']['y'] += ny * overlap

    v1n = b1['vel']['x'] * nx + b1['vel']['y'] * ny
    v2n = b2['vel']['x'] * nx + b2['vel']['y'] * ny
    m1, m2 = b1['mass'], b2['mass']
    v1n_new = (v1n * (m1 - m2) + 2 * m2 * v2n) / (m1 + m2)
    v2n_new = (v2n * (m2 - m1) + 2 * m1 * v1n) / (m1 + m2)

    b1['vel']['x'] += (v1n_new - v1n) * nx
    b1['vel']['y'] += (v1n_new - v1n) * ny
    b2['vel']['x'] += (v2n_new - v2n) * nx
    b2['vel']['y'] += (v2n_new - v2n) * ny

# --- solver RK4 ---
def acceleration(pos, vel):
    v = np.linalg.norm(vel)
    drag = -air_resistance * v * vel
    return np.array([gravity['x'], gravity['y']]) + drag

def rk4_step(pos, vel, dt, accel_func):
    k1v = accel_func(pos, vel)
    k1x = vel

    k2v = accel_func(pos + 0.5*dt*k1x, vel + 0.5*dt*k1v)
    k2x = vel + 0.5*dt*k1v

    k3v = accel_func(pos + 0.5*dt*k2x, vel + 0.5*dt*k2v)
    k3x = vel + 0.5*dt*k2v

    k4v = accel_func(pos + dt*k3x, vel + dt*k3v)
    k4x = vel + dt*k3v

    pos_new = pos + (dt/6.0)*(k1x + 2*k2x + 2*k3x + k4x)
    vel_new = vel + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
    return pos_new, vel_new

# --- pętla główna ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
           event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # lewy - podbijanie w górę
                for ball in balls:
                    ball['vel']['y'] += kick_force
            elif event.button == 3:  # prawy - losowy kąt i moc
                for ball in balls:
                    angle = random.uniform(0, 2*np.pi)
                    force = random.uniform(kick_force_min, kick_force_max)
                    ball['vel']['x'] += force * np.cos(angle)
                    ball['vel']['y'] += force * np.sin(angle)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                angle = np.radians(45)
                for ball in balls:
                    ball['vel']['x'] += kick_force * np.cos(angle)
                    ball['vel']['y'] += kick_force * np.sin(angle)
            elif event.key == pygame.K_LEFT:
                angle = np.radians(135)
                for ball in balls:
                    ball['vel']['x'] += kick_force * np.cos(angle)
                    ball['vel']['y'] += kick_force * np.sin(angle)

    # --- fizyka ---
    for ball in balls:
        pos = np.array([ball['pos']['x'], ball['pos']['y']])
        vel = np.array([ball['vel']['x'], ball['vel']['y']])
        pos, vel = rk4_step(pos, vel, time_step, acceleration)
        ball['pos']['x'], ball['pos']['y'] = pos
        ball['vel']['x'], ball['vel']['y'] = vel

        # kolizje z domkiem
        for (x1, y1), (x2, y2) in house_segments:
            px, py = ball['pos']['x'], ball['pos']['y']
            line_vec = np.array([x2 - x1, y2 - y1])
            p_vec = np.array([px - x1, py - y1])
            t = np.clip(np.dot(p_vec, line_vec) / np.dot(line_vec, line_vec), 0, 1)
            closest = np.array([x1, y1]) + t * line_vec
            dist = np.linalg.norm(np.array([px, py]) - closest)
            if dist < ball['radius']:
                ball['vel']['x'], ball['vel']['y'] = reflect(
                    ball['vel']['x'], ball['vel']['y'], x1, y1, x2, y2, bounciness
                )
                normal = np.array([px - closest[0], py - closest[1]])
                normal /= np.linalg.norm(normal)
                ball['pos']['x'] = closest[0] + normal[0] * ball['radius']
                ball['pos']['y'] = closest[1] + normal[1] * ball['radius']

        # odbicia od ścian, podłogi i sufitu
        if ball['pos']['x'] < 0.0:
            ball['pos']['x'] = 0.0
            ball['vel']['x'] *= -bounciness
        if ball['pos']['x'] > sim_width:
            ball['pos']['x'] = sim_width
            ball['vel']['x'] *= -bounciness
        if ball['pos']['y'] < 0.0:
            ball['pos']['y'] = 0.0
            ball['vel']['y'] *= -bounciness
        if ball['pos']['y'] > sim_height:
            ball['pos']['y'] = sim_height
            ball['vel']['y'] *= -bounciness

    # kolizje między piłkami
    for b1, b2 in itertools.combinations(balls, 2):
        collide_balls(b1, b2)

    # --- rysowanie ---
    screen.fill((255, 255, 255))
    for i, ((x1, y1), (x2, y2)) in enumerate(house_segments):
        color = (0, 0, 0)
        if i < 3: color = (0, 0, 255)
        elif i < 5: color = (200, 0, 0)
        else: color = (100, 100, 100)
        pygame.draw.line(screen, color, (cX(x1), cY(y1)), (cX(x2), cY(y2)), 4)

    for ball in balls:
        pygame.draw.circle(screen, ball['color'], (cX(ball['pos']['x']), cY(ball['pos']['y'])),
                           int(c_scale * ball['radius']))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
