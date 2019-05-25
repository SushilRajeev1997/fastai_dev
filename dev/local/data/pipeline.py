#AUTOGENERATED! DO NOT EDIT! File to edit: dev/02_data_pipeline.ipynb (unless otherwise specified).

__all__ = ['Transform', 'Pipeline', 'PipedList', 'Pipelines']

from ..imports import *
from ..test import *
from ..core import *
from ..notebook.showdoc import show_doc

@docs
class Transform():
    "A function that `encodes` if `filt` matches, and optionally `decodes`, with an optional `setup`"
    order,filt = 0,None

    def __init__(self, encodes=None, **kwargs):
        if encodes is not None: self.encodes=encodes
        for k,v in kwargs.items(): setattr(self, k, v)

    @classmethod
    def create(cls, f, filt=None):
        "classmethod: Turn `f` into a `Transform` unless it already is one"
        return f if hasattr(f,'decode') or isinstance(f,Transform) else cls(f)

    def _filt_match(self, filt): return self.filt is None or self.filt==filt
    def __call__(self, o, filt=None, **kwargs): return self.encodes(o, **kwargs) if self._filt_match(filt) else o
    def __getitem__(self, x): return self(x)
    def decode  (self, o, filt=None, **kwargs): return self.decodes(o, **kwargs) if self._filt_match(filt) else o
    def decodes(self, o, *args, **kwargs): return o
    def __repr__(self): return str(self.encodes) if self.__class__==Transform else str(self.__class__)
    def show(self, o, filt=None, **kwargs): return self.shows(self.decode(o, filt=filt), **kwargs)

    _docs=dict(__call__="Call `self.encodes` unless `filt` is passed and it doesn't match `self.filt`",
              decode="Call `self.decodes` unless `filt` is passed and it doesn't match `self.filt`",
              decodes="Override to implement custom decoding",
              show="Call `shows` with decoded `o`")

@docs
class Pipeline():
    "A pipeline of composed (for encode/decode) transforms, setup one at a time"
    def __init__(self, tfms):
        self.tfms,self._tfms = [],[Transform.create(t) for t in listify(tfms)]

    def setup(self, items=None):
        "Transform setup"
        self.add(self._tfms, items)
        self._tfms = None

    def add(self, tfms, items=None):
        "Call `setup` on all `tfms` and append them to this pipeline"
        for t in sorted(listify(tfms), key=lambda o: getattr(o, 'order', 0)):
            self.tfms.append(t)
            if hasattr(t, 'setup'): t.setup(items)

    def composed(self, x, rev=False, fname='__call__', **kwargs):
        "Compose `{fname}` of all `self.tfms` (reversed if `rev`) on `x`"
        tfms = reversed(self.tfms) if rev else self.tfms
        for f in tfms: x = opt_call(f, fname, x, **kwargs)
        return x

    def __call__(self, x, **kwargs): return self.composed(x, **kwargs)
    def __getitem__(self, x): return self(x)
    def decode(self, x, **kwargs): return self.composed(x, rev=True, fname='decode', **kwargs)
    def decode_at(self, idx): return self.decode(self[idx])
    def show_at(self, idx): return self.show(self[idx])
    def __repr__(self): return str(self.tfms)
    def delete(self, idx): del(self.tfms[idx])
    def remove(self, tfm): self.tfms.remove(tfm)

    def show(self, o, *args, **kwargs):
        "Find last transform that supports `shows` and call it"
        for t in reversed(self.tfms):
            if hasattr(t, 'shows'): return t.show(o, *args, **kwargs)
            o = getattr(t, 'decode', noop)(o)

    _docs = dict(__call__="Compose `__call__` of all `tfms` on `x`",
                decode="Compose `decode` of all `tfms` on `x`",
                decode_at="Decoded item at `idx`",
                show_at="Show item at `idx`",
                delete="Delete transform `idx` from pipeline",
                remove="Remove `tfm` from pipeline")

@docs
class PipedList(GetAttr):
    "A `Pipeline` of transforms applied to a collection of `items`"
    _xtra = 'decode __call__ show'.split()

    def __init__(self, items, tfms):
        self.items = ListContainer(items)
        self.default = self.tfm = Pipeline(tfms)
        self.tfm.setup(self)

    def __getitem__(self, i):
        "Transformed item(s) at `i`"
        its = self.items[i]
        return its.mapped(self.tfm) if is_iter(i) else self.tfm(its)

    def decode_at(self, idx): return self.decode(self[idx])
    def show_at(self, idx): return self.show(self[idx])
    def __eq__(self, b): return all_equal(self, b)
    def __len__(self): return len(self.items)
    def __repr__(self): return f"{self.__class__.__name__}: {self.items}\ntfms - {self.tfm}"

    _docs = dict(decode_at="Decoded item at `idx`",
                 show_at  ="Show item at `idx`")

class Pipelines(Transform):
    "Create a `Pipeline` for each tfm in `tfms`. Generally used inside a `PipedList`"
    def __init__(self, tfms): self.activ,self.tfms = None,[Pipeline(t) for t in listify(tfms)]
    def __repr__(self): return f'Pipelines({self.tfms})'

    def encodes(self, o, *args, **kwargs):
        "List of output of each of `tfms` on `o`"
        if self.activ is not None: return self.activ(o, *args, **kwargs)
        return [t(o, *args, **kwargs) for t in self.tfms]

    def decodes(self, o, **kwargs):
        return [t.decode(p, **kwargs) for p,t in zip(o,self.tfms)]

    def show(self, o, ctx=None, **kwargs):
        "Show result of `show` from each of `tfms`"
        for p,t in zip(o,self.tfms): ctx = t.show(p, ctx=ctx, **kwargs)
    def shows(self): pass # needed for `Pipeline` method search for `show`

    def setup(self, o):
        "Setup each of `tfms` independently"
        for tfm in self.tfms:
            self.activ = tfm
            tfm.setup(o)
        self.activ=None

    @classmethod
    def create(cls, items, tfms, xtra=None):
        "PipedList over `items` with `tfms` `Pipelines` as first tfm optionally followed by any `xtra` tfms"
        return PipedList(items, [cls(tfms)]+listify(xtra))

    xt,yt = add_props(lambda i,x:x.tfms[i])