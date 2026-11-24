"""Original still-life inventory props. Dimensions are in metres."""
from math import cos, pi, sin, tau
from random import Random
try:
    from .prop_shapes import bead, lathe, place, plank, swept, tube
except ImportError:
    from prop_shapes import bead, lathe, place, plank, swept, tube


def box(parts,w,d,h,material='dark_wood',trim='brass',z=0):
    """An open, rebated chest with separate boards and corner hardware."""
    thick=.012
    parts.append(plank((0,0,z+.009),(w,d,.018),material))
    for s in [-1,1]:
        parts.append(plank((0,s*(d-thick)/2,z+h/2),(w,thick,h),material))
        parts.append(plank((s*(w-thick)/2,0,z+h/2),(thick,d-2*thick,h),material))
        for x in [-w*.38,w*.38]:
            parts.append(plank((x,s*(d/2+.001),z+h/2),(.016,.004,h-.003),trim,.0015))
        parts.append(plank((0,s*d/2,z+h-.006),(w+.003,.016,.014),trim,.002))
    for x in [-1,1]:
        parts.append(plank((x*w/2,0,z+h-.006),(.016,d-.016,.014),trim,.002))


def nugget(x,y,z,r,material,rng):
    n=rng.choice((5,6,7))
    aspect=rng.uniform(.57,1.02)
    angles=[tau*i/n+rng.uniform(-.125,.125) for i in range(n)]
    facets=[rng.uniform(.69,1.22) for i in angles]
    return swept([[(x+r*f*size*cos(a+turn)+dx*r, y+r*aspect*f*size*sin(a+turn),
                    z+r*(height+rng.uniform(-.045,.045))) for a,f in zip(angles,facets)]
                  for height,size,turn,dx in [(-.68,.56,0,-.12),(-.22,1,.12,0),
                                               (.37,.87,.25,.09),(.72,.38,.29,.14)]],material)


def incense(parts,rng):
    box(parts,.35,.24,.087)
    for i in range(3):
        for j in range(5):
            parts.append(nugget((j-2)*.054+rng.uniform(-.007,.007),
                                (i-1)*.057+rng.uniform(-.006,.006),
                                rng.uniform(.062,.079),rng.uniform(.023,.042),rng.choice(('resin','amber','dark_resin')),rng))
    for i in range(5):
        parts.append(nugget(rng.uniform(-.09,.09),rng.uniform(-.06,.06),
                            rng.uniform(.092,.112),rng.uniform(.025,.038),'amber',rng))
    parts.append(plank((0,-.122,.054),(.051,.005,.027),'brass',.005))
    parts.append(bead((0,-.128,.054),(.009,.005,.008),'dark_iron',8))


def jars(parts, honey):
    jarspec = [(-.103,.035,1.02),(.100,.047,.87)] if honey else [
        (-.103,.033,1.04),(.086,.055,.9),(.006,-.087,.72)]
    for i,(x,y,scale) in enumerate(jarspec):
        outline = [(0,.045),(.006,.056),(.018,.059),(.042,.069),(.091,.080),
                   (.124,.076),(.151,.06),(.17,.038),(.178,.034),(.188,.037),
                   (.192,.045),(.20,.045),(.204,.036)]
        if honey:
            outline=[(h,r*(1.12 if .025<h<.16 else 1)) for h,r in outline]
        parts.append(lathe((x,y,0),[(h*scale,r*scale) for h,r in outline],'clay',20))
        if honey:
            # Scalloped dipped-linen cap with a tied waist.
            n=20
            rings=[[(x+r*scale*cos(tau*k/n),y+r*scale*sin(tau*k/n),
                     scale*(h+amplitude*cos(5*tau*k/n+.42*i))) for k in range(n)]
                   for h,r,amplitude in [(.17,.052,.007),(.178,.042,.003),
                                          (.198,.045,0),(.208,.042,.002),(.211,.015,.001)]]
            parts.append(swept(rings,'linen'))
            parts.append(lathe((x,y,0),[(.181*scale,.041*scale),(.185*scale,.042*scale),
                                        (.188*scale,.041*scale)],'wicker',16))
        else:
            parts.append(lathe((x,y,0),[(.201*scale,.029*scale),(.223*scale,.031*scale),
                                        (.228*scale,.026*scale)],'ash',12))
            colour=['purple','blue','red'][i]
            # Pigment follows the shoulder through the lower lip, pooling in two drips.
            for delta,width,bottom in [(0,.29,.104),(.33,.15,.137)]:
                a=-pi/2+delta+.13*i
                rings=[]
                for h,r,s in [(bottom,.08 if bottom<.12 else .069,.18),
                              (.15,.061,.65),(.17,.039,.85),(.185,.039,1),(.201,.046,.95)]:
                    rings.append([(x+(r+off)*scale*cos(a+side*width*s),
                                   y+(r+off)*scale*sin(a+side*width*s),h*scale)
                                  for side,off in [(-1,-.001),(1,-.001),(1,.002),(-1,.002)]])
                parts.append(swept(rings,colour))
    if honey:
        center=(.015,-.105,.041)
        tilt=pi*.49
        profile=[(-.157,.007),(-.147,.011),(-.13,.008),(.075,.006),(.082,.014)]
        for j in range(5):
            h=.083+j*.009
            r=.022-.0017*abs(j-2)
            profile.extend([(h,r*.8),(h+.0015,r),(h+.005,r),(h+.007,r*.58)])
        profile.append((.134,.007))
        parts.append(place(lathe((0,0,0),profile,'ash',14),center,-.24,tilt))


def glassware(parts,rng):
    box(parts,.39,.265,.098,'ash','dark_wood')
    parts.append(plank((0,0,.065),(.355,.237,.055),'wicker'))
    for i in range(16):
        x,y=rng.uniform(-.166,.166),rng.uniform(-.103,.103)
        a=rng.uniform(0,tau)
        parts.append(tube([(x+t*.029*cos(a),y+t*.029*sin(a),.091+.008*sin(pi*t)+.006*t)
                           for t in [-1,-.33,.33,1]],.0025,'sand',4))
    for i,(x,y,k) in enumerate([(-.117,.052,1.02),(-.024,.053,.87),(.095,.058,.97)]):
        profile=[(0,.024),(.004,.036),(.018,.04),(.086,.04),(.107,.038),
                 (.132,.019),(.154,.014),(.18,.014),(.184,.020),(.191,.020),
                 (.193,.012),(.164,.010)]
        parts.append(lathe((x,y,.082),[(h*k,r*k) for h,r in profile],'glass',12))
    for x,y in [(-.10,-.058),(.010,-.064),(.103,-.047)]:
        parts.append(lathe((x,y,.085),[(0,.024),(.004,.03),(.009,.026),(.018,.018),
                                      (.033,.022),(.062,.038),(.071,.039),(.072,.036),
                                      (.062,.034),(.027,.014)],'glass',12))


def cask(parts, pitch):
    profile=[(0,.108),(.042,.122),(.11,.137),(.17,.139),
             (.232,.129),(.292,.112),(.297,.106)]
    body_material='dark_wood' if pitch else 'ash'
    pieces=[]
    # Each stave has a narrow chamfer along each edge.
    for i in range(14):
        a,b=tau*i/14,tau*(i+1)/14
        rings=[]
        for h,r in profile:
            angles=[a+.008,a+.016,(a+b)/2,b-.016,b-.008,b-.008,(a+b)/2,a+.008]
            radii=[r-.002,r,r,r,r-.002,r-.012,r-.012,r-.012]
            rings.append([(rad*cos(angle),rad*sin(angle),h) for rad,angle in zip(radii,angles)])
        pieces.append(swept(rings,body_material))
    for h,r in [(.024,.119),(.085,.133),(.202,.137),(.264,.122)]:
        pieces.append(lathe((0,0,0),[(h-.006,r-.0005),(h-.004,r+.002),
                                     (h+.006,r+.002),(h+.008,r-.0005)],'dark_iron',18))
    pieces.append(lathe((0,0,0),[(.002,.104),(.013,.104)],body_material,24))
    if pitch:
        pieces.append(lathe((0,0,0),[(.263,.103),(.275,.102),(.278,.089),(.276,.028)],'black',24))
        for i in range(3):
            a=4.2+i*.15
            pieces.append(tube([(r*cos(a),r*sin(a),h) for h,r in
                                [(.276,.085),(.296,.104),(.286,.115),(.253-.014*i,.125+i*.003)]],
                               [.004,.007,.006,.0025],'black',6))
        pieces.append(tube([(.006,.014,.266),(.052,.024,.308),(.16,.056,.403)],
                           [.012,.009,.009],'dark_wood'))
        pieces.append(bead((.012,.013,.281),(.032,.022,.010),'dark_iron'))
        parts.extend(pieces)
    else:
        pieces.append(lathe((0,0,0),[(.281,.104),(.288,.103)],'dark_wood',24))
        for y in [-.055,0,.055]:
            half=(.10**2-y**2)**.5
            pieces.append(tube([(-half,y,.289),(half,y,.289)],.0018,'ash',5))
        pieces.append(lathe((0,0,.29),[(0,.023),(.006,.023),(.013,.018)],'ash',14))
        for angle in [0,2.09,4.19]:
            pieces.append(tube([(0,0,.304),(.012*cos(angle),.012*sin(angle),.304)],.0013,'dark_wood',5))
        parts.extend(place(p,(-.148,0,.154),-.13,pi/2) for p in pieces)
        for x in [-.091,.093]:
            parts.append(plank((x,-.015,.018),(.041,.205,.036),'dark_wood'))
            for s in [-1,1]:
                parts.append(plank((x,s*.084-.016,.039),(.041,.035,.046),'dark_wood'))


def amber(parts,rng):
    n=26
    heights=[(0,.065,.01),(.012,.088,.04),(.060,.111,.075),(.105,.096,.075),
             (.138,.069,.09),(.149,.072,.09),(.179,.092,.16),(.183,.086,.16),
             (.154,.062,.09),(.124,.056,.065)]
    rings=[]
    for z,r,wave in heights:
        rings.append([((r*(1+wave*cos(7*a+.7)))*cos(a),
                       .78*(r*(1+wave*cos(7*a+.7)))*sin(a),
                       z+(.007*cos(5*a+.1) if z>.16 else 0))
                      for a in [tau*i/n for i in range(n)]])
    parts.append(swept(rings,'leather'))
    for z in [.141,.146]:
        parts.append(tube([(.074*cos(a),.057*sin(a),z+.002*sin(2*a)) for a in
                           [tau*i/26 for i in range(26)]],.003,'rawhide',6,True))
    for s in [-1,1]:
        parts.append(tube([(.016,-.056,.147),(.027+s*.012,-.064,.125),
                           (.022+s*.035,-.080,.106),(.025+s*.041,-.078,.092)],.003,'rawhide'))
    for i in range(9):
        a=tau*i/9
        parts.append(nugget(.046*cos(a),.035*sin(a),rng.uniform(.160,.175),
                            rng.uniform(.025,.034),'amber',rng))
    parts.append(nugget(-.007,.004,.185,.039,'amber',rng))
    for x,y in [(.126,-.07),(.096,-.109),(.139,-.116)]:
        parts.append(nugget(x,y,.014,.021,'amber',rng))


def spiral_end(parts,c,r,m,turns=2):
    x,y,z=c
    pts=[]
    for i in range(27):
        a=tau*turns*i/26
        rad=r*(.1+.86*i/26)
        pts.append((x,y+rad*cos(a),z+rad*sin(a)))
    parts.append(tube(pts,.0016,m,4))


def carpets(parts):
    for i,(y,r,mat,pattern) in enumerate([(-.066,.060,'red','sand'),(.067,.065,'teal','brass')]):
        length=.37-.023*i
        def roll(x,prof,material,n=18):
            return place(lathe((0,0,0),prof,material,n),(x,y,r),0,pi/2)
        parts.append(roll(-length/2,[(0,r*.96),(.006,r),(length-.006,r),(length,r*.96)],mat))
        for end in [-1,1]:
            x=end*length/2
            spiral_end(parts,(x+end*.001,y,r),r,'wool')
            for off,width in [(.018,.004),(.028,.009),(.041,.003)]:
                start=x-end*off
                parts.append(roll(start-width/2,[(0,r+.001),(width,r+.001)],pattern))
        for x in [-.067,.067]:
            parts.append(roll(x,[(-.004,r+.001),(0,r+.003),(.004,r+.001)],'wicker'))
        for j in range(5):
            x=(j-2)*.052
            a=pi*.39
            pts=[(x+dx,y+(r+.0015)*cos(a+da),r+(r+.0015)*sin(a+da))
                 for dx,da in [(-.018,0),(0,.24),(.018,0),(0,-.24)]]
            parts.append(tube(pts,.002,pattern,4,True))


def scroll(parts,center,length,radius,angle):
    # Rolled sheet has a true open spiral cavity at either end.
    path=[]
    for i in range(36):
        t=i/35
        a=tau*1.45*t
        rr=radius*(.24+.76*t)
        path.append([(along*length/2, (rr+off)*cos(a), (rr+off)*sin(a))
                     for along,off in [(-1,-.0015),(1,-.0015),(1,.0015),(-1,.0015)]])
    parts.append(place(swept(path,'parchment'),center,angle))
    for x in [-.0045,.0045]:
        ring=[(x,radius*.91*cos(tau*j/16),radius*.91*sin(tau*j/16)) for j in range(16)]
        parts.append(place(tube(ring,.002,'leather',5,True),center,angle))


def parchment(parts,rng):
    for i in range(8):
        parts.append(place(plank((0,0,0),(.225,.15,.0038),'parchment',.002),
                           (-.046+rng.uniform(-.002,.002),-.045,.002+i*.0038),-.11+rng.uniform(-.02,.02)))
    for j in range(3):
        scroll(parts,(.026,.040+j*.041,.052),.31-j*.018,.023,.19)
    scroll(parts,(.031,.096,.083),.313,.022,.17)


def pearls(parts,rng):
    box(parts,.323,.218,.069,'dark_wood','bronze')
    parts.append(plank((0,0,.052),(.294,.188,.019),'purple'))
    # A hinged, moulded lid, leaning behind the lining.
    a=-.36
    def lid(x,z):
        return (x,.107-z*sin(a),.068+z*cos(a))
    parts.append(swept([[(x,.102+dy-z*sin(a),.068+z*cos(a)) for x,z in
                                       [(-.151,0),(.151,0),(.157,.01),(.157,.135),(.146,.146),
                                        (-.146,.146),(-.157,.135),(-.157,.01)]]
                                      for dy in [0,.014]],'dark_wood'))
    for i in range(5):
        x=(i-2)*.052
        parts.append(bead(lid(x,.073),(.014,.012,.026),'pearl',7))
    for i in range(16):
        a=tau*i/16
        x=.09*cos(a)-.013
        y=.047*sin(a)-.006
        r=rng.uniform(.010,.014)
        parts.append(bead((x,y,.063+r),(r,r*.96,r),'pearl',7))
    for i in range(3):
        r=rng.uniform(.011,.016)
        parts.append(bead((rng.uniform(-.055,.058),rng.uniform(-.023,.024),.065+r),
                          (r,r*.91,r*.95),'pearl',7))


def stockfish(parts):
    for j,(cx,cy,cz,angle) in enumerate([(0,-.070,.023,-.08),(.014,.004,.029,.06),
                                         (-.012,.078,.023,.13),(.004,-.014,.058,-.13)]):
        local=[]
        # Two flattened fillets join at the backbone and narrow to a forked tail.
        for s in [-1,1]:
            rings=[]
            for x,w,h in [(-.175,.011,.005),(-.145,.034,.011),(-.113,.046,.016),
                          (-.056,.052,.019),(.032,.045,.016),(.104,.024,.009),
                          (.136,.009,.004),(.158,.011,.004),(.184,.022,.002)]:
                outer=w*(1+.035*cos(53*x+j))
                rings.append([(x+skew,s*y,z) for y,z,skew in
                              [(.002,-h*.73,0),(outer*.73,-h*.55,0),(outer,0,0),
                               (outer*.70,h*.46,0),(outer*.26,h,0),(.002,h*.49,0)]])
                if x>.17:
                    rings[-1]=[(px+.012*abs(y)/w,y,z) for px,y,z in rings[-1]]
            local.append(swept(rings,'fish'))
            for k,w in enumerate([.028,.033,.036,.035,.031,.025]):
                x=-.109+k*.034
                height=.013 if k<4 else .010
                local.append(tube([(x,.004*s,height),(x+.004,.014*s,height*.89),
                                   (x+.012,s*w,height*.44)],.0018,'bone',4))
        local.append(tube([(-.147,0,.007),(-.10,0,.016),(-.04,0,.019),(.036,0,.016),
                           (.114,0,.008),(.15,0,.004)],.0032,'bone',5))
        parts.extend(place(p,(cx,cy,cz),angle) for p in local)
    for x in [-.092,.082]:
        loop=[(x,-.007+.135*cos(tau*i/18),.047+.043*sin(tau*i/18)) for i in range(18)]
        parts.append(tube(loop,.004,'wicker',6,True))
    parts.append(tube([(.081,-.132,.039),(.098,-.156,.023),(.147,-.168,.012),
                       (.163,-.151,.009)],.004,'wicker'))


def sailcloth(parts):
    # Each folded edge forms a rounded return at the side of the bolt.
    for j in range(5):
        z=.010+j*.020
        rings=[]
        for i,x in enumerate([-.18,-.175,-.12,0,.12,.176,.18]):
            b=.116+.004*cos(i+j)
            edge=.005*sin(1.3*i+j)
            section=[(-b+.006,-.009),(b-.006,-.009),(b,-.006),(b+.002,.003),
                     (b-.005,.009),(-b+.005,.009),(-b-.002,.005),(-b-.003,-.005)]
            rings.append([(x+.002*sin(j),y+edge,z+dz+.0015*sin(i+j)) for y,dz in section])
        parts.append(swept(rings,'linen' if j!=2 else 'sand'))
    for x in [-.078,.071]:
        pts=[(x,-.116,.004),(x,.116,.004),(x,.122,.013),(x,.122,.092),
             (x,.115,.106),(x,.09,.109),(x,-.090,.109),(x,-.118,.103),
             (x,-.123,.095),(x,-.123,.014)]
        for dx in [-.003,.003]:
            parts.append(tube([(a+dx,b,c) for a,b,c in pts],.004,'wicker',7,True))
    for i in range(4):
        a=tau*i/3.9
        pts=[(.075+.024*cos(tau*j/22+a),-.044+.023*sin(tau*j/22+a),.108+.005*i)
             for j in range(22)]
        parts.append(tube(pts,.0037,'wicker',6,True))
    parts.append(tube([(.073,-.019,.124),(.101,.007,.114),(.132,.020,.109),
                       (.146,.047,.107),(.160,.050,.106)],.0038,'wicker'))


def generate(entry):
    name=entry['id'].removeprefix('ce_tg_')
    rng=Random('coop-expanded:'+name)
    parts=[]
    if name in ('honey','dyes'):
        jars(parts,name=='honey')
    elif name in ('mead','pitch'):
        cask(parts,name=='pitch')
    elif name in ('incense','glassware','amber','parchment','pearls'):
        {'incense':incense,'glassware':glassware,'amber':amber,'parchment':parchment,
         'pearls':pearls}[name](parts,rng)
    else:
        {'carpets':carpets,'stockfish':stockfish,'sailcloth':sailcloth}[name](parts)
    # Unbalanced still lifes have their ground-plane origin at the centre of the footprint.
    vertices=[v for verts,_,_ in parts for v in verts]
    center=[(min(v[i] for v in vertices)+max(v[i] for v in vertices))/2 for i in [0,1]]
    floor=min(v[2] for v in vertices)
    return {'':[([(x-center[0],y-center[1],z-floor) for x,y,z in verts],faces,mat)
                for verts,faces,mat in parts]}
