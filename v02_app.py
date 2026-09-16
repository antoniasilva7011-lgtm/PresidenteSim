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
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

APP_NAME = "Presidente Simulator V0.2"
SAVE_FILE = "presidente_simulator_save.json"

BG = (0.008, 0.018, 0.032, 1)
PANEL = (0.028, 0.055, 0.082, 1)
PANEL_ALT = (0.040, 0.082, 0.115, 1)
CYAN = (0.10, 0.63, 0.86, 1)
TEXT = (0.93, 0.96, 1, 1)
MUTED = (0.56, 0.66, 0.76, 1)
WARN = (0.95, 0.63, 0.24, 1)
GOOD = (0.25, 0.82, 0.55, 1)
DANGER = (0.95, 0.30, 0.34, 1)

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
    "last_news": "Governo inicia novo ciclo politico.",
    "headline": "GOVERNO PREPARA NOVAS MEDIDAS",
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


def safe_label(text="", **kwargs):
    kwargs.setdefault("color", TEXT)
    kwargs.setdefault("font_size", dp(11))
    kwargs.setdefault("halign", "left")
    kwargs.setdefault("valign", "middle")
    label = Label(text=text, **kwargs)
    label.bind(size=lambda inst, _value: setattr(inst, "text_size", (inst.width, None)))
    return label


class Panel(BoxLayout):
    def __init__(self, bg=PANEL, radius=12, **kwargs):
        super().__init__(**kwargs)
        self._bg_color = bg
        with self.canvas.before:
            Color(*self._bg_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._sync_panel, size=self._sync_panel)

    def _sync_panel(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class ActionButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0.045, 0.115, 0.165, 1))
        kwargs.setdefault("color", TEXT)
        kwargs.setdefault("font_size", dp(10))
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(CYAN[0], CYAN[1], CYAN[2], 0.70)
            self.outline = Line(rounded_rectangle=(0, 0, 100, 100, dp(8)), width=0.8)
        self.bind(pos=self._sync_outline, size=self._sync_outline)

    def _sync_outline(self, *_):
        self.outline.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))


class StatTile(Panel):
    def __init__(self, title, value, subtitle="", accent=CYAN, **kwargs):
        super().__init__(orientation="vertical", padding=dp(7), spacing=dp(1), bg=PANEL_ALT, **kwargs)
        self.title_label = safe_label(title.upper(), color=MUTED, font_size=dp(8), bold=True)
        self.value_label = safe_label(value, color=accent, font_size=dp(16), bold=True)
        self.sub_label = safe_label(subtitle, color=MUTED, font_size=dp(7))
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)
        self.add_widget(self.sub_label)

    def set_value(self, value, subtitle=None, accent=None):
        self.value_label.text = value
        if subtitle is not None:
            self.sub_label.text = subtitle
        if accent is not None:
            self.value_label.color = accent


class GameState:
    def __init__(self):
        self.data = json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))

    @property
    def d(self):
        return self.data

    def _merge_defaults(self, loaded, defaults):
        if isinstance(defaults, dict):
            out = dict(defaults)
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
                    ["Cortar gastos", {"debt_ratio": -0.7, "approval": -0.8}],
                    ["Aumentar impostos", {"debt_ratio": -1.0, "approval": -1.5}],
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

    def apply_choice(self, changes):
        for key, value in changes.items():
            if key not in self.d:
                continue
            self.d[key] += value
            if key in ("approval", "congress", "stability", "coup_risk", "impeachment_risk"):
                self.d[key] = clamp(self.d[key])
        self.d["event"] = None
        self.d["last_news"] = "O governo tomou uma decisao diante de uma nova crise."
        self.d["headline"] = "GOVERNO TOMA DECISAO EM MEIO A CRISE"
        self.d["feed"].insert(0, ["SocialNet", "A decisao do governo divide opinioes.", random.randint(1200, 8000)])
        self.d["feed"] = self.d["feed"][:8]
        self.save()


class CabinetView(BoxLayout):
    def __init__(self, game, **kwargs):
        super().__init__(orientation="vertical", padding=dp(7), spacing=dp(6), **kwargs)
        self.game = game
        with self.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(0.02, 0.07, 0.10, 1)
            self.top_glow = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        self._build()

    def _sync_bg(self, *_):
        self.bg.pos, self.bg.size = self.pos, self.size
        self.top_glow.pos = (self.x, self.y + self.height * 0.72)
        self.top_glow.size = (self.width, self.height * 0.28)

    def _build(self):
        header = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        brand = safe_label("PRESIDENTE SIMULATOR  |  CENTRO DE COMANDO", font_size=dp(14), bold=True)
        self.date_label = safe_label("", color=CYAN, font_size=dp(10), bold=True, size_hint_x=0.28, halign="right")
        header.add_widget(brand)
        header.add_widget(self.date_label)
        self.add_widget(header)

        body = BoxLayout(spacing=dp(7))
        self.add_widget(body)

        left = Panel(orientation="vertical", padding=dp(8), spacing=dp(6), size_hint_x=0.20)
        left.add_widget(safe_label("CENTRO EXECUTIVO", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(28)))
        left.add_widget(safe_label("Acesso rapido as principais areas do governo.", color=MUTED, font_size=dp(8), size_hint_y=None, height=dp(42)))
        for text, target in [
            ("LEIS E CONGRESSO", "politics"),
            ("ECONOMIA NACIONAL", "economy"),
            ("DIPLOMACIA", "diplomacy"),
            ("FORCAS ARMADAS", "military"),
            ("MIDIA E IMPRENSA", "media"),
            ("MAPA ESTRATEGICO", "map"),
        ]:
            b = ActionButton(text=text, size_hint_y=None, height=dp(39))
            b.bind(on_release=lambda _btn, s=target: self.game.show_screen(s))
            left.add_widget(b)
        left.add_widget(Widget())
        save = ActionButton(text="SALVAR PARTIDA", size_hint_y=None, height=dp(39))
        save.bind(on_release=lambda *_: self.game.save_game())
        left.add_widget(save)
        body.add_widget(left)

        center = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_x=0.54)
        situation = Panel(orientation="vertical", padding=dp(9), spacing=dp(5), size_hint_y=0.55)
        top = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        top.add_widget(safe_label("SALA DE SITUACAO  /  TELEJORNAL", color=CYAN, font_size=dp(10), bold=True))
        self.alert_label = safe_label("AO VIVO", color=DANGER, font_size=dp(9), bold=True, size_hint_x=0.22, halign="right")
        top.add_widget(self.alert_label)
        situation.add_widget(top)
        self.tv_headline = safe_label("", font_size=dp(20), bold=True, halign="center", color=TEXT)
        self.tv_news = safe_label("", font_size=dp(10), halign="center", color=MUTED)
        situation.add_widget(self.tv_headline)
        situation.add_widget(self.tv_news)
        ticker = Panel(orientation="horizontal", padding=dp(6), size_hint_y=None, height=dp(32), bg=(0.05, 0.09, 0.12, 1))
        self.ticker_label = safe_label("", color=WARN, font_size=dp(8), bold=True, halign="center")
        ticker.add_widget(self.ticker_label)
        situation.add_widget(ticker)
        center.add_widget(situation)

        desk = Panel(orientation="vertical", padding=dp(8), spacing=dp(6), size_hint_y=0.45)
        desk.add_widget(safe_label("MESA PRESIDENCIAL", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(26)))
        grid = GridLayout(cols=3, spacing=dp(6))
        actions = [
            ("TELEFONE DE CRISE", lambda *_: self.game.show_message("Telefone de crise", "Nenhuma chamada urgente no momento.")),
            ("PASTAS DE LEIS", lambda *_: self.game.show_screen("politics")),
            ("MAPA MUNDIAL", lambda *_: self.game.show_screen("map")),
            ("COLETIVA", lambda *_: self.game.press_conference()),
            ("DIPLOMACIA", lambda *_: self.game.show_screen("diplomacy")),
            ("MIDIA", lambda *_: self.game.show_screen("media")),
        ]
        for text, callback in actions:
            b = ActionButton(text=text)
            b.bind(on_release=callback)
            grid.add_widget(b)
        desk.add_widget(grid)
        center.add_widget(desk)
        body.add_widget(center)

        right = Panel(orientation="vertical", padding=dp(7), spacing=dp(5), size_hint_x=0.26)
        right.add_widget(safe_label("INDICADORES NACIONAIS", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(28)))
        self.stats = GridLayout(cols=2, spacing=dp(5))
        right.add_widget(self.stats)
        body.add_widget(right)

        nav = GridLayout(cols=6, size_hint_y=None, height=dp(44), spacing=dp(5))
        for text, screen in [
            ("GOVERNO", "cabinet"),
            ("ECONOMIA", "economy"),
            ("POLITICA", "politics"),
            ("MILITAR", "military"),
            ("DIPLOMACIA", "diplomacy"),
            ("MIDIA", "media"),
        ]:
            b = ActionButton(text=text, font_size=dp(8))
            b.bind(on_release=lambda _btn, s=screen: self.game.show_screen(s))
            nav.add_widget(b)
        self.add_widget(nav)
        self.refresh()

    def refresh(self):
        d = self.game.state.d
        self.date_label.text = f"DATA  {d['day']}"
        self.tv_headline.text = d["headline"]
        self.tv_news.text = d["last_news"]
        self.ticker_label.text = f"APROVACAO {d['approval']:.0f}%   |   INFLACAO {d['inflation']:.1f}%   |   CONGRESSO {d['congress']:.0f}%"
        self.stats.clear_widgets()
        values = [
            ("Aprovacao", f"{d['approval']:.0f}%", "popular", GOOD if d["approval"] >= 50 else DANGER),
            ("PIB", fmt_money(d["gdp"]), f"{d['gdp_growth']:+.1f}%", CYAN),
            ("Inflacao", f"{d['inflation']:.1f}%", "precos", WARN if d["inflation"] > 6 else GOOD),
            ("Desemprego", f"{d['unemployment']:.1f}%", "trabalho", CYAN),
            ("Congresso", f"{d['congress']:.0f}%", "apoio", GOOD if d["congress"] >= 50 else WARN),
            ("Impeachment", f"{d['impeachment_risk']:.0f}%", "risco", DANGER if d["impeachment_risk"] >= 40 else WARN),
        ]
        for title, value, subtitle, accent in values:
            self.stats.add_widget(StatTile(title, value, subtitle, accent=accent))


class ScreenBase(BoxLayout):
    def __init__(self, game, title, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(7), **kwargs)
        self.game = game
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        head = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(7))
        head.add_widget(safe_label(title, color=CYAN, font_size=dp(15), bold=True))
        back = ActionButton(text="VOLTAR AO GABINETE", size_hint_x=0.24)
        back.bind(on_release=lambda *_: self.game.show_screen("cabinet"))
        head.add_widget(back)
        self.add_widget(head)

    def _sync_bg(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size


class EconomyView(ScreenBase):
    def __init__(self, game, **kwargs):
        super().__init__(game, "ECONOMIA NACIONAL", **kwargs)
        self.grid = GridLayout(cols=4, spacing=dp(6), size_hint_y=0.62)
        self.add_widget(self.grid)
        actions = Panel(orientation="vertical", padding=dp(8), spacing=dp(6), size_hint_y=0.38)
        actions.add_widget(safe_label("DECISOES ECONOMICAS", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(26)))
        button_grid = GridLayout(cols=4, spacing=dp(6))
        for text, cb in [
            ("IMPOSTO -1", lambda *_: self.change("tax_rate", -1, "Impostos reduzidos.")),
            ("IMPOSTO +1", lambda *_: self.change("tax_rate", 1, "Impostos aumentados.")),
            ("JUROS -0,5", lambda *_: self.change("interest_rate", -0.5, "Pressao por juros menores.")),
            ("GASTO SOCIAL +1", lambda *_: self.change("social_spending", 1, "Gasto social ampliado.")),
        ]:
            b = ActionButton(text=text)
            b.bind(on_release=cb)
            button_grid.add_widget(b)
        actions.add_widget(button_grid)
        self.add_widget(actions)
        self.refresh()

    def change(self, key, amount, news):
        d = self.game.state.d
        d[key] += amount
        if key == "tax_rate":
            d["treasury"] -= amount * 1.2
            d["approval"] += -amount * 0.5
        elif key == "interest_rate":
            d["inflation"] += amount * 0.15
            d["gdp_growth"] -= amount * 0.2
        elif key == "social_spending":
            d["treasury"] -= amount
            d["approval"] += amount * 0.6
            d["debt_ratio"] += amount * 0.15
        d["approval"] = clamp(d["approval"])
        d["last_news"] = news
        d["headline"] = news.upper()
        self.game.state.save()
        self.game.refresh_all()

    def refresh(self):
        self.grid.clear_widgets()
        d = self.game.state.d
        stats = [
            ("PIB", fmt_money(d["gdp"]), f"crescimento {d['gdp_growth']:+.1f}%"),
            ("Inflacao", f"{d['inflation']:.1f}%", "nivel de precos"),
            ("Desemprego", f"{d['unemployment']:.1f}%", "mercado de trabalho"),
            ("Divida/PIB", f"{d['debt_ratio']:.1f}%", "fiscal"),
            ("Juros", f"{d['interest_rate']:.1f}%", "taxa basica"),
            ("Impostos", f"{d['tax_rate']:.1f}%", "carga tributaria"),
            ("Tesouro", f"{d['treasury']:.1f}", "reserva relativa"),
            ("Gasto social", f"{d['social_spending']:.1f}", "indice"),
        ]
        for title, value, subtitle in stats:
            self.grid.add_widget(StatTile(title, value, subtitle))


class PoliticsView(ScreenBase):
    def __init__(self, game, **kwargs):
        super().__init__(game, "POLITICA E GOVERNO", **kwargs)
        body = BoxLayout(spacing=dp(7))
        self.info = Panel(orientation="vertical", padding=dp(10), spacing=dp(5), size_hint_x=0.42)
        self.info_label = safe_label("", font_size=dp(11), color=TEXT, valign="top")
        self.info.add_widget(self.info_label)
        body.add_widget(self.info)

        laws = Panel(orientation="vertical", padding=dp(8), spacing=dp(6), size_hint_x=0.58)
        laws.add_widget(safe_label("PROJETOS DE LEI", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(28)))
        for title, effect in [
            ("REFORMA TRIBUTARIA", {"congress": -2, "approval": -1}),
            ("EXPANSAO DA SAUDE PUBLICA", {"congress": 1, "approval": 2, "debt_ratio": 0.8}),
            ("PLANO NACIONAL DE EDUCACAO", {"congress": 0.5, "approval": 1.5, "debt_ratio": 0.5}),
            ("LEI DE SEGURANCA NACIONAL", {"congress": -1, "approval": -1, "stability": 1}),
        ]:
            b = ActionButton(text=title, size_hint_y=None, height=dp(48))
            b.bind(on_release=lambda _btn, e=effect, t=title: self.pass_law(t, e))
            laws.add_widget(b)
        laws.add_widget(Widget())
        body.add_widget(laws)
        self.add_widget(body)
        self.refresh()

    def pass_law(self, title, effect):
        d = self.game.state.d
        if d["congress"] < 40:
            self.game.show_message("Lei rejeitada", "O apoio parlamentar e insuficiente para aprovar esta proposta.")
            return
        for key, value in effect.items():
            d[key] += value
            if key in ("approval", "congress", "stability"):
                d[key] = clamp(d[key])
        d["last_news"] = f"{title} foi aprovado pelo Congresso."
        d["headline"] = "CONGRESSO APROVA NOVA LEI"
        self.game.state.save()
        self.game.refresh_all()

    def refresh(self):
        d = self.game.state.d
        self.info_label.text = (
            f"APOIO NO CONGRESSO:  {d['congress']:.0f}%\n\n"
            f"APROVACAO:  {d['approval']:.0f}%\n\n"
            f"ESTABILIDADE:  {d['stability']:.0f}%\n\n"
            f"RISCO DE IMPEACHMENT:  {d['impeachment_risk']:.0f}%\n\n"
            "Projetos de lei dependem de apoio parlamentar. "
            "As decisoes alteram indicadores e podem gerar novas crises."
        )


class DiplomacyView(ScreenBase):
    def __init__(self, game, **kwargs):
        super().__init__(game, "DIPLOMACIA E RELACOES EXTERIORES", **kwargs)
        scroll = ScrollView(do_scroll_x=False)
        self.list_box = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, padding=(0, 0, 0, dp(8)))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        self.add_widget(scroll)
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        for name, country in self.game.state.d["countries"].items():
            if name == "Brasil":
                continue
            row = Panel(orientation="horizontal", size_hint_y=None, height=dp(72), padding=dp(7), spacing=dp(6))
            row.add_widget(safe_label(f"{name}\nRelacao: {country['relation']:+d}   Poder: {country['power']}/100", font_size=dp(9)))
            button = ActionButton(text="NEGOCIAR", size_hint_x=0.33)
            button.bind(on_release=lambda _btn, n=name: self.negotiate(n))
            row.add_widget(button)
            self.list_box.add_widget(row)

    def negotiate(self, name):
        country = self.game.state.d["countries"][name]
        country["relation"] = int(clamp(country["relation"] + random.randint(2, 6), -100, 100))
        self.game.state.d["approval"] = clamp(self.game.state.d["approval"] + 0.2)
        self.game.state.d["last_news"] = f"Negociacao diplomatica avancou com {name}."
        self.game.state.d["headline"] = f"BRASIL AVANCA EM NEGOCIACOES COM {name.upper()}"
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
            Line(points=[self.x + self.width * .25, self.y + self.height * .44,
                         self.x + self.width * .49, self.y + self.height * .62,
                         self.x + self.width * .72, self.y + self.height * .56], width=1.2)
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
            button = ActionButton(text=name.upper(), size_hint=(None, None), size=(dp(105), dp(34)))
            button.map_pos = (px, py)
            button.bind(on_release=lambda _btn, n=name: self.select_country(n))
            self.add_widget(button)
            self.country_buttons.append(button)
        self._position_buttons()

    def _position_buttons(self):
        for button in self.country_buttons:
            px, py = button.map_pos
            button.pos = (self.x + self.width * px, self.y + self.height * py)

    def select_country(self, name):
        country = self.game.state.d["countries"].get(name)
        if country:
            self.game.show_message(name, f"Relacao diplomatica: {country['relation']:+d}\nPoder: {country['power']}/100\nPIB: US$ {country['gdp']:.2f} tri")


class MapView(ScreenBase):
    def __init__(self, game, **kwargs):
        super().__init__(game, "MAPA ESTRATEGICO MUNDIAL", **kwargs)
        self.add_widget(WorldMap(game))


class MediaView(ScreenBase):
    def __init__(self, game, **kwargs):
        super().__init__(game, "MIDIA E IMPRENSA", **kwargs)
        main = BoxLayout(spacing=dp(7))
        left = Panel(orientation="vertical", padding=dp(8), spacing=dp(5), size_hint_x=0.42)
        left.add_widget(safe_label("CAPA DO DIA", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(26)))
        self.headline = safe_label("", font_size=dp(18), bold=True, halign="center")
        self.news = safe_label("", font_size=dp(10), color=MUTED, halign="center")
        left.add_widget(self.headline)
        left.add_widget(self.news)
        press = ActionButton(text="CONVOCAR COLETIVA DE IMPRENSA", size_hint_y=None, height=dp(48))
        press.bind(on_release=lambda *_: self.game.press_conference())
        left.add_widget(press)
        main.add_widget(left)

        right = Panel(orientation="vertical", padding=dp(7), spacing=dp(5), size_hint_x=0.58)
        right.add_widget(safe_label("REDE SOCIAL / REPERCUSSAO", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(26)))
        scroll = ScrollView(do_scroll_x=False)
        self.feed_box = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.feed_box.bind(minimum_height=self.feed_box.setter("height"))
        scroll.add_widget(self.feed_box)
        right.add_widget(scroll)
        main.add_widget(right)
        self.add_widget(main)
        self.refresh()

    def refresh(self):
        d = self.game.state.d
        self.headline.text = d["headline"]
        self.news.text = d["last_news"]
        self.feed_box.clear_widgets()
        for name, text, likes in d["feed"]:
            row = Panel(orientation="vertical", size_hint_y=None, height=dp(68), padding=dp(6), spacing=dp(1), bg=PANEL_ALT)
            row.add_widget(safe_label(f"@{str(name).replace(' ', '').lower()}", color=CYAN, font_size=dp(8), bold=True))
            row.add_widget(safe_label(str(text), font_size=dp(9)))
            row.add_widget(safe_label(f"Curtidas: {int(likes):,}".replace(",", "."), color=MUTED, font_size=dp(7)))
            self.feed_box.add_widget(row)


class MilitaryView(ScreenBase):
    def __init__(self, game, **kwargs):
        super().__init__(game, "FORCAS ARMADAS", **kwargs)
        body = BoxLayout(spacing=dp(7))
        self.info = Panel(orientation="vertical", padding=dp(10), size_hint_x=0.50)
        self.info_label = safe_label("", font_size=dp(12), valign="top")
        self.info.add_widget(self.info_label)
        body.add_widget(self.info)
        actions = Panel(orientation="vertical", padding=dp(8), spacing=dp(7), size_hint_x=0.50)
        actions.add_widget(safe_label("COMANDO ESTRATEGICO", color=CYAN, font_size=dp(10), bold=True, size_hint_y=None, height=dp(28)))
        for text, change in [
            ("AUMENTAR ORCAMENTO MILITAR", 0.2),
            ("REDUZIR ORCAMENTO MILITAR", -0.2),
            ("REALIZAR EXERCICIO MILITAR", 1.0),
        ]:
            button = ActionButton(text=text, size_hint_y=None, height=dp(50))
            button.bind(on_release=lambda _btn, c=change, t=text: self.action(t, c))
            actions.add_widget(button)
        actions.add_widget(Widget())
        body.add_widget(actions)
        self.add_widget(body)
        self.refresh()

    def action(self, title, change):
        d = self.game.state.d
        d["military_budget"] = max(0.1, d["military_budget"] + change)
        if "EXERCICIO" in title:
            d["stability"] = clamp(d["stability"] + 1)
            d["approval"] = clamp(d["approval"] + 0.3)
        else:
            d["treasury"] -= change * 1.5
        d["last_news"] = title.title() + "."
        d["headline"] = "GOVERNO ANUNCIA NOVA MEDIDA MILITAR"
        self.game.state.save()
        self.game.refresh_all()

    def refresh(self):
        d = self.game.state.d
        self.info_label.text = (
            f"ORCAMENTO MILITAR:  {d['military_budget']:.1f}% do PIB\n\n"
            f"ESTABILIDADE NACIONAL:  {d['stability']:.0f}%\n\n"
            f"RISCO DE GOLPE:  {d['coup_risk']:.0f}%\n\n"
            "A V0.2 mantem o modelo abstrato de defesa enquanto a interface estrategica e desenvolvida."
        )


class GameApp(App):
    title = APP_NAME

    def build(self):
        Window.clearcolor = BG
        self.state = GameState()
        self.state.load()
        self.views = {}

        self.root_box = BoxLayout(orientation="vertical", padding=0, spacing=0)
        self.content = BoxLayout()
        self.root_box.add_widget(self.content)

        timebar = Panel(orientation="horizontal", size_hint_y=None, height=dp(48), padding=dp(5), spacing=dp(5), bg=(0.015, 0.04, 0.06, 1), radius=0)
        for text, days in [("AVANCAR 1 DIA", 1), ("7 DIAS", 7), ("30 DIAS", 30)]:
            b = ActionButton(text=text)
            b.bind(on_release=lambda _btn, amount=days: self.advance(amount))
            timebar.add_widget(b)
        save = ActionButton(text="SALVAR")
        save.bind(on_release=lambda *_: self.save_game())
        timebar.add_widget(save)
        self.root_box.add_widget(timebar)

        self.root = self.root_box
        self.show_screen("cabinet")
        Clock.schedule_interval(self.auto_refresh, 1.0)
        return self.root

    def get_view(self, name):
        if name not in self.views:
            builders = {
                "cabinet": CabinetView,
                "economy": EconomyView,
                "politics": PoliticsView,
                "diplomacy": DiplomacyView,
                "map": MapView,
                "media": MediaView,
                "military": MilitaryView,
            }
            cls = builders.get(name, CabinetView)
            self.views[name] = cls(self)
        return self.views[name]

    def show_screen(self, name):
        self.content.clear_widgets()
        self.content.add_widget(self.get_view(name))
        self.refresh_all()

    def refresh_all(self):
        for view in self.views.values():
            if hasattr(view, "refresh"):
                view.refresh()

    def auto_refresh(self, _dt):
        self.refresh_all()
        if self.state.d.get("event"):
            self.show_event_if_needed()

    def advance(self, days):
        if self.state.d.get("event"):
            self.show_event_if_needed()
            return
        self.state.advance_day(days)
        self.refresh_all()
        self.show_event_if_needed()

    def show_event_if_needed(self):
        event = self.state.d.get("event")
        if not event:
            return
        self.state.d["event"] = None
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(safe_label(event["title"].upper(), color=WARN, font_size=dp(17), bold=True, halign="center"))
        box.add_widget(safe_label(event["text"], font_size=dp(11), halign="center"))
        choices = GridLayout(cols=1, spacing=dp(7))
        popup = Popup(title="EVENTO NACIONAL", content=box, size_hint=(0.78, 0.74), auto_dismiss=False)
        for title, changes in event["choices"]:
            b = ActionButton(text=title, size_hint_y=None, height=dp(48))
            b.bind(on_release=lambda _btn, ch=changes: self.finish_event(popup, ch))
            choices.add_widget(b)
        box.add_widget(choices)
        popup.open()

    def finish_event(self, popup, changes):
        self.state.apply_choice(changes)
        popup.dismiss()
        self.refresh_all()

    def press_conference(self):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        box.add_widget(safe_label("Jornalista: A inflacao esta subindo. O governo perdeu o controle?", font_size=dp(11), halign="center"))
        popup = Popup(title="COLETIVA DE IMPRENSA", content=box, size_hint=(0.82, 0.82), auto_dismiss=False)
        options = [
            ("Nao ha motivo para preocupacao.", {"approval": -1.2, "inflation": 0.1}),
            ("Estamos trabalhando para resolver.", {"approval": 0.5}),
            ("A situacao e seria e assumimos responsabilidade.", {"approval": 1.5, "congress": 0.5}),
            ("A imprensa esta exagerando.", {"approval": -1.5, "stability": -0.5}),
        ]
        for text, changes in options:
            b = ActionButton(text=text, size_hint_y=None, height=dp(48))
            b.bind(on_release=lambda _btn, ch=changes: self.finish_press(popup, ch))
            box.add_widget(b)
        popup.open()

    def finish_press(self, popup, changes):
        for key, value in changes.items():
            self.state.d[key] += value
            if key in ("approval", "congress", "stability"):
                self.state.d[key] = clamp(self.state.d[key])
        self.state.d["headline"] = "PRESIDENTE FALA EM COLETIVA"
        self.state.d["last_news"] = "Mercado e populacao repercutem a declaracao presidencial."
        self.state.d["feed"].insert(0, ["Reporter", "A coletiva presidencial gera forte repercussao.", random.randint(2000, 15000)])
        self.state.d["feed"] = self.state.d["feed"][:8]
        self.state.save()
        popup.dismiss()
        self.refresh_all()

    def save_game(self):
        self.state.save()
        self.show_message("Partida salva", "O estado atual foi salvo no armazenamento do aplicativo.")

    def show_message(self, title, message):
        content = safe_label(message, font_size=dp(11), halign="center")
        Popup(title=title, content=content, size_hint=(0.72, 0.38)).open()
