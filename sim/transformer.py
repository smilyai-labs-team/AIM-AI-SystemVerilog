"""Small functional kernels for correctness, not an optimized runtime."""
import math
from .aim import gemm


def rmsnorm(x, weight, epsilon=1e-6):
    if len(x)!=len(weight) or not x: raise ValueError('shape')
    scale=1/math.sqrt(sum(v*v for v in x)/len(x)+epsilon)
    return [v*scale*w for v,w in zip(x,weight)]


def rope(x, position, base=10000.0):
    if len(x)%2: raise ValueError('even head dimension required')
    out=x[:]
    for i in range(0,len(x),2):
        angle=position/(base**(i/len(x)))
        co,si=math.cos(angle),math.sin(angle)
        out[i]=x[i]*co-x[i+1]*si
        out[i+1]=x[i]*si+x[i+1]*co
    return out


def attention(q,k,v,causal=True):
    """Stable online softmax (one query at a time), q/k/v are token x dim."""
    if not q or not k or len(k)!=len(v): raise ValueError('shape')
    d=len(q[0]); dv=len(v[0]); output=[]
    if not d or any(len(row)!=d for row in q+k) or any(len(row)!=dv for row in v): raise ValueError('shape')
    for qi,row in enumerate(q):
        mx=-math.inf; denom=0.;acc=[0.]*dv
        for ki,key in enumerate(k):
            if causal and ki>qi: continue
            score=sum(a*b for a,b in zip(row,key))/math.sqrt(d)
            new_max=max(mx,score)
            old_weight=math.exp(mx-new_max) if mx!=-math.inf else 0.
            new_weight=math.exp(score-new_max)
            denom=denom*old_weight+new_weight
            acc=[a*old_weight+new_weight*b for a,b in zip(acc,v[ki])]
            mx=new_max
        if denom==0: raise ValueError('empty context')
        output.append([a/denom for a in acc])
    return output


def topk_route(logits,k):
    if not 0<k<=len(logits): raise ValueError('top-k')
    return sorted(range(len(logits)),key=lambda i:(-logits[i],i))[:k]


def swiglu(gate,up):
    if len(gate)!=len(up): raise ValueError('shape')
    return [g/(1+math.exp(-g))*u for g,u in zip(gate,up)]
