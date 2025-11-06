import random
import math
import time
import statistics

class Circle:
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

    @property
    def left(self):
        return self.x - self.r

    @property
    def right(self):
        return self.x + self.r


def overlap_circle(a: Circle, b: Circle) -> bool:
    dx = a.x - b.x
    dy = a.y - b.y
    return dx * dx + dy * dy < (a.r + b.r) ** 2


def brute_force_detect(circles):
    checks = 0
    collisions = 0
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)):
            checks += 1
            if overlap_circle(circles[i], circles[j]):
                collisions += 1
    return checks, collisions


def sweep_and_prune_detect(circles):
    intervals = [(c.left, c.right, i) for i, c in enumerate(circles)]
    intervals.sort(key=lambda t: t[0])
    checks = 0
    collisions = 0
    active = []
    for min_x, max_x, idx in intervals:
        new_active = []
        for a_min, a_max, a_idx in active:
            if a_max > min_x:
                checks += 1
                if overlap_circle(circles[idx], circles[a_idx]):
                    collisions += 1
                new_active.append((a_min, a_max, a_idx))
        new_active.append((min_x, max_x, idx))
        active = new_active
    return checks, collisions


def benchmark_detection(width=1000, height=1000, radiuss=(2, 8),
                        counts=(100, 200, 500, 1000, 2000), trials=3):
    print("\n=== BENCHMARK: wykrywanie kolizji (tylko detekcja) ===")
    print("Ustawienia: area={}x{}, r∈[{},{}], próby/próba={}".format(width, height, radiuss[0], radiuss[1], trials))
    for n in counts:
        times_bf, times_sap = [], []
        for _ in range(trials):
            circles = [Circle(random.random()*width, random.random()*height,
                              random.uniform(radiuss[0], radiuss[1])) for _ in range(n)]

            t0 = time.perf_counter()
            brute_force_detect(circles)
            t1 = time.perf_counter()

            t2 = time.perf_counter()
            sweep_and_prune_detect(circles)
            t3 = time.perf_counter()

            times_bf.append((t1 - t0)*1000)
            times_sap.append((t3 - t2)*1000)

        mean_b = statistics.mean(times_bf)
        mean_s = statistics.mean(times_sap)
        ratio = mean_b / mean_s if mean_s > 0 else float('inf')
        print(f"n={n:5d} | Brute Force: {mean_b:8.3f} ms | Sweep & Prune: {mean_s:8.3f} ms | Speedup: {ratio:5.2f}x")
    print("=== KONIEC BENCHMARKU ===\n")


def run_pygame_simulation(initial_count=200):
    try:
        import pygame
    except Exception:
        print("Brak pygame — pomiń symulację 2D.")
        return

    pygame.init()
    WIDTH, HEIGHT = 1000, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Kolizje 2D — Brute Force vs Sweep & Prune")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 18)

    class BallSim:
        def __init__(self, x, y, vx, vy, r):
            self.x, self.y, self.vx, self.vy, self.r = x, y, vx, vy, r
            self.mass = math.pi * r * r
            self.base_color = pygame.Color(0, 200, 0)
            self.color = self.base_color
            self.timer = 0.0

        @property
        def left(self): return self.x - self.r
        @property
        def right(self): return self.x + self.r

        def mark_collision(self):
            self.color = pygame.Color(255, 50, 50)
            self.timer = 0.12

        def update(self, dt):
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.x - self.r < 0 or self.x + self.r > WIDTH:
                self.vx *= -1
                self.mark_collision()
            if self.y - self.r < 0 or self.y + self.r > HEIGHT:
                self.vy *= -1
                self.mark_collision()
            if self.timer > 0:
                self.timer -= dt
                if self.timer <= 0:
                    self.color = self.base_color

        def draw(self, surf):
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), int(self.r))

    def resolve(a: BallSim, b: BallSim):
        dx = b.x - a.x
        dy = b.y - a.y
        dist = math.hypot(dx, dy)
        if dist == 0 or dist >= a.r + b.r:
            return False
        nx, ny = dx/dist, dy/dist
        dvx, dvy = b.vx - a.vx, b.vy - a.vy
        vn = dvx*nx + dvy*ny
        if vn > 0: return False
        j = -(1+1.0)*vn / (1/a.mass + 1/b.mass)
        a.vx -= (j*nx)/a.mass; a.vy -= (j*ny)/a.mass
        b.vx += (j*nx)/b.mass; b.vy += (j*ny)/b.mass
        overlap = (a.r + b.r - dist)/2
        a.x -= overlap*nx; a.y -= overlap*ny
        b.x += overlap*nx; b.y += overlap*ny
        a.mark_collision(); b.mark_collision()
        return True

    def create_balls(n):
        arr = []
        for _ in range(n):
            r = random.uniform(6, 14)
            arr.append(BallSim(random.uniform(r, WIDTH-r),
                               random.uniform(r, HEIGHT-r),
                               random.uniform(-150,150),
                               random.uniform(-150,150),
                               r))
        return arr

    balls = create_balls(initial_count)
    algorithm = "sap"

    running = True
    while running:
        dt = clock.tick(60) / 1000
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    algorithm = "brute" if algorithm == "sap" else "sap"

        for b in balls:
            b.update(dt)

        checks = collisions = 0
        if algorithm == "brute":
            for i in range(len(balls)):
                for j in range(i+1, len(balls)):
                    checks += 1
                    if resolve(balls[i], balls[j]):
                        collisions += 1
        else:
            sorted_balls = sorted(balls, key=lambda b: b.left)
            active = []
            for min_x, max_x, idx in [(b.left, b.right, i) for i,b in enumerate(sorted_balls)]:
                new_active = []
                for a_min,a_max,a_idx in active:
                    if a_max > min_x:
                        checks += 1
                        if abs(sorted_balls[idx].y - sorted_balls[a_idx].y) < (sorted_balls[idx].r + sorted_balls[a_idx].r):
                            if resolve(sorted_balls[idx], sorted_balls[a_idx]):
                                collisions += 1
                        new_active.append((a_min,a_max,a_idx))
                new_active.append((min_x,max_x,idx))
                active = new_active

        screen.fill((12,12,20))
        for b in balls: b.draw(screen)
        info = f"{algorithm.upper()} | Balls: {len(balls)} | Checks: {checks} | Collisions: {collisions}"
        screen.blit(font.render(info, True, (240,240,240)), (12,12))
        pygame.display.flip()

    pygame.quit()



def run_vpython_bouncing():
    """Symulacja 3D: pojedyncza piłka odbijająca się od podłogi.
    Zielona normalnie, czerwona w momencie kolizji.
    """
    try:
        from vpython import sphere, box, vector, color, rate
    except Exception:
        print("\nBrak VPython — pomiń symulację 3D.")
        return

    print("\nUruchamiam prostą symulację 3D (odbicie piłki od podłogi)...")

    g = 9.81              # przyspieszenie grawitacyjne
    dt = 0.01             # krok czasowy
    restitution = 0.9     # współczynnik odbicia
    radius = 0.5          # promień piłki
    floor_y = -5          # położenie podłogi

    floor = box(pos=vector(0, floor_y - 0.05, 0),
                size=vector(10, 0.1, 10),
                color=color.gray(0.5))

    ball = sphere(pos=vector(0, 2, 0),
                  radius=radius,
                  color=color.green,
                  make_trail=True)
    velocity = vector(0, 0, 0)
    color_timer = 0.0

    while True:
        rate(100)
        velocity.y -= g * dt
        ball.pos += velocity * dt

        if ball.pos.y - radius <= floor_y:
            ball.pos.y = floor_y + radius
            velocity.y = -velocity.y * restitution
            ball.color = color.red
            color_timer = 0.15  

        if color_timer > 0:
            color_timer -= dt
            if color_timer <= 0:
                ball.color = color.green
    try:
        from vpython import sphere, box, vector, rate, color
    except Exception:
        print("\nBrak VPython — pomiń symulację 3D.")
        return

    print("\nUruchamiam symulację 3D — zamknij okno, by zakończyć.")
    N = 25
    BOX_SIZE = 5
    SPEED = 3.0
    RADIUS = 0.3

    for pos,size in [
        (vector(0,BOX_SIZE,0), vector(2*BOX_SIZE,0.05,2*BOX_SIZE)),
        (vector(0,-BOX_SIZE,0), vector(2*BOX_SIZE,0.05,2*BOX_SIZE)),
        (vector(BOX_SIZE,0,0), vector(0.05,2*BOX_SIZE,2*BOX_SIZE)),
        (vector(-BOX_SIZE,0,0), vector(0.05,2*BOX_SIZE,2*BOX_SIZE)),
        (vector(0,0,BOX_SIZE), vector(2*BOX_SIZE,2*BOX_SIZE,0.05)),
        (vector(0,0,-BOX_SIZE), vector(2*BOX_SIZE,2*BOX_SIZE,0.05))
    ]:
        box(pos=pos, size=size, color=color.gray(0.5))

    class Ball:
        def __init__(self, pos, vel):
            self.obj = sphere(pos=pos, radius=RADIUS, color=color.green)
            self.vel = vel
            self.timer = 0

        def update(self, dt):
            self.obj.pos += self.vel * dt
            for axis in ['x','y','z']:
                val = getattr(self.obj.pos, axis)
                if val + RADIUS > BOX_SIZE:
                    setattr(self.obj.pos, axis, BOX_SIZE - RADIUS)
                    setattr(self.vel, axis, -getattr(self.vel, axis))
                    self.mark_collision()
                elif val - RADIUS < -BOX_SIZE:
                    setattr(self.obj.pos, axis, -BOX_SIZE + RADIUS)
                    setattr(self.vel, axis, -getattr(self.vel, axis))
                    self.mark_collision()
            if self.timer > 0:
                self.timer -= dt
                if self.timer <= 0:
                    self.obj.color = color.green

        def mark_collision(self):
            self.obj.color = color.red
            self.timer = 0.2

    balls = [
        Ball(vector(random.uniform(-BOX_SIZE+RADIUS, BOX_SIZE-RADIUS),
                    random.uniform(-BOX_SIZE+RADIUS, BOX_SIZE-RADIUS),
                    random.uniform(-BOX_SIZE+RADIUS, BOX_SIZE-RADIUS)),
             vector(random.uniform(-SPEED, SPEED),
                    random.uniform(-SPEED, SPEED),
                    random.uniform(-SPEED, SPEED)))
        for _ in range(N)
    ]

    def collide(a, b):
        dp = b.obj.pos - a.obj.pos
        dist = dp.mag
        if dist < 2 * RADIUS:
            n = dp.hat
            rel = b.vel - a.vel
            vn = rel.dot(n)
            if vn < 0:
                j = -1.1 * vn / 2
                a.vel -= j*n
                b.vel += j*n
                overlap = (2*RADIUS - dist)/2
                a.obj.pos -= n*overlap
                b.obj.pos += n*overlap
                a.mark_collision(); b.mark_collision()

    dt = 0.01
    while True:
        rate(100)
        for b in balls: b.update(dt)
        for i in range(N):
            for j in range(i+1, N):
                collide(balls[i], balls[j])


if __name__ == "__main__":
    benchmark_detection(counts=(200, 500, 1000), trials=3)
    print("Uruchamiam symulację 2D...")
    run_pygame_simulation(initial_count=200)
    run_vpython_bouncing()
