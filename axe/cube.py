from __future__ import division
from lib    import *
from demos  import *
from counts import *
from table  import *
import sys
sys.dont_write_bytecode = True

def sides0(**also):
  return Thing().override(also)

dists={}
def dist(t,x,y,opt):
  if not opt.cache:
    return dist0(t,x,y,opt)
  k1=(x._id,y._id)
  k2=(y._id,x._id)
  if k1 in dists:
    return dists[k1]
  tmp = dist0(t,x,y,opt)
  dists[k1] = dists[k2] = tmp
  return tmp

def dist0(t,x,y,opt):
  d,n    = 0, 0.0001
  cellsX = opt.cells(x)
  cellsY = opt.cells(y)
  for h in opt.what(t):
    a = cellsX[h.col]
    b = cellsY[h.col]
    missa =  a == opt.missing
    missb =  b == opt.missing
    if missa and missb: continue
    b  =  h.far(a) if missb else b
    a  =  h.far(b) if missa else a
    d += h.w*h.dist(a,b)
    n += h.w
  return d**0.5/n**0.5

def furthests(t,b4,opt):
  out,d = None,0
  for x in t._rows:
    if not x in b4: 
      tmp = sum(dist(t,x,y,opt) for y in b4)
      if tmp > d:
        out,d = x,tmp
  return out,d

def furthest(t,x,opt):
  out,d = x,0
  for y in t._rows:
    tmp = dist(t,x,y,opt)
    if tmp > d:
      out,d = y,tmp
  return out,d

def closest(t,x,opt):
  out,d = x,10**32
  for y in t._rows:
    if not x._id == y._id: 
      tmp = dist(t,x,y,opt)
      if tmp < d:
        out,d = y,tmp
  return out,d

def mostDistant(t,rows,opt):
  one,two,d=None,None,0
  for x in rows:
    y,tmp = furthest(t,x,opt)
    if tmp > d:
      one,two,d=x,y,tmp
  return x,y,d
    
def twoDistant(t,rows,opt):
  one     = any(rows)
  two,_   = furthest(t,one,opt)
  three,d = furthest(t,two,opt)
  return two,three,d

def leaves(t):
  if  t._kids: 
    for kid in t._kids:
      for leaf in leaves(kid):
        yield leaf
  else:
    yield t

def loo(tbl1,some=None):
  rows = map(lambda x :x.cells,tbl1._rows)
  if some:
    rows = shuffle(rows)
  for n in xrange(len(rows)):
    if some and n < some:
      tbl2=clone(tbl1, rows[:n] + rows[n+1:])
      yield Row(rows[n]),tbl2

def nearest1(ds):
  return ds[0][1]

def nearest2(ds):
  if len(ds)==1: return ds[0][1]
  d0,n0 = ds[0]; w0 = 1/d0
  d1,n1 = ds[1]; w1 = 1/d1
  ws    = w0 + w1
  return (w0*n0 + w1*n1)/ws

def weights(tbl0,opt,cr=0.3,f=0.5,size=30,big=0.5,lives0=5,better=lambda x,y: x < y,best0=10**32):
  def reweigh(new):
    for w,what in zip(new,opt.what(tbl)):
      what.w = w
  def candidate0():
    return [rand() for _ in opt.what(tbl)]
  def move1(old,new):
    j = random.randint(0,len(old))
    new[j] = old[j]
    return new  
  def zeroOne(x): return x % 1
  def score(new):
    reweigh(new)
    s=Num()
    for _ in range(20):
      test   = any(tbl._rows)
      near,_ = closest(tbl,test,opt)
      want   = opt.klass(test,tbl,opt)
      got    = opt.klass(near,tbl,opt)
      s + abs(want - got)/(want + 0.00001)
    return s.median()
  tbl = clone(tbl0,[x.cells for x in tbl0._rows])
  frontier = []
  for i in range(size):
    x = candidate0()
    frontier += [(score(x),x)]
  best = 10**32
  lives = lives0
  while lives > 0:
    inc = -1
    for i in range(size):
      s0,old = frontier[i]
      new = []
      one = any(frontier)[1]
      for a,b,c in zip(one,any(frontier)[1],any(frontier)[1]):
        new += [zeroOne(a + f*(b-c) if rand()< cr else a)]
      new = move1(old,new)
      s1 = score(new)
      if better(s1,s0):
        frontier[i] = (s1,new)
        if better(s1,best): 
          best = s1
          inc  = lives0
    lives += inc
  reweigh(new)

def loos(tbl,opt):
  score=Num()
  for test,train in loo(tbl,opt.some):
    say(".")
    #weights(train,opt)
    relevant  = loos1(train,test,opt,score)
    got =   opt.how(relevant)
    want = opt.klass(test,train,opt)
    score + opt.err(got,want)
  return score

def loosMoea(tbl,opt):
  scores={}
  for h in tbl.less + tbl.more:
    score = Num()
    score.h = h
    scores[h.col] = score
  for test,train in loo(tbl,opt.some):
    say(".")
    cells = opt.cells(test)
    neighbors = loos1(train,test,opt,score)
    relevant = neighbors[0][2]
    tbl1 = clone(tbl,[opt.cells(r) for r in relevant.rows])
    for h in tbl1.less + tbl1.more:
      got = h.median()
      want= cells[h.col]
      scores[h.col] + opt.err(got,want)
  for score in scores.values():
    print score.h.name, score.median(), score.iqr()

def loos1(train,test,opt,score): 
  tree = idea(train,opt=opt)
  wsd  = sum(leaf.wsd for leaf in leaves(tree))
  first = None
  lives,n = opt.retry,0
  while lives > 1:
    n += 1
    lives -= 1
    tree1 = idea(train,opt=opt)
    wsd1 = sum(leaf.wsd for leaf in leaves(tree1))
    first = first or wsd1
    if wsd1 < wsd:
      lives = min(opt.retry,lives+opt.retry)
      wsd,tree = wsd1,tree1
    #print n,lives,first,wsd, int(100*wsd/first)
  ns = [len(l.rows) for l in leaves(tree)]
  print ':clusters',len(ns),':using',sum(ns), ns
  a = dist(train,test,tree.west,opt)
  b = dist(train,test,tree.east,opt)
  c = tree.c
  x1 = (a**2 + c**2 - b**2)/(2*c)
  y1 = max(0,(a**2 - x1**2))**0.5
  d = lambda  x2,y2: ((x1- x2)**2 + (y1 - y2)**2)**0.5
  ds = [(d(leaf.x,leaf.y),leaf.z,leaf) 
        for leaf in leaves(tree)]
  return sorted(ds)
 
def idea(tbl,rows=None,opt=distings(),up=None,lvl=0):
  return idea1(tbl,rows=rows,opt=opt,up=up,lvl=lvl)

def idea1(t,rows=None,opt=distings(),up=None,lvl=0):
  here   = Thing(t=t,_up=up,_kids=[],cuts=[],rows=rows,
                 west=None,east=None,leafp=False)
  if not rows:
    rows = t._rows
  west,east,c= opt.two(t,rows,opt)
  return idea2(t,here,rows,west,c,east,opt,lvl)

def idea2(     t,here,rows,west,c,east,opt,lvl):
  if lvl > opt.deep:
    return here
  all= Num(opt.klass(row,t,opt) for row in rows)
  here.all=all
  if opt.verbose:   
    saysln('|..' * lvl,here._id,len(rows),
         g3(c),':med',all.median(),':iqr',all.iqr())
  cache = []
  for row in rows:
    a = dist(t,row,west,opt)
    b = dist(t,row,east,opt)
    if a > c:
      return idea2(t,here,rows,row, a,east,opt,lvl)
    if b > c:
      return idea2(t,here,rows,west,b, row,opt,lvl)
    x = (a**2 + c**2 - b**2)/(2*c)
    if not row.x0:
      row.x0 = x
      row.y0 = max(0,a**2 - x**2)**0.5
    cache += [(x,opt.klass(row,t,opt),row)]
    #cache += [(x,x,row)]
  xs = [row.x0 for row in rows]
  ys = [row.y0 for row in rows]
  zs = all.median()
  here.x, here.y, here.z = g2(median(xs)),g2(median(ys)),zs
  here.west = west
  here.east = east
  here.c    = c
  here.wsd  = zs * len(rows)/len(t._rows)
  for cut,sd,rows3 in sdiv(cache,tiny=opt.tiny(t)):
    some= [x[2] for x in rows3]
    if opt.tiny(t) < len(some) < len(rows) and sd < all.sd():
      here.cuts  += [cut]
      here._kids += [idea1(t,rows=some,
                         opt=opt,up=here,lvl=lvl+1)]
  return here

def fromHell(t,row,opt):
  def val(what):
    for h in what:
      cell = opt.cells(row)[h.col]
      if not cell == The.reader.missing:
        yield h,h.w,h.norm(cell)
  total = n = 0
  for h,w, val in val(t.more):
    total += w*(val**2)
    n     += w
  for h,w,val in val(t.less):
    total += w*((1-val)**2)
    n     += w
  return total**2/n**2

def sides(t,opt=distings()):
  one  = any(t._rows)
  here,_ = furthests(t,[one], opt)
  return sides1(t,furthests(t,[here],opt),
                  [here], opt)

def sides1(t, (there,perimeter), corners, opt):
  if len(corners) > opt.deep:
    return corners
  here = corners[-1]
  c    = dist(t,here,there,opt)
  #print '|..' * len(corners), perimeter/len(corners)
  for row in t._rows:
    a = dist(t,row,here, opt)
    b = dist(t,row,there,opt)
    #if b > c:
     # return sides1(t,(row,b),corners,opt)
    x = (a**2 + c**2 - b**2)/(2*c)
    row.pos += [x]
    if not row.x0:
      row.x0 = x
      row.y0 = max(0, a**2 - x**2)**0.5
  corners += [there]
  return sides1(t,
                furthests(t,corners,opt),corners,opt)


def sdiv(lst, tiny=3,cohen=0.3,
         num1=lambda x:x[0], num2=lambda x:x[1]):
  "Divide lst of (num1,num2) using variance of num2."
  #----------------------------------------------
  def divide(this,small): #Find best divide of 'this'
    lhs,rhs = Num(), Num(num2(x) for x in this)
    n0, least, cut = 1.0*rhs.n, rhs.sd(), None
    for j,x  in enumerate(this): 
      if lhs.n > tiny and rhs.n > tiny: 
        maybe= lhs.n/n0*lhs.sd()+ rhs.n/n0*rhs.sd()
        if maybe < least :  
          if abs(lhs.mu - rhs.mu) >= small:
            cut,least = j,maybe
      rhs - num2(x)
      lhs + num2(x)    
    return cut,least
  #----------------------------------------------
  def recurse(this, small,cuts):
    cut,sd = divide(this,small)
    if cut: 
      recurse(this[:cut], small, cuts)
      recurse(this[cut:], small, cuts)
    else:   
      cuts += [(num1(this[0]),sd, this)]
    return cuts
  #---| main |-----------------------------------
  n = len(lst)
  small = Num(num2(x) for x in lst).sd()*cohen
  if lst: 
    return recurse(sorted(lst,key=num1),small,[])

@demo
def _sdiv():
  "Demo code to test the above."
  import random
  bell= random.gauss
  random.seed(1)
  def go(lst,cohen=0.3,
         num1=lambda x:x[0],
         num2=lambda x:x[1]):
    print ""; print sorted(lst)[:10],"..."
    for d in  sdiv(lst,cohen=cohen,num1=num1,num2=num2):
      print d[1][0][0]
  l = [ (1,10), (2,11),  (3,12),  (4,13),
       (20,20),(21,21), (22,22), (23,23), (24,24),
       (30,30),(31,31), (32,32), (33,33),(34,34)]
  go(l,cohen=0.3)
  go(map(lambda x:(x[1],x[1]),l))
  ten     = lambda: bell(10,2)
  twenty  = lambda: bell(20,2)
  thirty  = lambda: bell(30,2)
  l=[]
  for _ in range(1000): 
    l += [(ten(),   ten()), 
          (twenty(),twenty()),
          (thirty(),thirty())]
  go(l,cohen=0.5)

@demo
def ideaed(f='data/nasa93.csv'):
  dists={}
  t=table(f)
  #seed(1)
  opt= distings(
    klass = lambda x,t,o: x.cells[t.less[0].col],
    how   = nearest1,
    tiny  = lambda x: 4,
    two   = lambda x,y,z: mostDistant(x,y,z))
  #rprint(t.klass[0]); exit()
  t=idea(t,opt=opt)
  for x in leaves(t):
    print x._id, x.all.median(),x.all.iqr(),x.x,x.y,x.z

def loosed(f='data/nasa93.csv'):
  dists={}
  t=table(f)
  opt= distings(
    klass = lambda x,t,o: x.cells[t.less[0].col],
    how   = nearest1,
    tests = 5,
    #tiny  = lambda x: 8,
    two   =  twoDistant
  #rprint(t.klass[0]); exit()
  )
  nums = loos(t,opt)
  print "", int(100*nums.median()), int(100*nums.iqr())#sorted(nums.all())

def moea(f='data/coc81dem.csv'):
  dists={}
  t=table(f)
  opt= distings(
    klass = lambda x,t,o: fromHell(t,x,o),
    how   = nearest1,
    tiny  = lambda x: 10,
    some  = 20,
    two   =  twoDistant,
    err   = lambda p,a: abs(p-a)/(a + 0.001)
  #rprint(t.klass[0]); exit()
  )
  loosMoea(t,opt)
 

@demo
def sidesed(f='data/diabetes.csv'):
  t=table(f)

if __name__ == '__main__': eval(cmd())

# July 17
# housing: 10m8 s nearest1 0.154 0.158
#           9m8 s nearest2 0.170 0.134 (dist cache)
