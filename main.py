from PIL import Image, ImageDraw
import math

STEP = 1 / 60
PRE_SIM_FRAMES = 0
TOTAL_FRAMES = 600
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 800
ZOOM = 300
TAIL_LENGTH = 100 # frames
TAIL_WIDTH = 2 # pixels
G = 1 # gravitational constant
ALIAS_SCALE = 2 # WARNING: values greater than 1 will use much more memory
BODY_RADIUS = 5 * ALIAS_SCALE
FOLLOW_CENTER = False

# f = m a
# f = G m1 m2 / r^2
# therefore:
# a = G m2 / r^2
# where a is the acceleration towards m2

class Vector(object):

    x = 0
    y = 0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def scale(self, scalar: float):
        return Vector(self.x * scalar, self.y * scalar)

    def normalized(self):
        return self.scale(1 / self.magnitude())

    def add(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def neg(self):
        return self.scale(-1)

    def sub(self, other):
        return self.add(other.neg())

    def world_to_screen(self, center):
        if FOLLOW_CENTER:
            return self.sub(center).scale(ZOOM).add(Vector(IMAGE_WIDTH / 2, IMAGE_HEIGHT / 2))
        else:
            return self.scale(ZOOM).add(Vector(IMAGE_WIDTH / 2, IMAGE_HEIGHT / 2))

class Body(object):

    mass = 1
    radius = 1
    position = Vector(0, 0)
    velocity = Vector(0, 0)
    tail = []

    def __init__(self, mass: float, radius: float, position, velocity, tail=[]):
        self.mass = mass
        self.radius = radius
        self.position = position
        self.velocity = velocity
        self.tail = tail


    def move(self):
        return Body(
            self.mass,
            self.radius,
            self.position.add(self.velocity.scale(STEP)),
            self.velocity,
            self.extend_tail(self.position)
        )

    def accelerate_towards(self, other):
        displacement = other.position.sub(self.position)
        acceleration = G * other.mass / (displacement.magnitude() ** 2)
        new_velocity = self.velocity.add(displacement.normalized().scale(acceleration * STEP))
        return Body(
            self.mass,
            self.radius,
            self.position,
            new_velocity,
            self.tail
        )

    def extend_tail(self, pos):
        tail = self.tail
        tail.append(pos)
        if len(tail) > TAIL_LENGTH:
            tail = tail[1:]
        return tail

def render(bodies):
    img = Image.new('RGB', (IMAGE_WIDTH * ALIAS_SCALE, IMAGE_HEIGHT * ALIAS_SCALE), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for body in bodies:
        pos = body.position.world_to_screen(bodies[0].position)
        # draw body
        draw.ellipse(
            [
                (pos.x - body.radius) * ALIAS_SCALE,
                (pos.y - body.radius) * ALIAS_SCALE,
                (pos.x + body.radius) * ALIAS_SCALE,
                (pos.y + body.radius) * ALIAS_SCALE,
            ],
            fill=(0,0,0),
        )
        # draw tail
        prev_pos = body.tail[0].world_to_screen(bodies[0].position)
        for tail_pos in body.tail[1:]:
            tail_pos = tail_pos.world_to_screen(bodies[0].position)
            draw.line(
                [
                    tail_pos.x * ALIAS_SCALE,
                    tail_pos.y * ALIAS_SCALE,
                    prev_pos.x * ALIAS_SCALE,
                    prev_pos.y * ALIAS_SCALE,
                ],
                fill=(0,0,0),
                width=TAIL_WIDTH * ALIAS_SCALE,
            )
            prev_pos = tail_pos
    del draw
    return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.ANTIALIAS)

def main():
    bodies = [
        Body(1, BODY_RADIUS, Vector(0.97000436, -0.24308753), Vector(0.466203685, 0.43236573), tail=[]),
        Body(1, BODY_RADIUS, Vector(-0.97000436, 0.24308753), Vector(0.466203685, 0.43236573), tail=[]),
        Body(1, BODY_RADIUS, Vector(0, 0), Vector(-0.93240737, -0.86473146), tail=[]),
    ]
    frames = []
    print("begining pre simulation of", PRE_SIM_FRAMES, "frames...")
    for frame in range(PRE_SIM_FRAMES + TOTAL_FRAMES):
        if(frame >= PRE_SIM_FRAMES):
            print("rendering frame", frame - PRE_SIM_FRAMES)
        # accelerate
        for i in range(len(bodies)):
            for other in bodies:
                if bodies[i] is other:
                    continue
                bodies[i] = bodies[i].accelerate_towards(other)
        # move
        for i in range(len(bodies)):
            bodies[i] = bodies[i].move()
        # render
        if frame < PRE_SIM_FRAMES:
            continue
        frames.append(render(bodies))
    print("saving GIF...")
    frames[0].save('out.gif', format='GIF', append_images=frames[1:], save_all=True, duration=20, loop=0)

if __name__ == '__main__':
    main()

