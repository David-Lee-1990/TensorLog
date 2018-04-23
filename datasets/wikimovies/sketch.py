import sys
import time
import random
import getopt
from tensorlog.helper.countmin_embeddings import Sketcher,Sketcher2
from tensorlog.helper.fast_sketch import FastSketcher,FastSketcher2
from tensorlog import comline,matrixdb

def path_1(db,sk,M_edge,rel):
  native_p = 0
  sketch_p = 0
  n = db.dim()
  k=0
  errors=[]
  for x in range(n):
      #xsymb = "qtrain%04d"%x#db.asSymbol(x)
      xsymb = db.asSymbol(x)
      if xsymb == None: continue
      if not xsymb.startswith("qtrain"): continue
      k+=1
      start = time.time()
      q = db.onehot(xsymb)
      a = q.dot(M_edge)
      native_t = time.time()
      sq = sk.sketch(q)
      sa = sk.follow(rel,sq)
      sketch_t = time.time()
      native_p += native_t-start
      sketch_p += sketch_t - native_t
      fp,fn = sk.compareRows(a,sk.unsketch(sa),interactive=False)
      errors.append( (len(fp),len(fn)) )
  print "native qps",k/native_p
  print "sketch qps",k/sketch_p
  fp = [p for p,n in errors]
  fn = [n for p,n in errors]
  print "min / avg / max fp:",min(fp),sum(fp)/k,max(fp)
  print "#fn > 0:",sum(1 if n>0 else 0 for n in fn )

def probe(db,sk,M_edge,rel):
    q = db.onehot("qtrain0001")
    a = q.dot(M_edge)
    sq = sk.sketch(q)
    return sk.follow(rel,sq)
  
def path_2(db,sk,M_edges,rel):
  native_p = 0
  sketch_p = 0
  n = db.dim()
  k=0
  errors=[]
  for x in range(n):
      #xsymb = "qtrain%04d"%x#db.asSymbol(x)
      xsymb = db.asSymbol(x)
      if xsymb == None: continue
      if not xsymb.startswith("qtrain"):continue
      k+=1
      start = time.time()
      q = db.onehot(xsymb)
      a = q.dot(M_edges[0]).dot(M_edges[1])
      native_t = time.time()
      sq = sk.sketch(q)
      sa = sk.follow(rel[1],sk.follow(rel[0],sq))
      sketch_t = time.time()
      native_p += native_t - start
      sketch_p += sketch_t - native_t
      fp,fn = sk.compareRows(a,sk.unsketch(sa),interactive=False)
      errors.append( (len(fp),len(fn)) )
  print "native qps",k/native_p
  print "sketch qps",k/sketch_p
  fp = [p for p,n in errors]
  fn = [n for p,n in errors]
  print "min / avg / max fp:",min(fp),sum(fp)/k,max(fp)
  print "#fn > 0:",sum(1 if n>0 else 0 for n in fn )

defaults = 'sketch-train-250.db|inputs/train-250.cfacts 9'.split()
def do_expt():
  if len(sys.argv)<2:
      print "sample usage:"
      print sys.argv[0],"--db '%s' --rel mentions_entity,directed_by --k %s --seed 314159" % tuple(defaults)
      exit(0)
      
  optlist,args = getopt.getopt(sys.argv[1:],'x',["db=","x=", "rel=","k=","delta=","seed="])
  optdict = dict(optlist)
  print "Ignoring types"
  matrixdb.conf.ignore_types = True
  print 'loading db...'
  #db = matrixdb.MatrixDB.loadFile('g10.cfacts')
  print 'optdict',optdict
  db = comline.parseDBSpec(optdict.get('--db',defaults[0]))
  #db.listing()
  print "db nnz:",db.size()
  rels = optdict.get('--rel','mentions_entity,directed_by').split(",")
  k = int(optdict.get('--k',defaults[1]))
  delta = float(optdict.get('--delta','0.01'))
  seed = optdict.get('--seed',-1)
  
  M_edge = [db.matEncoding[(rel,2)] for rel in rels]

  n=db.dim()
  data = []
  for sclass in [FastSketcher2,
                 FastSketcher,
                 Sketcher2,
                 Sketcher]:
      if seed>0: random.seed(seed)
      start = time.time()
      sk = sclass(db,k,delta/n,verbose=False)
      sk.describe()
      print "load",time.time()-start,"sec"
      #foo = probe(db,sk,M_edge[0],rels[0])
      #data.append( (foo,sk) )
      path_1(db,sk,M_edge[0],rels[0])
      path_2(db,sk,M_edge,rels)
  return data

def do_diagnostic():
  matrixdb.conf.ignore_types=True
  db = comline.parseDBSpec("sketch-train-250.db|inputs/train-250.cfacts")


if __name__=='__main__':
  data=do_expt()
