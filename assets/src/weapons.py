"""Original rigid inventory props. Meshes are authored in the canonical art frame."""

from math import cos, sin, pi, sqrt, tau


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _unit(v):
    length = sqrt(sum(x*x for x in v))
    return tuple(x / length for x in v)


def _subtract(a, b):
    return tuple(x-y for x, y in zip(a, b))


class Sculpt:
    def __init__(self):
        self.parts = []

    def mesh(self, vertices, faces, mat):
        self.parts.append((vertices, faces, mat))

    def loft(self, rings, mat, loop=False):
        """Each ring is CCW when seen looking back along the sweep."""
        n = len(rings[0])
        vertices = [p for ring in rings for p in ring]
        faces = []
        for row in range(len(rings) if loop else len(rings)-1):
            a, b = row*n, ((row+1) % len(rings))*n
            for i in range(n):
                j = (i+1) % n
                faces.extend(((a+i, a+j, b+j), (a+i, b+j, b+i)))
        if not loop:
            for row, end in [(0, False), (len(rings)-1, True)]:
                c = len(vertices)
                vertices.append(tuple(sum(p[k] for p in rings[row])/n for k in range(3)))
                for i in range(n):
                    a, b = row*n+i, row*n+(i+1)%n
                    faces.append((c, a, b) if end else (c, b, a))
        self.mesh(vertices, faces, mat)

    def lathe(self, rows, mat, n=12, center=(0, 0), angle=0):
        rings = [[(center[0]+rx*cos(tau*i/n+angle), center[1]+ry*sin(tau*i/n+angle), z)
                  for i in range(n)] for z, rx, ry in rows]
        self.loft(rings, mat)

    def tube(self, path, radii, mat, n=8, loop=False):
        if isinstance(radii, (int, float)):
            radii = [radii]*len(path)
        rings = []
        for i, (point, r) in enumerate(zip(path, radii)):
            before = path[(i-1) % len(path)] if loop or i else point
            after = path[(i+1) % len(path)] if loop or i+1 < len(path) else point
            tangent = _unit(_subtract(after, before))
            ref = (0, 1, 0) if abs(tangent[1]) < .95 else (1, 0, 0)
            u = _unit(_cross(ref, tangent))
            v = _cross(tangent, u)
            rings.append([tuple(point[k]+r*(u[k]*cos(tau*j/n)+v[k]*sin(tau*j/n)) for k in range(3)) for j in range(n)])
        self.loft(rings, mat, loop)

    def plate(self, points, thick, mat, y=0, bevel=.035):
        """Bevel and triangulate an illustrated profile, including concave outlines."""
        signed = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(points, points[1:]+points[:1]))
        if signed < 0:
            points = points[::-1]
        n = len(points)
        cx, cz = (sum(p[k] for p in points)/n for k in range(2))
        vertices = [(cx+(x-cx)*s, y+depth, cz+(z-cz)*s)
                    for s, depth in [(1-bevel, -thick), (1, -.53*thick), (1, .53*thick), (1-bevel, thick)]
                    for x, z in points]
        faces = []
        for row in range(3):
            for i in range(n):
                j = (i+1) % n
                a, b = row*n+i, row*n+j
                faces.extend(((a, a+n, b+n), (a, b+n, b)))
        def orient(a, b, c):
            return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        remaining = list(range(n))
        while len(remaining) > 2:
            for j, b in enumerate(remaining):
                a, c = remaining[j-1], remaining[(j+1)%len(remaining)]
                if orient(points[a], points[b], points[c]) <= 1e-13:
                    continue
                if any(min(orient(points[i],points[k],points[p]) for i,k in ((a,b),(b,c),(c,a))) >= -1e-13
                       for p in remaining if p not in (a,b,c)):
                    continue
                faces.extend(((a,b,c), (3*n+c,3*n+b,3*n+a)))
                remaining.pop(j)
                break
            else:
                raise ValueError(f'Invalid profile polygon {points}')
        self.mesh(vertices, faces, mat)

    def orb(self, x, y, z, rx, ry, rz, mat, n=12):
        # A pair of clipped poles makes a small polished flat on either crown.
        self.lathe([(z+rz*sin(a),rx*cos(a),ry*cos(a)) for a in (-1.49,-1.1,-.65,0,.65,1.1,1.49)], mat,n,(x,y))

    def ring(self, x, y, z, rx, rz, r, mat, n=20):
        self.tube([(x+rx*cos(tau*i/n),y,z+rz*sin(tau*i/n)) for i in range(n)],r,mat,8,True)

    def band(self,z,r,d,h,mat,n=12,center=(0,0)):
        self.lathe([(z-h/2,.94*r,.94*d),(z-h*.29,r,d),(z+h*.29,r,d),(z+h/2,.94*r,.94*d)],mat,n,center)

    def braid(self, z0,z1,rx,ry,turns,r,mat):
        steps = max(12,round(abs(turns)*12))
        self.tube([(rx*cos(tau*turns*i/steps),ry*sin(tau*turns*i/steps),z0+(z1-z0)*i/steps)
                   for i in range(steps+1)],r,mat,5)

    def blade(self, rows, mat='steel', section='ridge'):
        # Each authored station carries independent left and right contours.
        sections = {
            'ridge': [(-1,0),(0,-1),(1,0),(0,1)],
            'flat': [(-1,0),(-.65,-1),(.54,-1),(1,0),(.54,1),(-.65,1)],
            'single': [(-1,-.55),(-.72,-1),(.2,-.92),(1,0),(.2,.92),(-.72,1),(-1,.55)],
            'fuller': [(-1,0),(-.70,-.82),(-.44,-1),(-.24,-.66),(.24,-.66),(.44,-1),(.70,-.82),
                       (1,0),(.70,.82),(.44,1),(.24,.66),(-.24,.66),(-.44,1),(-.70,.82)]
        }
        self.loft([[((l+r)/2+(r-l)/2*x,d*y,z) for x,y in sections[section]] for z,l,r,d in rows],mat)


def _diamond(s,x,y,z,w,h,mat):
    s.plate([(x-w,z),(x,z-h),(x+w,z),(x,z+h)],.00065,mat,y)


def _fern(s,x,y,z,size,mat):
    s.tube([(x,y,z),(x,y,z+size)],.00085,mat,5)
    for i in range(3):
        for side in (-1,1):
            h=z+size*(i+.25)/4
            s.plate([(x,h),(x+side*size*.23,h+size*.25),(x+side*size*.08,h+size*.20)],.00055,mat,y)


def _scroll(s,x,z,r,side,mat,y=0):
    path=[]
    for i in range(25):
        t=i/24
        a=-pi*.5+tau*t*1.28
        rad=r*(1-.77*t)
        path.append((x+side*rad*cos(a),y,z+rad*sin(a)))
    s.tube(path,.0026,mat,7)


def _grip(s, half, rx, ry, material, trim, wrap=None):
    s.lathe([(-half,rx*.79,ry*.83),(-.84*half,rx,ry),(-.22*half,rx*1.055,ry*1.03),
             (.56*half,rx*.96,ry*.97),(half,rx*.83,ry*.85)],material,14)
    for end in (-1,1):
        s.band(end*(half-.003),rx*1.02,ry*1.04,.009,trim,14)
    if wrap:
        s.braid(-half*.88,half*.88,rx,ry,round(half*118),.0015,wrap)


def _grip_rivets(s,half,ry,mat):
    for t in (-.64,0,.64):
        for side in (-1,1):
            s.orb(0,side*ry,half*t,.0033,.0018,.0033,mat,8)


def _guard(s,z,w,drop,mat):
    # Eight illustrated stations shape the quillons and the peaked central collar.
    upper=[(-w,z+drop),(-w*.86,z+drop*.87+.007),(-w*.4,z+drop*.27+.007),
           (-.020,z+.013),(0,z+.026),(.020,z+.013),(w*.4,z+drop*.27+.007),
           (w*.86,z+drop*.87+.007),(w,z+drop)]
    lower=[(w*.97,z+drop-.012),(w*.72,z+drop*.66-.007),(.021,z-.008),(0,z-.019),
           (-.021,z-.008),(-w*.72,z+drop*.66-.007),(-w*.97,z+drop-.012)]
    s.plate(upper+lower,.010,mat)


def _wheel(s,z,r,mat,inlay):
    s.tube([(0,-.012,z),(0,-.009,z),(0,.009,z),(0,.012,z)],[r*.85,r,r,r*.85],mat,20)
    for side in (-1,1):
        s.ring(0,.012*side,z,r*.70,r*.70,.0018,inlay,18)
        _diamond(s,0,.0125*side,z,r*.40,r*.55,inlay)


def _sword(code):
    s=Sculpt()
    two=code in ('greatsword','rhomphaia','claymore','nightfall')
    half=.145 if two else .055
    steel='dark_iron' if code=='nightfall' else 'steel'
    trim={'spatha':'bronze','arming':'steel','broadblade':'silver','leaf':'bronze','sabre':'brass',
          'saif':'gold','langseax':'dark_iron','dawnbrand':'gold','greatsword':'steel','rhomphaia':'bronze',
          'claymore':'bronze','nightfall':'silver'}[code]
    base={'leaf':'dark_wood','langseax':'bone','saif':'horn','rhomphaia':'red','nightfall':'black'}.get(code,'leather')
    wrap={'spatha':'red','broadblade':'blue','sabre':'teal','dawnbrand':'white','greatsword':'red','claymore':'green',
          'rhomphaia':'leather','nightfall':'purple','arming':'dark_wood'}.get(code)
    _grip(s,half,.021 if code=='langseax' else .018,.013,base,trim,wrap)
    if not wrap:
        _grip_rivets(s,half,.013,trim)
    # Normalized height, left silhouette, right silhouette. Curvature is drawn individually.
    blades={
        'spatha':(.825,'fuller',[(0,-26,26),(.08,-28,28),(.60,-24,24),(.88,-20,20),(1,-.5,.5)]),
        'arming':(.84,'ridge',[(0,-29,29),(.10,-26,26),(.57,-18,18),(.85,-11,11),(1,-.45,.45)]),
        'broadblade':(.80,'fuller',[(0,-32,32),(.14,-32,32),(.68,-27,27),(.90,-20,20),(1,-.6,.6)]),
        'leaf':(.81,'ridge',[(0,-23,23),(.17,-18,18),(.48,-25,25),(.65,-31,31),(.75,-29,29),(.90,-17,17),(1,-.55,.55)]),
        'sabre':(.815,'single',[(0,-17,21),(.20,-17,23),(.42,-25,18),(.66,-42,4),(.83,-67,-13),(.93,-83,-40),(1,-97,-96)]),
        'saif':(.83,'single',[(0,-19,24),(.23,-18,25),(.52,-25,21),(.78,-39,12),(.88,-49,3),(.97,-66,-40),(1,-72,-71)]),
        'langseax':(.81,'single',[(0,-21,24),(.19,-23,25),(.68,-24,30),(.79,-23,32),(1,24,25)]),
        'dawnbrand':(.84,'fuller',[(0,-25,25),(.05,-30,30),(.13,-24,24),(.74,-18,18),(.91,-10,10),(1,-.5,.5)]),
        'greatsword':(1.02,'fuller',[(0,-17,17),(.13,-18,18),(.18,-26,26),(.22,-29,29),(.72,-20,20),(.88,-13,13),(1,-.5,.5)]),
        'rhomphaia':(1.02,'single',[(0,-16,18),(.15,-13,21),(.34,-13,27),(.57,-7,40),(.76,8,61),(.89,26,75),(1,70,71)]),
        'claymore':(1.04,'ridge',[(0,-32,32),(.08,-30,30),(.61,-23,23),(.85,-14,14),(1,-.5,.5)]),
        'nightfall':(1.01,'ridge',[(0,-25,25),(.10,-28,28),(.20,-25,25),(.72,-18,18),(.90,-11,11),(1,-.6,.6)])
    }
    length,section,stations=blades[code]
    rows=[(half+length*t,l*.001,r*.001,.0007+.0047*(1-t**2)) for t,l,r in stations]
    s.blade(rows,steel,section)
    if code=='nightfall':
        for side in (-1,1):
            outline=[(l if side<0 else r,z) for z,l,r,d in rows]
            inner=[((x*.90),z) for x,z in outline]
            s.plate(outline+inner[::-1],.0007,'silver',bevel=0)
    guard_z=half+.005
    widths={'spatha':.054,'arming':.113,'broadblade':.080,'leaf':.075,'sabre':.083,'saif':.093,'langseax':.034,
            'dawnbrand':.097,'greatsword':.143,'rhomphaia':.052,'claymore':.130,'nightfall':.123}
    drops={'leaf':-.014,'sabre':.011,'saif':.021,'claymore':.061,'nightfall':.043,'greatsword':.017,'broadblade':-.012}
    _guard(s,guard_z,widths[code],drops.get(code,0),trim)
    p=-half-.021
    if code=='spatha':
        s.plate([(-.025,p+.011),(-.026,p-.010),(-.013,p-.025),(.006,p-.024),(.022,p-.013),
                 (.038,p-.010),(.035,p+.002),(.024,p+.009),(.016,p+.019),(-.011,p+.016)],.012,'bronze',bevel=.10)
        for side in (-1,1):
            s.orb(.015,side*.012,p+.001,.0027,.0015,.0027,'dark_iron',8)
            _fern(s,-.008,side*.0125,p-.021,.021,'brass')
    elif code in ('arming','greatsword'):
        _wheel(s,p-.004,.026 if two else .025,trim,'brass' if two else 'gold')
        if two:
            _guard(s,half+length*.145,.051,.018,'steel')
            s.braid(half+.020,half+.12,.019,.006,8,.0017,'leather')
    elif code=='broadblade':
        s.plate([(-.044,p+.002),(-.038,p-.012),(0,p-.018),(.038,p-.012),(.044,p+.002),(.035,p+.012),(-.035,p+.012)],.012,'dark_iron')
        for i in range(-2,3):
            s.orb(i*.013,0,p-.011,.011,.012,.016-.003*abs(i),'steel')
        for side in (-1,1):
            for i in (-2,-1,1,2):
                _diamond(s,i*.026,side*.0105,guard_z-.002-abs(i)*.003,.011,.005,'dark_iron')
    elif code=='leaf':
        for side in (-1,1):
            _scroll(s,side*.070,guard_z-.002,.013,side,'bronze')
        s.plate([(-.033,p+.005),(-.032,p-.005),(-.020,p-.015),(0,p-.006),(.020,p-.015),(.032,p-.005),(.033,p+.005),(0,p+.013)],.012,'bronze')
        for side in (-1,1):
            _scroll(s,side*.022,p-.005,.008,side,'brass',-.012)
    elif code=='sabre':
        s.ring(-.008,0,p-.004,.019,.021,.005,'brass')
        for i in range(7):
            x=-.015-(i-3)*.002
            s.tube([(-.012,0,p-.022),(x-.009,.002*sin(i),p-.043),(x-.015,.004*sin(i),p-.086+.009*cos(i))],
                   [.0017,.0024,.0008],'teal' if i%3 else 'sand',5)
    elif code=='saif':
        s.plate([(-.018,p+.017),(-.019,p-.001),(-.032,p-.009),(-.044,p+.001),(-.039,p-.016),(-.021,p-.025),
                 (.001,p-.021),(.018,p-.006),(.018,p+.014)],.013,'horn')
        for side in (-1,1):
            s.tube([(-.039,side*.013,p-.003),(-.027,side*.013,p-.014),(-.015,side*.013,p-.015),(.010,side*.013,p+.004)],.0017,'gold',6)
            _diamond(s,0,side*.0105,guard_z,.010,.016,'green')
    elif code=='langseax':
        s.lathe([(p-.004,.016,.010),(p,.022,.014),(p+.016,.023,.015)],'bone',12)
        s.band(p+.008,.024,.016,.005,'dark_iron')
    elif code=='dawnbrand':
        _wheel(s,p-.004,.022,'brass','gold')
        for side in (-1,1):
            for i in range(4):
                a=(18+i*16)*pi/180
                x,z=.022*side,guard_z+.003
                s.plate([(x,z),(x+side*(.037-i*.003)*cos(a),z+.047*sin(a)),(x+side*.012,z-.004)],.007,'gold')
            _fern(s,0,side*.004,half+.055,.12,'gold')
    elif code=='claymore':
        for side in (-1,1):
            for dx,dz in ((-.007,0),(.007,0),(0,-.007),(0,.007)):
                s.ring(side*.128+dx,0,guard_z+.061+dz,.0064,.0064,.0028,'bronze',14)
        s.orb(0,0,p-.006,.024,.020,.030,'bronze')
        s.band(p-.008,.025,.021,.006,'green')
    elif code=='nightfall':
        for side in (-1,1):
            s.plate([(side*.046,guard_z+.012),(side*.085,guard_z+.026),(side*.12,guard_z+.043),
                     (side*.128,guard_z+.070),(side*.129,guard_z+.039),(side*.105,guard_z+.013)],.006,'silver')
        s.orb(0,0,p-.008,.022,.015,.027,'dark_iron')
        _diamond(s,0,-.015,p-.008,.009,.016,'silver')
    else:
        s.lathe([(p-.018,.010,.009),(p-.010,.020,.016),(p+.002,.024,.017),(p+.016,.016,.012)],'bronze')
        for side in (-1,1):
            _fern(s,0,side*.0105,guard_z-.010,.030,'brass')
    return {'':s.parts}


def generate(entry):
    """Return one mesh-part list per object suffix for a manifest item."""
    identifier = entry['id']
    group, name = identifier.split('_')[1], identifier.split('_')[-1]
    if group in ('sw','2h'):
        return _sword(name)
    if group=='ax' or name=='francisca':
        return _axe(name)
    if group=='mc':
        return _mace(name)
    if group in ('pl','th'):
        return _pole(identifier.split('_',3)[3])
    if group=='dg':
        return _dagger(name)
    if group=='am':
        return _ammo(identifier[6:])
    raise KeyError(identifier)


def _haft(s,bottom,top,rad,mat,accent,grip='leather',bend=0,wrap=True):
    path=[(bend*.35,0,bottom),(bend*.24,0,bottom+.027),(0,0,-.065),(0,0,.055),
          (-bend*.18,0,.36*top),(bend*.24,0,.72*top),(bend,0,top)]
    s.tube(path,[rad*.82,rad*1.09,rad,rad*.97,rad*.91,rad*.88,rad*.78],mat,12)
    s.band(bottom+.016,rad*1.10,rad*1.10,.019,accent,12,(bend*.26,0))
    if wrap:
        _grip(s,.062,rad*1.06,rad*1.06,grip,accent,'rawhide' if grip=='leather' else 'leather')


_AXES={
    # The last five points on each profile describe its distinctive cutting arc.
    'bearded':[(0,.036),(.039,.029),(.077,.041),(.109,.061),(.130,.051),(.143,.018),(.146,-.029),
               (.139,-.077),(.109,-.125),(.092,-.135),(.090,-.085),(.073,-.057),(.039,-.022),(-.017,-.017),(-.026,.020)],
    'dane':[(0,.030),(.045,.021),(.104,.052),(.162,.109),(.179,.104),(.202,.058),(.212,.009),
            (.205,-.047),(.187,-.094),(.145,-.145),(.128,-.149),(.136,-.093),(.111,-.061),(.062,-.031),(.005,-.018),(-.024,-.014),(-.029,.020)],
    'war':[(0,.030),(.052,.040),(.086,.069),(.097,.071),(.126,.038),(.141,-.003),(.135,-.044),(.100,-.086),
           (.086,-.087),(.080,-.049),(.047,-.028),(0,-.018),(-.022,-.012),(-.025,.018)],
    'tabar':[(0,.018),(.050,.023),(.078,.053),(.079,.091),(.098,.082),(.136,.050),(.156,.003),
             (.152,-.042),(.127,-.078),(.083,-.102),(.075,-.101),(.088,-.060),(.072,-.033),(.047,-.020),(-.023,-.016),(-.025,.015)],
    'horseman':[(0,.020),(.063,.024),(.085,.051),(.104,.049),(.126,.019),(.131,-.019),(.117,-.053),
                (.087,-.080),(.083,-.077),(.082,-.044),(.051,-.022),(-.017,-.016),(-.020,.017)],
    'stormcleaver':[(0,.029),(.057,.022),(.096,.047),(.122,.086),(.143,.082),(.171,.041),(.185,-.005),
                    (.176,-.047),(.136,-.092),(.117,-.092),(.101,-.053),(.060,-.024),(-.003,-.013),(-.010,.018)],
    'francisca':[(0,.013),(.041,.023),(.079,.059),(.095,.066),(.113,.049),(.120,.024),(.117,-.011),
                 (.100,-.042),(.084,-.054),(.072,-.037),(.034,-.013),(-.016,-.009),(-.022,.010)]}


def _axe(code):
    s=Sculpt()
    long=code in ('dane','stormcleaver')
    throw=code=='francisca'
    bottom=-.34 if long else (-.11 if throw else -.17)
    z=.91 if long else (.29 if throw else .52)
    trim={'bearded':'dark_iron','dane':'dark_iron','war':'bronze','tabar':'brass',
          'horseman':'dark_iron','stormcleaver':'silver','francisca':'dark_iron'}[code]
    wood={'dane':'dark_wood','stormcleaver':'black','tabar':'dark_wood'}.get(code,'ash')
    bend={'horseman':.012,'war':-.010,'bearded':.016,'dane':.022,'francisca':.028}.get(code,.003)
    _haft(s,bottom,z+.020,.016 if throw else (.020 if long else .017),wood,trim,bend=bend,wrap=not throw)
    outline=_AXES[code]
    for side in ((1,-1) if code=='stormcleaver' else (1,)):
        p=[(bend+side*x,z+dz) for x,dz in outline]
        thick=.011 if throw else (.014 if long else .012)
        s.plate(p,thick,'dark_iron' if code in ('stormcleaver','dane','bearded','francisca') else 'steel',bevel=.10)
        first,last={'bearded':(4,9),'dane':(4,10),'war':(3,8),'tabar':(4,10),'horseman':(3,8),'stormcleaver':(4,9),'francisca':(3,8)}[code]
        arc=outline[first:last+1]
        edge=[(bend+side*x,z+dz) for x,dz in arc]
        inner=[(bend+side*(x*.82+.004),z+dz*.83) for x,dz in arc]
        # An illustrated ground edge follows the face bevel on both sides.
        for face in (-1,1):
            s.plate(edge+inner[::-1],.0006,'silver' if code=='stormcleaver' else 'steel',y=face*thick*.88,bevel=.012)
            if code=='tabar':
                for j in range(3):
                    _diamond(s,bend+side*(.066+j*.019),face*.0123,z,.010,.012+j*.003,'brass')
            elif code=='stormcleaver':
                s.tube([(bend+side*x,face*.0143,z+dz) for x,dz in [( .05,-.005),(.078,.008),(.091,.001),(.108,.016),(.129,.005),(.140,.016)]],.0021,'silver',6)
                s.tube([(bend+side*x,face*.0143,z+dz) for x,dz in [(.095,-.008),(.113,-.004),(.103,-.019),(.124,-.012)]],.0014,'silver',6)
            elif code=='war':
                _scroll(s,bend+.076,z+.003,.016,1,'bronze',face*thick)
    s.lathe([(z-.030,.022,.020),(z-.019,.025,.024),(z+.014,.025,.024),(z+.027,.021,.021)],trim,14,(bend,0))
    if code=='horseman':
        s.plate([(bend-.012,z+.016),(bend-.062,z+.013),(bend-.084,z+.023),(bend-.091,z+.016),
                 (bend-.090,z-.021),(bend-.078,z-.024),(bend-.061,z-.012),(bend-.012,z-.013)],.015,'dark_iron')
    for i in range(4 if long or code=='war' else 2):
        h=z-.051-i*.022
        t = (h/(z+.020)-.72)/.28
        cx = bend*(.24+.76*t) if t>=0 else bend*(.24+.42*t*.28/.36)
        radius = .015 if throw else .0205
        s.band(h,radius,radius,.011,trim if i%2==0 else 'rawhide',12,(cx,0))
    if code=='bearded':
        for i in range(5):
            zz=.13+i*.045
            s.tube([(-.009,-.014,zz),(.001,-.016,zz+.010),(.009,-.012,zz+.022)],.0018,'dark_wood',6)
    if code=='war':
        for h in (.16,.29):
            s.band(h,.0175,.0175,.022,'bronze',12)
    return {'':s.parts}


def _spin_parts(s,parts,angle):
    for verts,faces,mat in parts:
        s.mesh([(x*cos(angle)-y*sin(angle),x*sin(angle)+y*cos(angle),z) for x,y,z in verts],faces,mat)


def _horizontal(s,z,rows,mat,n=12):
    # A longitudinal profile rotated to the transverse axis of a hammer head.
    tmp=Sculpt()
    tmp.lathe(rows,mat,n,angle=pi/n)
    for verts,faces,m in tmp.parts:
        s.mesh([(h,y,z-x) for x,y,h in verts],faces,m)


def _feathers(s,z,span,width,mat,count=3,angle=0,narrow=False):
    feather=Sculpt()
    base=.0035 if narrow else .006
    feather.plate([(base,z),(base+width*.90,z+span*.035),(base+width,z+span*.19),
                   (base+width*.76,z+span*.53),(base+width*.43,z+span*.79),
                   (base+.0005,z+span),(base-.0005,z+span*.93)],.00065,mat)
    for i in range(count):
        _spin_parts(s,feather.parts,angle+tau*i/count)


def _pole(code):
    s=Sculpt()
    # Complete prop height, grip-origin offset, illustrated head height.
    total,bottom,long_head={
        'kontarion':(2.94,-.91,.27),'billhook':(2.08,-.72,.36),'boar_spear':(2.19,-.71,.31),
        'long_spear':(2.38,-.77,.34),'glaive':(2.22,-.72,.48),'rumh':(2.79,-.88,.28),
        'atgeir':(2.19,-.70,.42),'sunspear':(2.50,-.83,.37),'jarid':(1.25,-.48,.18),
        'pilum':(1.41,-.57,.42),'dart':(1.12,-.43,.16)}[code]
    tip=bottom+total
    z=tip-long_head
    thrown=code in ('jarid','pilum','dart')
    rad=.0115 if thrown else (.016 if code=='rumh' else .019)
    trim={'kontarion':'bronze','billhook':'dark_iron','boar_spear':'dark_iron','long_spear':'bronze',
          'glaive':'brass','rumh':'brass','atgeir':'dark_iron','sunspear':'gold','jarid':'brass',
          'pilum':'dark_iron','dart':'bronze'}[code]
    wood={'rumh':'sand','glaive':'dark_wood','atgeir':'dark_wood','sunspear':'black'}.get(code,'ash')
    s.lathe([(bottom,.72*rad,.72*rad),(bottom+.025,rad,rad),(-.065,rad,rad),(.080,rad*.99,rad*.99),
             (z-.09,rad*.78,rad*.78),(z+.011,rad*.68,rad*.68)],wood,12)
    s.lathe([(bottom,.64*rad,.64*rad),(bottom+.014,rad*1.04,rad*1.04),
             (bottom+.043,rad*1.01,rad*1.01)],trim,12)
    if code not in ('rumh','pilum','dart'):
        _grip(s,.068 if not thrown else .045,rad*1.03,rad*1.03,'leather',trim,
              'rawhide' if code!='glaive' else 'teal')
    s.lathe([(z-.075,rad*.95,rad*.95),(z-.064,rad,rad),(z-.043,rad*.93,rad*.93),
             (z+.020,rad*.72,rad*.72)],trim,12)
    s.band(z-.060,rad*1.025,rad*1.025,.008,'silver' if code=='sunspear' else trim)
    if code=='pilum':
        s.lathe([(z-.055,.013,.013),(z-.023,.024,.022),(z+.025,.024,.022),(z+.052,.008,.008),
                 (tip-.077,.005,.005)],'dark_iron',8,angle=pi/8)
        s.blade([(tip-.083,-.006,.006,.005),(tip-.052,-.014,.014,.009),
                 (tip,-.0006,.0006,.0007)],'steel')
        for y in (-.022,.022):
            s.orb(0,y,z+.004,.005,.002,.005,'bronze',8)
    else:
        profiles={
            'kontarion':[(0,-8,8),(.14,-21,21),(.33,-18,18),(.80,-8,8),(1,-.5,.5)],
            'billhook':[(0,-12,12),(.11,-20,23),(.30,-23,24),(.57,-20,15),(.70,-9,10),(1,-3,-2)],
            'boar_spear':[(0,-10,10),(.11,-28,28),(.26,-34,34),(.49,-25,25),(.80,-10,10),(1,-.5,.5)],
            'long_spear':[(0,-8,8),(.12,-14,14),(.29,-30,30),(.43,-32,32),(.62,-22,22),(.85,-9,9),(1,-.5,.5)],
            'glaive':[(0,-13,17),(.14,-17,31),(.42,-24,44),(.64,-39,42),(.81,-59,22),(.93,-74,-13),(1,-86,-85)],
            'rumh':[(0,-7,7),(.11,-17,17),(.34,-15,15),(.81,-6,6),(1,-.5,.5)],
            'atgeir':[(0,-12,15),(.12,-20,32),(.24,-21,45),(.50,-20,42),(.71,-16,30),(.88,-9,14),(1,1,2)],
            'sunspear':[(0,-9,10),(.10,-26,18),(.23,-38,20),(.35,-30,32),(.48,-11,38),
                        (.62,-18,21),(.76,-24,9),(.89,-18,8),(1,0,1)],
            'jarid':[(0,-5,5),(.16,-12,12),(.60,-8,8),(1,-.5,.5)],
            'dart':[(0,-5,5),(.13,-16,16),(.33,-13,13),(.74,-7,7),(1,-.5,.5)]}
        stations=profiles[code]
        rows=[(z+h*long_head,left*.001,right*.001,(.0044 if thrown else .0065)*(1-.89*h))
              for h,left,right in stations]
        s.blade(rows,'gold' if code=='sunspear' else 'steel','single' if code in ('glaive','billhook','atgeir') else 'ridge')
    if code=='kontarion':
        pennon=[(.012,z-.045),(.084,z-.054),(.145,z-.034),(.220,z-.042),(.312,z-.022),
                (.230,z-.091),(.270,z-.104),(.166,z-.105),(.103,z-.133),(.012,z-.143)]
        s.plate(pennon,.002,'red')
        for face in (-1,1):
            _fern(s,.078,face*.0025,z-.114,.051,'gold')
            s.tube([(.015,face*.002,z-.055),(.080,face*.002,z-.065),(.146,face*.002,z-.044),(.211,face*.002,z-.051)],.0023,'gold',6)
        for zz in (z-.046,z-.138):
            s.band(zz,rad,rad,.008,'brass')
    elif code=='billhook':
        s.plate([(.006,z+.093),(.040,z+.095),(.074,z+.061),(.089,z+.027),(.091,z+.071),
                 (.074,z+.113),(.045,z+.144),(.017,z+.169)],.006,'steel',bevel=.12)
        s.plate([(-.012,z+.138),(-.071,z+.102),(-.086,z+.113),(-.038,z+.171),(-.012,z+.195)],.005,'dark_iron')
    elif code=='boar_spear':
        for side in (-1,1):
            s.plate([(side*.009,z-.019),(side*.037,z-.020),(side*.092,z+.003),(side*.100,z+.026),
                     (side*.061,z+.009),(side*.012,z+.004)],.007,'dark_iron')
            s.orb(side*.081,0,z+.010,.004,.008,.004,'silver',8)
    elif code=='long_spear':
        s.braid(z-.140,z-.055,rad*.90,rad*.90,7,.0028,'rawhide')
        for y in (-.007,.007):
            _fern(s,0,y,z+.054,.071,'bronze')
    elif code=='glaive':
        for i in range(11):
            a=tau*i/11
            s.tube([(.014*cos(a),.014*sin(a),z-.057),(.029*cos(a),.029*sin(a),z-.097),
                    ((.033+.008*sin(i))*cos(a),.032*sin(a),z-.188+.018*cos(i))],[.0034,.0045,.0008],'fur' if i%4 else 'teal',5)
    elif code=='rumh':
        for i in range(1,10):
            zz=bottom+i*(z-bottom)/10
            r=rad*(1.08-.19*i/10)
            s.band(zz,r,r,.017,'dark_wood')
            s.band(zz+.009,r*.97,r*.97,.007,'sand')
        for i in range(4):
            s.band(z-.097-i*.016,rad*.91,rad*.91,.005,'green')
    elif code=='atgeir':
        s.plate([(-.008,z-.013),(-.061,z-.041),(-.082,z-.064),(-.072,z-.024),(-.050,z+.002),(-.009,z+.033)],.007,'dark_iron')
        s.braid(z-.13,z-.074,rad*.90,rad*.90,5,.002,'rawhide')
    elif code=='sunspear':
        for side in (-1,1):
            s.plate([(side*.012,z-.008),(side*.040,z+.001),(side*.063,z+.054),(side*.053,z+.018),
                     (side*.031,z-.016),(side*.012,z-.034)],.004,'bronze')
        s.braid(z-.17,z-.071,rad*.88,rad*.88,5,.0018,'gold')
    elif code=='dart':
        _feathers(s,bottom+.037,.134,.025,'white',4)
        s.lathe([(z-.098,.011,.011),(z-.075,.021,.021),(z-.041,.022,.022),(z-.026,.012,.012)],'bronze',10)
    return {'':s.parts}


def _mace(code):
    s=Sculpt()
    long=code=='maul'
    bottom, z = (-.32,.90) if long else (-.15,.51)
    trim={'flanged':'bronze','gurz':'brass','warhammer':'steel','maul':'dark_iron','knobbed':'brass'}[code]
    _haft(s,bottom,z+.015,.020 if long else .017,'dark_wood' if long or code=='flanged' else 'ash',trim)
    if code=='flanged':
        s.lathe([(z-.09,.021,.021),(z-.07,.026,.026),(z+.047,.023,.023),(z+.073,.015,.015),(z+.081,.006,.006)],'dark_iron',16)
        flange=Sculpt()
        flange.plate([(.018,z-.072),(.038,z-.059),(.061,z+.005),(.064,z+.032),(.054,z+.056),(.024,z+.066),(.018,z+.052)],.006,'steel',bevel=.12)
        for i in range(6):
            _spin_parts(s,flange.parts,tau*i/6)
        s.band(z-.069,.027,.027,.012,'bronze',18)
    elif code in ('gurz','knobbed'):
        rows=[(-.083,.015),(-.067,.022),(-.042,.026),(-.014,.040),(.020,.052),(.050,.049),(.070,.032),(.081,.012)] if code=='gurz' else [(-.067,.021),(-.053,.037),(-.032,.050),(0,.055),(.032,.049),(.050,.036),(.062,.017)]
        s.lathe([(z+h,r,r) for h,r in rows],'dark_iron' if code=='gurz' else 'bronze',16)
        rings=[(-.012,.040,6),(.035,.051,8)] if code=='gurz' else [(-.034,.049,7),(0,.055,9),(.034,.047,7)]
        for row,(dz,r,count) in enumerate(rings):
            for i in range(count):
                a=tau*(i+.5*row)/count
                s.orb(r*cos(a),r*sin(a),z+dz,.011,.011,.012,'brass' if code=='knobbed' else 'steel',8)
        s.band(z+rows[0][0],.022,.022,.015,trim)
        s.orb(0,0,z+rows[-1][0],.015,.015,.009,trim)
        if code=='gurz':
            s.tube([(.003,0,bottom+.021),(.035,0,bottom+.008),(.056,.003,bottom+.036),
                    (.051,.006,bottom+.063),(.025,.004,bottom+.068),(.003,0,bottom+.024)],.0034,'leather',7)
    elif code=='warhammer':
        _horizontal(s,z,[(-.13,.002,.002),(-.095,.012,.008),(-.042,.022,.014),(-.012,.027,.019),
                    (.020,.025,.021),(.055,.015,.018),(.081,.026,.024),(.095,.029,.026),(.100,.025,.022)],'steel',8)
        for side in (-1,1):
            _diamond(s,0,side*.022,z,.016,.017,'brass')
        s.band(z-.05,.019,.019,.045,'dark_iron')
    else:
        _horizontal(s,z,[(-.12,.051,.044),(-.103,.060,.052),(-.067,.062,.054),(.067,.062,.054),
                    (.103,.060,.052),(.12,.051,.044)],'dark_wood',8)
        for x in (-.100,-.063,.063,.100):
            _horizontal(s,z,[(x-.010,.061,.054),(x-.007,.064,.057),(x+.007,.064,.057),(x+.010,.061,.054)],'dark_iron',8)
        s.band(z-.084,.025,.025,.060,'dark_iron')
        for i in (-1,1):
            s.orb(i*.062,-.055,z,.005,.004,.005,'steel',8)
    return {'':s.parts}


def _pocket(s,rows,mat,n=16,square=False):
    """Follow the exterior, roll over the rim, and return into the hollow interior."""
    rim=rows[-1]
    wall=.003
    inside=[(x,z,a-wall,b-wall) for x,z,a,b in reversed(rows)]
    x,z,a,b=inside[-1]
    inside[-1]=(x,z+.008,a,b)
    shape=[(-.87,-1),(.87,-1),(1,-.85),(1,.85),(.87,1),(-.87,1),(-1,.85),(-1,-.85)] if square else [
        (cos(tau*i/n),sin(tau*i/n)) for i in range(n)]
    all_rows=rows+[(rim[0],rim[1]+.002,rim[2]-.0015,rim[3]-.0015)]+inside
    rings=[[(x+a*u,b*v,z) for u,v in shape] for x,z,a,b in all_rows]
    s.loft(rings,mat)


def _curved_profile(rows):
    """Sample a smooth silhouette through the cross sections of a curved prop."""
    result=[]
    for i,(a,b) in enumerate(zip(rows, rows[1:])):
        before=rows[max(0,i-1)]
        after=rows[min(i+2,len(rows)-1)]
        dz=b[0]-a[0]
        for step in range(4):
            t=step/4
            coords=[a[0]+dz*t]
            for axis in range(1,len(a)):
                m0=(b[axis]-before[axis])*dz/(b[0]-before[0])
                m1=(after[axis]-a[axis])*dz/(after[0]-a[0])
                coords.append((2*t**3-3*t**2+1)*a[axis]+(t**3-2*t**2+t)*m0
                              +(-2*t**3+3*t**2)*b[axis]+(t**3-t**2)*m1)
            result.append(tuple(coords))
    return result+[rows[-1]]


def _dagger(code):
    s=Sculpt()
    half=.048
    if code=='jambiya':
        _grip(s,half,.023,.012,'horn','brass')
        for z in (-half,half):
            s.plate([(-.040,z-.010),(-.036,z+.010),(-.019,z+.013),(0,z+.006),(.019,z+.013),
                     (.036,z+.010),(.040,z-.010),(.021,z-.007),(0,z-.012),(-.021,z-.007)],.012,'horn')
        s.blade(_curved_profile([(half,-.027,.030,.006),(.089,-.025,.036,.007),(.177,-.032,.034,.007),
                 (.23,-.047,.024,.006),(.275,-.074,-.006,.005),(.309,-.103,-.045,.004),
                 (.327,-.143,-.100,.003),(.335,-.162,-.161,.0007)]),'steel')
        for z in (-.034,.031):
            for y in (-.012,.012):
                _diamond(s,0,y,z,.012,.007,'gold')
        _grip_rivets(s,.035,.013,'brass')
    elif code=='rondel':
        _grip(s,half,.014,.014,'dark_wood','steel','leather')
        for z in (-half-.002,half+.002):
            s.lathe([(z-.006,.026,.026),(z-.003,.035,.035),(z+.003,.035,.035),(z+.006,.027,.027)],'steel',20)
            s.band(z,.0355,.0355,.003,'brass',20)
            for i in range(8):
                a=tau*i/8
                s.orb(.025*cos(a),.025*sin(a),z+.005,.002,.002,.002,'brass',7)
        s.blade([(.054,-.011,.013,.008),(.085,-.012,.013,.008),(.22,-.008,.010,.006),
                 (.331,-.003,.004,.003),(.364,-.0005,.0005,.0007)],'steel')
    else:
        _grip(s,half,.018,.011,'bone','dark_iron')
        _grip_rivets(s,half,.011,'bronze')
        s.blade([(half,-.015,.020,.004),(.09,-.016,.022,.004),(.22,-.019,.022,.0037),
                 (.273,-.019,.024,.0033),(.338,.017,.018,.0006)],'steel','single')
        s.band(-.052,.019,.013,.011,'dark_iron')
        sheath=Sculpt()
        _pocket(sheath,[(.013,.026,.011,.007),(.003,.048,.023,.011),(0,.116,.027,.012),
                        (0,.290,.026,.012),(0,.324,.024,.013)],'leather')
        sheath.lathe([(.021,.007,.005),(.029,.014,.009),(.051,.023,.012)],'bronze',12,(.010,0))
        sheath.band(.318,.025,.014,.012,'bronze',16)
        for side in (-1,1):
            for i in range(8):
                x=side*.019
                h=.07+i*.028
                sheath.tube([(x,-.0088,h),(x+side*.001,-.009,h+.012)],.001,'rawhide',5)
        for i in range(3):
            _diamond(sheath,0,-.012,.105+i*.073,.012,.025,'dark_wood')
            _diamond(sheath,0,-.013,.105+i*.073,.006,.014,'bronze')
        sheath.ring(.028,0,.259,.009,.018,.0028,'bronze',14)
        return {'':s.parts,'_sheath':sheath.parts}
    return {'':s.parts}


def _ammo(code):
    s=Sculpt()
    bolt=code=='steel_bolts'
    whistle=code=='khuzait_whistling_arrows'
    broad=code=='broadhead_arrows'
    r=.0049 if bolt else .0039
    end=.425 if bolt else .90
    low=-.11 if bolt else -.23
    high=low+end
    arrowhead=high-(.059 if bolt else .082)
    s.lathe([(low,r*.93,r*.93),(low+.015,r,r),(arrowhead,r,r),(arrowhead+.004,r*.77,r*.77)],'ash' if not whistle else 'dark_wood',8)
    feather='white' if not whistle else 'teal'
    _feathers(s,low+.017,.085 if bolt else .132,.014 if bolt else .019,feather,2 if bolt else 3,narrow=True)
    s.band(low+.018,r*1.22,r*1.22,.009,'leather',8)
    s.band(arrowhead,r*1.30,r*1.30,.014,'dark_iron',8)
    if whistle:
        s.lathe([(arrowhead-.021,.005,.005),(arrowhead-.014,.011,.011),(arrowhead+.002,.013,.013),
                 (arrowhead+.012,.011,.011),(arrowhead+.020,.005,.005)],'bone',12)
        for i in range(4):
            a=tau*(i+.125)/4
            spot=Sculpt()
            _diamond(spot,0,-.012,arrowhead+.001,.0037,.005,'black')
            _spin_parts(s,spot.parts,a)
    if broad:
        s.blade([(arrowhead,-.004,.004,.003),(arrowhead+.014,-.024,.024,.004),
                 (arrowhead+.033,-.021,.021,.004),(high,-.0005,.0005,.0005)],'steel')
    else:
        s.blade([(arrowhead+( .017 if whistle else 0),-.005,.005,.004),(arrowhead+.025,-.008,.008,.007),
                 (high,-.0005,.0005,.0005)],'steel')
    q=Sculpt()
    skin='rawhide' if broad else ('dark_wood' if bolt else 'leather')
    metal='brass' if whistle or broad else 'dark_iron'
    trim='teal' if whistle else ('rawhide' if broad else 'dark_wood')
    tall=.455 if bolt else .497
    width=.073 if bolt else (.082 if broad else .073)
    depth=.043 if bolt else (.059 if broad else .052)
    _pocket(q,[(-.018,0,width*.61,depth*.73),(-.016,.024,width*.70,depth*.80),(-.007,tall*.45,width*.82,depth*.90),
               (0,tall-.034,width*.99,depth*.99),(0,tall,width,depth)],skin,16,bolt)
    n=4 if bolt else 16
    # A square-rimmed belt case receives a separate quadrilateral binding.
    for z,fac,height,mat in [(.027,.72,.016,metal),(tall*.36,.82,.015,trim),(tall-.038,1,.033,trim)]:
        cx=-.016 if z<.1 else (-.008 if z<tall*.5 else 0)
        if bolt:
            _pocket(q,[(cx,z-height/2,width*fac+.002,depth*(.78+.22*z/tall)+.002),
                       (cx,z+height/2,width*fac+.003,depth*(.78+.22*z/tall)+.003)],mat,8,True)
        else:
            q.band(z,width*fac+.003,depth*(.78+.22*z/tall)+.003,height,mat,n,(cx,0))
    if whistle:
        for i in range(-2,3):
            x=i*.022
            y=-(depth+.002)*sqrt(1-(x/width)**2)
            _diamond(q,x,y,tall-.038,.009,.012,'brass')
    elif broad:
        for i in range(16):
            a=tau*i/16
            tuft=Sculpt()
            tuft.plate([(-.012,tall-.046),( .010,tall-.046),(.008,tall-.067),(0,tall-.076-.011*cos(3*a)),
                        (-.008,tall-.064)],.0024,'fur',-depth*.98)
            for verts,faces,mat in tuft.parts:
                q.mesh([(x*cos(a)-y*sin(a)*width/depth,x*sin(a)*depth/width+y*cos(a),z) for x,y,z in verts],faces,mat)
    else:
        for i in range(12):
            zz=.065+i*.027
            q.tube([(-.010,-depth*(.80+.20*zz/tall),zz),(.002,-depth*(.80+.20*zz/tall)-.001,zz+.010)],.0015,'rawhide',5)
    q.tube([(width*.68,.008,tall-.120),(width*1.12,.010,tall-.105),(width*1.16,.012,tall-.050),
            (width*.92,.010,tall-.036)],.008,'leather',8)
    # Only the upper parts of the stowed ammunition are visible inside the case.
    for i in range(7 if bolt else 8):
        a=tau*i/(7 if bolt else 8)
        x=width*.56*cos(a)
        y=depth*.55*sin(a)
        tip=tall+(.112 if bolt else .138)+.014*cos(3*a)
        spread=.009
        q.tube([(x*.91,y*.91,tall-.090),(x+spread*cos(a),y+spread*sin(a),tip)],[r,r], 'ash' if not whistle else 'dark_wood',7)
        f=Sculpt()
        _feathers(f,0,.073 if bolt else .098,.012 if bolt else .015,feather if i%3 else ('sand' if whistle else 'dark_wood'),
                  2 if bolt else 3,a,narrow=True)
        for verts,faces,mat in f.parts:
            q.mesh([(vx+x+spread*cos(a),vy+y+spread*sin(a),tip-.012-vz) for vx,vy,vz in verts],
                   [tuple(reversed(face)) for face in faces],mat)
        q.band(tip-.005,r*1.15,r*1.15,.006,trim,7,(x+spread*cos(a),y+spread*sin(a)))
    return {'':s.parts,'_quiver':q.parts}
