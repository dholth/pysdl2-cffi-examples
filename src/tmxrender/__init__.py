# pysdl2-cffi + PyTMX rendering example

from __future__ import absolute_import

import os.path
import sys

import sdl

from . import tmxrender

def run():

    frames = 0
    last_ticks = 0

    sdl.init(sdl.INIT_VIDEO)

    window = sdl.createWindow("TMX Render Example",
                              sdl.WINDOWPOS_UNDEFINED,
                              sdl.WINDOWPOS_UNDEFINED,
                              1280, # ignored for fs desktop
                              720, # ignored for fs desktop
                              sdl.WINDOW_SHOWN)

    renderer = sdl.Renderer(sdl.createRenderer(window, -1, flags=0))

    window = sdl.Window(window)
    width, height = window.getWindowSize()

    # Logical size:
    width = width // 2
    height = height // 2

    renderer.renderSetLogicalSize(width, height)

    try:
        map = tmxrender.TMXRender(sys.argv[1])
    except:
        sys.stderr.write("Pass the path of a .tmx map as the first argument.")
        raise

    # Load the map's image data
    map.load(renderer)

    pos = [0, 0]

    k_up, k_down, k_left, k_right = (sdl.SCANCODE_UP, sdl.SCANCODE_DOWN,
                                     sdl.SCANCODE_LEFT, sdl.SCANCODE_RIGHT)

    class Hero(object):
        def __init__(self):
            self.x = 0
            self.y = 0

    hero = Hero()

    event = sdl.Event()
    running = True
    while running:
        renderer.setRenderDrawColor(0, 0, 0, 255)
        renderer.renderClear()

        while event.pollEvent():
            if event.type == sdl.QUIT:
                running = False
                break
            elif event.type == sdl.KEYDOWN:
                keysym = event.key.keysym
                if (event.key.keysym.scancode == sdl.SCANCODE_ESCAPE or
                    event.key.keysym.sym == sdl.K_q):
                    running = False
                    break

        # Movement with arrow keys
        keystate, keystate_length = sdl.getKeyboardState()
        hero.x += (-1 * keystate[k_left]) + (1 * keystate[k_right])
        hero.y += (-1 * keystate[k_up]) + (1 * keystate[k_down])

        # Draw the map under the centered hero position
        pos[0] = int(hero.x - width/2)
        pos[1] = int(hero.y - height/2)

        map.render(renderer, pos)

        renderer.renderPresent()

        # Keep track of frame rate
        frames += 1
        ticks = sdl.getTicks()
        if ticks - last_ticks > 1000:
            last_ticks = ticks
            print("Frames: %s" % frames)
            frames = 0

        # Limit frame rate (optional)
        # sdl.delay(max(10, 1000/120 - (ticks % (1000/120))))
