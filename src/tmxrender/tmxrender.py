# Render tmx from pytmx

import os.path
import itertools
import sdl
import pytmx

class TMXRender(object):
    def __init__(self, filename):
        """
        :param filename: the map data
        """
        self.filename = filename
        self.tmx = pytmx.TiledMap(self.filename)

    def load(self, renderer):
        """Load the graphical data into textures compatible with renderer."""

        # mainly from pytmx.tmxloader
        tmxdata = self.tmx

        # initialize the array of images
        tmxdata.images = [0] * tmxdata.maxgid

        # convert angles to float:
        for ob in self.tmx.objects:
            ob.rotation = float(ob.rotation)

        for ts in tmxdata.tilesets:
            path = os.path.join(os.path.dirname(tmxdata.filename), ts.source)

            colorkey = getattr(ts, 'trans', None)
            if colorkey:
                # Convert HTML-format hex color to (r, g, b):
                colorkey = tuple(int(colorkey[x:x+2], 16) for x in range(0,6,2))

            surface = sdl.image.load(path)
            if not surface:
                raise Exception(sdl.getError())
            try:
                if colorkey and surface.format.BitsPerPixel == 8:
                    i = sdl.mapRGB(surface.format, *colorkey)
                    assert sdl.setColorKey(surface, 1, i) == 0
                ts.image = sdl.createTextureFromSurface(renderer, surface)
            finally:
                sdl.freeSurface(surface)
            rc, format, access, w, h = sdl.queryTexture(ts.image)

            # TODO our PyTMX is patched to allow floats

            # margins and spacing
            tilewidth = ts.tilewidth + ts.spacing
            tileheight = ts.tileheight + ts.spacing
            tile_size = ts.tilewidth, ts.tileheight

            # some tileset images may be slightly larger than the tile area
            # ie: may include a banner, copyright, ect.  this compensates for that
            width = int((((w - ts.margin * 2 + ts.spacing) / tilewidth) * tilewidth) - ts.spacing)
            height = int((((h - ts.margin * 2 + ts.spacing) / tileheight) * tileheight) - ts.spacing)

            # trim off any pixels on the right side that isn't a tile
            # this happens if extra graphics are included on the left, but they are not actually part of the tileset
            width -= (w - ts.margin) % tilewidth

            # using product avoids the overhead of nested loops
            p = itertools.product(xrange(ts.margin, height + ts.margin, tileheight),
                                  xrange(ts.margin, width + ts.margin, tilewidth))

            for real_gid, (y, x) in enumerate(p, ts.firstgid):
                if x + ts.tilewidth-ts.spacing > width:
                    continue

                gids = tmxdata.map_gid(real_gid)

                if gids:
                    tile_location = tuple(int(v) for v in
                                          (x, y, tile_size[0], tile_size[1]))

                    for gid, flags in gids:
                        # are flags for flipping?
                        # XXX store source image & location;
                        # only support one tile image for now.
                        tmxdata.images[gid] = tile_location

    def render(self, renderer, origin):
        """
        Draw something!

        :param renderer sdl.Renderer:
        :param origin: (x, y) pair of top left corner in pixels.
        :param layers: list of layers to render, or None for all.

        Out-of-bounds drawing is handled by repeating the edge tile.
        """
        viewport = sdl.Rect()
        renderer.renderGetViewport(viewport)
        width = viewport.w
        height = viewport.h
        layer = 0

        max_x = self.tmx.width - 1
        max_y = self.tmx.height - 1

        tw = self.tmx.tilesets[layer].tilewidth
        th = self.tmx.tilesets[layer].tileheight

        x0 = origin[0] // tw
        y0 = origin[1] // th

        def clamp(n, limit):
            if n <= 0:
                return 0
            elif n >= limit:
                return limit
            return n

        source = self.tmx.tilesets[layer].image

        srcrect = sdl.Rect()
        dstrect = sdl.Rect()

        for layer in self.tmx.visible_tile_layers:

            for y in range(y0, (y0 + height // th) + 2):
                for x in range(x0, (x0 + width // tw) + 2):
                    image = self.tmx.get_tile_image(clamp(x, max_x),
                                                    clamp(y, max_y), layer)
                    if image == 0: # blank area
                        continue

                    srcrect.x, srcrect.y, srcrect.w, srcrect.h = image

                    dstrect.x = x*tw - origin[0]
                    dstrect.y = y*th - origin[1]
                    dstrect.w = tw
                    dstrect.h = th

                    renderer.renderCopy(source, srcrect, dstrect)

        NULL = sdl.ffi.NULL

        # Object coordinates are in pixels.
        for ob in self.tmx.objects:
            if ob.visible and ob.gid:
                image = self.tmx.get_tile_image_by_gid(ob.gid)
                # Are object coords the lower left corner?
                srcrect.x, srcrect.y, srcrect.w, srcrect.h = image
                dstrect.x = int(ob.x) - origin[0]
                dstrect.y = int(ob.y) - origin[1] -th
                dstrect.w = tw
                dstrect.h = th

                flip = getattr(ob, 'flip', sdl.FLIP_NONE)

                renderer.renderCopyEx(source,
                                      srcrect,
                                      dstrect,
                                      ob.rotation,
                                      NULL, flip)
