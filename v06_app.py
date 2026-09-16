import math

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Mesh, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from countries_data import WORLD_COUNTRIES
from v03_app import fmt_money
from v04_app import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    RED,
    TEXT,
    TopBar,
    IconButton,
    GlassPanel,
    SmallButton,
    label,
)
from v05_app import (
    BG,
    MediaNewsOverlay,
    GameApp as V05GameApp,
    ensure_media_state,
)

APP_NAME = "Presidente Simulator V0.6.3"
WORLD_MAP_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/"
    "World_map_geographical.jpg/1280px-World_map_geographical.jpg"
)


def _power_for(name):
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(name))
    return 20 + seed % 76


def ensure_world_countries(data):
    countries = data.setdefault("countries", {})
    for name, _lon, _lat, _threshold in WORLD_COUNTRIES:
        countries.setdefault(name, {"relation": 0, "power": _power_for(name)})
    aliases = {
        "Rússia": "Russia",
        "Índia": "India",
        "França": "Franca",
        "Irã": "Ira",
        "Canadá": "Canada",
        "México": "Mexico",
    }
    for canonical, old in aliases.items():
        if old in countries:
            countries[canonical] = countries[old]


class CountryLabel(Label):
    def __init__(self, country, threshold, **kwargs):
        super().__init__(**kwargs)
        self.country = country
        self.threshold = float(threshold)
        self.size_hint = (None, None)
        self.size = (dp(76), dp(13))
        self.font_size = dp(4.1)
        self.bold = True
        self.color = (0.96, 0.98, 1.0, 0.86)
        self.halign = "center"
        self.valign = "middle"
        self.text_size = self.size
        self.bind(size=lambda inst, _v: setattr(inst, "text_size", inst.size))


class FallbackWorld(Widget):
    """Always-visible vector fallback so the map never becomes an empty black screen."""

    POLYS = [
        [(-0.92, 0.34), (-0.74, 0.66), (-0.46, 0.60), (-0.36, 0.38), (-0.49, 0.13), (-0.72, 0.10)],
        [(-0.48, 0.06), (-0.34, -0.05), (-0.28, -0.40), (-0.39, -0.77), (-0.52, -0.48)],
        [(-0.12, 0.52), (0.10, 0.68), (0.46, 0.62), (0.78, 0.40), (0.67, 0.12), (0.38, 0.00), (0.05, 0.17)],
        [(0.01, 0.11), (0.25, 0.02), (0.28, -0.34), (0.12, -0.62), (-0.06, -0.35)],
        [(0.56, -0.34), (0.77, -0.27), (0.87, -0.48), (0.68, -0.60)],
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)

    def redraw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        with self.canvas:
            Color(0.015, 0.08, 0.12, 1)
            Rectangle(pos=(x, y), size=(w, h))
            Color(0.04, 0.20, 0.24, 0.85)
            for poly in self.POLYS:
                verts = []
                for px, py in poly:
                    verts.extend([x + (px + 1) * 0.5 * w, y + (py + 1) * 0.5 * h, 0, 0])
                Mesh(vertices=verts, indices=list(range(len(poly))), mode="triangle_fan")
            Color(CYAN[0], CYAN[1], CYAN[2], 0.08)
            for i in range(1, 12):
                gx = x + w * i / 12.0
                Line(points=[gx, y, gx, y + h], width=0.35)
            for i in range(1, 6):
                gy = y + h * i / 6.0
                Line(points=[x, gy, x + w, gy], width=0.35)


class GestureWorldMap(FloatLayout):
    """Map with native one-finger pan, two-finger pinch zoom and country selection."""

    def __init__(self, game, on_country=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_country = on_country
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.min_zoom = 1.0
        self.max_zoom = 6.0
        self._touches = {}
        self._gesture_multitouch = False
        self._pinch_dist = None
        self._pinch_zoom = 1.0
        self._pinch_world = (0.5, 0.5)

        self.fallback = FallbackWorld(size_hint=(None, None))
        self.add_widget(self.fallback)

        self.map_image = AsyncImage(
            source=WORLD_MAP_URL,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(None, None),
        )
        self.add_widget(self.map_image)

        self.labels = []
        for name, lon, lat, threshold in WORLD_COUNTRIES:
            lab = CountryLabel(name, threshold, text=name.upper())
            lab._geo = (float(lon), float(lat))
            self.labels.append(lab)
            self.add_widget(lab)

        self.bind(pos=self._layout_map, size=self._layout_map)
        Clock.schedule_once(self._layout_map, 0)

    def _map_rect(self):
        draw_w = max(1.0, self.width * self.zoom)
        draw_h = max(1.0, self.height * self.zoom)
        x = self.center_x - draw_w * 0.5 + self.pan_x
        y = self.center_y - draw_h * 0.5 + self.pan_y
        return x, y, draw_w, draw_h

    def _clamp_pan(self):
        max_x = max(0.0, (self.width * self.zoom - self.width) * 0.5)
        max_y = max(0.0, (self.height * self.zoom - self.height) * 0.5)
        self.pan_x = max(-max_x, min(max_x, self.pan_x))
        self.pan_y = max(-max_y, min(max_y, self.pan_y))

    def _layout_map(self, *_):
        if self.width <= 2 or self.height <= 2:
            return
        self._clamp_pan()
        x, y, w, h = self._map_rect()
        self.fallback.pos = (x, y)
        self.fallback.size = (w, h)
        self.map_image.pos = (x, y)
        self.map_image.size = (w, h)

        font = dp(4.0 if self.zoom < 1.5 else 4.8 if self.zoom < 2.7 else 5.4)
        for lab in self.labels:
            lon, lat = lab._geo
            px = x + (lon + 180.0) / 360.0 * w
            py = y + (lat + 90.0) / 180.0 * h
            lab.center = (px, py)
            lab.font_size = font
            if self.zoom >= lab.threshold:
                lab.opacity = 0.96
            elif lab.threshold >= 2.5:
                lab.opacity = 0.30
            elif lab.threshold >= 1.8:
                lab.opacity = 0.48
            else:
                lab.opacity = 0.72

    def _screen_to_world(self, sx, sy):
        x, y, w, h = self._map_rect()
        return ((sx - x) / max(1.0, w), (sy - y) / max(1.0, h))

    def _set_zoom_at(self, target, sx, sy, world=None):
        target = max(self.min_zoom, min(self.max_zoom, float(target)))
        if world is None:
            world = self._screen_to_world(sx, sy)
        u, v = world
        self.zoom = target
        draw_w = self.width * self.zoom
        draw_h = self.height * self.zoom
        base_x = self.center_x - draw_w * 0.5
        base_y = self.center_y - draw_h * 0.5
        self.pan_x = sx - u * draw_w - base_x
        self.pan_y = sy - v * draw_h - base_y
        self._layout_map()

    def zoom_by(self, factor):
        self._set_zoom_at(self.zoom * factor, self.center_x, self.center_y)

    def reset_view(self):
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._layout_map()

    def _select_nearest(self, sx, sy):
        x, y, w, h = self._map_rect()
        best_name = None
        best_dist = dp(34)
        for name, lon, lat, _threshold in WORLD_COUNTRIES:
            px = x + (float(lon) + 180.0) / 360.0 * w
            py = y + (float(lat) + 90.0) / 180.0 * h
            dist = math.hypot(sx - px, sy - py)
            if dist < best_dist:
                best_dist, best_name = dist, name
        if best_name and self.on_country:
            self.on_country(best_name)

    def _start_pinch(self):
        if len(self._touches) < 2:
            self._pinch_dist = None
            return
        touches = list(self._touches.values())[:2]
        a, b = touches
        midx = (a.x + b.x) * 0.5
        midy = (a.y + b.y) * 0.5
        self._pinch_dist = max(dp(1), math.hypot(a.x - b.x, a.y - b.y))
        self._pinch_zoom = self.zoom
        self._pinch_world = self._screen_to_world(midx, midy)
        self._gesture_multitouch = True

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._touches[touch.uid] = touch
        touch.ud["presim_start"] = touch.pos
        touch.ud["presim_last"] = touch.pos
        touch.ud["presim_moved"] = False
        touch.grab(self)
        if len(self._touches) >= 2:
            self._start_pinch()
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self or touch.uid not in self._touches:
            return super().on_touch_move(touch)

        if len(self._touches) >= 2:
            touches = list(self._touches.values())[:2]
            a, b = touches
            current_dist = max(dp(1), math.hypot(a.x - b.x, a.y - b.y))
            if self._pinch_dist is None:
                self._start_pinch()
            ratio = current_dist / max(dp(1), self._pinch_dist)
            midx = (a.x + b.x) * 0.5
            midy = (a.y + b.y) * 0.5
            self._set_zoom_at(self._pinch_zoom * ratio, midx, midy, self._pinch_world)
            for t in touches:
                t.ud["presim_moved"] = True
            return True

        last_x, last_y = touch.ud.get("presim_last", touch.pos)
        dx, dy = touch.x - last_x, touch.y - last_y
        if abs(dx) + abs(dy) > dp(1):
            touch.ud["presim_moved"] = True
            self.pan_x += dx
            self.pan_y += dy
            self._layout_map()
        touch.ud["presim_last"] = touch.pos
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self and touch.uid not in self._touches:
            return super().on_touch_up(touch)

        moved = touch.ud.get("presim_moved", False)
        was_multi = self._gesture_multitouch
        self._touches.pop(touch.uid, None)
        if touch.grab_current is self:
            touch.ungrab(self)

        if len(self._touches) >= 2:
            self._start_pinch()
        elif len(self._touches) == 1:
            rem = next(iter(self._touches.values()))
            rem.ud["presim_last"] = rem.pos
            self._pinch_dist = None
        else:
            self._pinch_dist = None
            self._gesture_multitouch = False

        if not moved and not was_multi:
            self._select_nearest(touch.x, touch.y)
        return True


class GameSectionPanel(GlassPanel):
    TITLES = {
        "cabinet": "GABINETE PRESIDENCIAL",
        "gov": "POLÍTICA / GOVERNO",
        "eco": "ECONOMIA",
        "def": "FORÇAS ARMADAS",
        "dip": "DIPLOMACIA",
        "news": "MÍDIA / IMPRENSA",
    }

    def __init__(self, root_view, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(5), bg=(0.018, 0.04, 0.065, 0.98), **kwargs)
        self.root_view = root_view
        self.game = root_view.game
        self.section = None
        self.opacity = 0
        self.disabled = True

    def close(self):
        self.opacity = 0
        self.disabled = True
        self.section = None

    def open(self, section):
        self.section = section
        self.opacity = 1
        self.disabled = False
        self.rebuild()

    def _header(self, title):
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
        row.add_widget(label(title, color=CYAN, font_size=dp(8.0), bold=True))
        close = SmallButton(text="X", size_hint_x=None, width=dp(32), font_size=dp(7))
        close.bind(on_release=lambda *_: self.close())
        row.add_widget(close)
        self.add_widget(row)

    def _stat(self, title, value, color=TEXT):
        row = GlassPanel(orientation="horizontal", padding=(dp(7), dp(2)), size_hint_y=None, height=dp(29), bg=(0.055, 0.085, 0.12, 0.90))
        row.add_widget(label(title, color=MUTED, font_size=dp(5.8)))
        row.add_widget(label(value, color=color, font_size=dp(7.0), bold=True, halign="right"))
        self.add_widget(row)

    def _button(self, text, callback):
        b = SmallButton(text=text, size_hint_y=None, height=dp(31), font_size=dp(5.8))
        b.bind(on_release=callback)
        self.add_widget(b)
        return b

    def rebuild(self):
        self.clear_widgets()
        d = self.game.state.d
        sec = self.section
        self._header(self.TITLES.get(sec, "PAINEL"))

        if sec == "cabinet":
            self._stat("Aprovação", f"{d['approval']:.0f}%", GREEN if d["approval"] >= 50 else RED)
            self._stat("Congresso", f"{d['congress']:.0f}%")
            self._stat("Estabilidade", f"{d['stability']:.0f}%")
            self._button("COLETIVA DE IMPRENSA", lambda *_: self.game.show_press_overlay())
            self._button("ABRIR TELEJORNAL", lambda *_: self.game.show_newsroom())
            self._button("SALVAR PARTIDA", lambda *_: self.game.save_game())
            self._button("AVANÇAR 1 DIA", lambda *_: self.game.advance(1))

        elif sec == "gov":
            self._stat("Aprovação", f"{d['approval']:.0f}%", GREEN if d["approval"] >= 50 else RED)
            self._stat("Congresso", f"{d['congress']:.0f}%")
            self._stat("Estabilidade", f"{d['stability']:.0f}%")
            self._stat("Risco de impeachment", f"{d['impeachment_risk']:.0f}%", AMBER)
            self._button("COLETIVA DE IMPRENSA", lambda *_: self.game.show_press_overlay())
            self._button("SALVAR PARTIDA", lambda *_: self.game.save_game())

        elif sec == "eco":
            self._stat("PIB", fmt_money(d["gdp"]), CYAN)
            self._stat("Inflação", f"{d['inflation']:.1f}%")
            self._stat("Desemprego", f"{d['unemployment']:.1f}%")
            self._stat("Dívida / PIB", f"{d['debt_ratio']:.1f}%")
            grid = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(68))
            for text, key, amount in [("IMPOSTO -1", "tax_rate", -1), ("IMPOSTO +1", "tax_rate", 1), ("JUROS -0,5", "interest_rate", -0.5), ("GASTO SOCIAL +1", "social_spending", 1)]:
                b = SmallButton(text=text, font_size=dp(5.1))
                b.bind(on_release=lambda _btn, k=key, a=amount, t=text: self._economic(k, a, t))
                grid.add_widget(b)
            self.add_widget(grid)

        elif sec == "def":
            self._stat("Orçamento militar", f"{d['military_budget']:.1f}% do PIB")
            self._stat("Estabilidade", f"{d['stability']:.0f}%")
            self._stat("Risco de golpe", f"{d['coup_risk']:.0f}%", AMBER)
            self._button("AUMENTAR ORÇAMENTO", lambda *_: self._military("Aumentar orçamento militar", 0.2))
            self._button("REDUZIR ORÇAMENTO", lambda *_: self._military("Reduzir orçamento militar", -0.2))
            self._button("REALIZAR EXERCÍCIO", lambda *_: self._military("Realizar exercício militar", 1.0))

        elif sec == "dip":
            selected = self.root_view.selected_country or "Brasil"
            c = d["countries"].get(selected, {"relation": 0, "power": 50})
            self._stat("País selecionado", selected.upper(), CYAN)
            self._stat("Relação", f"{c.get('relation', 0):+d}")
            self._stat("Poder", f"{c.get('power', 50)}/100")
            if selected != "Brasil":
                self._button("NEGOCIAR COM PAÍS", lambda *_: self._negotiate(selected))
            self.add_widget(label("TODOS OS PAÍSES / TERRITÓRIOS", color=CYAN, font_size=dp(5.6), bold=True, size_hint_y=None, height=dp(20)))
            scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
            body = GridLayout(cols=1, spacing=dp(2), size_hint_y=None)
            body.bind(minimum_height=body.setter("height"))
            for name, _lon, _lat, _thr in sorted(WORLD_COUNTRIES, key=lambda item: item[0]):
                row = SmallButton(text=name.upper(), size_hint_y=None, height=dp(25), font_size=dp(4.8), halign="left")
                row.bind(on_release=lambda _btn, n=name: self._select_country(n))
                body.add_widget(row)
            scroll.add_widget(body)
            self.add_widget(scroll)

        elif sec == "news":
            self._stat("Mercado", f"{d['market_sentiment']:.0f}%")
            self._stat("Risco de crise", f"{d['crisis_risk']:.0f}%", AMBER)
            hero = GlassPanel(orientation="vertical", padding=dp(6), spacing=dp(2), size_hint_y=None, height=dp(92), bg=(0.055, 0.085, 0.12, 0.92))
            hero.add_widget(label("ÚLTIMA HORA", color=RED, font_size=dp(6.0), bold=True))
            hero.add_widget(label(d["headline"], font_size=dp(6.8), bold=True))
            hero.add_widget(label(d["last_news"], color=MUTED, font_size=dp(5.4)))
            self.add_widget(hero)
            self._button("ABRIR TELEJORNAL", lambda *_: self.game.show_newsroom())
            self._button("CONVOCAR COLETIVA", lambda *_: self.game.show_press_overlay())

        self.add_widget(Widget())

    def _economic(self, key, amount, title):
        self.game.economic_action(key, amount, title)
        self.rebuild()
        self.root_view.refresh()

    def _military(self, title, amount):
        self.game.military_action(title, amount)
        self.rebuild()
        self.root_view.refresh()

    def _negotiate(self, name):
        self.game.negotiate(name)
        self.rebuild()
        self.root_view.refresh()

    def _select_country(self, name):
        self.root_view.select_country(name)
        self.rebuild()


class SelectedCountryPanel(GlassPanel):
    def __init__(self, root_view, **kwargs):
        super().__init__(orientation="horizontal", padding=(dp(7), dp(3)), spacing=dp(5), bg=(0.02, 0.05, 0.08, 0.95), **kwargs)
        self.root_view = root_view
        self.name_label = label("BRASIL", color=CYAN, font_size=dp(5.8), bold=True, size_hint_x=0.27)
        self.info_label = label("RELAÇÃO +0  |  PODER 50/100", color=MUTED, font_size=dp(5.0), size_hint_x=0.49)
        self.action = SmallButton(text="DIPLOMACIA", font_size=dp(5.0), size_hint_x=0.24)
        self.action.bind(on_release=lambda *_: self.root_view.open_section("dip"))
        self.add_widget(self.name_label)
        self.add_widget(self.info_label)
        self.add_widget(self.action)

    def set_country(self, name):
        country = self.root_view.game.state.d.get("countries", {}).get(name, {"relation": 0, "power": 50})
        self.name_label.text = name.upper()
        self.info_label.text = f"RELAÇÃO {country.get('relation', 0):+d}  |  PODER {country.get('power', 50)}/100"


class V06Root(FloatLayout):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.selected_country = "Brasil"

        self.globe = GestureWorldMap(game, on_country=self.select_country, size_hint=(0.93, 0.80), pos_hint={"x": 0.035, "y": 0.10})
        self.add_widget(self.globe)

        self.topbar = TopBar(game, size_hint=(0.82, None), height=dp(39), pos_hint={"x": 0.13, "top": 0.988})
        self.add_widget(self.topbar)

        toolbar = GlassPanel(orientation="vertical", padding=dp(3), spacing=dp(3), bg=(0.02, 0.05, 0.075, 0.95), size_hint=(None, None), width=dp(40), height=dp(242), pos_hint={"x": 0.009, "center_y": 0.52})
        for icon, hint, section in [("gov", "GAB", "cabinet"), ("eco", "ECO", "eco"), ("def", "MIL", "def"), ("dip", "DIP", "dip"), ("news", "MÍD", "news"), ("save", "SAVE", "save")]:
            b = IconButton(icon=icon, hint=hint, size_hint_y=None, height=dp(35))
            if section == "save":
                b.bind(on_release=lambda *_: self.game.save_game())
            else:
                b.bind(on_release=lambda _btn, s=section: self.open_section(s))
            toolbar.add_widget(b)
        self.add_widget(toolbar)

        zoom = GlassPanel(orientation="vertical", padding=dp(3), spacing=dp(3), bg=(0.02, 0.05, 0.075, 0.95), size_hint=(None, None), width=dp(39), height=dp(126), pos_hint={"right": 0.987, "center_y": 0.52})
        for txt, cb in [("+", lambda *_: self.globe.zoom_by(1.35)), ("−", lambda *_: self.globe.zoom_by(1 / 1.35)), ("RESET", lambda *_: self.globe.reset_view())]:
            b = SmallButton(text=txt, font_size=dp(11 if txt != "RESET" else 4.5), size_hint_y=None, height=dp(37))
            b.bind(on_release=cb)
            zoom.add_widget(b)
        self.add_widget(zoom)

        bottom = GlassPanel(orientation="horizontal", padding=dp(3), spacing=dp(3), bg=(0.02, 0.045, 0.07, 0.96), size_hint=(0.58, None), height=dp(34), pos_hint={"center_x": 0.54, "y": 0.012})
        for title, section in [("GABINETE", "cabinet"), ("ECONOMIA", "eco"), ("POLÍTICA", "gov"), ("MILITAR", "def"), ("DIPLOMACIA", "dip"), ("MÍDIA", "news")]:
            b = SmallButton(text=title, font_size=dp(5.0))
            b.bind(on_release=lambda _btn, s=section: self.open_section(s))
            bottom.add_widget(b)
        self.add_widget(bottom)

        self.country_panel = SelectedCountryPanel(self, size_hint=(0.30, None), height=dp(30), pos_hint={"x": 0.055, "y": 0.060})
        self.add_widget(self.country_panel)

        self.status = GlassPanel(orientation="horizontal", padding=(dp(7), dp(2)), bg=(0.02, 0.04, 0.06, 0.86), size_hint=(0.27, None), height=dp(27), pos_hint={"right": 0.985, "y": 0.060})
        self.status_label = label("", color=MUTED, font_size=dp(5.1))
        self.status.add_widget(self.status_label)
        self.add_widget(self.status)

        self.section_panel = GameSectionPanel(self, size_hint=(0.35, 0.72), pos_hint={"right": 0.965, "center_y": 0.50})
        self.add_widget(self.section_panel)

        self.news_overlay = MediaNewsOverlay(game, size_hint=(1, 1))
        game.news_overlay = self.news_overlay
        self.add_widget(self.news_overlay)

        game.drawer = self.section_panel
        self.country_panel.set_country("Brasil")
        Clock.schedule_once(lambda *_: self.refresh(), 0)

    def open_section(self, section):
        self.section_panel.open(section)

    def select_country(self, name):
        self.selected_country = name
        self.country_panel.set_country(name)
        country = self.game.state.d.get("countries", {}).get(name)
        if country:
            self.status_label.text = f"{name.upper()}  |  REL {country.get('relation', 0):+d}  |  PODER {country.get('power', 50)}/100"
        if self.section_panel.section == "dip" and not self.section_panel.disabled:
            self.section_panel.rebuild()

    def refresh(self):
        self.topbar.refresh()
        d = self.game.state.d
        self.status_label.text = f"MERCADO {d['market_sentiment']:.0f}%  |  CONGRESSO {d['congress']:.0f}%  |  CRISE {d['crisis_risk']:.0f}%"
        self.country_panel.set_country(self.selected_country)
        if not self.section_panel.disabled and self.section_panel.section and self.section_panel.section != "dip":
            self.section_panel.rebuild()


class GameApp(V05GameApp):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        from v03_app import GameState

        self.state = GameState()
        self.state.load()
        ensure_media_state(self.state.d)
        ensure_world_countries(self.state.d)
        self.state.save()
        self.playing = False
        self.overlay_open = False
        self.drawer = None
        self.news_overlay = None
        self._play_accumulator = 0.0

        self.root_view = V06Root(self)
        Clock.schedule_interval(self._tick, 0.25)
        Clock.schedule_interval(lambda _dt: self.root_view.refresh(), 0.8)
        self.root_view.refresh()
        return self.root_view
