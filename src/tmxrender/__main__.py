# Run it...
from __future__ import absolute_import

import tmxrender
try:
    tmxrender.run()
finally:
    import sdl
    sdl.quit()
