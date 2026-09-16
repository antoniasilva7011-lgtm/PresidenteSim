import json
import os
import random
from datetime import date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

APP_NAME = "Presidente Simulator V0.3"
SAVE_FILE = "presidente_simulator_save.json"

# Dark mobile game palette requested for the newsroom.
BG = (15 / 255, 23 / 255, 42 / 255, 1)          # #0F172A
PANEL = (30 / 255, 41 / 255, 59 / 255, 1)      # #1E293B
PANEL_DARK = (8 / 255, 15 / 255, 27 / 255, 1)
PANEL_SOFT = (24 / 255, 34 / 255, 52 / 255, 1)
CYAN = (0.10, 0.67, 0.90, 1)
TEXT = (0.95, 0.97, 1.0, 1)
MUTED = (0.60, 0.68, 0.78, 1)
RED = (0.92, 0.16, 0.21, 1)
GREEN = (0.18, 0.80, 0.45, 1)
AMBER = (0.96, 0.63, 0.20, 1)

COUNTRIES = {
    "Brasil": {"relation": 72, "gdp": 2.1, "power": 72},
    "Estados Unidos": {"relation": 55, "gdp": 28.8, "power": 100},
    "China": {"relation": -34, "gdp": 18.7, "power": 98},
    "Russia": {"relation": 45, "gdp": 2.0, "power": 83},
    "Argentina": {"relation": 20, "gdp": 0.63, "power": 32},
    "Franca": {"relation": 38, "gdp": 3.2, "power": 70},
    "Alemanha": {"relation": 44, "gdp": 4.6, "power": 69},
    "India": {"relation": 30, "gdp": 3.9, "power": 73},
    "Japao": {"relation": 36, "gdp": 4.2, "power": 67},
    "Mexico": {"relation": 28, "gdp": 1.8, "power": 43},
}

DEFAULT_RELATED_NEWS = [
    {"category": "Economia", "headline": "Mercado acompanha novas medidas", "subtitle": "Investidores avaliam juros, inflacao e trajetoria fiscal."},
    {"category": "Diplomacia", "headline": "Brasil inicia nova rodada de negociacoes", "subtitle": "Parceiros estrategicos entram na agenda internacional."},
    {"category": "Politica", "headline": "Congresso debate agenda presidencial", "subtitle": "Liderancas negociam apoio para os proximos projetos."},
    {"category": "Sociedade", "headline": "Custo de vida domina debate publico", "subtitle": "Familias acompanham precos, emprego e renda."},
]

INITIAL_STATE = {
    "day": "2026-09-15",
    "approval": 57.0,
    "congress": 51.0,
    "inflation": 4.8,
    "unemployment": 7.2,
    "debt_ratio": 78.4,
    "gdp": 12.4,
    "gdp_growth": 2.3,
    "stability": 68.0,
    "coup_risk": 8.0,
    "impeachment_risk": 12.0,
    "treasury": 100.0,
    "tax_rate": 27.0,
    "interest_rate": 10.5,
    "military_budget": 2.0,
    "social_spending": 18.0,
    "market_sentiment": 52.0,
    "crisis_risk": 18.0,
    "last_news": "Governo inicia novo ciclo politico.",
    "headline": "GOVERNO PREPARA NOVAS MEDIDAS",
    "media_impact": {"approval": 0.0, "market": 0.0, "crisis": 0.0},
    "related_news": DEFAULT_RELATED_NEWS,
    "feed": [
        ["Carlos Silva", "O governo precisa mostrar resultados.", 1840],
        ["Mariana Costa", "Debate economico movimenta o Congresso.", 920],
        ["Joao Santos", "Espero que o custo de vida caia.", 710],
    ],
    "countries": COUNTRIES,
    "event": None,
}


def clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


def fmt_money(value):
    return f"R$ {value:,.1f} tri".replace(",", "X").replace(".", ",").replace("X", ".")


def make_label(text="", **kwargs):
    kwargs.setdefault("color", TEXT)
    kwargs.setdefault("font_size", dp(10))
    kwargs.setdefault("halign", "left")
    kwargs.setdefault("valign", "middle")
    label = Label(text=text, **kwargs)
    label.bind(size=lambda inst, _value: setattr(inst, "text_size", (inst.width, inst.height)))
    return label


class Panel(BoxLayout):
    def __init__(self, bg=PANEL, radius=12, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg)
            self._panel_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._sync_panel, size=self._sync_panel)

    def _sync_panel(self, *_):
        self._panel_bg.pos = self.pos
        self._panel_bg.size = self.size


class CommandButton(Button):
    """Custom button name intentionally avoids Kivy's built-in ActionButton rule."""

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.04, 0.12, 0.18, 1))
        kwargs.setdefault("color", TEXT)
        kwargs.setdefault("font_size", dp(8.5))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(CYAN[0], CYAN[1], CYAN[2], 0.62)
            self._outline = Line(rounded_rectangle=(0, 0, 100, 40, dp(7)), width=0.8)
        self.bind(pos=self._sync_outline, size=self._sync_outline)

    def _sync_outline(self, *_):
        self._outline.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(7))


class StatTile(Panel):
    def __init__(self, title, value, subtitle="", accent=CYAN, **kwargs):
        super().__init__(orientation="vertical", padding=dp(6), spacing=dp(1), bg=PANEL_SOFT, **kwargs)
        self.add_widget(make_label(title.upper(), color=MUTED, font_size=dp(7.5), bold=True))
        self.value_label = make_label(value, color=accent, font_size=dp(14), bold=True)
        self.add_widget(self.value_label)
        self.add_widget(make_label(subtitle, color=MUTED, font_size=dp(7)))


class GameState:
    def __init__(self):
        self.data = json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))

    @property
    def d(self):
        return self.data

    def _merge_defaults(self, loaded, defaults):
        if isinstance(defaults, dict):
            out = json.loads(json.dumps(defaults, ensure_ascii=False))
            if isinstance(loaded, dict):
                for key, value in loaded.items():
                    if key in defaults:
                        out[key] = self._merge_defaults(value, defaults[key])
                    else:
                        out[key] = value
            return out
        return loaded

    def save(self):
        path = os.path.join(App.get_running_app().user_data_dir, SAVE_FILE)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)

    def load(self):
        path = os.path.join(App.get_running_app().user_data_dir, SAVE_FILE)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            self.data = self._merge_defaults(loaded, INITIAL_STATE)
            return True
        except Exception:
            return False

    def advance_day(self, days=1):
        for _ in range(days):
            self._daily_tick()
            if self.d.get("event"):
                break
        self.save()

    def _daily_tick(self):
        d = self.d
        current = date.fromisoformat(d["day"])
        d["day"] = (current + timedelta(days=1)).isoformat()

        demand = (d["gdp_growth"] - 2.0) * 0.025
        fiscal_pressure = (d["debt_ratio"] - 70) * 0.002
        d["inflation"] = max(0.5, min(30, d["inflation"] + random.uniform(-0.05, 0.07) + demand + fiscal_pressure))
        d["unemployment"] = max(2, min(30, d["unemployment"] + random.uniform(-0.08, 0.08)))

        target = 62 - (d["inflation"] - 4.0) * 1.2 - (d["unemployment"] - 6.0) * 0.8
        d["approval"] = clamp(d["approval"] + (target - d["approval"]) * 0.035 + random.uniform(-0.18, 0.18))
        d["congress"] = clamp(d["congress"] + ((d["approval"] - 50) * 0.025) + random.uniform(-0.12, 0.12))
        d["stability"] = clamp(d["stability"] + (d["approval"] - 50) * 0.006 - (d["inflation"] - 5) * 0.01)
        d["impeachment_risk"] = clamp(8 + max(0, 50 - d["approval"]) * 0.65 + max(0, 45 - d["congress"]) * 0.55 + max(0, d["inflation"] - 10) * 1.4)
        d["coup_risk"] = clamp(2 + max(0, 45 - d["stability"]) * 0.8 + max(0, 40 - d["approval"]) * 0.25)
        d["gdp_growth"] = max(-10, min(12, d["gdp_growth"] + random.uniform(-0.08, 0.08)))
        d["gdp"] *= 1 + d["gdp_growth"] / 100 / 365
        d["market_sentiment"] = clamp(60 + d["gdp_growth"] * 2 - d["inflation"] * 1.8 - max(0, d["debt_ratio"] - 70) * 0.35)
        d["crisis_risk"] = clamp((100 - d["stability"]) * 0.35 + d["impeachment_risk"] * 0.35 + d["coup_risk"] * 0.30)

        if random.random() < 0.08:
            self.create_random_event()

    def create_random_event(self):
        events = [
            {
                "title": "Greve nacional",
                "text": "Sindicatos convocam paralisacao contra o custo de vida.",
                "choices": [
                    ["Negociar", {"approval": 1.5, "stability": 1}],
                    ["Adotar linha dura", {"approval": -2.5, "stability": -2}],
                    ["Ignorar", {"approval": -1, "stability": -1}],
                ],
            },
            {
                "title": "Pressao no mercado",
                "text": "Investidores demonstram preocupacao com a trajetoria fiscal.",
                "choices": [
                    ["Cortar gastos", {"debt_ratio": -0.7, "approval": -0.8, "treasury": 1.0}],
                    ["Aumentar impostos", {"debt_ratio": -1.0, "approval": -1.5, "treasury": 2.0}],
                    ["Manter politica", {"approval": 0.3, "stability": -0.5}],
                ],
            },
            {
                "title": "Crise diplomatica",
                "text": "Um governo estrangeiro fez uma declaracao hostil.",
                "choices": [
                    ["Responder diplomaticamente", {"stability": 0.5, "approval": 0.5}],
                    ["Adotar tom duro", {"approval": 1.0, "stability": -0.5}],
                    ["Nao responder", {"approval": -0.4}],
                ],
            },
            {
                "title": "Escandalo no governo",
                "text": "Documentos levantam suspeitas envolvendo uma autoridade.",
                "choices": [
                    ["Abrir investigacao", {"approval": 1.2, "congress": 0.8}],
                    ["Defender o ministro", {"approval": -2.0, "congress": -1}],
                    ["Exonerar", {"approval": 0.5, "stability": -0.2}],
                ],
            },
        ]
        self.d["event"] = random.choice(events)

    def apply_choice(self, title, changes):
        d = self.d
        before_approval = d["approval"]
        before_market = d["market_sentiment"]
        before_crisis = d["crisis_risk"]

        for key, value in changes.items():
            if key in d and isinstance(d[key], (int, float)):
                d[key] += value
                if key in ("approval", "congress", "stability", "coup_risk", "impeachment_risk"):
                    d[key] = clamp(d[key])

        d["market_sentiment"] = clamp(60 + d["gdp_growth"] * 2 - d["inflation"] * 1.8 - max(0, d["debt_ratio"] - 70) * 0.35)
        d["crisis_risk"] = clamp((100 - d["stability"]) * 0.35 + d["impeachment_risk"] * 0.35 + d["coup_risk"] * 0.30)
        d["media_impact"] = {
            "approval": d["approval"] - before_approval,
            "market": d["market_sentiment"] - before_market,
            "crisis": d["crisis_risk"] - before_crisis,
        }
        d["event"] = None
        d["headline"] = title.upper()
        d["last_news"] = "A decisao presidencial provoca repercussao imediata no pais."
        d["related_news"].insert(0, {"category": "Plantao", "headline": title, "subtitle": d["last_news"]})
        d["related_news"] = d["related_news"][:8]
        d["feed"].insert(0, ["SocialNet", "A decisao do governo divide opinioes.", random.randint(1200, 8000)])
        d["feed"] = d["feed"][:8]
        self.save()


class GameScreen(Screen):
    def __init__(self, game, title="", show_nav=True, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        with self.canvas.before:
            Color(*BG)
            self._screen_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        self.root_layout = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(5))
        self.add_widget(self.root_layout)

        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        header.add_widget(make_label(title, color=CYAN, font_size=dp(13), bold=True))
        self.date_label = make_label("", color=MUTED, font_size=dp(8), size_hint_x=0.22, halign="right")
        header.add_widget(self.date_label)
        self.root_layout.add_widget(header)

        self.content = BoxLayout(orientation="vertical")
        self.root_layout.add_widget(self.content)

        if show_nav:
            self.root_layout.add_widget(self._make_nav())

    def _sync_bg(self, *_):
        self._screen_bg.pos = self.pos
        self._screen_bg.size = self.size

    def _make_nav(self):
        nav = GridLayout(cols=7, size_hint_y=None, height=dp(38), spacing=dp(4))
        items = [
            ("GOVERNO", "cabinet"),
            ("ECONOMIA", "economy"),
            ("POLITICA", "politics"),
            ("MILITAR", "military"),
            ("DIPLOMACIA", "diplomacy"),
            ("MIDIA", "media"),
            ("MAPA", "map"),
        ]
        for text, target in items:
            button = CommandButton(text=text, font_size=dp(7.5))
            button.bind(on_release=lambda _btn, name=target: self.game.show_screen(name))
            nav.add_widget(button)
        return nav

    def refresh(self):
        self.date_label.text = self.game.state.d["day"]


class CabinetScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "PRESIDENTE SIMULATOR  |  CENTRO DE COMANDO", **kwargs)
        body = BoxLayout(spacing=dp(6))
        self.content.add_widget(body)

        center = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_x=0.70)
        hero = Panel(orientation="vertical", padding=dp(8), spacing=dp(4), size_hint_y=0.60, bg=PANEL_DARK)
        top = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(6))
        top.add_widget(make_label("SALA DE SITUACAO / TELEJORNAL", color=CYAN, font_size=dp(9), bold=True))
        live = make_label("AO VIVO", color=RED, font_size=dp(8), bold=True, size_hint_x=0.16, halign="right")
        top.add_widget(live)
        hero.add_widget(top)
        self.headline_label = make_label("", font_size=dp(18), bold=True, halign="center")
        self.news_label = make_label("", color=MUTED, font_size=dp(9), halign="center")
        hero.add_widget(self.headline_label)
        hero.add_widget(self.news_label)
        ticker = Panel(orientation="horizontal", padding=dp(4), size_hint_y=None, height=dp(30), bg=PANEL_SOFT)
        self.ticker_label = make_label("", color=AMBER, font_size=dp(7.5), bold=True, halign="center")
        ticker.add_widget(self.ticker_label)
        hero.add_widget(ticker)
        open_news = CommandButton(text="ABRIR TELEJORNAL COMPLETO", size_hint_y=None, height=dp(34))
        open_news.bind(on_release=lambda *_: self.game.show_screen("media"))
        hero.add_widget(open_news)
        center.add_widget(hero)

        desk = Panel(orientation="vertical", padding=dp(7), spacing=dp(5), size_hint_y=0.40)
        desk.add_widget(make_label("MESA PRESIDENCIAL", color=CYAN, font_size=dp(9), bold=True, size_hint_y=None, height=dp(22)))
        actions = GridLayout(cols=3, spacing=dp(5))
        for text, target in [
            ("TELEFONE DE CRISE", "crisis"),
            ("PASTAS DE LEIS", "politics"),
            ("MAPA MUNDIAL", "map"),
            ("COLETIVA", "press"),
            ("DIPLOMACIA", "diplomacy"),
            ("MIDIA", "media"),
        ]:
            b = CommandButton(text=text)
            if target == "crisis":
                b.bind(on_release=lambda *_: self.game.show_message("Telefone de crise", "Nenhuma chamada urgente no momento."))
            elif target == "press":
                b.bind(on_release=lambda *_: self.game.press_conference())
            else:
                b.bind(on_release=lambda _btn, name=target: self.game.show_screen(name))
            actions.add_widget(b)
        desk.add_widget(actions)
        center.add_widget(desk)
        body.add_widget(center)

        right = Panel(orientation="vertical", padding=dp(6), spacing=dp(5), size_hint_x=0.30)
        right.add_widget(make_label("INDICADORES NACIONAIS", color=CYAN, font_size=dp(9), bold=True, size_hint_y=None, height=dp(24)))
        self.stats = GridLayout(cols=2, spacing=dp(5))
        right.add_widget(self.stats)
        body.add_widget(right)

    def refresh(self):
        super().refresh()
        d = self.game.state.d
        self.headline_label.text = d["headline"]
        self.news_label.text = d["last_news"]
        self.ticker_label.text = f"APROVACAO {d['approval']:.0f}%   |   INFLACAO {d['inflation']:.1f}%   |   CONGRESSO {d['congress']:.0f}%   |   RISCO {d['crisis_risk']:.0f}%"
        self.stats.clear_widgets()
        values = [
            ("Aprovacao", f"{d['approval']:.0f}%", "popular", GREEN if d["approval"] >= 50 else RED),
            ("PIB", fmt_money(d["gdp"]), f"{d['gdp_growth']:+.1f}%", CYAN),
            ("Inflacao", f"{d['inflation']:.1f}%", "precos", AMBER if d["inflation"] > 6 else GREEN),
            ("Desemprego", f"{d['unemployment']:.1f}%", "trabalho", CYAN),
            ("Congresso", f"{d['congress']:.0f}%", "apoio", GREEN if d["congress"] >= 50 else AMBER),
            ("Impeachment", f"{d['impeachment_risk']:.0f}%", "risco", RED if d["impeachment_risk"] >= 40 else AMBER),
        ]
        for title, value, subtitle, accent in values:
            self.stats.add_widget(StatTile(title, value, subtitle, accent=accent))


class StudioBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)

    def redraw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        with self.canvas:
            Color(*PANEL_DARK)
            Rectangle(pos=(x, y), size=(w, h))
            Color(0.025, 0.08, 0.13, 1)
            RoundedRectangle(pos=(x + w * 0.08, y + h * 0.08), size=(w * 0.84, h * 0.82), radius=[dp(18)])
            Color(0.03, 0.15, 0.22, 1)
            RoundedRectangle(pos=(x + w * 0.18, y + h * 0.22), size=(w * 0.64, h * 0.52), radius=[dp(14)])
            Color(CYAN[0], CYAN[1], CYAN[2], 0.55)
            Line(rounded_rectangle=(x + w * 0.18, y + h * 0.22, w * 0.64, h * 0.52, dp(14)), width=1.1)
            Color(0.04, 0.11, 0.17, 1)
            RoundedRectangle(pos=(x + w * 0.27, y + h * 0.08), size=(w * 0.46, h * 0.13), radius=[dp(12)])


class RelatedNewsCard(Button):
    def __init__(self, category, headline, subtitle, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = PANEL_SOFT
        self.color = TEXT
        self.markup = True
        self.halign = "left"
        self.valign = "middle"
        self.font_size = dp(8)
        self.padding = (dp(8), dp(5))
        self.text = f"[color=48c7f5][b]{category.upper()}[/b][/color]\n[b]{headline}[/b]\n[color=98a9bd]{subtitle}[/color]"
        self.bind(size=lambda inst, _value: setattr(inst, "text_size", (inst.width - dp(16), inst.height - dp(8))))
        if callback:
            self.bind(on_release=lambda *_: callback(headline, subtitle))


class ImpactCard(Panel):
    def __init__(self, title, bad_when_positive=False, **kwargs):
        super().__init__(orientation="vertical", padding=dp(6), spacing=dp(2), bg=PANEL_SOFT, **kwargs)
        self.bad_when_positive = bad_when_positive
        top = BoxLayout(size_hint_y=None, height=dp(21))
        top.add_widget(make_label(title.upper(), color=MUTED, font_size=dp(7), bold=True))
        self.delta_label = make_label("0.0%", font_size=dp(11), bold=True, halign="right", size_hint_x=0.38)
        top.add_widget(self.delta_label)
        self.add_widget(top)
        self.progress = ProgressBar(max=10, value=0, size_hint_y=None, height=dp(7))
        self.add_widget(self.progress)
        self.status_label = make_label("SEM ALTERACAO", color=MUTED, font_size=dp(6.5), size_hint_y=None, height=dp(16))
        self.add_widget(self.status_label)

    def set_delta(self, value):
        value = float(value)
        self.progress.value = min(abs(value), 10)
        if abs(value) < 0.05:
            color, status, prefix = MUTED, "SEM ALTERACAO", ""
        else:
            positive = value > 0
            negative_effect = positive if self.bad_when_positive else not positive
            color = RED if negative_effect else GREEN
            status = "IMPACTO NEGATIVO" if negative_effect else "IMPACTO POSITIVO"
            prefix = "+" if positive else ""
        self.delta_label.text = f"{prefix}{value:.1f}%"
        self.delta_label.color = color
        self.status_label.text = status
        self.status_label.color = color


class MediaScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "PRESIDENTE NEWS  |  PLANTAO DE NOTICIAS", **kwargs)

        main = BoxLayout(spacing=dp(6))
        self.content.add_widget(main)

        studio_panel = Panel(orientation="vertical", padding=dp(6), spacing=dp(4), size_hint_x=0.70, bg=PANEL)
        studio_header = BoxLayout(size_hint_y=None, height=dp(24))
        studio_header.add_widget(make_label("CANAL NACIONAL 24H", color=CYAN, font_size=dp(8.5), bold=True))
        studio_header.add_widget(make_label("AO VIVO", color=RED, font_size=dp(8), bold=True, size_hint_x=0.16, halign="right"))
        studio_panel.add_widget(studio_header)

        stage = RelativeLayout()
        stage.add_widget(StudioBackground())
        overlay = BoxLayout(orientation="vertical", padding=dp(12))
        overlay.add_widget(Widget())
        overlay.add_widget(make_label("PLANTAO PRESIDENCIAL", font_size=dp(18), bold=True, halign="center"))
        overlay.add_widget(make_label("CENTRAL DE NOTICIAS DO GOVERNO", color=MUTED, font_size=dp(7.5), halign="center"))
        overlay.add_widget(Widget())
        stage.add_widget(overlay)
        studio_panel.add_widget(stage)

        lower = Panel(orientation="vertical", padding=dp(7), spacing=dp(3), size_hint_y=None, height=dp(92), bg=PANEL_DARK)
        tag = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(5))
        tag.add_widget(make_label("PLANTAO", color=RED, font_size=dp(8), bold=True, size_hint_x=0.16))
        tag.add_widget(make_label("ULTIMA HORA", color=AMBER, font_size=dp(7.5), bold=True))
        lower.add_widget(tag)
        self.headline_label = make_label("", font_size=dp(14), bold=True)
        self.subheadline_label = make_label("", color=MUTED, font_size=dp(8))
        lower.add_widget(self.headline_label)
        lower.add_widget(self.subheadline_label)
        studio_panel.add_widget(lower)
        main.add_widget(studio_panel)

        sidebar = Panel(orientation="vertical", padding=dp(6), spacing=dp(5), size_hint_x=0.30, bg=PANEL)
        sidebar.add_widget(make_label("NOTICIAS RELACIONADAS", color=CYAN, font_size=dp(8.5), bold=True, size_hint_y=None, height=dp(24)))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.news_list = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.news_list.bind(minimum_height=self.news_list.setter("height"))
        scroll.add_widget(self.news_list)
        sidebar.add_widget(scroll)
        main.add_widget(sidebar)

        impact_bar = Panel(orientation="horizontal", size_hint_y=None, height=dp(72), padding=dp(6), spacing=dp(5), bg=PANEL)
        impact_bar.add_widget(make_label("IMPACTO\nIMEDIATO", color=CYAN, font_size=dp(8), bold=True, size_hint_x=0.14))
        self.approval_impact = ImpactCard("Aprovacao")
        self.market_impact = ImpactCard("Mercado")
        self.crisis_impact = ImpactCard("Risco de crise", bad_when_positive=True)
        impact_bar.add_widget(self.approval_impact)
        impact_bar.add_widget(self.market_impact)
        impact_bar.add_widget(self.crisis_impact)
        self.content.add_widget(impact_bar)

    def _select_news(self, headline, subtitle):
        self.headline_label.text = headline.upper()
        self.subheadline_label.text = subtitle

    def refresh(self):
        super().refresh()
        d = self.game.state.d
        self.headline_label.text = d["headline"]
        self.subheadline_label.text = d["last_news"]
        impact = d.get("media_impact", {})
        self.approval_impact.set_delta(impact.get("approval", 0))
        self.market_impact.set_delta(impact.get("market", 0))
        self.crisis_impact.set_delta(impact.get("crisis", 0))
        self.news_list.clear_widgets()
        for item in d.get("related_news", DEFAULT_RELATED_NEWS):
            card = RelatedNewsCard(
                item.get("category", "Geral"),
                item.get("headline", "Nova noticia"),
                item.get("subtitle", ""),
                callback=self._select_news,
                size_hint_y=None,
                height=dp(66),
            )
            self.news_list.add_widget(card)


class EconomyScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "ECONOMIA NACIONAL", **kwargs)
        self.grid = GridLayout(cols=4, spacing=dp(5), size_hint_y=0.60)
        self.content.add_widget(self.grid)
        actions = Panel(orientation="vertical", padding=dp(6), spacing=dp(5), size_hint_y=0.40)
        actions.add_widget(make_label("DECISOES ECONOMICAS", color=CYAN, font_size=dp(8.5), bold=True, size_hint_y=None, height=dp(22)))
        buttons = GridLayout(cols=4, spacing=dp(5))
        for text, key, amount in [
            ("IMPOSTO -1", "tax_rate", -1),
            ("IMPOSTO +1", "tax_rate", 1),
            ("JUROS -0,5", "interest_rate", -0.5),
            ("GASTO SOCIAL +1", "social_spending", 1),
        ]:
            b = CommandButton(text=text)
            b.bind(on_release=lambda _btn, k=key, a=amount, t=text: self.change(k, a, t))
            buttons.add_widget(b)
        actions.add_widget(buttons)
        self.content.add_widget(actions)

    def change(self, key, amount, title):
        d = self.game.state.d
        before_approval = d["approval"]
        before_market = d["market_sentiment"]
        before_crisis = d["crisis_risk"]
        d[key] += amount
        if key == "tax_rate":
            d["treasury"] -= amount * 1.2
            d["approval"] = clamp(d["approval"] - amount * 0.5)
        elif key == "interest_rate":
            d["inflation"] += amount * 0.15
            d["gdp_growth"] -= amount * 0.2
        elif key == "social_spending":
            d["treasury"] -= amount
            d["approval"] = clamp(d["approval"] + amount * 0.6)
            d["debt_ratio"] += amount * 0.15
        d["market_sentiment"] = clamp(60 + d["gdp_growth"] * 2 - d["inflation"] * 1.8 - max(0, d["debt_ratio"] - 70) * 0.35)
        d["crisis_risk"] = clamp((100 - d["stability"]) * 0.35 + d["impeachment_risk"] * 0.35 + d["coup_risk"] * 0.30)
        d["media_impact"] = {"approval": d["approval"] - before_approval, "market": d["market_sentiment"] - before_market, "crisis": d["crisis_risk"] - before_crisis}
        d["headline"] = title.upper()
        d["last_news"] = "Nova decisao economica provoca reacao imediata."
        self.game.state.save()
        self.game.refresh_all()

    def refresh(self):
        super().refresh()
        d = self.game.state.d
        self.grid.clear_widgets()
        for title, value, subtitle in [
            ("PIB", fmt_money(d["gdp"]), f"crescimento {d['gdp_growth']:+.1f}%"),
            ("Inflacao", f"{d['inflation']:.1f}%", "nivel de precos"),
            ("Desemprego", f"{d['unemployment']:.1f}%", "mercado de trabalho"),
            ("Divida/PIB", f"{d['debt_ratio']:.1f}%", "fiscal"),
            ("Juros", f"{d['interest_rate']:.1f}%", "taxa basica"),
            ("Impostos", f"{d['tax_rate']:.1f}%", "carga"),
            ("Tesouro", f"{d['treasury']:.1f}", "reserva"),
            ("Mercado", f"{d['market_sentiment']:.0f}%", "sentimento"),
        ]:
            self.grid.add_widget(StatTile(title, value, subtitle))


class PoliticsScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "POLITICA E GOVERNO", **kwargs)
        body = BoxLayout(spacing=dp(6))
        self.content.add_widget(body)
        info = Panel(orientation="vertical", padding=dp(8), size_hint_x=0.40)
        self.info_label = make_label("", font_size=dp(10), valign="top")
        info.add_widget(self.info_label)
        body.add_widget(info)
        laws = Panel(orientation="vertical", padding=dp(6), spacing=dp(5), size_hint_x=0.60)
        laws.add_widget(make_label("PROJETOS DE LEI", color=CYAN, font_size=dp(8.5), bold=True, size_hint_y=None, height=dp(24)))
        for title, effect in [
            ("REFORMA TRIBUTARIA", {"congress": -2, "approval": -1}),
            ("EXPANSAO DA SAUDE", {"congress": 1, "approval": 2, "debt_ratio": 0.8}),
            ("PLANO DE EDUCACAO", {"congress": 0.5, "approval": 1.5, "debt_ratio": 0.5}),
            ("PACOTE DE SEGURANCA", {"congress": -1, "approval": -1, "stability": 1}),
        ]:
            b = CommandButton(text=title, size_hint_y=None, height=dp(38))
            b.bind(on_release=lambda _btn, t=title, e=effect: self.pass_law(t, e))
            laws.add_widget(b)
        laws.add_widget(Widget())
        body.add_widget(laws)

    def pass_law(self, title, effect):
        d = self.game.state.d
        if d["congress"] < 40:
            self.game.show_message("Lei rejeitada", "O apoio parlamentar e insuficiente para aprovar a proposta.")
            return
        self.game.state.apply_choice(f"Congresso aprova {title}", effect)
        self.game.refresh_all()

    def refresh(self):
        super().refresh()
        d = self.game.state.d
        self.info_label.text = (
            f"APOIO NO CONGRESSO: {d['congress']:.0f}%\n\n"
            f"APROVACAO: {d['approval']:.0f}%\n\n"
            f"ESTABILIDADE: {d['stability']:.0f}%\n\n"
            f"RISCO DE IMPEACHMENT: {d['impeachment_risk']:.0f}%\n\n"
            f"RISCO DE CRISE: {d['crisis_risk']:.0f}%"
        )


class DiplomacyScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "DIPLOMACIA E RELACOES EXTERIORES", **kwargs)
        scroll = ScrollView(do_scroll_x=False)
        self.list_box = GridLayout(cols=2, spacing=dp(5), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        self.content.add_widget(scroll)

    def refresh(self):
        super().refresh()
        self.list_box.clear_widgets()
        for name, country in self.game.state.d["countries"].items():
            if name == "Brasil":
                continue
            row = Panel(orientation="horizontal", size_hint_y=None, height=dp(58), padding=dp(6), spacing=dp(5))
            row.add_widget(make_label(f"{name}\nRelacao {country['relation']:+d}  |  Poder {country['power']}/100", font_size=dp(8)))
            b = CommandButton(text="NEGOCIAR", size_hint_x=0.32)
            b.bind(on_release=lambda _btn, n=name: self.negotiate(n))
            row.add_widget(b)
            self.list_box.add_widget(row)

    def negotiate(self, name):
        d = self.game.state.d
        country = d["countries"][name]
        gain = random.randint(2, 6)
        country["relation"] = int(clamp(country["relation"] + gain, -100, 100))
        d["approval"] = clamp(d["approval"] + 0.2)
        d["headline"] = f"BRASIL AVANCA EM NEGOCIACOES COM {name.upper()}"
        d["last_news"] = "A rodada diplomatica melhora a relacao bilateral."
        d["media_impact"] = {"approval": 0.2, "market": 0.1, "crisis": -0.3}
        self.game.state.save()
        self.game.refresh_all()


class WorldMap(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.country_buttons = []
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(lambda *_: self._build_buttons(), 0)

    def redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0.006, 0.020, 0.038, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.025, 0.12, 0.18, 1)
            Ellipse(pos=(self.x + self.width * 0.06, self.y + self.height * 0.08), size=(self.width * 0.88, self.height * 0.84))
            for points in [
                [(0.14, .62), (0.24, .73), (0.34, .62), (0.29, .46), (0.22, .34), (0.13, .46)],
                [(0.39, .69), (0.56, .77), (0.73, .65), (0.77, .52), (0.63, .42), (0.49, .50)],
                [(0.70, .39), (0.83, .48), (0.90, .34), (0.79, .22), (0.67, .29)],
                [(0.35, .30), (0.44, .22), (0.49, .09), (0.41, .06), (0.33, .18)],
            ]:
                Color(0.08, 0.36, 0.25, 1)
                vertices = []
                for px, py in points:
                    vertices.extend([self.x + self.width * px, self.y + self.height * py, 0, 0])
                Mesh(vertices=vertices, indices=list(range(len(points))), mode="triangle_fan")
            Color(CYAN[0], CYAN[1], CYAN[2], 0.55)
            Line(points=[self.x + self.width * .25, self.y + self.height * .44, self.x + self.width * .49, self.y + self.height * .62, self.x + self.width * .72, self.y + self.height * .56], width=1.2)
        self._position_buttons()

    def _build_buttons(self):
        if self.country_buttons:
            return
        positions = [
            ("Brasil", .18, .39),
            ("Estados Unidos", .29, .68),
            ("China", .72, .58),
            ("Argentina", .18, .27),
            ("Russia", .61, .73),
            ("India", .65, .43),
        ]
        for name, px, py in positions:
            b = CommandButton(text=name.upper(), size_hint=(None, None), size=(dp(92), dp(30)), font_size=dp(6.8))
            b.map_pos = (px, py)
            b.bind(on_release=lambda _btn, n=name: self.select_country(n))
            self.add_widget(b)
            self.country_buttons.append(b)
        self._position_buttons()

    def _position_buttons(self):
        for button in self.country_buttons:
            px, py = button.map_pos
            button.pos = (self.x + self.width * px, self.y + self.height * py)

    def select_country(self, name):
        country = self.game.state.d["countries"].get(name)
        if country:
            self.game.show_message(name, f"Relacao: {country['relation']:+d}\nPoder: {country['power']}/100\nPIB: US$ {country['gdp']:.2f} tri")


class MapScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "MAPA ESTRATEGICO MUNDIAL", **kwargs)
        self.content.add_widget(WorldMap(game))


class MilitaryScreen(GameScreen):
    def __init__(self, game, **kwargs):
        super().__init__(game, "FORCAS ARMADAS", **kwargs)
        body = BoxLayout(spacing=dp(6))
        self.content.add_widget(body)
        info = Panel(orientation="vertical", padding=dp(8), size_hint_x=0.48)
        self.info_label = make_label("", font_size=dp(10), valign="top")
        info.add_widget(self.info_label)
        body.add_widget(info)
        actions = Panel(orientation="vertical", padding=dp(7), spacing=dp(6), size_hint_x=0.52)
        actions.add_widget(make_label("COMANDO ESTRATEGICO", color=CYAN, font_size=dp(8.5), bold=True, size_hint_y=None, height=dp(24)))
        for text, amount in [("AUMENTAR ORCAMENTO", 0.2), ("REDUZIR ORCAMENTO", -0.2), ("REALIZAR EXERCICIO", 1.0)]:
            b = CommandButton(text=text, size_hint_y=None, height=dp(38))
            b.bind(on_release=lambda _btn, t=text, a=amount: self.action(t, a))
            actions.add_widget(b)
        actions.add_widget(Widget())
        body.add_widget(actions)

    def action(self, title, amount):
        d = self.game.state.d
        d["military_budget"] = max(0.1, d["military_budget"] + amount)
        if "EXERCICIO" in title:
            effect = {"stability": 1, "approval": 0.3}
        else:
            d["treasury"] -= amount * 1.5
            effect = {"approval": 0.1 if amount > 0 else -0.1}
        self.game.state.apply_choice(title, effect)
        self.game.refresh_all()

    def refresh(self):
        super().refresh()
        d = self.game.state.d
        self.info_label.text = (
            f"ORCAMENTO MILITAR: {d['military_budget']:.1f}% do PIB\n\n"
            f"ESTABILIDADE: {d['stability']:.0f}%\n\n"
            f"RISCO DE GOLPE: {d['coup_risk']:.0f}%\n\n"
            f"RISCO DE CRISE: {d['crisis_risk']:.0f}%"
        )


class GameApp(App):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        self.state = GameState()
        self.state.load()

        root = BoxLayout(orientation="vertical", spacing=0)
        self.manager = ScreenManager(transition=NoTransition())
        root.add_widget(self.manager)

        for name, cls in [
            ("cabinet", CabinetScreen),
            ("economy", EconomyScreen),
            ("politics", PoliticsScreen),
            ("military", MilitaryScreen),
            ("diplomacy", DiplomacyScreen),
            ("media", MediaScreen),
            ("map", MapScreen),
        ]:
            self.manager.add_widget(cls(self, name=name))

        timebar = Panel(orientation="horizontal", size_hint_y=None, height=dp(42), padding=dp(4), spacing=dp(4), bg=PANEL_DARK, radius=0)
        for text, days in [("AVANCAR 1 DIA", 1), ("7 DIAS", 7), ("30 DIAS", 30)]:
            b = CommandButton(text=text)
            b.bind(on_release=lambda _btn, amount=days: self.advance(amount))
            timebar.add_widget(b)
        save = CommandButton(text="SALVAR")
        save.bind(on_release=lambda *_: self.save_game())
        timebar.add_widget(save)
        root.add_widget(timebar)

        self.show_screen("cabinet")
        Clock.schedule_interval(self.auto_refresh, 1.0)
        return root

    def show_screen(self, name):
        if name in self.manager.screen_names:
            self.manager.current = name
            self.refresh_all()

    def refresh_all(self):
        for screen in self.manager.screens:
            if hasattr(screen, "refresh"):
                screen.refresh()

    def auto_refresh(self, _dt):
        current = self.manager.current_screen
        if current and hasattr(current, "refresh"):
            current.refresh()
        if self.state.d.get("event"):
            self.show_event_if_needed()

    def advance(self, days):
        if self.state.d.get("event"):
            self.show_event_if_needed()
            return
        self.state.advance_day(days)
        self.refresh_all()
        self.show_event_if_needed()

    def _effect_summary(self, changes):
        labels = {
            "approval": "Aprovacao",
            "congress": "Congresso",
            "stability": "Estabilidade",
            "debt_ratio": "Divida",
            "treasury": "Tesouro",
        }
        parts = []
        for key, value in changes.items():
            if key in labels:
                sign = "+" if value > 0 else ""
                parts.append(f"{labels[key]} {sign}{value:g}")
        return "  |  ".join(parts) if parts else "Impacto indireto"

    def show_event_if_needed(self):
        event = self.state.d.get("event")
        if not event or getattr(self, "_event_open", False):
            return
        self._event_open = True

        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(make_label(event["title"].upper(), color=AMBER, font_size=dp(15), bold=True, halign="center", size_hint_y=None, height=dp(36)))
        box.add_widget(make_label(event["text"], font_size=dp(9.5), halign="center", size_hint_y=None, height=dp(52)))
        box.add_widget(make_label("ESCOLHA UMA RESPOSTA", color=CYAN, font_size=dp(8), bold=True, size_hint_y=None, height=dp(22)))

        popup = Popup(title="EVENTO NACIONAL", content=box, size_hint=(0.74, 0.76), auto_dismiss=False)
        for title, changes in event["choices"]:
            row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(56), spacing=dp(2))
            b = CommandButton(text=title)
            b.bind(on_release=lambda _btn, t=title, ch=changes: self.finish_event(popup, t, ch))
            row.add_widget(b)
            row.add_widget(make_label(self._effect_summary(changes), color=MUTED, font_size=dp(6.5), halign="center", size_hint_y=None, height=dp(16)))
            box.add_widget(row)
        popup.open()

    def finish_event(self, popup, title, changes):
        self.state.apply_choice(title, changes)
        popup.dismiss()
        self._event_open = False
        self.refresh_all()
        self.show_screen("media")

    def press_conference(self):
        box = BoxLayout(orientation="vertical", padding=dp(9), spacing=dp(5))
        box.add_widget(make_label("Jornalista: A inflacao esta subindo. Qual e a resposta do governo?", font_size=dp(9.5), halign="center", size_hint_y=None, height=dp(48)))
        popup = Popup(title="COLETIVA DE IMPRENSA", content=box, size_hint=(0.76, 0.78), auto_dismiss=False)
        options = [
            ("Nao ha motivo para preocupacao.", {"approval": -1.2, "inflation": 0.1}),
            ("Estamos trabalhando para resolver.", {"approval": 0.5}),
            ("A situacao e seria e assumimos responsabilidade.", {"approval": 1.5, "congress": 0.5}),
            ("A imprensa esta exagerando.", {"approval": -1.5, "stability": -0.5}),
        ]
        for text, changes in options:
            b = CommandButton(text=text, size_hint_y=None, height=dp(38))
            b.bind(on_release=lambda _btn, t=text, ch=changes: self.finish_press(popup, t, ch))
            box.add_widget(b)
        popup.open()

    def finish_press(self, popup, title, changes):
        self.state.apply_choice("Presidente fala em coletiva", changes)
        self.state.d["last_news"] = title
        popup.dismiss()
        self.refresh_all()
        self.show_screen("media")

    def save_game(self):
        self.state.save()
        self.show_message("Partida salva", "O estado atual foi salvo no armazenamento do aplicativo.")

    def show_message(self, title, message):
        Popup(title=title, content=make_label(message, font_size=dp(9), halign="center"), size_hint=(0.66, 0.34)).open()
