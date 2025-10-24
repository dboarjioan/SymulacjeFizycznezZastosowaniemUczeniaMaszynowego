import pygame
import math
import random

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def set(self, v):
        self.x = v.x
        self.y = v.y

    def clone(self):
        return Vector2(self.x, self.y)

    def add(self, v, s=1.0):
        self.x += v.x * s
        self.y += v.y * s
        return self

    def add_vectors(self, a, b):
        self.x = a.x + b.x
        self.y = a.y + b.y
        return self

    def subtract(self, v, s=1.0):
        self.x -= v.x * s
        self.y -= v.y * s
        return self

    def subtract_vectors(self, a, b):
        self.x = a.x - b.x
        self.y = a.y - b.y
        return self

    def length(self):
        return math.sqrt(self.x**2 + self.y**2)

    def scale(self, s):
        self.x *= s
        self.y *= s
        return self

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def perp(self):
        return Vector2(-self.y, self.x)

class Bead:
    def __init__(self, radius, mass, pos):
        self.radius = radius
        self.mass = mass
        self.pos = pos.clone()
        self.prev_pos = pos.clone()
        self.vel = Vector2()

    def start_step(self, dt, gravity):
        self.vel.add(gravity, dt)
        self.prev_pos.set(self.pos)
        self.pos.add(self.vel, dt)

    def keep_on_wire(self, center, radius):
        dir = Vector2()
        dir.subtract_vectors(self.pos, center)
        length = dir.length()
        if length == 0.0:
            return
        dir.scale(1.0 / length)
        lambda_ = radius - length
        self.pos.add(dir, lambda_)
        return lambda_

    def end_step(self, dt):
        self.vel.subtract_vectors(self.pos, self.prev_pos)
        self.vel.scale(1.0 / dt)

class PhysicsScene:
    def __init__(self):
        self.gravity = Vector2(0.0, -10.0)
        self.dt = 1/60
        self.num_steps = 100
        self.wire_center = Vector2()
        self.wire_radius = 0.0
        self.beads = []

scene = PhysicsScene()

def setup_scene(screen_width, screen_height):
    scene.beads = []
    sim_min_width = 2.0
    c_scale = min(screen_width, screen_height) / sim_min_width
    sim_width = screen_width / c_scale
    sim_height = screen_height / c_scale

    scene.wire_center.x = sim_width / 2.0
    scene.wire_center.y = sim_height / 2.0
    scene.wire_radius = sim_min_width * 0.4

    num_beads = 5
    r = 0.1
    angle = 0.0
    for i in range(num_beads):
        mass = math.pi * r * r
        pos = Vector2(
            scene.wire_center.x + scene.wire_radius * math.cos(angle),
            scene.wire_center.y + scene.wire_radius * math.sin(angle)
        )
        scene.beads.append(Bead(r, mass, pos))
        angle += math.pi / num_beads
        r = 0.05 + random.random() * 0.1

def draw_circle(screen, pos, radius, scale, color, filled=True):
    x = int(pos.x * scale)
    y = int(screen.get_height() - pos.y * scale)
    r = int(radius * scale)
    if filled:
        pygame.draw.circle(screen, color, (x, y), r)
    else:
        pygame.draw.circle(screen, color, (x, y), r, 2)

def handle_bead_bead_collision(b1, b2):
    restitution = 1.0
    dir = Vector2()
    dir.subtract_vectors(b2.pos, b1.pos)
    d = dir.length()
    if d == 0.0 or d > b1.radius + b2.radius:
        return
    dir.scale(1.0 / d)
    corr = (b1.radius + b2.radius - d) / 2.0
    b1.pos.add(dir, -corr)
    b2.pos.add(dir, corr)

    v1 = b1.vel.dot(dir)
    v2 = b2.vel.dot(dir)
    m1 = b1.mass
    m2 = b2.mass
    new_v1 = (m1*v1 + m2*v2 - m2*(v1-v2)*restitution) / (m1 + m2)
    new_v2 = (m1*v1 + m2*v2 - m1*(v2-v1)*restitution) / (m1 + m2)
    b1.vel.add(dir, new_v1 - v1)
    b2.vel.add(dir, new_v2 - v2)

def simulate():
    sdt = scene.dt / scene.num_steps
    for step in range(scene.num_steps):
        for bead in scene.beads:
            bead.start_step(sdt, scene.gravity)
        for bead in scene.beads:
            bead.keep_on_wire(scene.wire_center, scene.wire_radius)
        for bead in scene.beads:
            bead.end_step(sdt)
        for i, bead1 in enumerate(scene.beads):
            for bead2 in scene.beads[:i]:
                handle_bead_bead_collision(bead1, bead2)

def main():
    pygame.init()
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Constrained Dynamics")
    clock = pygame.time.Clock()
    setup_scene(screen_width, screen_height)

    sim_min_width = 2.0
    c_scale = min(screen_width, screen_height) / sim_min_width

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                setup_scene(screen_width, screen_height)

        simulate()
        screen.fill((0, 0, 0))
        draw_circle(screen, scene.wire_center, scene.wire_radius, c_scale, (255, 0, 0), filled=False)
        for bead in scene.beads:
            draw_circle(screen, bead.pos, bead.radius, c_scale, (255, 0, 0), filled=True)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
