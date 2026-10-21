"""SVG -> PDF (vector) and PNG preview with librsvg + cairo through ctypes, so the paper
figures build on saul without matplotlib or cairosvg.

Fonts: the figures name Arimo (same metrics as Helvetica/Arial). If paper/figs/fonts/
holds Arimo TTFs (Google Fonts, SIL OFL 1.1, licence in fonts/LICENSE.txt), they are used through a private fontconfig
file; otherwise fontconfig falls back to the system sans. The PDF embeds the font."""
import ctypes
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Arimo, Helvetica, Arial, sans-serif"


def _use_local_fonts():
    fdir = os.path.join(HERE, "fonts")
    if not os.path.isdir(fdir) or "FONTCONFIG_FILE" in os.environ:
        return
    conf = os.path.join(fdir, "fonts.conf")
    with open(conf, "w") as f:
        f.write('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
                f'<include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>{fdir}</dir>'
                f'<cachedir>{fdir}/cache</cachedir></fontconfig>')
    os.environ["FONTCONFIG_FILE"] = conf


_use_local_fonts()
_rsvg = ctypes.CDLL("librsvg-2.so.2")
_cairo = ctypes.CDLL("libcairo.so.2")
_rsvg.rsvg_handle_new_from_file.restype = ctypes.c_void_p
_rsvg.rsvg_handle_new_from_file.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
for _f in ("cairo_image_surface_create", "cairo_pdf_surface_create", "cairo_create"):
    getattr(_cairo, _f).restype = ctypes.c_void_p
_cairo.cairo_pdf_surface_create.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double]
_cairo.cairo_create.argtypes = [ctypes.c_void_p]
_cairo.cairo_surface_write_to_png.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
for _f in ("cairo_surface_finish", "cairo_surface_destroy", "cairo_destroy"):
    getattr(_cairo, _f).argtypes = [ctypes.c_void_p]


class _Rect(ctypes.Structure):
    _fields_ = [(k, ctypes.c_double) for k in ("x", "y", "width", "height")]


_rsvg.rsvg_handle_render_document.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                              ctypes.POINTER(_Rect), ctypes.c_void_p]


def _draw(svg, surf, w, h):
    handle = _rsvg.rsvg_handle_new_from_file(svg.encode(), None)
    assert handle, f"cannot parse {svg}"
    cr = _cairo.cairo_create(surf)
    assert _rsvg.rsvg_handle_render_document(handle, cr, ctypes.byref(_Rect(0, 0, w, h)), None)
    _cairo.cairo_destroy(cr)


def render(svg, w, h, pdf=None, png=None, png_scale=5):
    """w, h in points (1/72 in), as in the SVG's width/height."""
    if pdf:
        surf = _cairo.cairo_pdf_surface_create(pdf.encode(), w, h)
        _draw(svg, surf, w, h)
        _cairo.cairo_surface_finish(surf)
        _cairo.cairo_surface_destroy(surf)
    if png:
        surf = _cairo.cairo_image_surface_create(0, int(w * png_scale), int(h * png_scale))
        _draw(svg, surf, w * png_scale, h * png_scale)
        _cairo.cairo_surface_write_to_png(surf, png.encode())
        _cairo.cairo_surface_destroy(surf)


class Svg:
    """Tiny SVG writer for plots: shapes plus text in the figure font."""

    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>']

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, t, size=6.5, anchor="start", fill="#222222", weight="normal", italic=False, rotate=None):
        st = ' font-style="italic"' if italic else ""
        tr = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
                 f'text-anchor="{anchor}" font-weight="{weight}"{st}{tr}>{t}</text>')

    def save(self, base):
        """Write base.svg, base.pdf and base.png."""
        self.parts.append("</svg>")
        with open(base + ".svg", "w") as f:
            f.write("\n".join(self.parts))
        render(base + ".svg", self.w, self.h, pdf=base + ".pdf", png=base + ".png")
