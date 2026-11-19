#!/usr/bin/env python3
"""The World Today - 19 November 2026. One dense 1024x1024 news image.

Pure stdlib Python, deterministic, no network. 2x supersampling with true
device-space rasterisation: all geometry is computed at 2048x2048 and
averaged down to 1024x1024. Small text uses a 5x7 bitmap font, display
text a hand-built 12x16 stroke font. Two runs are byte-identical.
Run: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into MAKEFUN_OUTPUT_DIR (or /output, or ./out).
"""
import os
import struct
import sys
import zlib

SS = 2
LW, LH = 1024, 1024
DW, DH = LW * SS, LH * SS

NAVY = (13, 27, 46)
NAVY2 = (18, 38, 62)
CARD = (24, 48, 76)
CARD2 = (30, 58, 90)
INK = (235, 240, 246)
MUT = (168, 186, 205)
ACC = (255, 196, 66)
ACC2 = (86, 199, 255)
RED = (255, 107, 97)
GRN = (96, 214, 149)
LINE = (58, 92, 128)
MAPLAND = (46, 98, 88)
MAPSEA = (16, 42, 68)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '1' = ink.
F5 = {}
def _g(ch, rows):
    F5[ch] = rows
_g('A', ["01110","10001","10001","11111","10001","10001","10001"])
_g('B', ["11110","10001","10001","11110","10001","10001","11110"])
_g('C', ["01110","10001","10000","10000","10000","10001","01110"])
_g('D', ["11110","10001","10001","10001","10001","10001","11110"])
_g('E', ["11111","10000","10000","11110","10000","10000","11111"])
_g('F', ["11111","10000","10000","11110","10000","10000","10000"])
_g('G', ["01110","10001","10000","10111","10001","10001","01111"])
_g('H', ["10001","10001","10001","11111","10001","10001","10001"])
_g('I', ["01110","00100","00100","00100","00100","00100","01110"])
_g('J', ["00111","00010","00010","00010","00010","10010","01100"])
_g('K', ["10001","10010","10100","11000","10100","10010","10001"])
_g('L', ["10000","10000","10000","10000","10000","10000","11111"])
_g('M', ["10001","11011","10101","10101","10001","10001","10001"])
_g('N', ["10001","11001","10101","10011","10001","10001","10001"])
_g('O', ["01110","10001","10001","10001","10001","10001","01110"])
_g('P', ["11110","10001","10001","11110","10000","10000","10000"])
_g('Q', ["01110","10001","10001","10001","10101","10010","01101"])
_g('R', ["11110","10001","10001","11110","10100","10010","10001"])
_g('S', ["01111","10000","10000","01110","00001","00001","11110"])
_g('T', ["11111","00100","00100","00100","00100","00100","00100"])
_g('U', ["10001","10001","10001","10001","10001","10001","01110"])
_g('V', ["10001","10001","10001","10001","10001","01010","00100"])
_g('W', ["10001","10001","10001","10101","10101","11011","10001"])
_g('X', ["10001","10001","01010","00100","01010","10001","10001"])
_g('Y', ["10001","10001","01010","00100","00100","00100","00100"])
_g('Z', ["11111","00001","00010","00100","01000","10000","11111"])
_g('0', ["01110","10001","10011","10101","11001","10001","01110"])
_g('1', ["00100","01100","00100","00100","00100","00100","01110"])
_g('2', ["01110","10001","00001","00110","01000","10000","11111"])
_g('3', ["11111","00010","00100","00010","00001","10001","01110"])
_g('4', ["00010","00110","01010","10010","11111","00010","00010"])
_g('5', ["11111","10000","11110","00001","00001","10001","01110"])
_g('6', ["00110","01000","10000","11110","10001","10001","01110"])
_g('7', ["11111","00001","00010","00100","01000","01000","01000"])
_g('8', ["01110","10001","10001","01110","10001","10001","01110"])
_g('9', ["01110","10001","10001","01111","00001","00010","01100"])
_g(' ', ["00000","00000","00000","00000","00000","00000","00000"])
_g('.', ["00000","00000","00000","00000","00000","01100","01100"])
_g(',', ["00000","00000","00000","00000","01100","00100","01000"])
_g(':', ["00000","01100","01100","00000","01100","01100","00000"])
_g(';', ["00000","01100","01100","00000","01100","00100","01000"])
_g('-', ["00000","00000","00000","01110","00000","00000","00000"])
_g("'", ["00100","00100","01000","00000","00000","00000","00000"])
_g('/', ["00001","00010","00010","00100","01000","01000","10000"])
_g('(', ["00010","00100","01000","01000","01000","00100","00010"])
_g(')', ["01000","00100","00010","00010","00010","00100","01000"])
_g('%', ["10001","10010","00100","01000","01001","10001","10001"])
_g('+', ["00000","00100","00100","11111","00100","00100","00000"])
_g('=', ["00000","00000","11111","00000","11111","00000","00000"])
_g('?', ["01110","10001","00001","00110","00100","00000","00100"])
_g('!', ["00100","00100","00100","00100","00100","00000","00100"])
_g('&', ["01100","10010","10100","01000","10101","10010","01101"])
_g('$', ["00100","01111","10100","01110","00101","11110","00100"])
_g('#', ["01010","01010","11111","01010","11111","01010","01010"])
_g('*', ["00000","00100","10101","01110","10101","00100","00000"])
_g('_', ["00000","00000","00000","00000","00000","00000","11111"])
_g('>', ["10000","01000","00100","00010","00100","01000","10000"])
_g('<', ["00001","00010","00100","01000","00100","00010","00001"])
_g('\u2022', ["00000","00000","01100","01100","01100","00000","00000"])
_g('"', ["01010","01010","00000","00000","00000","00000","00000"])
_g('[', ["01110","01000","01000","01000","01000","01000","01110"])
_g(']', ["01110","00010","00010","00010","00010","00010","01110"])

def text5_width(s, adv=6):
    return max(0, len(s) * adv - 1)

def wrap5(s, max_chars):
    words = s.split(' ')
    lines, cur = [], ''
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur += ' ' + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ------------------------------------------------------- 12x16 stroke font
# Strokes in a 12 wide x 16 tall grid; each glyph = list of polylines.
S16 = {}
def _s(ch, strokes):
    S16[ch] = strokes
_s('A', [[(1,15),(6,1),(11,15)],[(4,10),(8,10)]])
_s('B', [[(1,1),(1,15)],[(1,1),(8,1),(10,3),(10,6),(8,8),(1,8)],[(1,8),(8,8),(10,10),(10,13),(8,15),(1,15)]])
_s('C', [[(10,3),(8,1),(4,1),(2,3),(1,8),(2,13),(4,15),(8,15),(10,13)]])
_s('D', [[(1,1),(1,15)],[(1,1),(8,1),(11,4),(11,12),(8,15),(1,15)]])
_s('E', [[(1,1),(1,15)],[(1,1),(10,1)],[(1,8),(8,8)],[(1,15),(10,15)]])
_s('F', [[(1,1),(1,15)],[(1,1),(10,1)],[(1,8),(8,8)]])
_s('G', [[(10,3),(8,1),(4,1),(2,3),(1,8),(2,13),(4,15),(8,15),(10,13),(10,9),(6,9)]])
_s('H', [[(1,1),(1,15)],[(11,1),(11,15)],[(1,8),(11,8)]])
_s('I', [[(4,1),(8,1)],[(6,1),(6,15)],[(4,15),(8,15)]])
_s('J', [[(11,1),(11,12),(9,15),(5,15),(3,13)]])
_s('K', [[(1,1),(1,15)],[(10,1),(1,8)],[(3,7),(11,15)]])
_s('L', [[(1,1),(1,15)],[(1,15),(10,15)]])
_s('M', [[(1,15),(1,1),(6,9),(11,1),(11,15)]])
_s('N', [[(1,15),(1,1),(11,15),(11,1)]])
_s('O', [[(4,1),(8,1),(11,4),(11,12),(8,15),(4,15),(1,12),(1,4),(4,1)]])
_s('P', [[(1,1),(1,15)],[(1,1),(8,1),(11,4),(11,6),(8,9),(1,9)]])
_s('Q', [[(4,1),(8,1),(11,4),(11,12),(8,15),(4,15),(1,12),(1,4),(4,1)],[(7,11),(11,15)]])
_s('R', [[(1,1),(1,15)],[(1,1),(8,1),(11,4),(11,6),(8,9),(1,9)],[(4,9),(11,15)]])
_s('S', [[(10,3),(8,1),(4,1),(2,3),(1,5),(3,8),(9,8),(11,10),(10,13),(8,15),(4,15),(2,13)]])
_s('T', [[(1,1),(11,1)],[(6,1),(6,15)]])
_s('U', [[(1,1),(1,12),(3,15),(8,15),(11,12),(11,1)]])
_s('V', [[(1,1),(6,15),(11,1)]])
_s('W', [[(1,1),(3,15),(6,8),(9,15),(11,1)]])
_s('X', [[(1,1),(11,15)],[(11,1),(1,15)]])
_s('Y', [[(1,1),(6,8)],[(11,1),(6,8)],[(6,8),(6,15)]])
_s('Z', [[(1,1),(11,1),(1,15),(11,15)]])
_s('0', [[(4,1),(8,1),(11,4),(11,12),(8,15),(4,15),(1,12),(1,4),(4,1)],[(3,4),(9,12)]])
_s('1', [[(6,1),(6,15)],[(4,3),(6,1)],[(3,15),(9,15)]])
_s('2', [[(2,3),(4,1),(8,1),(10,3),(10,6),(1,15),(11,15)]])
_s('3', [[(1,1),(10,1),(10,5),(6,8),(10,11),(10,13),(8,15),(1,15)]])
_s('4', [[(9,1),(9,15)],[(1,10),(9,10)],[(9,1),(1,10)]])
_s('5', [[(10,1),(1,1),(1,8),(8,8),(10,10),(10,13),(8,15),(1,15)]])
_s('6', [[(10,3),(8,1),(4,1),(2,3),(1,8),(1,12),(3,15),(8,15),(10,13),(10,10),(8,8),(1,8)]])
_s('7', [[(1,1),(11,1),(5,15)]])
_s('8', [[(4,1),(8,1),(11,4),(11,6),(8,8),(4,8),(1,6),(1,4),(4,1)],[(4,8),(8,8),(11,11),(11,13),(8,15),(4,15),(1,13),(1,11),(4,8)]])
_s('9', [[(1,13),(1,10),(3,8),(8,8),(11,10),(11,12),(9,15),(4,15),(2,13)]])
_s(' ', [])
_s('-', [[(2,8),(10,8)]])
_s('.', [[(5,14),(7,14),(7,15),(5,15)]])
_s(':', [[(5,5),(7,5),(7,7),(5,7)],[(5,11),(7,11),(7,13),(5,13)]])
_s('/', [[(10,15),(2,1)]])
_s('\u2022', [[(5,7),(7,7),(7,9),(5,9)]])
_s("'", [[(5,1),(7,4)]])

def stroke_width(s, adv=14):
    return max(0, len(s) * adv - 2)

# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self):
        self.buf = bytearray(DW * DH * 3)
        self.fill_rect(0, 0, LW, LH, NAVY)

    def _px(self, dx, dy, col):
        if 0 <= dx < DW and 0 <= dy < DH:
            i = (dy * DW + dx) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = col

    def fill_rect(self, x, y, w, h, col):
        x0, y0 = max(0, int(x * SS)), max(0, int(y * SS))
        x1, y1 = min(DW, int((x + w) * SS)), min(DH, int((y + h) * SS))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(col) * (x1 - x0)
        for dy in range(y0, y1):
            o = (dy * DW + x0) * 3
            self.buf[o:o + len(row)] = row

    def hline(self, x, y, w, col, thick=1):
        self.fill_rect(x, y, w, thick, col)

    def vline(self, x, y, h, col, thick=1):
        self.fill_rect(x, y, thick, h, col)

    def line(self, x0, y0, x1, y1, col, thick=1):
        # Bresenham at device resolution; thick in device px.
        ax0, ay0 = int(round(x0 * SS)), int(round(y0 * SS))
        ax1, ay1 = int(round(x1 * SS)), int(round(y1 * SS))
        dx, dy = abs(ax1 - ax0), abs(ay1 - ay0)
        sx = 1 if ax0 < ax1 else -1
        sy = 1 if ay0 < ay1 else -1
        err = dx - dy
        r = max(0, thick // 2)
        while True:
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    self._px(ax0 + ox, ay0 + oy, col)
            if ax0 == ax1 and ay0 == ay1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                ax0 += sx
            if e2 < dx:
                err += dx
                ay0 += sy

    def circle(self, cx, cy, r, col, fill=True):
        cr = int(round(r * SS))
        ccx, ccy = int(round(cx * SS)), int(round(cy * SS))
        for dy in range(-cr, cr + 1):
            dx = int((cr * cr - dy * dy) ** 0.5)
            if fill:
                for xx in range(ccx - dx, ccx + dx + 1):
                    self._px(xx, ccy + dy, col)
            else:
                self._px(ccx - dx, ccy + dy, col)
                self._px(ccx + dx, ccy + dy, col)
                self._px(ccx, ccy + dy, col)

    def poly(self, pts, col, fill=True):
        dpts = [(int(round(x * SS)), int(round(y * SS))) for x, y in pts]
        if fill:
            ys = [p[1] for p in dpts]
            for y in range(max(0, min(ys)), min(DH, max(ys) + 1)):
                xs = []
                n = len(dpts)
                for i in range(n):
                    x0, y0 = dpts[i]
                    x1, y1 = dpts[(i + 1) % n]
                    if (y0 <= y < y1) or (y1 <= y < y0):
                        xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
                xs.sort()
                for k in range(0, len(xs) - 1, 2):
                    for xx in range(max(0, int(xs[k])), min(DW, int(xs[k + 1]) + 1)):
                        self._px(xx, y, col)
        else:
            for i in range(len(dpts)):
                x0, y0 = dpts[i]
                x1, y1 = dpts[(i + 1) % len(dpts)]
                self.line(x0 / SS, y0 / SS, x1 / SS, y1 / SS, col, thick=2)

    def arc(self, cx, cy, r, a0, a1, col, thick=2, steps=40):
        import math
        prev = None
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            p = (cx + r * math.cos(a), cy + r * math.sin(a))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], col, thick=thick)
            prev = p

    # -- text -------------------------------------------------------------
    def text5(self, x, y, s, col, adv=6, scale=1):
        s = s.upper()
        cx = x
        for ch in s:
            rows = F5.get(ch, F5[' '])
            for r, row in enumerate(rows):
                for c, bit in enumerate(row):
                    if bit == '1':
                        self.fill_rect(cx + c * scale, y + r * scale, scale, scale, col)
            cx += adv * scale

    def text5_center(self, x, y, w, s, col, adv=6, scale=1):
        tw = text5_width(s, adv * scale)
        self.text5(x + (w - tw) / 2, y, s, col, adv=adv, scale=scale)

    def text_stroke(self, x, y, s, col, adv=14, h=30, thick=3):
        # h = glyph height in logical px; glyph grid is 12x16.
        s = s.upper()
        cx = x
        sx = adv / 12.0
        sy = h / 16.0
        for ch in s:
            for poly in S16.get(ch, []):
                for i in range(len(poly) - 1):
                    x0 = cx + poly[i][0] * sx
                    y0 = y + poly[i][1] * sy
                    x1 = cx + poly[i + 1][0] * sx
                    y1 = y + poly[i + 1][1] * sy
                    self.line(x0, y0, x1, y1, col, thick=thick)
            cx += adv

    def text_stroke_center(self, x, y, w, s, col, adv=14, h=30, thick=3):
        tw = len(s) * adv - 2
        self.text_stroke(x + (w - tw) / 2, y, s, col, adv=adv, h=h, thick=thick)

    # -- output -----------------------------------------------------------
    def downsample_png(self):
        out = bytearray(LW * LH * 3)
        for y in range(LH):
            for x in range(LW):
                r = g = b = 0
                for dy in range(SS):
                    base = ((y * SS + dy) * DW + x * SS) * 3
                    for dx in range(SS):
                        o = base + dx * 3
                        r += self.buf[o]
                        g += self.buf[o + 1]
                        b += self.buf[o + 2]
                o = (y * LW + x) * 3
                out[o] = (r + 2) // 4
                out[o + 1] = (g + 2) // 4
                out[o + 2] = (b + 2) // 4
        raw = bytearray()
        stride = LW * 3
        for y in range(LH):
            raw.append(0)
            raw += out[y * stride:(y + 1) * stride]
        comp = zlib.compress(bytes(raw), 9)

        def chunk(typ, data):
            c = struct.pack('>I', len(data)) + typ + data
            return c + struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
        png = b'\x89PNG\r\n\x1a\n'
        png += chunk(b'IHDR', struct.pack('>IIBBBBB', LW, LH, 8, 2, 0, 0, 0))
        png += chunk(b'IDAT', comp)
        png += chunk(b'IEND', b'')
        return png

# ------------------------------------------------------------------ stories
# 14 main cards. lon/lat pins the card on the map. Illustration kind per card.
MAIN = [
    dict(n=1, region="GAMES", head="GTA VI IS OUT: 99 ON METACRITIC",
         body="Unlocks at midnight local, NZ first. 13 years after GTA V. Sensor Tower: ~17.1m copies, $1.65bn pre-launch. Take-Two +6.5%. 30fps cap.",
         lon=-80, lat=26, ill="gta"),
    dict(n=2, region="UKRAINE", head="KERCH BRIDGE HIT A THIRD TIME",
         body="Rail section struck overnight; traffic halted. Road span fell 17 Nov, a 227m section into the strait, blocking shipping.",
         lon=36, lat=45, ill="kerch"),
    dict(n=3, region="GULF", head="HORMUZ: TANKER STRUCK, 1 MISSING",
         body="ADNOC tanker Navig8 Messi hit near Khasab: 1 missing, 11 hurt, fire out. Iran claims 3 tankers hit mines - not verified. Traffic ~7%.",
         lon=56, lat=26, ill="hormuz"),
    dict(n=4, region="ASIA", head="BANGLADESH LOCKDOWN, YUNUS HOME TORCHED",
         body="Awami League lockdown Thu as Hasina plans Dec return. Yunus home in Chattogram torched; family safe. 2 killed; 37 Grameen sites hit.",
         lon=90, lat=24, ill="house"),
    dict(n=5, region="TECH", head="ANTHROPIC IPO: RECORD $81.3BN",
         body="Priced $83 a share, biggest IPO ever, beating SpaceX $75bn. About $1.5tn fully diluted. Trading starts Thu on Nasdaq as ANT. Plus $26bn private placement.",
         lon=-122, lat=38, ill="ipo"),
    dict(n=6, region="TECH", head="NVIDIA: $115.8BN QUARTER, +103%",
         body="Revenue to 25 Oct up 103% YoY; data-centre $107.6bn, profit $65.3bn. Next quarter ~$130bn. H-series chips halted to China.",
         lon=-121, lat=37, ill="chip"),
    dict(n=7, region="ASIA", head="CYCLONE AKVAN: 80,000 EVACUATED",
         body="Odisha moves 80,000+ to shelters, 74 rescue teams out, schools shut in 6 districts. IMD: landfall Fri noon near Gopalpur, winds 90-100 km/h, gusts 110.",
         lon=82, lat=17, ill="cyclone"),
    dict(n=8, region="EUROPE", head="EU PROPOSES 45BN EURO UKRAINE LOAN",
         body="European Commission plan: lend Kyiv 45bn euros, to be repaid after Russia pays reparations. UK separately to send 1,000 long-range strike drones.",
         lon=4, lat=51, ill="eu"),
    dict(n=9, region="EUROPE", head="ESTONIA TO SHUT ALL 3 RUSSIA CROSSINGS",
         body="Narva, Luhamaa and Koidula close from 1 Dec after an alleged GRU-ordered bomb and arson attempt on drone maker Threod Systems near Tallinn. Moscow denies.",
         lon=28, lat=59, ill="border"),
    dict(n=10, region="MIDDLE EAST", head="GAZA: TANKS CROSS YELLOW LINE",
         body="First ground operation since the Oct 2025 ceasefire, around Nuseirat and Bureij. At least 3 killed, families displaced. 4 nations urge aid access.",
         lon=34, lat=31, ill="tank"),
    dict(n=11, region="AMERICAS", head="US AND VENEZUELA SIGN MILITARY DEAL",
         body="Military cooperation pact restored. US State Dept publishes 53-page report on $12bn+ oil and mineral revenue, a year after US forces captured Nicolas Maduro.",
         lon=-67, lat=10, ill="oil"),
    dict(n=12, region="EUROPE", head="PRAGUE: HUGE PROTEST OVER MEDIA LAW",
         body="Hundreds of thousands march demanding press independence as parliament debates a media law. France: 4th weekend of protests, 146,000 out Sat.",
         lon=14, lat=50, ill="crowd"),
    dict(n=13, region="CULTURE", head="VAN GOGH SELLS FOR $190.4M RECORD",
         body="Chestnut trees in flower, painted 1890 in the last months of his life, sells at Sotheby's New York - a record for the artist, after a row over its Nazi history.",
         lon=-74, lat=41, ill="vangogh"),
    dict(n=14, region="SPACE", head="VOYAGER 1 REACHES ONE LIGHT-DAY",
         body="NASA: the probe is believed to have reached one light-day from Earth, ~5:16am EST Thu. First human-made object to travel that far. Confirmation due Thu.",
         lon=-118, lat=34, ill="voyager"),
]

ALSO = [
    "US-IRAN EXCHANGE: US jets hit IRGC site on Qeshm 17 Nov; Iran hit US base in Kuwait, Bahrain again 18 Nov.",
    "RUSSIA-UKRAINE DRONES FLY ON AS ABU DHABI PEACE TALKS RUN; US envoy Colby left a Kyiv defence meeting early.",
    "GERMANY: police warn of rising hybrid threats from cyberattacks.",
    "GAZA AID: Australia, Canada, Italy, UK urge Israel to allow immediate unrestricted access; flooding cited.",
    "NGO: Israel limits treatment access for 1,100 child amputees in Gaza.",
    "SAUDI ARABIA says danger has passed in three southern cities after alerts.",
    "INDIA-JAPAN 2+2 ministerial dialogue in Tokyo, 18-19 Nov.",
    "INDIA: Congress targets Modi govt over inflation, seeks white paper.",
    "US-CHINA: export controls on high-end AI accelerator chips extended 18 Nov; Microsoft in talks to sell AI services to ByteDance.",
    "TAIWAN: Liu Yunping elected House Democratic Caucus chair - first Taiwanese American in the post.",
    "LIBYA: cocaine and millions of pills seized in eastern Libya, officials say.",
    "SOMALIA accuses UAE of secretly building military bases without federal approval.",
    "FIVE EU COUNTRIES unveil a plan for a Rwanda return hub for migrants.",
    "FED MINUTES: most officials expect further rate hikes if inflation and labour develop as expected.",
    "US SENATORS warn AI-enabled cyber threats are outpacing defences.",
    "CANADA adjusts China ties, PM Carney says, aiming to clinch the right deal with the US.",
    "AUSTRALIA targets Israeli settlements with fresh sanctions; Albanese photographed with Putin at APEC.",
    "ACTOR STACY KEACH dies at 85 (Mike Hammer, 1980s CBS series).",
    "RUSSIAN arrested for spying on US defence company Palantir over Ukraine support.",
    "PENTAGON fails its financial audit for a 9th consecutive year.",
    "UK sanctions 8 Israeli settlement construction firms.",
    "COP31 ANTALYA: ministers meet in informal session Wed evening to unblock a deal.",
    "IEA: Hormuz crisis is the greatest threat ever observed to energy security.",
    "ETHIOPIA AND ERITREA mass forces along their border.",
    "EBOLA: strain-specific vaccines to be trialled in eastern DR Congo.",
    "FIJI AND TONGA declare emergencies over El Nino drought.",
    "ISOLATED AWA GROUP makes rare contact in Brazil.",
    "ARGENTINA: Milei bill to suspend primaries advances.",
    "AUSTRALIA: unemployment rises to 4.9%.",
    "ISRAEL delays E1 settlement; settler kills woman near Jericho.",
    "PEW: Muslims to outnumber Christians worldwide by 2035.",
    "SOUTH KOREA's Lee calls for renewed dialogue with Pyongyang; IAEA says North Korea expanded uranium enrichment.",
    "SANTA FE residents flee as the Parana River rises in Argentina.",
    "UGANDA landslide survivors seek justice at the UN.",
    "SPORT: Alcaraz beats Medvedev at the ATP Finals in Turin.",
]

SPORT = [
    "CHELSEA beat PSG 1-0 in the Women's Champions League.",
    "ENGLAND win ODI series in Australia; Duckett 133 in Hobart.",
    "LITTON DAS sets Test wicketkeeping record: 8 dismissals v South Africa.",
    "BANCROFT claims whole Australia team knew of 2018 ball tampering.",
    "MOROCCO reach a record 5th in the FIFA men's ranking.",
]

SOURCES = "SOURCES: BBC, REUTERS, AP, NYT, AL JAZEERA, THE HINDU, IMD, KYIV INDEPENDENT, BUSINESSWORLD, ONETURN, HORIZON, UKMTO, ADNOC, SOTHEBY'S, NASA, SEC FILINGS."

# ------------------------------------------------------------------- map
# Coastline polygons in (lon, lat), drawn from real coordinates.
N_AMERICA = [(-168,66),(-158,58),(-140,60),(-130,54),(-125,49),(-124,42),(-120,34),(-114,29),(-110,24),(-105,20),(-97,16),(-92,15),(-86,12),(-83,9),(-79,9),(-80,13),(-84,16),(-87,21),(-90,21),(-91,19),(-97,26),(-93,30),(-89,30),(-84,30),(-81,25),(-80,32),(-76,35),(-74,40),(-70,42),(-66,45),(-60,47),(-65,50),(-60,52),(-55,52),(-60,55),(-65,58),(-68,58),(-78,62),(-85,66),(-92,66),(-95,69),(-110,68),(-125,70),(-140,70),(-155,71),(-165,68),(-168,66)]
GREENLAND = [(-45,60),(-40,64),(-32,68),(-25,70),(-20,74),(-30,76),(-45,76),(-55,74),(-58,70),(-53,64),(-45,60)]
S_AMERICA = [(-79,9),(-75,11),(-72,12),(-64,11),(-60,8),(-55,6),(-52,5),(-50,0),(-44,-3),(-38,-5),(-35,-8),(-40,-20),(-48,-27),(-52,-33),(-57,-38),(-65,-41),(-68,-50),(-69,-52),(-74,-54),(-73,-45),(-73,-35),(-71,-30),(-70,-20),(-75,-15),(-79,-8),(-81,-4),(-80,1),(-79,9)]
AFRICA = [(-6,35),(-10,31),(-15,27),(-17,21),(-17,15),(-15,11),(-12,8),(-8,5),(-4,5),(0,6),(6,4),(9,4),(13,0),(12,-5),(13,-10),(12,-17),(16,-28),(20,-35),(28,-33),(32,-29),(36,-22),(40,-15),(40,-10),(42,-5),(46,-1),(51,2),(51,11),(48,11),(44,11),(40,15),(38,18),(37,22),(35,28),(32,31),(25,32),(19,33),(11,34),(10,37),(0,36),(-6,35)]
EURASIA = [(-10,36),(-9,43),(-2,44),(-1,46),(-4,48),(-1,50),(2,51),(5,53),(8,57),(10,59),(5,60),(5,62),(10,64),(12,66),(18,69),(25,71),(32,70),(40,68),(50,69),(60,69),(70,72),(80,73),(90,75),(100,77),(110,74),(120,73),(130,72),(140,72),(150,70),(158,69),(162,66),(170,66),(178,65),(178,62),(170,60),(162,60),(158,58),(156,52),(150,59),(142,55),(140,50),(135,45),(130,42),(127,40),(126,38),(122,38),(120,32),(121,28),(118,25),(112,22),(108,18),(105,10),(103,8),(100,7),(98,10),(95,16),(92,21),(90,22),(86,20),(82,17),(80,15),(77,8),(75,12),(72,20),(68,23),(66,25),(62,25),(58,25),(56,26),(54,27),(51,28),(50,30),(48,30),(44,29),(40,28),(38,25),(35,28),(34,31),(36,36),(30,36),(27,37),(23,36),(22,39),(19,42),(15,44),(12,45),(8,44),(3,43),(0,40),(-2,37),(-6,36),(-10,36)]
UK = [(-5,50),(-3,53),(-5,56),(-3,58),(-1,57),(0,53),(-1,51),(-5,50)]
AUSTRALIA = [(113,-22),(114,-30),(115,-33),(118,-35),(124,-33),(129,-32),(132,-32),(135,-35),(138,-35),(140,-38),(145,-38),(150,-37),(153,-32),(153,-27),(150,-23),(146,-19),(142,-15),(142,-11),(137,-12),(135,-15),(132,-12),(130,-13),(126,-14),(122,-17),(118,-20),(113,-22)]
NZ = [(167,-45),(170,-42),(174,-39),(177,-38),(175,-37),(172,-41),(168,-44),(167,-45)]
JAPAN = [(130,31),(132,33),(135,34),(138,35),(140,38),(141,41),(143,43),(145,44),(142,44),(140,40),(138,37),(135,35),(132,33),(130,31)]
MADAGASCAR = [(44,-16),(47,-15),(50,-16),(49,-20),(47,-24),(44,-25),(43,-21),(44,-16)]
INDONESIA = [(95,5),(98,3),(100,0),(103,-2),(106,-6),(110,-7),(114,-8),(118,-9),(120,-10),(124,-10),(128,-8),(130,-4),(132,-2),(131,1),(128,1),(124,0),(120,0),(116,1),(112,2),(108,3),(104,2),(100,5),(95,5)]
LAND = [N_AMERICA, GREENLAND, S_AMERICA, AFRICA, EURASIA, UK, AUSTRALIA, NZ, JAPAN, MADAGASCAR, INDONESIA]

# ------------------------------------------------------------- illustrations
def draw_ill(cv, kind, x, y, w, h):
    """One small original drawing at the top of a card, in (x,y,w,h)."""
    cx, cy = x + w / 2, y + h / 2
    if kind == "gta":
        for i, bh in enumerate((14, 26, 20, 30, 16)):
            bx = x + 8 + i * 16
            cv.fill_rect(bx, y + h - 18 - bh, 12, bh, ACC2)
            for wy in range(3):
                cv.fill_rect(bx + 3, y + h - 14 - bh + wy * 6, 3, 3, ACC)
        cv.circle(cx + 34, y + 12, 5, INK)
        cv.fill_rect(x + 8, y + h - 6, w - 16, 2, MUT)
        cv.fill_rect(cx - 26, y + h - 34, 52, 14, CARD2)
        cv.fill_rect(cx - 18, y + h - 30, 8, 6, GRN)
        cv.fill_rect(cx + 6, y + h - 30, 8, 6, RED)
    elif kind == "kerch":
        cv.line(x + 6, cy + 6, x + w - 6, cy + 6, INK, thick=4)
        cv.line(x + 14, cy + 6, x + 14, cy - 16, INK, thick=3)
        cv.line(x + w - 20, cy + 6, x + w - 20, cy - 16, INK, thick=3)
        cv.line(cx - 14, cy + 6, cx + 4, cy + 22, RED, thick=4)
        cv.circle(cx - 2, cy - 2, 4, ACC)
        cv.circle(cx + 6, cy - 8, 3, ACC2)
        cv.circle(cx + 12, cy - 14, 2, MUT)
    elif kind == "hormuz":
        cv.fill_rect(x + 10, cy - 2, w - 28, 14, RED)
        cv.fill_rect(x + 26, cy - 14, 10, 12, INK)
        cv.fill_rect(x + 44, cy - 14, 6, 12, INK)
        cv.line(x + 10, cy + 12, x + w - 18, cy + 12, ACC2, thick=3)
        cv.circle(x + w - 16, cy - 12, 5, MUT, fill=False)
        for a in range(0, 360, 45):
            import math as _m
            cv.line(x + w - 16 + 5 * _m.cos(_m.radians(a)), cy - 12 + 5 * _m.sin(_m.radians(a)),
                    x + w - 16 + 8 * _m.cos(_m.radians(a)), cy - 12 + 8 * _m.sin(_m.radians(a)), MUT, thick=2)
        cv.poly([(x + 30, cy - 16), (x + 34, cy - 26), (x + 38, cy - 16)], ACC)
    elif kind == "house":
        cv.poly([(x + 12, cy + 4), (cx, cy - 16), (x + w - 12, cy + 4)], RED)
        cv.fill_rect(x + 16, cy + 4, w - 32, 18, INK)
        cv.fill_rect(cx - 5, cy + 10, 10, 12, NAVY)
        cv.poly([(x + w - 24, cy - 2), (x + w - 18, cy - 14), (x + w - 12, cy - 2)], ACC)
        cv.poly([(x + w - 30, cy - 2), (x + w - 26, cy - 10), (x + w - 20, cy - 2)], ACC2)
    elif kind == "ipo":
        for i, bh in enumerate((8, 14, 20, 28)):
            cv.fill_rect(x + 12 + i * 16, y + h - 10 - bh, 10, bh, GRN)
        cv.line(x + 10, y + h - 12, x + w - 10, y + 10, ACC, thick=4)
        cv.line(x + w - 22, y + 10, x + w - 10, y + 10, ACC, thick=4)
        cv.line(x + w - 22, y + 22, x + w - 10, y + 10, ACC, thick=4)
    elif kind == "chip":
        cv.fill_rect(cx - 16, cy - 14, 32, 28, CARD2)
        cv.fill_rect(cx - 10, cy - 8, 20, 16, GRN)
        for i in range(4):
            cv.line(cx - 16 + i * 10, cy - 20, cx - 16 + i * 10, cy - 14, ACC, thick=2)
            cv.line(cx - 16 + i * 10, cy + 14, cx - 16 + i * 10, cy + 20, ACC, thick=2)
        cv.line(x + 8, cy + 20, x + w - 8, cy + 8, ACC2, thick=3)
    elif kind == "cyclone":
        import math as _m
        for k in range(3):
            cv.arc(cx, cy, 8 + k * 7, _m.radians(k * 50), _m.radians(200 + k * 50), INK, thick=3)
        cv.circle(cx, cy, 4, RED)
        cv.line(x + 6, y + h - 8, x + w - 6, y + h - 8, ACC2, thick=3)
    elif kind == "eu":
        for i in range(12):
            import math as _m
            a = _m.radians(i * 30)
            cv.circle(cx + 20 * _m.cos(a), cy - 2 + 14 * _m.sin(a), 2, ACC)
        cv.fill_rect(cx - 12, cy - 6, 24, 12, GRN)
        cv.text5(cx - 4, cy - 4, "E", INK)
    elif kind == "border":
        for i in range(5):
            col = RED if i % 2 == 0 else INK
            cv.fill_rect(x + 10 + i * 14, cy - 8, 14, 8, col)
        cv.line(x + 16, cy, x + 16, cy + 16, INK, thick=3)
        cv.line(x + w - 16, cy, x + w - 16, cy + 16, INK, thick=3)
        cv.fill_rect(x + 10, cy + 16, w - 20, 10, NAVY)
        cv.text5(x + 14, cy + 18, "CLOSED", RED)
    elif kind == "tank":
        cv.fill_rect(x + 12, cy - 2, 44, 12, INK)
        cv.line(x + 56, cy + 2, x + w - 10, cy - 6, INK, thick=4)
        cv.fill_rect(x + 26, cy - 10, 18, 8, INK)
        cv.fill_rect(x + 14, cy + 10, 40, 6, MUT)
        for i in range(3):
            cv.fill_rect(x + w - 26 + i * 8, cy - 18, 5, 18, CARD2)
    elif kind == "oil":
        cv.line(x + 14, y + h - 8, cx, y + 8, INK, thick=4)
        cv.line(x + w - 26, y + h - 8, cx, y + 8, INK, thick=4)
        cv.line(cx, y + 8, cx, y + h - 8, INK, thick=4)
        cv.fill_rect(cx - 14, y + h - 16, 28, 10, RED)
        cv.circle(cx + 22, y + 14, 4, ACC)
    elif kind == "crowd":
        for i, ox in enumerate((-28, -10, 8, 26)):
            cv.circle(cx + ox, cy - 6, 6, ACC if i % 2 else ACC2)
            cv.fill_rect(cx + ox - 7, cy + 2, 14, 12, INK)
        cv.fill_rect(cx - 34, cy + 16, 68, 3, RED)
    elif kind == "vangogh":
        for i in range(8):
            import math as _m
            a = _m.radians(i * 45)
            cv.line(cx, cy - 2, cx + 16 * _m.cos(a), cy - 2 + 16 * _m.sin(a), ACC, thick=4)
        cv.circle(cx, cy - 2, 7, (120, 60, 20))
        cv.line(cx, cy + 6, cx, y + h - 6, GRN, thick=3)
    elif kind == "voyager":
        cv.line(cx - 18, cy + 10, cx + 18, cy - 10, INK, thick=3)
        cv.line(cx, cy, cx - 6, cy - 16, INK, thick=3)
        cv.circle(cx - 18, cy + 10, 3, ACC)
        cv.circle(cx + 18, cy - 10, 3, ACC)
        for px, py in ((x + 10, y + 8), (x + w - 12, y + 12), (x + 14, y + h - 10), (x + w - 16, y + h - 12)):
            cv.circle(px, py, 2, INK)
        cv.arc(cx, cy, 26, 3.4, 5.6, ACC2, thick=2)

# ------------------------------------------------------------------ layout
TOTAL = len(MAIN) + len(ALSO) + len(SPORT)
PIN_OFF = {5: (-16, -12), 6: (12, 8), 8: (-4, -16), 9: (14, -10), 12: (-18, 4), 13: (10, -12)}

def build():
    cv = Canvas()
    # Masthead
    cv.fill_rect(0, 0, LW, 66, NAVY2)
    cv.text_stroke_center(0, 6, LW, "THE WORLD TODAY", INK, adv=27, h=36, thick=3)
    cv.text5_center(0, 48, LW, "THURSDAY 19 NOVEMBER 2026  -  %d STORIES  -  6 CONTINENTS" % TOTAL, ACC, adv=6)
    cv.hline(0, 66, LW, ACC, thick=2)
    # Timeline strip
    cv.fill_rect(0, 68, LW, 28, CARD)
    cv.text5(10, 77, "THE DAY IN ORDER  >  GTA VI UNLOCKS IN NZ  >  KERCH HIT AGAIN  >  HORMUZ TANKER STRUCK  >  BANGLADESH LOCKDOWN  >  ANTHROPIC DEBUTS  >  AKVAN NEARS LANDFALL", MUT)
    cv.hline(0, 96, LW, LINE, thick=1)

    # Main cards: 7 x 2
    cw, ch, gap = 138, 208, 6
    for idx, st in enumerate(MAIN):
        col, row = idx % 7, idx // 7
        x = 8 + col * (cw + gap)
        y = 102 + row * (ch + gap)
        cv.fill_rect(x, y, cw, ch, CARD)
        cv.fill_rect(x, y, cw, 2, ACC if idx % 2 == 0 else ACC2)
        cv.text5(x + 6, y + 7, st["region"], ACC2)
        cv.circle(x + cw - 12, y + 12, 8, ACC)
        cv.text5(x + cw - 15, y + 9, str(st["n"]), NAVY)
        draw_ill(cv, st["ill"], x + 6, y + 24, cw - 12, 52)
        cv.hline(x + 6, y + 80, cw - 12, LINE, thick=1)
        hl = wrap5(st["head"], 21)[:3]
        yy = y + 86
        for ln in hl:
            cv.text5(x + 6, yy, ln, INK)
            yy += 9
        body = wrap5(st["body"], 21)[:9]
        yy = y + 86 + 3 * 9 + 4
        for ln in body:
            cv.text5(x + 6, yy, ln, MUT)
            yy += 9

    # World map
    my0, my1 = 530, 672
    cv.fill_rect(0, my0, LW, my1 - my0, MAPSEA)
    cv.text5(10, my0 + 4, "WORLD MAP - WHERE IT HAPPENED  (NUMBERS = MAIN CARDS 1-14)", INK)
    mx0, mx1 = 8, 1016
    mtop, mbot = my0 + 18, my1 - 4
    def proj(lon, lat):
        px = mx0 + (lon + 180) / 360.0 * (mx1 - mx0)
        py = mtop + (84 - lat) / 142.0 * (mbot - mtop)
        return px, py
    # equator + graticule
    _, eqy = proj(0, 0)
    cv.line(mx0, eqy, mx1, eqy, LINE, thick=1)
    cv.text5(mx1 - 62, eqy + 2, "EQUATOR", MUT)
    for poly in LAND:
        cv.poly([proj(lon, lat) for lon, lat in poly], MAPLAND)
    for st in MAIN:
        px, py = proj(st["lon"], st["lat"])
        ox, oy = PIN_OFF.get(st["n"], (0, -14))
        cv.circle(px + ox, py + oy, 7, ACC)
        cv.line(px, py, px + ox, py + oy, ACC, thick=2)
        cv.circle(px, py, 2, RED)
        lab = str(st["n"])
        cv.text5(px + ox - (3 if len(lab) == 1 else 6), py + oy - 3, lab, NAVY)

    # Also today
    ay = 678
    cv.text5(10, ay, "ALSO TODAY - %d MORE STORIES" % (len(ALSO) + len(SPORT)), ACC)
    cv.hline(0, ay + 12, LW, LINE, thick=1)
    items = ["\u2022 " + s for s in ALSO + SPORT]
    cols = [[], [], []]
    for i, it in enumerate(items):
        cols[i % 3].append(it)
    for ci, colitems in enumerate(cols):
        cx = 8 + ci * 336
        yy = ay + 18
        for it in colitems:
            for ln in wrap5(it, 52)[:2]:
                cv.text5(cx, yy, ln, INK)
                yy += 8
            yy += 2

    # Footer
    fy = 950
    cv.hline(0, fy, LW, ACC, thick=2)
    src = wrap5(SOURCES, 165)
    yy = fy + 6
    for ln in src:
        cv.text5(8, yy, ln, MUT)
        yy += 9
    cv.text5(8, yy + 2, "DATE CHECK - 19 NOV 2026: EVERY STORY DATED 19 NOV OR LIVE ON 19 NOV. CLAIMS LABELLED AS CLAIMS.", INK)
    cv.text5(8, yy + 12, "ORIGINAL DRAWINGS  -  STDLIB PYTHON, DETERMINISTIC, NO NETWORK  -  2X SUPER-SAMPLED", MUT)
    return cv

def main():
    cv = build()
    png = cv.downsample_png()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "entry.png")
    with open(out, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes, %d stories)" % (out, len(png), TOTAL))

if __name__ == "__main__":
    main()
