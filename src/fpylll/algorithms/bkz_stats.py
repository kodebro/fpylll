# -*- coding: utf-8 -*-
"""
Collecting traces from BKZ-like computations

.. moduleauthor:: Martin R. Albrecht <fplll-devel@googlegroups.com>

"""
from __future__ import print_function
from __future__ import absolute_import

import time
import copy
from collections import OrderedDict
from math import log


def pretty_dict(d, keyword_width=None, round_bound=9999):
    """Return 'pretty' string representation of the dictionary ``d``.

    :param d: a dictionary
    :param keyword_width: width allocated for keywords
    :param round_bound: values beyond this bound are shown as `2^x`

    >>> from collections import OrderedDict
    >>> str(pretty_dict(OrderedDict([('d', 2), ('f', 0.1), ('large', 4097)])))
    '{"d":        2,  "f": 0.100000,  "large":     4097}'

    """
    s = []
    for k in d:

        v = d[k]

        if keyword_width:
            fmt = u"\"%%%ds\"" % keyword_width
            k = fmt % k
        else:
            k = "\"%s\""%k

        if isinstance(v, int):
            if abs(v) > round_bound:
                s.append(u"%s: %8s" %(k,  u"%s2^%.1f"%("" if v > 0 else "-", log(abs(v), 2))))
            else:
                s.append(u"%s: %8d"%(k, v))
            continue
        elif not isinstance(v, float):
            try:
                v = float(v)
            except TypeError:
                s.append(u"%s: %s"%(k, v))
                continue

        if 0 <= v < 10.0:
            s.append(u"%s: %8.6f"%(k, v))
        elif -10 < v < 0:
            s.append(u"%s: %8.5f"%(k, v))
        elif abs(v) < round_bound:
            s.append(u"%s: %8.3f"%(k, v))
        else:
            s.append(u"%s: %8s" %(k,  u"%s2^%.1f"%("" if v > 0 else "-", log(abs(v), 2))))

    return u"{" + u",  ".join(s) + u"}"


class Statistic(object):
    """
    A ``statistic`` collects observed facts about some random variable (e.g. running time).

    In particular,

    - minimum,
    - maximum,
    - mean and
    - variance

    are stored.

    >>> v = Statistic(1.0); v
    1.0

    >>> v += 2.0; v
    3.0

    >>> v = Statistic(-5.4, repr="avg"); v
    -5.4

    >>> v += 0.2
    >>> v += 5.2; v
    0.0

    >>> v.min, v.max
    (-5.4, 5.2)

    """

    def __init__(self, value, repr="sum", count=True):
        """
        Create a new instance.

        :param value: some initial value
        :param repr: how to represent this statistic: "min", "max", "avg", "sum" and "variance" are
            valid choices
        :param count: if ``True`` the provided value is considered as an observed datum, i.e. the
            counter is increased by one.
        """

        self._min = value
        self._max = value
        self._sum = value
        self._sqr = value*value
        self._ctr = 1 if count else 0
        self._repr = repr

    def add(self, value):
        """
        Add value to this statistic.

        >>> v = Statistic(10.0)
        >>> v.add(5.0)
        15.0

        :param value: some value
        :returns: itself

        """
        self._min = min(self._min, value)
        self._max = max(self._max, value)
        self._sum += value
        self._sqr += value*value
        self._ctr += 1
        return self

    @property
    def min(self):
        """
        >>> v = Statistic(2.0)
        >>> v += 5.0
        >>> v.min
        2.0

        """
        return self._min

    @property
    def max(self):
        """
        >>> v = Statistic(2.0)
        >>> v += 5.0
        >>> v.max
        5.0

        """
        return self._max

    @property
    def avg(self):
        """
        >>> v = Statistic(2.0)
        >>> v += 5.0
        >>> v.avg
        3.5

        """
        return self._sum/self._ctr

    @property
    def sum(self):
        """
        >>> v = Statistic(2.0)
        >>> v += 5.0
        >>> v.sum
        7.0

        """
        return self._sum

    @property
    def variance(self):
        """
        >>> v = Statistic(2.0)
        >>> v += 5.0
        >>> v.variance
        2.25

        """
        return self._sqr/self._ctr - self.avg**2

    def __add__(self, other):
        """
        Addition semantics are:

        - ``stat + None`` returns ``stat``
        - ``stat + stat`` returns the sum of their underlying values
        - ``stat + value`` inserts ``value`` into ``stat``

        >>> v = Statistic(2.0)
        >>> v + None
        2.0
        >>> v + v
        4.0
        >>> v + 3.0
        5.0

        """
        if other is None:
            return copy.copy(self)
        elif not isinstance(other, Statistic):
            ret = copy.copy(self)
            return ret.add(other)
        else:
            if self._repr != other._repr:
                raise ValueError("%s != %s"%(self._repr, other._repr))
            ret = Statistic(0)
            ret._min = min(self.min, other.min)
            ret._max = max(self.max, other.max)
            ret._sum = self._sum + other._sum
            ret._sqr = self._sqr + other._sqr
            ret._ctr = self._ctr + other._ctr
            ret._repr = self._repr
            return ret

    def __radd__(self, other):
        """
        Revert to normal addition.
        """
        return self + other

    def __float__(self):
        """
        Reduce this stats object down a float depending on strategy chosen in constructor.

        >>> v = Statistic(2.0, "min"); v += 3.0; float(v)
        2.0
        >>> v = Statistic(2.0, "max"); v += 3.0; float(v)
        3.0
        >>> v = Statistic(2.0, "avg"); v += 3.0; float(v)
        2.5
        >>> v = Statistic(2.0, "sum"); v += 3.0; float(v)
        5.0
        >>> v = Statistic(2.0, "variance"); v += 3.0; float(v)
        0.25
        """
        return float(self.__getattribute__(self._repr))

    def __str__(self):
        """
        Reduce this stats object down a float depending on strategy chosen in constructor.

        >>> v = Statistic(2.0, "min"); v += 3.0; str(v)
        '2.0'
        >>> v = Statistic(2.0, "max"); v += 3.0; str(v)
        '3.0'
        >>> v = Statistic(2.0, "avg"); v += 3.0; str(v)
        '2.5'
        >>> v = Statistic(2.0, "sum"); v += 3.0; str(v)
        '5.0'
        >>> v = Statistic(2.0, "variance"); v += 3.0; str(v)
        '0.25'
        """
        return str(self.__getattribute__(self._repr))

    __repr__ = __str__


class TraceContext(object):
    """
    A trace context collects data about an underlying process on entry/exit of particular parts of
    the code.
    """
    def __init__(self, tracer, *args, **kwds):
        """Create a new context for gathering statistics.

        :param tracer: a tracer object
        :param args: all args form a label for the trace context
        :param kwds: all kwds are considered auxiliary data

        """
        self.tracer = tracer
        self.what = args if len(args)>1 else args[0]
        self.kwds = kwds

    def __enter__(self):
        """
        Call ``enter`` on trace object
        """
        self.tracer.enter(self.what, **self.kwds)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """
        Call ``exit`` on trace object
        """
        self.tracer.exit(**self.kwds)


class Tracer(object):
    """
    A trace object is used to collect information about processes.

    This base class does nothing.
    """
    def __init__(self, instance, verbosity=False):
        """
        Create a new tracer instance.

        :param instance: BKZ-like object instance
        :param verbosity: print information, integers ≥ 0 are also accepted

        """
        self.instance = instance
        self.verbosity = int(verbosity)

    def context(self, *args, **kwds):
        """
        Return a new ``TraceCotext``.
        """
        return TraceContext(self, *args, **kwds)

    def enter(self, label, **kwds):
        """
        An implementation would implement this function which controls what happens when the context
        given by ``label`` is entered.
        """
        pass

    def exit(self, **kwds):
        """
        An implementation would implement this function which controls what happens when the context
        given by ``label`` is left.
        """
        pass


# use a dummy_trace whenever no tracing is required
dummy_tracer = Tracer(None)


class Node(object):
    """
    A simple tree implementation with labels and associated data.
    """
    def __init__(self, label, parent=None, data=None):
        """Create a new node.

        :param label: some label such as a string or a tuple
        :param parent: nodes know their parents
        :param data: nodes can have associated data which is a key-value store where typically the
            values are statistics
        """

        self.label = label
        if data is None:
            data = OrderedDict()
        self.data = OrderedDict(data)
        self.parent = parent
        self.children = []

    def add_child(self, child):
        """Add a child.

        :param child: a node
        :returns: the child

        """
        child.parent = self
        self.children.append(child)
        return child

    def child(self, label):
        """
        If node has a child labelled ``label`` return it, otherwise add a new child.

        :param label: a label
        :returns: a node

        >>> root = Node("root")
        >>> c1 = root.child("child"); c1
        {"child": {}}
        >>> c2 = root.child("child"); c2
        {"child": {}}
        >>> c1 is c2
        True

        """
        for child in self.children:
            if child.label == label:
                return child

        return self.add_child(Node(label))

    def __str__(self):
        """
        >>> str(Node("root", data={'a':1, 'b': 2}))
        '{"root": {"a":        1,  "b":        2}}'
        """
        return u"{\"%s\": %s}"%(self.label, pretty_dict(self.data))

    __repr__ = __str__

    def report(self, indentation=0, depth=None):
        """
        Return detailed string representation of this tree.

        :param indentation: add spaces to the left of the string representation
        :param depth: stop at this depth

        >>> root = Node("root")
        >>> c1 = root.child(("child",1))
        >>> c2 = root.child(("child",2))
        >>> c3 = c1.child(("child", 3))
        >>> c1.data["a"] = 100.0
        >>> c3.data["a"] = 4097

        >>> print(root.report())
        {"root": {}}
          {"('child', 1)": {"a":  100.000}}
            {"('child', 3)": {"a":     4097}}
          {"('child', 2)": {}}

        >>> print(root.report(indentation=2, depth=1))
          {"root": {}}
            {"('child', 1)": {"a":  100.000}}
            {"('child', 2)": {}}
        """
        s = [" "*indentation + str(self)]
        if depth is None or depth > 0:
            for child in self.children:
                depth = None if depth is None else depth-1
                s.append(child.report(indentation+2, depth=depth))
        return "\n".join(s)

    def sum(self, tag, include_self=True, raise_keyerror=False, label=None):
        """
        Return sum over all items tagged ``tag`` in associated data within this tree.

        :param tag: a string
        :param include_self: include data in this node
        :param raise_keyerror: if a node does not have an item tagged with ``tag`` raise a
            ``KeyError``
        :param label: filter by ``label``


        >>> root = Node("root")
        >>> c1 = root.child(("child",1))
        >>> c2 = root.child(("child",2))
        >>> c3 = c1.child(("child", 3))
        >>> c1.data["a"] = 100.0
        >>> c3.data["a"] = 4097

        >>> root.sum("a")
        4197.0

        >>> root.sum("a", label=("child",3))
        4097

        >>> root.sum("a", label=("child",2))
        0

        >>> root.sum("a", label=("child",2), raise_keyerror=True)
        Traceback (most recent call last):
        ...
        KeyError: 'a'

        """
        if include_self and (label is None or self.label == label):
            if raise_keyerror:
                r = self.data[tag]
            else:
                r = self.data.get(tag, 0)
        else:
            r = 0
        for child in self.children:
            r = r + child.sum(tag, include_self=True, raise_keyerror=raise_keyerror, label=label)
        return r

    def find(self, label, raise_keyerror=False):
        """
        Find the first child node matching label in a breadth-first search.

        :param label: a label
        :param raise_keyerror: raise a ``KeyError`` if ``label`` was not found.
        """
        for child in self.children:
            if child.label == label:
                return child
        for child in self.children:
            try:
                return child.find(label, raise_keyerror)
            except KeyError:
                pass

        if raise_keyerror:
            raise KeyError("Label '%s' not present in '%s"%(label, self))
        else:
            return None

    def merge(self, node):
        """
        Merge tree ``node`` into self.

        .. note :: The label of ``node`` is ignored.
        """

        for k, v in node.data.iteritems():
            if k in self.data:
                self.data[k] += v
            else:
                self.data[k] = v

        for child in node.children:
            self.child(child.label).merge(child)

    def get(self, label):
        """Return first child node with label ``label``

        :param label: label

        >>> root = Node("root")
        >>> _ = root.child("bar")
        >>> c1 = root.child(("foo",0))
        >>> c2 = root.child(("foo",3))
        >>> c3 = c1.child(("foo", 3))
        >>> c1.data["a"] = 100.0
        >>> c3.data["a"] = 4097
        >>> root.get("bar")
        {"bar": {}}

        >>> root.get("foo")
        ({"('foo', 0)": {"a":  100.000}}, {"('foo', 3)": {}})

        >>> root.get("foo")[0]
        {"('foo', 0)": {"a":  100.000}}
        >>> root.get("foo")[1]
        {"('foo', 3)": {}}

        """
        r = []
        for child in self.children:
            if child.label == label:
                return child
            if isinstance(child.label, tuple) and child.label[0] == label:
                r.append(child)
        if r:
            return tuple(r)
        else:
            raise AttributeError("'Node' object has no attribute '%s'"%(label))

    def __getitem__(self, tag):
        """Return associated data tagged ``tag```

        :param tag: Some tag

        >>> root = Node("root", data={"foo": 1})
        >>> c1 = root.child("foo")
        >>> root["foo"]
        1

        """
        return self.data[tag]

    @property
    def level(self):
        """
        Return level of this node, i.e. how many steps it takes to reach a node with parent
        ``None``.

        >>> root = Node("root")
        >>> _ = root.child("bar")
        >>> c1 = root.child(("foo",0))
        >>> c2 = root.child(("foo",3))
        >>> c3 = c1.child(("foo", 3))
        >>> root.level
        0
        >>> c1.level
        1
        >>> c3.level
        2

        """
        node, level = self, 0
        while node.parent is not None:
            level += 1
            node = node.parent
        return level


class TimeTreeTracer(Tracer):
    """
    Collect CPU and wall time for every context visited, creating a tree structure along the way.
    """

    entries = (("cputime", time.clock), ("walltime", time.time))

    def __init__(self, instance, verbosity=False):
        """
        Create a new tracer instance.

        :param instance: BKZ-like object instance
        :param verbosity: print information, integers ≥ 0 are also accepted

        """
        Tracer.__init__(self, instance, verbosity)
        self.trace = Node("root")
        self.current = self.trace

    def enter(self, label, **kwds):
        """
        Enter context, start tracking time.

        :param label: if a child with given label already exits, it is modified, otherwise a new
            label is created.
        """
        node = self.current.child(label)

        for t, f in TimeTreeTracer.entries:
            node.data[t] = node.data.get(t, 0) - f()

        self.current = node

    def exit(self, **kwds):
        """
        Leave context, record time spent.

        :param label: ignored

        .. note :: If verbosity ≥ to the current level, also print the current node.

        """
        node = self.current

        for t, f in TimeTreeTracer.entries:
            node.data[t] = node.data.get(t, 0) + f()

        if self.verbosity and self.verbosity >= self.current.level:
            print(self.current)

        self.current = self.current.parent


class BKZTreeTracer(Tracer):
    """
    Default tracer for BKZ-like algorithms.
    """
    def __init__(self, instance, verbosity=False, root_label="bkz", start_clocks=False):
        """
        Create a new tracer instance.

        :param instance: BKZ-like object instance
        :param verbosity: print information, integers ≥ 0 are also accepted
        :param root_label: label to give to root node
        :param start_clocks: start tracking time for the root node immediately

        """

        Tracer.__init__(self, instance, verbosity)
        self.trace = Node(root_label)
        self.current = self.trace
        if start_clocks:
            self.reenter()

    def enter(self, label, **kwds):
        """Enter new context with label

        :param label: label

        """
        self.current = self.current.child(label)
        self.reenter()

    def reenter(self, **kwds):
        """Reenter current context, i.e. restart clocks

        """

        node = self.current
        node.data["cputime"]  = node.data.get("cputime",  0) + Statistic(-time.clock(), repr="sum", count=False)
        node.data["walltime"] = node.data.get("walltime", 0) + Statistic(-time.time(),  repr="sum", count=False)

    def exit(self, **kwds):
        """
        By default CPU and wall time are recorded.  More information is recorded for "enumeration"
        and "tour" labels.  When the label is a tour then the status is printed if verbosity > 0.
        """
        node = self.current
        label = node.label

        node.data["cputime"] += time.clock()
        node.data["walltime"] += time.time()

        if label == "enumeration":
            full = kwds.get("full", True)
            if full:
                node.data["#enum"] = Statistic(kwds["enum_obj"].get_nodes(), repr="sum") + node.data.get("#enum", None)
                try:
                    node.data["%"] = Statistic(kwds["probability"], repr="avg") + node.data.get("%", None)
                except KeyError:
                    pass

        if label[0] == "tour":
            node.data["r_0"] = Statistic(self.instance.M.get_r(0, 0), repr="min")
            node.data["/"] = Statistic(self.instance.M.get_current_slope(0, self.instance.A.nrows), repr="min")

        if self.verbosity and label[0] == "tour":
            report = OrderedDict()
            report["i"] = label[1]
            report["cputime"] = node["cputime"]
            report["walltime"] = node["walltime"]
            try:
                report["preproc"] = node.find("preprocessing", True)["cputime"]
            except KeyError:
                pass
            try:
                report["svp"] = node.find("enumeration", True)["cputime"]
            except KeyError:
                pass
            report["lll"] = node.sum("cputime", label="lll")
            try:
                report["postproc"] = node.find("postprocessing", True)["cputime"]
            except KeyError:
                pass
            try:
                report["pruner"] = node.find("pruner", True)["cputime"]
            except KeyError:
                pass
            report["r_0"] = node["r_0"]
            report["/"] = node["/"]
            report["#enum"] = node.sum("#enum")

            print(pretty_dict(report))

        self.current = self.current.parent
