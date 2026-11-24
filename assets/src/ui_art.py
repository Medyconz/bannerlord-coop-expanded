"""Original heraldry and campaign interface graphics, drawn from vector coordinates.

Requires Pillow. All artwork, including the inscription capitals, is constructed here.
The vector surface is supersampled and each delivery size is rasterized independently.
"""
from math import sin, cos, pi, hypot
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageColor

WHITE = 255
INK = '#17252a'
BRASS = '#c89b59'
GOLD = '#f1d69c'
BONE = '#f3e8cd'


class Surface:
    """A uniform local coordinate system on a larger physical pixel surface."""

    def __init__(self, image, scale=1.0, x=0.0, y=0.0):
        self.im = image
        self.draw = ImageDraw.Draw(image)
        self.s, self.x, self.y = scale, x, y

    def local(self, x=0, y=0, scale=1):
        return Surface(self.im, self.s * scale, self.x + x * self.s, self.y + y * self.s)

    def pts(self, points):
        return [(round(self.x + x*self.s), round(self.y + y*self.s)) for x, y in points]

    def polygon(self, pts, color):
        self.draw.polygon(self.pts(pts), fill=color)

    def line(self, pts, color, width=1, rounded=True):
        points = self.pts(pts)
        w = max(1, round(self.s * width))
        self.draw.line(points, fill=color, width=w, joint='curve')
        if rounded:
            radius = (w-1)/2
            for x,y in points:
                self.draw.ellipse((round(x-radius),round(y-radius),round(x+radius),round(y+radius)),fill=color)

    def circle(self, x, y, r, color):
        self.draw.ellipse(self.pts([(x-r,y-r),(x+r,y+r)]),fill=color)

    def arc(self, x, y, rx, ry, start, end, color, width):
        pts = [(x + rx*cos(a*pi/180), y + ry*sin(a*pi/180))
               for a in [start+(end-start)*i/40 for i in range(41)]]
        self.line(pts,color,width)

    def box(self, x0,y0,x1,y1, color):
        self.draw.rectangle(self.pts([(x0,y0),(x1,y1)]), fill=color)


def curve(p0,p1,p2,p3, steps=28):
    """Samples a cubic segment. Endpoints are always included."""
    return [tuple((1-t)**3*p0[j]+3*(1-t)**2*t*p1[j]+3*(1-t)*t*t*p2[j]+t**3*p3[j]
                  for j in (0,1)) for t in [k/steps for k in range(steps+1)]]


def icon(d, key):
    w = 5.6
    def pen(*points):
        d.line(points, WHITE, w)
    def arc(x,y,rx,ry,a,b):
        d.arc(x,y,rx,ry,a,b,WHITE,w)
    def ring(x,y,r):
        arc(x,y,r,r,0,360)
    def dot(x,y,r=3):
        d.circle(x,y,r,WHITE)
    def rect(x0,y0,x1,y1,r):
        pen((x0+r,y0),(x1-r,y0))
        pen((x1,y0+r),(x1,y1-r))
        pen((x1-r,y1),(x0+r,y1))
        pen((x0,y1-r),(x0,y0+r))
        for x,y,a in [(x1-r,y0+r,270),(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180)]:
            arc(x,y,r,r,a,a+90)
    def arrow(a,b):
        x,y=b
        dx,dy = b[0]-a[0],b[1]-a[1]
        mag=hypot(dx,dy)
        dx,dy=dx/mag,dy/mag
        pen(a,b)
        pen((x-dx*11-dy*9,y-dy*11+dx*9),b,(x-dx*11+dy*9,y-dy*11-dx*9))
    if key == 'sort':
        for x1,y in [(94,28),(76,48),(57,68)]:
            pen((20,y),(x1,y))
        arrow((89,48),(89,94))
    elif key == 'filter':
        pen((17,22),(96,22),(68,57),(68,84),(48,95),(48,57),(17,22))
        pen((40,34),(73,34))
    elif key == 'compare':
        pen((15,90),(98,90))
        rect(22,51,47,89,3)
        rect(66,27,91,89,3)
        pen((17,25),(28,17),(39,25))
        pen((28,18),(28,37))
    elif key == 'sell_junk':
        pen((19,42),(59,42))
        pen((24,42),(28,86),(48,86))
        pen((30,32),(32,25),(47,25),(50,32))
        ring(75,72,22)
        pen((76,61),(83,72),(75,82),(68,72),(76,61))
    elif key in ('lock','unlock'):
        rect(24,49,89,91,8)
        if key == 'lock':
            arc(56,42,20,22,180,360)
            pen((36,42),(36,48))
            pen((76,42),(76,48))
        else:
            arc(57,38,21,20,180,345)
            pen((36,38),(36,48))
        dot(56,65,5)
        pen((56,67),(56,77))
    elif key == 'value_per_weight':
        ring(34,35,16)
        pen((33,29),(38,35),(33,42),(29,35),(33,29))
        pen((25,92),(85,21))
        arc(77,64,8,9,175,365)
        pen((61,67),(90,67),(97,92),(57,92),(61,67))
    elif key == 'upgrade_all':
        for x in (36,77):
            pen((x-15,72),(x,57),(x+15,72))
            pen((x-15,52),(x,37),(x+15,52))
        pen((21,87),(92,87))
    elif key == 'recruit_prisoners':
        ring(50,34,12)
        pen(*curve((30,80),(30,54),(61,46),(70,62)))
        pen((31,81),(49,81))
        pen((80,66),(80,94))
        pen((66,80),(94,80))
        pen((16,25),(16,66))
        pen((26,25),(26,55))
        pen((14,31),(28,31))
    elif key == 'transfer_all':
        arrow((23,39),(94,39))
        arrow((90,75),(19,75))
        pen((21,26),(21,47))
        pen((93,68),(93,88))
    elif key == 'troop_sort':
        pen((17,26),(60,26),(58,52),(39,66),(20,52),(17,26))
        pen((29,42),(38,49),(50,38))
        pen((18,81),(56,81))
        arrow((84,28),(84,85))
    elif key == 'food_days':
        pen((27,87),(66,43))
        for dx,dy in [(0,0),(14,-15)]:
            pen(*curve((39+dx,73+dy),(24+dx,72+dy),(22+dx,63+dy),(23+dx,56+dy)))
            pen(*curve((23+dx,56+dy),(35+dx,59+dy),(39+dx,66+dy),(39+dx,73+dy)))
            pen(*curve((40+dx,73+dy),(49+dx,73+dy),(59+dx,69+dy),(61+dx,62+dy)))
        pen(*curve((59,51),(55,36),(66,29),(74,27)),*curve((74,27),(76,38),(71,48),(59,51)))
        arc(83,83,10,10,0,360)
        pen((83,66),(83,63))
        pen((66,83),(63,83))
    elif key == 'wage_days':
        rect(17,29,84,89,6)
        pen((18,47),(83,47))
        for x in (34,65):
            pen((x,20),(x,36))
        # Leave the corner of the calendar behind the foreground coin.
        d.circle(79,77,22,0)
        ring(79,77,18)
        pen((79,69),(85,77),(79,85),(73,77),(79,69))
        pen((29,61),(41,61))
    elif key == 'production':
        ring(54,51,8)
        for quarter in range(4):
            def wind(x,y):
                angle = quarter*pi/2
                return (54+x*cos(angle)-y*sin(angle),51+x*sin(angle)+y*cos(angle))
            pen(*[wind(x,y) for x,y in [(5,-7),(21,-35),(31,-24),(14,-3)]])
        pen((42,72),(36,93),(74,93),(66,69))
    elif key in ('price_up','price_down'):
        ring(32,78,15)
        pen((32,72),(36,78),(32,84),(28,78),(32,72))
        if key == 'price_up':
            pen((20,49),(41,34),(57,47),(91,21))
            pen((73,20),(93,20),(91,39))
        else:
            pen((19,23),(41,37),(56,27),(92,53))
            pen((75,55),(94,55),(92,37))
    elif key == 'ledger':
        rect(25,20,88,93,5)
        pen((38,20),(38,93))
        for y in (45,58,71):
            pen((50,y),(73 if y!=71 else 65,y))
        pen((62,21),(62,34),(69,29),(76,34),(76,21))
    elif key == 'route':
        ring(28,82,9)
        ring(82,29,9)
        pen((38,82),(70,82),*curve((70,82),(89,82),(90,57),(71,57)),(45,57),
            *curve((45,57),(24,57),(25,29),(45,29)),(72,29))
    elif key == 'friend_marker':
        pts=curve((56,92),(46,80),(23,61),(23,43))+curve((23,43),(23,9),(89,9),(89,43))+curve((89,43),(89,61),(67,81),(56,92))
        pen(*pts)
        pen((56,63),*curve((56,63),(29,48),(45,33),(56,46)),*curve((56,46),(67,33),(83,48),(56,63)))
    elif key == 'ping':
        dot(55,52,6)
        for r in (22,39):
            arc(55,52,r,r,142,218)
            arc(55,52,r,r,-38,38)
        pen((48,80),(55,66),(62,80))
        pen((55,69),(55,94))
    elif key == 'party_status':
        ring(40,34,12)
        pen(*curve((18,74),(19,46),(57,44),(63,64)))
        arc(70,35,10,10,255,480)
        pen(*curve((69,53),(82,51),(94,62),(94,71)))
        pen((18,85),(39,85),(47,75),(56,94),(65,80),(91,80))
    elif key == 'ship':
        pen((16,67),(22,71),(88,71),(98,63),(83,84),(74,88),(35,88),(16,67))
        pen((55,69),(55,17),(71,21),(55,26))
        pen((45,33),*curve((45,33),(37,47),(29,55),(23,61)),(44,60),(45,33))
        pen((65,35),*curve((65,35),(78,43),(83,52),(86,60)),(65,60),(65,35))
    elif key == 'workshop':
        pen((17,48),(57,20),(96,48))
        pen((25,50),(25,89),(89,89),(89,50))
        pen((35,59),(78,59),(70,69),(59,71),(61,77),(65,80),(46,80),(50,76),(51,70),(42,68),(35,59))
    elif key == 'settings':
        pts=[]
        for i in range(8):
            for frac,r in [(0,31),(.17,31),(.27,39),(.64,39),(.74,31)]:
                a=(i+frac)*pi/4
                pts.append((56+cos(a)*r,56+sin(a)*r))
        pen(*pts,pts[0])
        ring(56,56,13)
    else:
        raise ValueError(f'Unknown icon {key!r}')


def render_icon(key, pixels):
    # Coverage is the only changing channel; translucent edge pixels retain white RGB.
    mask = Image.new('L',(pixels*4,)*2)
    icon(Surface(mask,pixels*4/112), key)
    mask = mask.resize((pixels,pixels),Image.Resampling.LANCZOS)
    result = Image.new('RGBA', mask.size, 'white')
    result.putalpha(mask)
    return result

# The inscription alphabet uses separate thick pen strokes and fine joins. Each
# character is in its own em-width, so narrow I and wide M need no font engine.
# Path records give the weight (heavy or hairline) followed by coordinate pairs.
ALPHABET = {
 'A':(74,['s 1 97 35 3','b 35 3 73 97','s 16 61 57 61']),
 'B':(69,['b 9 3 9 96','s 8 3 43 3 57 8 63 19 62 32 55 42 43 48 10 48','s 40 48 55 51 65 62 65 77 56 89 42 96 8 96','b 59 12 61 23 58 34','b 61 59 63 69 60 81']),
 'C':(72,['s 65 15 53 6 36 3 22 7 11 18 4 37 4 65 11 83 23 93 39 97 53 92 67 79','b 16 13 8 31 6 53 9 72 18 88','s 65 6 65 23']),
 'D':(74,['b 9 4 9 96','s 8 3 35 3 52 9 63 22 69 41 68 61 63 78 51 90 34 96 8 96','b 56 14 63 29 65 52 62 71 55 85']),
 'E':(65,['b 9 3 9 96','s 8 3 60 3 62 15','s 9 48 48 48','s 48 42 48 54','s 9 96 60 96 63 82']),
 'F':(63,['b 9 4 9 96','s 9 3 60 3 62 16','s 9 48 48 48','s 48 41 48 56']),
 'G':(77,['s 69 15 56 6 38 3 22 8 11 20 4 39 4 65 11 81 25 93 42 97 58 93 67 88','b 18 13 9 32 7 54 10 73 18 86','b 66 58 66 88','s 53 56 75 56']),
 'H':(78,['b 9 4 9 96','b 68 4 68 96','s 10 48 67 48']),
 'I':(20,['b 10 4 10 96']),
 'L':(64,['b 9 3 9 96','s 9 96 58 96 62 81']),
 'M':(95,['s 8 96 8 4','b 9 4 47 87','s 47 87 85 4','b 85 4 85 96']),
 'N':(78,['s 9 96 9 4','b 9 4 68 94','s 69 96 69 3']),
 'O':(79,['s 40 3 26 6 13 16 6 34 4 51 7 70 14 86 27 95 40 97 54 94 65 84 72 68 75 49 72 31 65 16 54 6 40 3','b 17 14 10 34 9 55 12 74 20 87','b 59 11 68 29 70 52 66 73 59 87']),
 'P':(70,['b 9 4 9 96','s 9 3 42 3 56 7 64 17 65 30 59 43 46 51 30 54 10 54','b 59 13 62 24 59 37']),
 'Q':(81,['o','s 40 75 56 91 72 103 84 104','b 49 83 64 97']),
 'R':(73,['p','b 37 54 66 95','s 64 93 74 97']),
 'S':(66,['s 59 15 47 6 32 3 18 7 8 18 8 29 15 39 30 47 46 54 57 64 61 75 57 87 46 94 31 97 16 93 6 84','b 9 24 13 34 26 43 41 50 51 57 58 66 59 76','s 59 8 59 23','s 6 75 6 90']),
 'T':(71,['s 4 15 6 3 65 3 68 15','b 36 4 36 96']),
 'U':(78,['b 9 4 9 62 11 76 17 87','s 10 69 13 81 20 91 32 96 45 97 57 92 65 82 69 65 69 3']),
 'V':(73,['b 2 3 38 96','s 38 96 71 3']),
 'W':(105,['b 3 3 29 96','s 29 96 54 21','b 49 3 78 96','s 78 96 102 3']),
 'X':(73,['b 4 3 67 96','s 68 3 4 96']),
 'Y':(72,['b 2 3 37 51','s 37 51 69 3','b 37 52 37 96']),
}


def inscription(d, text, x, y, height, color, tracking=11, align='center'):
    factors=[.76 if c.islower() else 1 for c in text]
    advances=[(ALPHABET[c.upper()][0] if c!=' ' else 38)*f for c,f in zip(text,factors)]
    width=(sum(advances)+(len(text)-1)*tracking)*height/100
    if align=='center':
        x -= width/2
    for c,advance,factor in zip(text,advances,factors):
        if c!=' ':
            g=d.local(x,y+height*(1-factor),height*factor/100)
            paths=ALPHABET[c.upper()][1]
            for path in paths:
                parts=ALPHABET[path.upper()][1] if path in ('o','p') else [path]
                for part in parts:
                    kind,*coords=part.split()
                    coords=list(map(float,coords))
                    ps=list(zip(coords[::2],coords[1::2]))
                    g.line(ps,color,7.5 if kind=='b' else 2.7)
                    for xx,yy in [ps[0],ps[-1]]:
                        if yy in (3,4,96,97) and kind=='b':
                            sgn=1 if yy<50 else -1
                            g.polygon([(xx-8,yy),(xx+8,yy),(xx+3,yy+sgn*3),(xx-3,yy+sgn*3)],color)
        x += (advance+tracking)*height/100
    return width


THEMES = {
 'core':('Core','#234e53','#12292f','#7b9c8e'),
 'armory':('Armory','#7d423a','#311e27','#b16651'),
 'troops':('Troops','#546440','#24332b','#a2aa70'),
 'factions':('Factions','#624768','#2c273b','#9c79a0'),
 'trade':('Trade','#846235','#3b3025','#c79c64'),
 'qol':('QoL','#435e74','#202f44','#829eaa'),
 'coophud':('CoopHUD','#426661','#19363b','#85afa1'),
}


def shield_shape(cx,top,width,height):
    def pt(x,y): return (cx+x*width,top+y*height)
    paths=[pt(-.50,.10),pt(-.25,.055),pt(0,0),pt(.25,.055),pt(.50,.10),pt(.48,.56)]
    paths+=curve(pt(.48,.56),pt(.46,.73),pt(.23,.90),pt(0,1))
    paths+=curve(pt(0,1),pt(-.23,.90),pt(-.46,.73),pt(-.48,.56))
    return paths


def star(d,x,y,r,fill):
    d.polygon([(x,y-r),(x+r*.23,y-r*.25),(x+r*.74,y),(x+r*.23,y+r*.23),
               (x,y+r),(x-r*.23,y+r*.23),(x-r*.74,y),(x-r*.23,y-r*.25)],fill)


def raven_pair(g, accent):
    """Two watchbirds face the beacon between their wings."""
    for side in (-1,1):
        def wing(ps,col):
            g.polygon([(50+side*x,y) for x,y in ps],col)
        wing([(6,33),(13,30),(17,24),(24,24),(29,30),(30,39),(34,35),(43,17),(42,35),
              (37,45),(42,40),(38,52),(31,59),(35,58),(32,65),(26,70),(27,82),
              (21,78),(17,70),(9,67),(14,62),(10,56),(13,48),(18,42),(19,36),
              (15,33)],GOLD)
        wing([(20,41),(25,32),(27,37),(25,46),(20,49)],accent)
        wing([(18,58),(33,46),(29,54),(22,59)],accent)
        wing([(20,62),(30,56),(26,62),(22,65)],accent)
        g.circle(50+side*20,28.5,1.3,INK)
        g.line([(50+side*20,70),(50+side*15,75),(50+side*9,75)],GOLD,1.7)
    g.polygon([(45,77),(47,61),(48,50),(52,50),(53,61),(55,77)],BONE)
    g.box(45,47,55,50,BRASS)
    g.polygon([(50,44),(46,41),(46,37),(50,33),(50,29),(54,35),(55,39)],GOLD)
    star(g,50,19,8,GOLD)


def device(g,key,accent):
    if key=='core':
        raven_pair(g,accent)
    elif key=='armory':
        # A crested closed helm, cut away at the eye slit.
        g.polygon([(24,28),(38,27),(41,21),(60,16),(68,17),(56,22),(71,20),(75,22),
                   (63,26),(76,26),(80,29),(66,31),(72,34),(60,35),(50,30),(39,34)],BRASS)
        g.polygon([(50,30),(61,35),(67,43),(75,48),(75,57),(63,59),(61,71),(49,78),
                   (29,68),(28,60),(34,51),(32,43),(36,35)],GOLD)
        g.polygon([(36,47),(43,37),(52,33),(46,42),(43,49)],BONE)
        g.polygon([(43,52),(71,48),(72,52),(47,58)],INK)
        g.line([(49,59),(48,72)],BRASS,2)
        for i in range(3):
            g.line([(54+i*3,61-i),(54+i*3,67-i*2)],accent,1.7)
        g.line([(32,64),(43,68)],accent,2)
        g.circle(38,53,2.3,BRASS)
    elif key=='troops':
        # Three gathered standards above a barred gateway.
        for i,(x,y) in enumerate([(27,32),(50,18),(70,33)]):
            g.line([(x,y),(x,71)],GOLD,2)
            g.polygon([(x-1.9,y),(x,y-5),(x+1.9,y)],BONE)
            g.polygon([(x+1,y+2),(x+16,y+5),(x+12,y+11),(x+15,y+16),(x+1,y+13)],GOLD if i==1 else BRASS)
        g.polygon([(20,62),(29,62),(29,67),(36,67),(36,61),(45,61),(45,67),(54,67),(54,61),
                   (63,61),(63,67),(70,67),(70,62),(79,62),(74,76),(50,86),(26,76)],GOLD)
        g.polygon([(45,81),(45,75),(50,70),(55,75),(55,81),(50,83)],accent)
    elif key=='factions':
        # A pomegranate cut open, exposing seven seeds in the shared rind.
        g.polygon([(41,34),(35,20),(44,25),(50,17),(56,25),(65,20),(59,34)],GOLD)
        rind=curve((50,31),(75,28),(86,55),(69,69))+curve((69,69),(59,79),(53,78),(50,85))+curve((50,85),(47,78),(40,78),(31,69))+curve((31,69),(14,52),(27,28),(50,31))
        g.polygon(rind,GOLD)
        g.polygon([(50,37),(61,41),(68,53),(65,65),(54,74),(49,76),(40,68),(32,57),(33,46),(40,41)],accent)
        for x,y in [(44,46),(55,46),(38,55),(49,55),(60,55),(45,64),(55,64)]:
            g.polygon([(x,y-4),(x+3,y-1),(x+2,y+3),(x,y+4),(x-3,y+1),(x-3,y-2)],GOLD)
        g.line([(33,41),(29,47),(28,53)],BONE,1.7)
    elif key=='trade':
        # Cog with a stitched square sail, on a curled wave.
        g.line([(52,21),(52,66)],BONE,2)
        g.polygon([(53,20),(68,23),(60,27),(53,27)],BRASS)
        g.line([(30,33),(75,31)],BRASS,2)
        sail=curve((34,35),(43,42),(41,55),(32,60))+curve((32,60),(48,56),(61,58),(75,55))+curve((75,55),(80,45),(75,37),(72,34))
        g.polygon(sail,GOLD)
        for x in (42,52,62):
            g.line(curve((x,36),(x+5,42),(x+5,51),(x,56)),BRASS,1)
        g.line([(30,34),(19,65),(51,28),(82,65)],BRASS,1)
        g.polygon([(16,61),(25,66),(70,66),(84,56),(82,65),(68,76),(34,77),(21,69)],GOLD)
        g.line([(31,70),(65,70),(77,65)],accent,1.6)
        g.line(curve((29,81),(41,75),(59,87),(71,79)),BONE,2)
    elif key=='qol':
        # Ornamental key bow and a deliberately stout notched bit.
        g.arc(59,39,13,13,0,360,GOLD,6)
        g.arc(59,39,7,7,0,360,BRASS,2)
        g.line([(48,49),(29,69),(35,75),(55,53)],GOLD,4)
        g.polygon([(31,64),(23,56),(20,60),(24,64),(21,67),(26,72),(30,67),(34,69)],GOLD)
        for x,y,r in [(28,34,5),(70,69,6),(40,24,3)]:
            star(g,x,y,r,BONE)
    elif key=='coophud':
        # Relay beacon with concentric signals and a crenellated tower.
        for r in (16,25):
            g.arc(50,40,r,r,-42,42,GOLD,3)
            g.arc(50,40,r,r,138,222,GOLD,3)
        g.polygon([(50,51),(43,46),(42,40),(48,33),(49,26),(57,34),(58,41),(55,47)],GOLD)
        g.polygon([(49,48),(48,43),(53,38),(53,44)],BRASS)
        g.polygon([(36,52),(64,52),(62,58),(58,60),(61,76),(66,80),(50,85),(34,80),
                   (39,76),(42,60),(38,58)],GOLD)
        g.polygon([(48,78),(48,68),(50,64),(53,68),(53,78)],accent)
        g.line([(42,58),(58,58)],BRASS,2)


def heraldry(d, cx, top, width, key):
    name,field,dark,accent=THEMES[key]
    height = width*1.13
    for dx,dy,w,h,color in [(0,0,1,1,INK),(0,2,.986,.986,BRASS),
            (0,5,.968,.966,GOLD),(0,8,.942,.943,INK),(0,11,.924,.925,field)]:
        d.polygon(shield_shape(cx+dx*width/260,top+dy*width/260,width*w,height*h),color)
    # Fine diapering follows the shield outline via an inset mask.
    unit=width/100
    area=shield_shape(cx,top+height*.061,width*.882,height*.875)
    d.line(area+[area[0]],accent,width*.004)
    def lozenge(x,y,r):
        d.line([(x,y-r),(x+r*.62,y),(x,y+r),(x-r*.62,y),(x,y-r)],accent,width*.0025)
    for row in range(5):
        for col in range(-3,4):
            if abs(col) + max(0,row-2)*.6 > 3 or (row+col)%2: continue
            lozenge(cx+col*width*.102,top+height*(.21+row*.115),width*.023)
    device(d.local(cx-width*.47,top+height*.062,width*.0094),key,dark)
    for side in (-1,1):
        for k in range(3):
            px=cx+side*width*(.36-.07*k)
            py=top+height*(.68+.065*k)
            d.line([(px-side*unit*3,py-unit*2),(px,py),(px+side*unit*.4,py-unit*4)],BRASS,unit*.62)
    star(d,cx,top+height*.867,width*.023,GOLD)

def mix(a,b,t):
    aa=ImageColor.getrgb(a) if isinstance(a,str) else a
    bb=ImageColor.getrgb(b) if isinstance(b,str) else b
    return tuple(round(v+(w-v)*t) for v,w in zip(aa,bb))


def frame(d,width,height,margin,border,bright):
    c=12
    for m in (margin,margin+5):
        pts=[(m+c,m),(width-m-c,m),(width-m,m+c),(width-m,height-m-c),
             (width-m-c,height-m),(m+c,height-m),(m,height-m-c),(m,m+c)]
        d.line(pts+[pts[0]],border,1.2)
    for x,sx in ((margin,1),(width-margin,-1)):
        for y,sy in ((margin,1),(height-margin,-1)):
            d.line([(x+sx*9,y+sy*19),(x+sx*19,y+sy*9),(x+sx*33,y+sy*9)],bright,1.5)
            d.line([(x+sx*9,y+sy*19),(x+sx*9,y+sy*32)],bright,1.5)
            star(d,x+sx*17,y+sy*17,3.3,bright)


def bough(g, side):
    """Brass olive branches, with engraved midribs and hand-shaped alternating leaves."""
    def pt(x,y): return (50+x*side,y)
    stalk=curve(pt(2,95),pt(30,91),pt(55,68),pt(54,45))
    g.line(stalk,BRASS,1)
    for k in range(8):
        t=(k+1)/10
        j=int(t*(len(stalk)-1))
        x,y=stalk[j]
        for flip in (-1,1):
            if flip==1:
                dx,dy=(6.5-3*t)*side,-2.3-3*t
            else:
                dx,dy=(-.5-3*t)*side,-7.1+1.9*t
            p=(x+dx,y+dy)
            outer=curve((x,y),(x+dx*.2+dy*.23,y+dy*.2-dx*.23),
                        (x+dx*.8+dy*.25,y+dy*.8-dx*.25),p)
            inner=curve(p,(x+dx*.7-dy*.26,y+dy*.7+dx*.26),
                        (x+dx*.25-dy*.25,y+dy*.25+dx*.25),(x,y))
            g.polygon(outer+inner,GOLD if (k+flip)%3 else BRASS)
            g.line([(x,y),(x+dx*.79,y+dy*.79)],BRASS,.30)


def seal(d,cx,cy,size):
    unit=size/120
    g=d.local(cx-50*unit,cy-51*unit,unit)
    for side in (-1,1):
        bough(g,side)
    # This is an emblem with a lightweight coronet of stars above it.
    for x,y,r in [(31,3,2.4),(41,.5,3.2),(50,-2,4.9),(59,.5,3.2),(69,3,2.4)]:
        star(g,x,y,r,GOLD)
    heraldry(g,50,7,75,'core')
    g.line([(44,97),(50,94),(56,97)],BRASS,1.1)


def background(d,w,h,key,seed):
    _,field,dark,accent=THEMES[key]
    for y in range(h):
        light=max(0,1-abs(y/h-.36)*1.65)
        color=mix(dark,field,light*.75)
        d.box(0,y,w,y+1,color)
    # Sparse flecks suggest paper and woven thread while keeping files compact.
    rng=Random(seed)
    for _ in range(w*h//65):
        x,y=rng.randrange(w),rng.randrange(h)
        local=mix(dark,field,max(0,1-abs(y/h-.36)*1.65)*.75)
        d.line([(x,y),(x+rng.uniform(.3,2.3),y-.35)],mix(local,accent,rng.uniform(.08,.18)),.55)


def landscape(d,w,h,seed,key):
    """Original line-cut coastal panorama, seeded and fitted to each panel."""
    rng=Random(seed)
    _,field,dark,accent=THEMES[key]
    g=d.local(0,h-w*.39,w/1000)
    land=mix(dark,field,.29)
    light=mix(field,accent,.36)
    far=mix(field,accent,.16)
    for base,rough,col in [(220,56,far),(252,46,mix(field,dark,.20))]:
        pts=[(-30,base)]
        while pts[-1][0]<1010:
            x=pts[-1][0]+rng.randrange(15,46)
            y=base+sin(x*.014+seed)*16+rng.uniform(-rough/2,rough/2)
            pts.append((x,y))
        g.polygon(pts+[(1030,400),(-30,400)],col)
        for (x,y),(nx,ny) in zip(pts,pts[1:]):
            if ny>y+6:
                g.line([(x,y+3),(x+8,y+10),(x+11,y+10),(x+20,y+21)],light,.65)
    # Harbor water and foreground headlands.
    g.box(0,279,1000,404,mix(field,dark,.48))
    for _ in range(170):
        x,y=rng.uniform(0,999),rng.uniform(280,391)
        length=rng.uniform(1,18)*(y-180)/100
        g.line([(x,y),(x+length,y-.7)],mix(field,accent,rng.random()*.25),rng.uniform(.4,1.35))
    def castle(cx,base,f):
        t=g.local(cx,base,f)
        t.polygon([(-113,0),(-90,-11),(-73,-13),(-47,-31),(28,-31),(53,-19),
                   (74,-16),(88,-3),(115,0)],land)
        t.box(-53,-41,48,-23,land)
        for ix in range(-51,48,9):
            t.box(ix,-45,ix+5,-39,land)
        for x,y,tw,roof in [(-52,-60,13,0),(-23,-75,12,1),(-3,-80,16,1),(27,-66,13,0),(43,-57,12,0)]:
            t.box(x,y,x+tw,-26,land)
            if roof:
                t.polygon([(x-3,y+1),(x+tw*.48,y-13),(x+tw+3,y+1)],land)
            else:
                for k in (0,.4,.8):
                    t.box(x+k*tw,y-4,x+k*tw+3,y+2,land)
            t.line([(x+2,y+4),(x+2,-38)],mix(field,accent,.09),1.1)
            for iy in (y+6,y+16):
                t.box(x+tw*.55,iy,x+tw*.55+1.7,iy+4,light)
        t.line([(-20,-86),(-20,-99)],land,1.6)
        t.polygon([(-20,-99),(-9,-97),(-20,-94)],light)
    castle(130,278,.75)
    castle(873,284,1)
    for x,y,f in [(325,307,.72),(653,319,.50),(935,354,.94)]:
        t=g.local(x,y,f)
        t.line([(0,3),(0,-40)],land,2)
        t.polygon([(-3,-37),(-20,-10),(-3,-12)],accent)
        t.polygon([(3,-32),(7,-25),(16,-8),(3,-11)],mix(field,accent,.44))
        t.polygon([(-23,-5),(19,-5),(25,-10),(19,-1),(12,3),(-13,3)],land)
        t.line([(-22,6),(18,6)],light,.7)


def module_cover(key):
    size=512
    img=Image.new('RGB',(size*2,)*2)
    d=Surface(img,2)
    name,field,dark,accent=THEMES[key]
    seed=list(THEMES).index(key)+107
    background(d,size,size,key,seed)
    landscape(d,size,size,seed,key)
    frame(d,512,512,14,mix(accent,BRASS,.3),BRASS)
    # Concentric registries with tiny divisions echo stamped manuscript seals.
    for r in (145,151):
        d.arc(256,221,r,r,0,360,mix(field,accent,.40),.95)
    for k in range(48):
        a=2*pi*k/48
        l=157 if k%4==0 else 153
        d.line([(256+150*cos(a),221+150*sin(a)),(256+l*cos(a),221+l*sin(a))],BRASS if k%4==0 else accent,1)
    heraldry(d,256,74,236,key)
    # A narrow ribbon leaves the headlands and watchtowers visible at each margin.
    spread=134 if key!='coophud' else 172
    left,right=256-spread,256+spread
    d.polygon([(left-18,387),(right+18,387),(right+12,406),(right+20,429),
               (left-20,429),(left-12,406)],mix(dark,field,.28))
    d.polygon([(left,375),(right,375),(right,435),(256,440),(left,435)],dark)
    d.line([(left,375),(210,375)],BRASS,1)
    d.line([(right,375),(302,375)],BRASS,1)
    d.line([(left+5,432),(256,436),(right-5,432)],mix(field,BRASS,.42),1)
    star(d,256,373,4,GOLD)
    word = name.upper() if key!='coophud' else 'Coop HUD'
    inscription(d,word,256,387,42,BONE,10)
    inscription(d,'COOP EXPANDED',256,45,12.5,GOLD,32)
    return img.resize((size,size),Image.Resampling.LANCZOS)


def repo_banner():
    w,h=1280,640
    img=Image.new('RGB',(w*2,h*2))
    d=Surface(img,2)
    background(d,w,h,'core',36)
    landscape(d,w,h,36,'core')
    # Thin constellations and meridian rings are engraved behind the emblem.
    for r in (189,196,222):
        d.arc(978,285,r,r,0,360,'#49665e',1.0)
    for i in range(80):
        angle=i*2*pi/80
        x,y=cos(angle),sin(angle)
        r=204 if i%5==0 else 199
        d.line([(978+x*196,285+y*196),(978+x*r,285+y*r)],BRASS if i%5==0 else '#678278',1)
    frame(d,w,h,22,'#7e8972',BRASS)
    seal(d,978,287,415)
    d.line([(91,157),(150,157),(165,151),(202,151)],BRASS,1.35)
    star(d,81,157,6,GOLD)
    inscription(d,'COOP',72,190,102,BONE,12,'left')
    inscription(d,'EXPANDED',74,318,92,GOLD,10,'left')
    d.line([(80,441),(280,441),(289,437),(298,441),(535,441)],BRASS,1.4)
    return img.resize((w,h),Image.Resampling.LANCZOS)


def logo():
    size=1024
    img=Image.new('RGBA',(size*2,)*2)
    seal(Surface(img,2),512,530,1040)
    return img.resize((size,size),Image.Resampling.LANCZOS)


def generate(entry, assets_root):
    """Build one manifest UI entry and return its final Paths in largest-first order."""
    root=Path(assets_root)/'ui'
    asset_id=entry['id']
    if asset_id.startswith('ce_ui_'):
        key=asset_id.removeprefix('ce_ui_')
        renders=[(root/'icons'/f'{key}_{size}.png',render_icon(key,size)) for size in (128,64)]
    elif asset_id.startswith('ce_brand_'):
        key=asset_id.removeprefix('ce_brand_')
        if key=='logo':
            result=logo()
        elif key=='repo_banner':
            result=repo_banner()
        else:
            result=module_cover(key)
        renders=[(root/'branding'/f'{key}.png',result)]
    else:
        raise ValueError(f'Unrecognized UI asset ID {asset_id!r}')
    for path,result in renders:
        path.parent.mkdir(parents=True,exist_ok=True)
        result.save(path,compress_level=9)
    return [path for path,_ in renders]
