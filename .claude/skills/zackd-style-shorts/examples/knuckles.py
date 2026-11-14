"""What happens when you crack your knuckles — example story for zackd-style-shorts.

Run:  python scripts/make_short.py all examples/knuckles.py -w work_knuckles
"""
import math

from zds import *  # noqa: F401,F403  (ball, box, capsule, ..., anim, env, Cam, Person, Hand, Shot)

TITLE = "What happens when you crack your knuckles"
FPS = 30
VOICE = "am_michael"      # Kokoro voice; `make_short.py voices` to compare others
VOICE_SPEED = 1.1

FACTS = [
    ("Finger joints are synovial joints: a capsule filled with lubricating synovial fluid.",
     "Standard anatomy (e.g. Gray's Anatomy; Kawchuk et al. 2015 intro)"),
    ("Synovial fluid holds dissolved gases (mainly CO2, O2, N2).",
     "Unsworth, Dowson & Wright 1971, Ann Rheum Dis 30:348"),
    ("Pulling the joint apart drops pressure; a gas cavity forms suddenly, at the moment of the crack.",
     "Kawchuk et al. 2015, PLOS ONE, 'Real-Time Visualization of Joint Cavitation' (cine MRI)"),
    ("The sound happens as the cavity forms (the cavity was not seen to collapse).",
     "Kawchuk et al. 2015, PLOS ONE"),
    ("The same joint can't crack again for roughly 20 minutes (refractory period, ~15-30 min).",
     "Unsworth et al. 1971; summarised in Wikipedia 'Joint cracking'"),
    ("Dr Donald Unger cracked only his left knuckles for 60+ years; no arthritis in either hand.",
     "Unger 1998, Arthritis & Rheumatism 41:949; 2009 Ig Nobel Prize in Medicine"),
    ("Larger studies also find no link between knuckle cracking and hand arthritis.",
     "deWeber et al. 2011, J Am Board Fam Med 24:169"),
]

# ----------------------------------------------------------------------------- shared props

BONE = (0.93, 0.89, 0.80)


def joint(gap_open=False):
    """Big x-ray finger joint lying along X: two bones, cartilage, capsule, fluid."""
    bm = mat(BONE, rough=0.4)
    cart = mat((0.55, 0.80, 0.95), rough=0.25)
    j = {}
    j["boneL"] = capsule(0.34, 2.4, loc=(-1.62, 0, 0), m=bm, axis="X", name="boneL")
    j["boneR"] = capsule(0.30, 2.4, loc=(1.58, 0, 0), m=bm, axis="X", name="boneR")
    j["cartL"] = ball(0.355, loc=(-0.42, 0, 0), m=cart, scale=(0.55, 1, 1), name="cartL")
    j["cartL"].parent = j["boneL"]
    j["cartL"].location = (1.2, 0, 0)
    j["cartR"] = ball(0.315, loc=(0, 0, 0), m=cart, scale=(0.55, 1, 1), name="cartR")
    j["cartR"].parent = j["boneR"]
    j["cartR"].location = (-1.2, 0, 0)
    j["fluid"] = ball(1.0, m=mat((1.0, 0.86, 0.45), alpha=0.30, rough=0.1), scale=(0.62, 0.46, 0.46),
                      name="fluid")
    j["capsule"] = ball(1.0, m=mat((0.55, 0.75, 1.0), alpha=0.18, rough=0.1), scale=(0.95, 0.60, 0.60),
                        name="capsule")
    # tendons on top and bottom
    tm = mat((0.95, 0.92, 0.85), rough=0.5)
    j["tendon"] = tube([(-3, 0.2, 0.40), (-0.5, 0.2, 0.60), (0.5, 0.2, 0.58), (3, 0.2, 0.36)], r=0.035, m=tm)
    return j


def gas_dots(n=40, seed=1, spread=(0.9, 0.55, 0.55)):
    gm = mat((1, 1, 1), emit=3, rough=0.1)
    return scatter(lambda i, p, r: ball(r.uniform(0.018, 0.035), loc=p, m=gm, seg=10, name="gas"),
                   n, center=(0, -0.05, 0), size=spread, seed=seed, shape="box")


def arrow(loc, direction=1, c="yellow", length=0.7):
    root = empty("arrow", loc=loc)
    m = mat(c, rough=0.3)
    cylinder(0.05, length, rot=(0, 90, 0), m=m, parent=root, seg=16)
    cylinder(0.13, 0.26, r2=0.0, loc=(direction * (length / 2 + 0.12), 0, 0),
             rot=(0, 90 * direction, 0), m=m, parent=root, seg=24)
    return root


def burst(loc, n=10, r=0.35, c="yellow", parent=None, name="burst"):
    """Cartoon impact star: short spokes around a point."""
    root = empty(name, loc=loc, parent=parent)
    m = mat(c, emit=2.0)
    for i in range(n):
        a = 2 * math.pi * i / n
        d = (math.cos(a), 0, math.sin(a))
        s = capsule(r * 0.06, r * 0.5, loc=tuple(v * r for v in d), m=m, parent=root, seg=10)
        aim(s, d)
    return root


def ring(loc, r=0.5, c=(1, 1, 1), name="ring", alpha=0.9):
    m = mat(c, alpha=alpha, emit=2.0, unique=True)
    pts = [(r * math.cos(a), 0, r * math.sin(a)) for a in [i * 2 * math.pi / 40 for i in range(41)]]
    o = tube(pts, r=0.025, m=m, smooth=False, name=name)
    o.location = loc
    return o, m


def check_mark(loc, size=0.4, parent=None):
    root = empty("check", loc=loc, parent=parent)
    m = mat((0.1, 0.85, 0.2), emit=1.0)
    capsule(size * 0.12, size * 0.42, m=m, parent=root, rot=(0, -45, 0),
            loc=(-size * 0.22, 0, -size * 0.08))
    capsule(size * 0.12, size * 0.95, m=m, parent=root, rot=(0, 35, 0),
            loc=(size * 0.16, 0, size * 0.18))
    return root


def joint_camera(lens=38):
    cam = Cam(loc=(0.15, -3.9, 0.55), target=(0, 0, 0.05), lens=lens)
    return cam


# ----------------------------------------------------------------------------- shots

def s_hook(c):
    env.studio(c=(0.70, 0.74, 0.80))
    p = Person(shirt="#2f6fd6")
    p.pose("hands_front", 1)
    p.face("smirk", 1)
    p.hand_R.curl(1, 0.2)
    p.hand_L.curl(1, 0.9)
    cam = Cam(loc=(0.55, -2.75, 1.42), target=(0, -0.1, 1.2), lens=38)
    cam.push(1, c.frames, 0.25)
    k = c.at("crack")
    pull = c.at("pull")
    # right hand pulls the left fingers
    p.pose("hands_front", pull, el_R=(-60, 0, 0), sh_R=(-30, -12, -20))
    p.pose("hands_front", k - 2, el_R=(-50, 0, 0), sh_R=(-24, -14, -16))
    p.pose("hands_front", k + 3, el_R=(-38, 0, 0), sh_R=(-18, -16, -10))
    p.face("worried", pull)
    p.face("wince", k)
    p.face("relief", k + 18)
    b = burst((0.0, -0.55, 1.18), n=12, r=0.16)
    anim.pop_in(b, k, dur=5)
    anim.pop_out(b, k + 10, dur=6)
    t = screen_text(cam, "CRACK!", pos=(0.05, 0.42), size=0.1, c="yellow", tilt=-8)
    anim.pop_in(t, k)
    cam.shake(k, k + 12, amp=0.035)


def s_capsule(c):
    env.medical(z=-1.8)
    j = joint()
    cam = joint_camera(34)
    cam.dolly(1, c.frames, (0.05, -2.9, 0.35))
    for nm in ("capsule", "fluid"):
        anim.pop_in(j[nm], c.at("capsule") if nm == "capsule" else c.at("fluid"), dur=10)
    anim.wobble(j["fluid"], c.at("fluid") + 10, c.frames, amp=0.04, period=20)
    lab = screen_text(cam, "SYNOVIAL FLUID", pos=(0, 0.33), size=0.055, c="yellow")
    anim.pop_in(lab, c.at("fluid"), dur=8)


def s_gas(c):
    env.dark()
    glass_m = mat((0.75, 0.9, 1.0), alpha=0.22, rough=0.05)
    soda_m = mat((0.35, 0.12, 0.03), alpha=0.85, rough=0.1)
    cylinder(0.42, 1.25, loc=(0, 0, 0.625), m=glass_m, seg=48, name="glass")
    cylinder(0.39, 1.0, loc=(0, 0, 0.52), m=soda_m, seg=48, name="soda")
    cam = Cam(loc=(0, -3.3, 1.05), target=(0, 0, 0.66), lens=36)
    cam.push(1, c.frames, 0.2)
    bm = mat((1, 1, 1), emit=2.5)
    import random
    rnd = random.Random(3)
    for i in range(36):
        x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)
        b = ball(rnd.uniform(0.012, 0.03), loc=(x, y, 0.08), m=bm, seg=10, name="fizz")
        f0 = 1 + rnd.randint(0, 25)
        dur = rnd.randint(35, 60)
        f = f0
        while f < c.frames:
            anim.key(b, "location", f, (x, y, 0.08), ease="snap")
            anim.key(b, "location", f + 1, (x, y, 0.08), ease="quad")
            anim.key(b, "location", min(f + dur, c.frames + 30), (x + rnd.uniform(-0.04, 0.04), y, 1.0),
                     ease="snap")
            f += dur + 1
    lab = screen_text(cam, "DISSOLVED GAS", pos=(0, 0.33), size=0.055, c="yellow")
    anim.pop_in(lab, c.at("gas"), dur=8)


def s_pull(c):
    env.medical(z=-1.8)
    j = joint()
    dots = gas_dots(30)
    cam = joint_camera(36)
    f0, f1 = c.at("pull"), c.at("widens") + 8
    anim.move(j["boneR"], f0, f1, (2.05, 0, 0))
    anim.move(j["boneL"], f0, f1, (-1.80, 0, 0))
    anim.scale_to(j["capsule"], f0, f1, (1.15, 0.55, 0.55))
    anim.scale_to(j["fluid"], f0, f1, (0.80, 0.42, 0.42))
    a1, a2 = arrow((1.25, -0.6, 0.0), 1), arrow((-1.25, -0.6, 0.0), -1)
    for a in (a1, a2):
        anim.pop_in(a, f0 - 3, dur=8)
    anim.move(a1, f0, f1, (1.6, -0.6, 0))
    anim.move(a2, f0, f1, (-1.6, -0.6, 0))
    # pressure gauge, top of frame
    g = empty("gauge", loc=(0, -1.2, 0.95))
    cylinder(0.26, 0.05, rot=(90, 0, 0), m=mat("white", rough=0.3), parent=g, seg=40)
    cylinder(0.29, 0.04, rot=(90, 0, 0), loc=(0, 0.02, 0), m=mat("black"), parent=g, seg=40)
    for i in range(7):
        a = math.radians(-120 + i * 40)
        box((0.012, 0.01, 0.05), loc=(0.2 * math.sin(a), -0.035, 0.2 * math.cos(a)),
            rot=(0, math.degrees(a), 0), m=mat("black"), parent=g)
    pivot = empty("needle", loc=(0, -0.04, 0), parent=g)
    box((0.02, 0.01, 0.2), loc=(0, 0, 0.09), m=mat("red"), parent=pivot)
    ball(0.03, m=mat("black"), parent=pivot)
    anim.key(pivot, "rotation_euler", 1, (0, 100, 0))
    anim.key(pivot, "rotation_euler", c.at("pressure"), (0, 100, 0), ease="back")
    anim.key(pivot, "rotation_euler", c.at("drops") + 10, (0, -110, 0))
    lab = screen_text(cam, "PRESSURE", pos=(0, 0.25), size=0.045, c="white")
    anim.pop_in(g, c.at("pressure") - 6, dur=8)
    anim.pop_in(lab, c.at("pressure") - 6)
    cam.shake(c.at("drops"), c.at("drops") + 10, amp=0.02)
    for d in dots:
        anim.jitter(d, 1, c.frames, amp=0.015, every=3, seed=hash(d.name) % 100)


def s_bubble(c):
    env.medical(z=-1.8)
    j = joint()
    j["boneR"].location = (2.05, 0, 0)
    j["boneL"].location = (-1.80, 0, 0)
    j["capsule"].scale = (1.15, 0.55, 0.55)
    j["fluid"].scale = (0.80, 0.42, 0.42)
    cam = joint_camera(36)
    cam.push(1, c.frames, 0.25)
    dots = gas_dots(40, seed=4, spread=(1.2, 0.6, 0.6))
    fb = c.at("bubble")
    fe = c.at("escapes")
    for i, d in enumerate(dots):
        anim.key(d, "location", fe + i % 6, tuple(d.location), ease="expo")
        anim.key(d, "location", fb, (0, -0.05, 0))
        anim.key(d, "scale", fb - 1, (1, 1, 1), ease="snap")
        anim.key(d, "scale", fb, (0.001,) * 3)
    bub = ball(0.24, loc=(0, -0.05, 0), m=mat((0.92, 0.97, 1.0), alpha=0.55, rough=0.02), name="bubble")
    ball(0.06, loc=(-0.08, -0.2, 0.1), m=mat("white", emit=3), parent=bub)  # highlight
    anim.pop_in(bub, fb, dur=4)
    anim.wobble(bub, fb + 4, c.frames, amp=0.06, period=12)
    lab = screen_text(cam, "GAS BUBBLE", pos=(0, 0.33), size=0.06, c="yellow")
    anim.pop_in(lab, fb, dur=6)
    cam.shake(fb, fb + 8, amp=0.03)


def s_pop(c):
    env.dark(z=-1.8)
    j = joint()
    j["boneR"].location = (2.05, 0, 0)
    j["boneL"].location = (-1.80, 0, 0)
    j["capsule"].scale = (1.15, 0.55, 0.55)
    j["fluid"].scale = (0.80, 0.42, 0.42)
    bub = ball(0.24, loc=(0, -0.05, 0), m=mat((0.92, 0.97, 1.0), alpha=0.55, rough=0.02))
    cam = joint_camera(40)
    k = c.at("pop")
    cam.zoom(1, k, 46)
    cam.zoom(k, k + 5, 30, ease="expo")
    for i in range(3):
        r, m = ring((0, -0.3, 0), 0.3)
        r.scale = (0.001,) * 3
        f = k + i * 5
        anim.key(r, "scale", f, (0.2, 0.2, 0.2), ease="expo")
        anim.key(r, "scale", f + 18, (3.2, 3.2, 3.2))
        anim.fade_alpha(m, f, f + 18, 0.9, 0.0)
    t = screen_text(cam, "POP!", pos=(0, 0.25), size=0.14, c="yellow")
    anim.pop_in(t, k, dur=6)
    anim.pulse(bub, k, c.frames, amp=0.08, period=16)
    cam.shake(k, k + 14, amp=0.05)


def s_again(c):
    env.studio(c=(0.70, 0.74, 0.80))
    p = Person(shirt="#2f6fd6")
    p.pose("hands_front", 1)
    p.face("smirk", 1)
    p.hand_L.curl(1, 0.9)
    cam = Cam(loc=(-0.5, -2.5, 1.45), target=(0, -0.1, 1.25), lens=40)
    cam.drift(1, c.frames, amp=0.02)
    pull = c.at("knuckle")
    p.pose("hands_front", pull, el_R=(-55, 0, 0), sh_R=(-28, -12, -18))
    p.pose("hands_front", pull + 10, el_R=(-40, 0, 0), sh_R=(-20, -15, -10))
    p.pose("hands_front", pull + 18, el_R=(-55, 0, 0), sh_R=(-28, -12, -18))
    n = c.at("nothing")
    p.face("worried", n)
    p.pose("shrug", n + 2)
    q = text3d("?", size=0.35, loc=(0.32, -0.3, 1.85), c="yellow", outline="black")
    anim.pop_in(q, n, dur=8)
    anim.wobble(q, n + 8, c.frames, amp=0.05)


def s_wait(c):
    env.medical(z=-1.8)
    j = joint()
    j["boneR"].location = (2.05, 0, 0)
    j["boneL"].location = (-1.80, 0, 0)
    bub = ball(0.24, loc=(0, -0.05, 0), m=mat((0.92, 0.97, 1.0), alpha=0.55, rough=0.02))
    cam = joint_camera(30)
    cam.dolly(1, c.frames, (0.4, -4.4, 0.85))
    anim.scale_to(bub, c.at("dissolve"), c.frames, (0.25, 0.25, 0.25))
    dots = gas_dots(25, seed=9)
    for i, d in enumerate(dots):
        d.scale = (0.001,) * 3
        anim.pop_in(d, c.at("dissolve") + i, dur=6, scale=1)
    # clock
    cl = empty("clock", loc=(0, -1.0, 1.15))
    cylinder(0.33, 0.06, rot=(90, 0, 0), m=mat("white", rough=0.3), parent=cl, seg=48)
    cylinder(0.36, 0.05, rot=(90, 0, 0), loc=(0, 0.02, 0), m=mat("red"), parent=cl, seg=48)
    for i in range(12):
        a = math.radians(i * 30)
        box((0.015, 0.01, 0.05), loc=(0.26 * math.sin(a), -0.04, 0.26 * math.cos(a)),
            rot=(0, i * 30, 0), m=mat("black"), parent=cl)
    mh = empty("min_hand", loc=(0, -0.05, 0), parent=cl)
    box((0.02, 0.01, 0.24), loc=(0, 0, 0.11), m=mat("black"), parent=mh)
    hh = empty("hour_hand", loc=(0, -0.055, 0), parent=cl)
    box((0.03, 0.01, 0.15), loc=(0, 0, 0.07), m=mat("black"), parent=hh)
    anim.pop_in(cl, c.at("twenty") - 6, dur=8)
    anim.spin(mh, c.at("twenty"), c.frames, axis="Y", turns=-2)
    anim.spin(hh, c.at("twenty"), c.frames, axis="Y", turns=-0.17)
    lab = screen_text(cam, "20 MINUTES", pos=(0, 0.2), size=0.065, c="yellow")
    anim.pop_in(lab, c.at("minutes"))


def s_myth(c):
    env.dark()
    h = Hand(side="L", scale=5, xray=True, skin=mat((0.9, 0.6, 0.45), alpha=0.3), loc=(0, 0, 0.45),
             rot=(0, 180, 0))
    h.curl(1, 0.15)
    cam = Cam(loc=(0, -3.0, 1.0), target=(0, 0, 0.95), lens=38)
    cam.push(1, c.frames, 0.2)
    k = c.at("arthritis")
    reds = []
    for kn in h.knuckles + [ch[1] for ch in h.fingers]:
        b = blob(0.075, m=mat((0.95, 0.08, 0.04), emit=2.0, alpha=0.85), lump=0.2, seed=len(reds),
                 parent=kn, name="inflamed")
        reds.append(b)
        anim.pop_in(b, k + len(reds), dur=8)
        anim.pulse(b, k + 10, c.frames, amp=0.2, period=18)
    t = screen_text(cam, "ARTHRITIS?", pos=(0, 0.35), size=0.08, c=(1, 0.15, 0.1))
    anim.pop_in(t, k, dur=8)
    cam.shake(k, k + 10, amp=0.03)


def s_doctor(c):
    env.room()
    p = Person(shirt="white", pants=(0.15, 0.15, 0.2), hair=(0.55, 0.55, 0.57))
    p.face("smile", 1)
    cam = Cam(loc=(0.9, -3.3, 1.45), target=(0.1, 0, 1.18), lens=36)
    cam.push(1, c.frames, 0.2)
    # stethoscope
    tube([(-0.12, -0.13, 1.42), (-0.1, -0.17, 1.25), (0, -0.18, 1.15), (0.1, -0.17, 1.25),
          (0.12, -0.13, 1.42)], r=0.012, m=mat("black"))
    ball(0.03, loc=(0, -0.19, 1.13), m=mat((0.7, 0.7, 0.75), metal=1, rough=0.2))
    up = c.at("left")
    p.pose("stand", up, sh_L=(-30, -75, 0), el_L=(-20, -85, 0), head=(0, 0, 14))
    k0 = c.at("cracks")
    for i, f in enumerate(range(k0, c.frames - 10, 14)):
        p.hand_L.curl(f, 1.0)
        p.hand_L.curl(f + 7, 0.1)
    b = burst((0.0, 0, 0), n=10, r=0.12)
    b.parent = p.joint("wr_L")
    b.location = (0, 0, -0.12)
    anim.pop_in(b, k0 + 7, dur=4)
    anim.pop_out(b, k0 + 14, dur=4)
    yrs = screen_text(cam, "60 YEARS", pos=(0, 0.38), size=0.085, c="yellow", tilt=-5)
    anim.pop_in(yrs, c.at("sixty"))
    lab = screen_text(cam, "LEFT HAND ONLY", pos=(0, 0.27), size=0.045, c="white")
    anim.pop_in(lab, c.at("left"))


def s_payoff(c):
    env.studio(c=(0.70, 0.74, 0.80))
    sk = mat((0.9, 0.6, 0.45), alpha=0.3)
    hl = Hand(side="L", scale=4.3, xray=True, skin=sk, loc=(0.34, 0, 0.42), rot=(0, 180, 0))
    hr = Hand(side="R", scale=4.3, xray=True, skin=sk, loc=(-0.34, 0, 0.42), rot=(0, 180, 0))
    for h in (hl, hr):
        h.curl(1, 0.1)
    cam = Cam(loc=(0, -3.4, 1.05), target=(0, 0, 1.0), lens=36)
    cam.drift(1, c.frames, amp=0.02)
    k = c.at("neither")
    for i, x in enumerate((0.4, -0.4)):
        ck = check_mark((x * 0.9, -0.4, 1.66), size=0.24)
        anim.pop_in(ck, k + 4 + i * 6, dur=8)
    st = screen_text(cam, "MYTH BUSTED", pos=(0, 0.05), size=0.09, c=(0.95, 0.06, 0.04),
                     outline="white", tilt=8)
    ka = c.at("crack")
    anim.pop_in(st, ka)
    cam.shake(ka, ka + 10, amp=0.03)
    for i, h in enumerate((hl, hr)):
        h.curl(ka + 12 + i * 3, 0.8)
        h.curl(ka + 22 + i * 3, 0.1)


SHOTS = [
    Shot("hook", "You pull on your finger, and your knuckle goes crack.", s_hook,
         sfx=[("crack", "w9", 1.0), ("impact", "w9", 0.5)], hold=0.5),
    Shot("capsule", "Inside your finger, the joint sits in a capsule of slippery fluid.", s_capsule,
         sfx=[("glug", "w10", 0.35)]),
    Shot("gas", "That fluid holds dissolved gas, like the fizz in your soda.", s_gas,
         sfx=[("sizzle", 0.3, 0.45)]),
    Shot("pull", "When you pull, the joint gap widens and the pressure drops.", s_pull,
         sfx=[("riser", "w1", 0.5), ("rumble", "w9", 0.5)]),
    Shot("bubble", "The gas escapes the fluid and forms a bubble in a split second.", s_bubble,
         sfx=[("glug", "w2", 0.5), ("pop", "w8", 0.9)]),
    Shot("pop", "That bubble forming is the pop you hear.", s_pop,
         sfx=[("crack", "w5", 1.0), ("impact", "w5", 0.6)], hold=0.6),
    Shot("again", "Try that same knuckle again, and you get nothing.", s_again,
         sfx=[("tick", "w8", 0.7)], hold=0.6),
    Shot("wait", "Your joint needs about twenty minutes for the gas to dissolve back in.", s_wait,
         sfx=[("tick", t / 2, 0.5) for t in range(2, 9)]),
    Shot("myth", "But everyone says cracking gives you arthritis.", s_myth,
         sfx=[("rumble", "w2", 0.6), ("impact", "w6", 0.7), ("heartbeat", "end-1.2", 0.5)], hold=0.6),
    Shot("doctor", "One doctor cracks only his left hand for sixty years to test it.", s_doctor,
         sfx=[("crack", "w2", 0.9), ("ding", "w8", 0.4)]),
    Shot("payoff", "Sixty years later, neither hand has arthritis. Crack away.", s_payoff,
         sfx=[("ding", "w4", 0.6), ("impact", "w7", 0.8), ("crack", "w7", 0.7)], hold=1.2),
]
