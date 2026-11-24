"""Original shield faces, fittings and reverse grips, in metres."""
from math import cos, sin, pi, tau
try:
    from .prop_shapes import bead, swept, tube
except ImportError:
    from prop_shapes import bead, swept, tube


def ellipse(a,b,n=40):
    return [(a*cos(tau*i/n), b*sin(tau*i/n)) for i in range(n)]


def outline(name):
    if name == 'vlandic_heater':
        return [(-.292,.42),(-.255,.45),(.255,.45),(.292,.42),(.30,.23),(.28,-.01),
                (.22,-.19),(.12,-.34),(.0,-.45),(-.12,-.34),(-.22,-.19),(-.28,-.01),(-.30,.23)]
    if name == 'vlandic_pavise':
        return [(-.33,.57),(-.275,.61),(-.11,.61),(-.05,.65),(.05,.65),(.11,.61),
                (.275,.61),(.33,.57),(.35,.40),(.34,.0),(.31,-.56),(.27,-.63),
                (.13,-.65),(-.13,-.65),(-.27,-.63),(-.31,-.56),(-.34,0),(-.35,.4)]
    a,b = {'imperial_oval':(.36,.51),'battanian_hide_oval':(.31,.50),'merc_buckler':(.172,.172),
           'nord_painted_round':(.443,.443),'aserai_daraqa':(.387,.387)}.get(name,(.42,.42))
    return ellipse(a,b)


def generate(entry):
    name = entry['id'].removeprefix('ce_sh_')
    out = []
    perimeter = outline(name)
    w = max(x for x,z in perimeter)
    h = max(z for x,z in perimeter)
    buckler = name == 'merc_buckler'
    def face(x,z):
        return -.072 - (.034 if buckler else .047)*(1-(x/w)**2) + .008*(z/h)**2

    def plate(poly, material, lift=.002, thickness=.002):
        out.append(swept([[(x,face(x,z)-lift+offset,z) for x,z in poly]
                          for offset in [thickness,0]],material))

    def line(xzs, radius, material, lift=.004, sides=6, loop=False):
        out.append(tube([(x,face(x,z)-lift,z) for x,z in xzs],radius,material,sides,loop))

    def rim(scale,rad,mat):
        line([(x*scale,z*scale) for x,z in perimeter],rad,mat,.003,8,True)

    def boss(x,z,r,depth,mat, n=20):
        # Stamped flange and a bulbous crown meet on a small, stepped neck.
        profile = [(1,-.001),(1,.004),(.89,.007),(.79,.006),(.73,depth*.36),
                   (.54,depth*.79),(.29,depth*.96),(.09,depth)]
        out.append(swept([[(x+r*s*cos(tau*i/n),face(x,z)-d,z+r*s*sin(tau*i/n))
                           for i in range(n)] for s,d in profile], mat))

    def pins(scale,material, count, r=.007):
        for i in range(count):
            idx = round(i*len(perimeter)/count) % len(perimeter)
            x,z = (v*scale for v in perimeter[idx])
            boss(x,z,r,.005,material,6)

    base, edge = {
        'imperial_oval':('red','bronze'),'vlandic_heater':('red','rawhide'),
        'vlandic_pavise':('red','dark_iron'),'sturgian_ironbound':('blue','dark_iron'),
        'nord_painted_round':('dark_wood','rawhide'),'battanian_hide_oval':('leather','rawhide'),
        'khuzait_wicker':('wicker','leather'),'aserai_daraqa':('leather','brass'),
        'merc_buckler':('steel','dark_iron'),'relic_aegis':('bronze','gold')}[name]
    # Concentric sections keep the visible front curved between the centre and edge.
    rings = [[(x*s,face(x*s,z*s)+d,z*s) for x,z in perimeter] for s,d in
             [(.07,.024),(.5,.024),(.988,.024),(1,.018),(1,.005),(.99,0),(.5,0),(.07,0)]]
    out.append(swept(rings,base))
    rim(.986, .0045 if buckler else .008, edge)
    # The central portion of the handle passes exactly through the grip origin.
    grip = .046 if buckler else .078
    out.append(tube([(-grip*1.45,face(grip,0)+.022,0),(-grip*1.27,-.020,0),
                     (-grip,0,0),(grip,0,0),(grip*1.27,-.020,0),
                     (grip*1.45,face(grip,0)+.022,0)],.012, 'dark_wood' if not buckler else 'dark_iron',8))
    out.append(tube([(-grip,0,0),(-grip*.75,0,0),(0,0,0),(grip*.75,0,0),(grip,0,0)],
                    [.013,.014,.016,.014,.013],'leather',10))
    if name == 'imperial_oval':
        rim(.925,.003,'sand')
        boss(0,0,.105,.07,'bronze')
        for sign in [-1,1]:
            def branch(t):
                return (sign*(.032+.212*sin(pi*t*.93)), -.34+.64*t)
            line([branch(i/14) for i in range(15)],.004,'brass')
            for i in range(9):
                t = .08+i*.095
                x,z=branch(t)
                for side in [-1,1]:
                    dx=sign*.053*side
                    dz=.035+.014*(1-t)
                    plate([(x,z),(x+dx*.48-.009,z+dz*.6+.005),(x+dx,z+dz),
                           (x+dx*.52+.009,z+dz*.4-.005)],'sand',.006)
    elif name == 'vlandic_heater':
        # Sweep each painted band across the curved face. Its ends taper inward
        # with the heater silhouette and leave the inner border visible.
        for top,bottom,top_span,bottom_span,material in [
                (.230,.128,.244,.232,'gold'),(.107,.084,.229,.225,'sand')]:
            sections = []
            for station in range(-12,13):
                t = station/12
                section = []
                for apex,span,lift in [(top,top_span,.003),(bottom,bottom_span,.003),
                                       (bottom,bottom_span,.005),(top,top_span,.005)]:
                    x = t*span
                    z = apex-.71*abs(x)
                    section.append((x,face(x,z)-lift,z))
                sections.append(section)
            out.append(swept(sections,material))
        rim(.935,.004,'gold')
        pins(.90,'brass',12)
    elif name == 'vlandic_pavise':
        for s in [-1,1]:
            plate([(s*.075,-.55),(s*.125,-.53),(s*.167,.55),(s*.108,.55)],'sand',.008)
            for level in [-.31,.02,.35]:
                plate([(s*.157,level),(s*.245,level+.075),(s*.292,level+.15),
                       (s*.205,level+.074)],'gold',.008)
        # The raised longitudinal crest tapers towards its metal shoe.
        out.append(swept([[(x*width,face(0,z)+y*depth,z) for x,y in
                            [(-1,.01),(1,.01),(.82,-.38),(.18,-1),(-.18,-1),(-.82,-.38)]]
                          for z,width,depth in [(-.62,.023,.024),(-.46,.044,.046),
                                               (.33,.057,.064),(.59,.045,.048),(.634,.028,.03)]],'dark_wood'))
        rim(.94,.004,'sand')
        pins(.91,'brass',12)
    elif name == 'sturgian_ironbound':
        for angle in [0,pi*.5]:
            for side in [-1,1]:
                def rot(x,z):
                    return (side*(x*cos(angle)-z*sin(angle)),side*(x*sin(angle)+z*cos(angle)))
                plate([rot(x,z) for x,z in [(.06,-.032),(.13,-.022),(.39,-.020),(.41,-.027),
                                              (.41,.027),(.39,.02),(.13,.022),(.06,.032)]],'dark_iron',.009)
                for r in [.18,.34]:
                    x,z=rot(r,0)
                    boss(x,z,.009,.005,'steel',6)
        boss(0,0,.11,.077,'dark_iron')
        rim(.94,.006,'steel')
    elif name == 'nord_painted_round':
        def clip(poly,axis,bound,sign):
            new=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                start,end = sign*(a[axis]-bound),sign*(b[axis]-bound)
                if start>=0: new.append(a)
                if (start<0) != (end<0):
                    t=start/(start-end)
                    new.append(tuple(a[k]+(b[k]-a[k])*t for k in range(2)))
            return new
        for i in range(8):
            for s in [-1,1]:
                section=clip(clip(clip([(x*.972,z*.972) for x,z in perimeter],
                                       0,(i/4-1)*w+.001,1),0,((i+1)/4-1)*w-.001,-1),1,.001*s,s)
                if len(section)>=3:
                    plate(section,'white' if (i<4) == (s>0) else 'blue',.005)
        boss(0,0,.119,.078,'dark_iron')
        pins(.935,'dark_iron',12)
    elif name == 'battanian_hide_oval':
        for s in [-1,1]:
            path=[(s*(.117+.060*(1-i/42)*cos(i*.22)),.037+.074*(1-i/42)*sin(i*.22))
                  for i in range(40)]
            line(path,.004,'bronze')
        for s in [-1,1]:
            out.append(swept([[(x*width,face(0,z*s)-d*depth,z*s) for x,d in
                               [(-1,0),(1,0),(.58,.68),(0,1),(-.58,.68)]]
                              for z,width,depth in [(.002,.055,.05),(.13,.051,.045),
                                                    (.25,.021,.028),(.428,.021,.018),(.455,.005,.01)]],'bronze'))
        pins(.93,'rawhide',14,.006)
    elif name == 'khuzait_wicker':
        line([((.07+.328*i/196)*cos(tau*i/20),(.07+.328*i/196)*sin(tau*i/20))
              for i in range(197)],.009,'wicker',.008,4)
        for i in range(12):
            a=tau*i/12
            line([(r*cos(a),r*sin(a)) for r in [.306,.338,.37,.401]],.005,'teal',.018)
        boss(0,0,.092,.056,'steel')
    elif name == 'aserai_daraqa':
        rim(.90,.004,'brass')
        rim(.865,.0025,'green')
        for i in range(8):
            a=tau*i/8
            x,z=.235*cos(a),.235*sin(a)
            plate([(x+u*cos(a)-v*sin(a),z+u*sin(a)+v*cos(a))
                   for u,v in [(-.039,0),(0,.013),(.065,0),(0,-.013)]],'brass',.004)
        for sx in [-1,1]:
            for sz in [-1,1]:
                boss(.09*sx,.09*sz,.047,.03,'brass',16)
    elif name == 'merc_buckler':
        boss(0,0,.106,.091,'steel',32)
        rim(.84,.004,'steel')
        pins(.735,'brass',8,.006)
    else:
        for i in range(16):
            a=tau*i/16
            points=[(.110,-.020),(.194,.004),(.335,.056),(.244,.015),(.165,-.018)]
            poly=[(r*cos(a)-k*sin(a),r*sin(a)+k*cos(a)) for r,k in points]
            # Two tapered strokes describe each engraved ray.
            line([poly[0],poly[1],poly[2]],.0032,'dark_iron',sides=4)
            line([poly[0],poly[-1],poly[-2],poly[2]],.0024,'gold',sides=4)
        rim(.88,.0035,'dark_iron')
        rim(.91,.003,'gold')
        boss(0,0,.113,.060,'bronze')
    return {'':out}
