"""Small swept-surface constructors for original inventory and shield sculptures."""
from math import cos, sin, sqrt, tau


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(v, k):
    return tuple(x * k for x in v)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(v):
    return mul(v, 1 / sqrt(dot(v, v)))


def swept(rings, material, loop=False):
    """Join consistently indexed sections, triangulating the two convex end caps."""
    n = len(rings[0])
    v = [p for row in rings for p in row]
    faces = []
    for j in range(len(rings) if loop else len(rings)-1):
        current, following = j*n, (j+1) % len(rings)*n
        for i in range(n):
            nxt = (i+1) % n
            faces.append((current+i, current+nxt, following+nxt, following+i))
    if not loop:
        for base, rev in [(0, True), ((len(rings)-1)*n, False)]:
            center = tuple(sum(p[k] for p in v[base:base+n])/n for k in range(3))
            ci = len(v)
            v.append(center)
            for i in range(n):
                pair = [base+i, base+(i+1) % n]
                faces.append(tuple(([ci] + pair)[::-1] if rev else [ci] + pair))
    p0 = v[0]
    volume = sum(dot(sub(v[a[0]], p0), cross(sub(v[a[k]], p0), sub(v[a[k+1]], p0)))
                 for a in faces for k in range(1, len(a)-1))
    if volume < 0:
        faces = [tuple(reversed(face)) for face in faces]
    return (v, faces, material)


def tube(points, radius, material, sides=7, loop=False):
    tangents = []
    for i, p in enumerate(points):
        a = points[i-1] if i or loop else p
        b = points[(i+1) % len(points)] if i+1 < len(points) or loop else p
        tangents.append(unit(sub(b, a)))
    # Parallel transport avoids section flips along a curved path.
    t = tangents[0]
    up = min(((1,0,0), (0,1,0), (0,0,1)), key=lambda u: abs(dot(t, u)))
    old = unit(cross(t, up))
    rings = []
    for i, (p, t) in enumerate(zip(points, tangents)):
        local = sub(old, mul(t, dot(old, t)))
        if dot(local, local) < 1e-10:
            local = cross(t, min(((1,0,0), (0,1,0), (0,0,1)), key=lambda u: abs(dot(t,u))))
        old = unit(local)
        other = cross(t, old)
        r = radius[i] if isinstance(radius, (tuple, list)) else radius
        rings.append([add(p, add(mul(old, r*cos(tau*j/sides)), mul(other, r*sin(tau*j/sides))))
                      for j in range(sides)])
    return swept(rings, material, loop)


def lathe(center, profile, material, n=20, aspect=1.0):
    x, y, z = center
    return swept([[(x+r*cos(tau*i/n), y+aspect*r*sin(tau*i/n), z+h)
                   for i in range(n)] for h, r in profile], material)


def bead(center, radii, material, n=10):
    x, y, z = center
    rx, ry, rz = radii
    profile = [(-.97,.25),(-.67,.74),(-.18,.985),(.35,.94),(.78,.62),(.98,.2)]
    return swept([[(x+rx*r*cos(tau*i/n), y+ry*r*sin(tau*i/n), z+rz*h)
                   for i in range(n)] for h, r in profile], material)


def plank(center, size, material, corner=.005):
    x,y,z = center
    a,b,c = (s/2 for s in size)
    k = min(corner, a*.4, b*.4)
    section = [(-a+k,-b),(a-k,-b),(a,-b+k),(a,b-k),(a-k,b),(-a+k,b),(-a,b-k),(-a,-b+k)]
    bevel = min(k*.32,c*.25)
    return swept([[(x+i*s,y+j*s,z+h) for i,j in section]
                  for h,s in [(-c,.97),(-c+bevel,1),(c-bevel,1),(c,.97)]],material)


def place(part, center=(0,0,0), angle=0, tilt=0):
    """Rotate about Y then Z and translate."""
    v,f,m = part
    def transform(p):
        x,y,z = p
        xx,zz = x*cos(tilt)+z*sin(tilt), z*cos(tilt)-x*sin(tilt)
        return add((xx*cos(angle)-y*sin(angle), xx*sin(angle)+y*cos(angle), zz), center)
    return ([transform(p) for p in v],f,m)
