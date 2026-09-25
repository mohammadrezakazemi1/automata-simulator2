"""Context-Free Grammar engine used by the Grammar Lab.

The module is intentionally independent from the GUI. It contains the parsing
and transformation algorithms that are demonstrated by the application.
"""

from dataclasses import dataclass
from collections import defaultdict, deque
import re

EPSILON = "ε"

@dataclass(frozen=True)
class Production:
    left: str
    right: tuple

class ContextFreeGrammar:
    """Small, dependency-free CFG engine for the Grammar Lab."""

    def __init__(self, start="S"):
        self.start = start
        self.productions = []
        self.nonterminals = set()
        self.terminals = set()

    def parse(self, text):
        self.productions = []
        self.nonterminals = set()
        self.terminals = set()
        lines = [x.strip() for x in text.splitlines() if x.strip() and not x.strip().startswith("#")]
        if not lines:
            raise ValueError("Grammar is empty.")
        for line in lines:
            if "->" not in line:
                raise ValueError(f"Invalid production: {line}")
            left, rhs = [x.strip() for x in line.split("->", 1)]
            if not left or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", left):
                raise ValueError(f"Invalid nonterminal: {left}")
            self.nonterminals.add(left)
            for alt in rhs.split("|"):
                alt = alt.strip()
                if alt in ("", EPSILON, "epsilon", "eps"):
                    symbols = ()
                else:
                    tokens = self._tokenize(alt)
                    symbols = tuple(tokens)
                self.productions.append(Production(left, symbols))
        if self.start not in self.nonterminals:
            self.start = next(iter(self.nonterminals))
        self.terminals = {s for p in self.productions for s in p.right if s not in self.nonterminals}
        return self

    def _tokenize(self, text):
        quoted = re.findall(r"'([^']*)'|\"([^\"]*)\"|([A-Za-z_][A-Za-z0-9_']*|ε)", text)
        if quoted:
            tokens = []
            pos = 0
            pattern = re.compile(r"'([^']*)'|\"([^\"]*)\"|([A-Za-z_][A-Za-z0-9_']*|ε)")
            for m in pattern.finditer(text):
                if text[pos:m.start()].strip():
                    tokens.extend(text[pos:m.start()].strip().split())
                tokens.append(next(g for g in m.groups() if g is not None))
                pos = m.end()
            if text[pos:].strip():
                tokens.extend(text[pos:].strip().split())
            return tokens
        return text.split()

    def validate(self):
        errors = []
        if self.start not in self.nonterminals:
            errors.append("Start symbol is not defined.")
        for p in self.productions:
            if p.left not in self.nonterminals:
                errors.append(f"Undefined left symbol: {p.left}")
            for s in p.right:
                if s not in self.nonterminals and s == EPSILON:
                    errors.append("Use ε as an empty production, not as a normal symbol.")
        reachable = {self.start}
        changed = True
        while changed:
            changed = False
            for p in self.productions:
                if p.left in reachable:
                    for s in p.right:
                        if s in self.nonterminals and s not in reachable:
                            reachable.add(s); changed = True
        unreachable = sorted(self.nonterminals - reachable)
        if unreachable:
            errors.append("Unreachable nonterminals: " + ", ".join(unreachable))
        return errors

    # FIRST is calculated with fixed-point iteration until no set changes.
    def first_sets(self):
        first = {n: set() for n in self.nonterminals}
        changed = True
        while changed:
            changed = False
            for p in self.productions:
                if not p.right:
                    if EPSILON not in first[p.left]:
                        first[p.left].add(EPSILON); changed = True
                    continue
                nullable = True
                for sym in p.right:
                    if sym in self.nonterminals:
                        before = len(first[p.left])
                        first[p.left] |= (first[sym] - {EPSILON})
                        changed |= len(first[p.left]) != before
                        if EPSILON not in first[sym]:
                            nullable = False
                            break
                    else:
                        if sym not in first[p.left]:
                            first[p.left].add(sym); changed = True
                        nullable = False
                        break
                if nullable and EPSILON not in first[p.left]:
                    first[p.left].add(EPSILON); changed = True
        return first

    def first_of_sequence(self, seq, first=None):
        first = first or self.first_sets()
        out = set()
        nullable = True
        for sym in seq:
            if sym in self.nonterminals:
                out |= first[sym] - {EPSILON}
                if EPSILON not in first[sym]:
                    nullable = False; break
            else:
                out.add(sym); nullable = False; break
        if nullable:
            out.add(EPSILON)
        return out

    # FOLLOW starts with $ for the start symbol and propagates information.
    def follow_sets(self):
        first = self.first_sets()
        follow = {n: set() for n in self.nonterminals}
        follow[self.start].add("$")
        changed = True
        while changed:
            changed = False
            for p in self.productions:
                for i, sym in enumerate(p.right):
                    if sym not in self.nonterminals:
                        continue
                    tail = p.right[i+1:]
                    f = self.first_of_sequence(tail, first)
                    before = len(follow[sym])
                    follow[sym] |= f - {EPSILON}
                    if EPSILON in f or not tail:
                        follow[sym] |= follow[p.left]
                    changed |= len(follow[sym]) != before
        return follow

    # Input parsing uses a compact Earley-style chart representation.
    def parse_string(self, text):
        tokens = text.split() if " " in text.strip() else list(text.strip()) if text.strip() else []
        n = len(tokens)
        # Earley-style chart storing one representative derivation per state.
        chart = [dict() for _ in range(n + 1)]
        # key=(lhs,rhs,dot,start), value=children
        for p in self.productions:
            chart[0][(p.left,p.right,0,0)] = []
        for i in range(n + 1):
            changed = True
            while changed:
                changed = False
                for key, children in list(chart[i].items()):
                    lhs,rhs,dot,start = key
                    if dot < len(rhs):
                        sym = rhs[dot]
                        if sym in self.nonterminals:
                            for p in self.productions:
                                k=(p.left,p.right,0,i)
                                if k not in chart[i]:
                                    chart[i][k]=[]; changed=True
                        else:
                            if i < n and sym == tokens[i]:
                                k=(lhs,rhs,dot+1,start)
                                if k not in chart[i+1]:
                                    chart[i+1][k]=children + [("token", sym)]; 
                    else:
                        completed=("node",lhs,children)
                        for parent, ch in list(chart[start].items()):
                            pl,pr,pdot,ps=parent
                            if pdot < len(pr) and pr[pdot] == lhs:
                                k=(pl,pr,pdot+1,ps)
                                if k not in chart[i]:
                                    chart[i][k]=ch + [completed]; changed=True
            # Advance terminals after closure.
            if i < n:
                for key, children in list(chart[i].items()):
                    lhs,rhs,dot,start=key
                    if dot < len(rhs) and rhs[dot] not in self.nonterminals and rhs[dot] == tokens[i]:
                        k=(lhs,rhs,dot+1,start)
                        if k not in chart[i+1]:
                            chart[i+1][k]=children+[("token",tokens[i])]
        accepted = any(k[0]==self.start and k[3]==0 and k[2]==len(k[1]) for k in chart[n])
        if not accepted:
            return False, None, tokens
        # Build a readable leftmost derivation using a separate recursive search.
        tree = self._find_tree(self.start, tokens, 0, len(tokens), {})
        return True, tree, tokens

    def _find_tree(self, symbol, tokens, lo, hi, memo):
        key=(symbol,lo,hi)
        if key in memo: return memo[key]
        if symbol not in self.nonterminals:
            return ("token",symbol) if hi-lo==1 and tokens[lo]==symbol else None
        for p in self.productions:
            if not p.right:
                if lo==hi: return ("node",symbol,[])
                continue
            result = self._match_rhs(p.right,tokens,lo,hi,memo)
            if result is not None:
                return ("node",symbol,result)
        memo[key]=None
        return None

    def _match_rhs(self,rhs,tokens,lo,hi,memo):
        if not rhs:
            return [] if lo==hi else None
        def rec(j,pos):
            if j==len(rhs):
                return [] if pos==hi else None
            sym=rhs[j]
            if sym in self.nonterminals:
                for end in range(pos,hi+1):
                    node=self._find_tree(sym,tokens,pos,end,memo)
                    if node is not None:
                        tail=rec(j+1,end)
                        if tail is not None: return [node]+tail
            elif pos<hi and tokens[pos]==sym:
                tail=rec(j+1,pos+1)
                if tail is not None: return [("token",sym)]+tail
            return None
        return rec(0,lo)

    def leftmost_derivation(self, tree):
        if tree is None: return []
        steps=[self.start]
        current=[("node",self.start,tree[2])]
        while any(x[0]=="node" for x in current):
            idx=next(i for i,x in enumerate(current) if x[0]=="node")
            node=current[idx]
            repl=node[2]
            current=current[:idx]+repl+current[idx+1:]
            symbols=[]
            for x in current:
                if x[0]=="node": symbols.append(x[1])
                else: symbols.append(x[1])
            steps.append(" ".join(symbols) if symbols else EPSILON)
            if len(steps)>200: break
        return steps

    def classification(self):
        regular = True
        for p in self.productions:
            r=p.right
            if len(r)==0: continue
            if len(r)==1 and r[0] in self.terminals: continue
            if len(r)==2 and r[0] in self.terminals and r[1] in self.nonterminals: continue
            regular=False
        return "Type 3 — Regular" if regular else "Type 2 — Context-Free"

    # Transformation used to prepare grammars for predictive parsing.
    def remove_left_recursion(self):
        # Direct left-recursion elimination for each nonterminal.
        new=[]
        for A in list(self.nonterminals):
            prods=[p.right for p in self.productions if p.left==A]
            alpha=[r[1:] for r in prods if r and r[0]==A]
            beta=[r for r in prods if not (r and r[0]==A)]
            if alpha and beta:
                Apr=A+"'"
                while Apr in self.nonterminals: Apr+="'"
                self.nonterminals.add(Apr)
                for b in beta: new.append(Production(A,b+(Apr,)))
                for a in alpha: new.append(Production(Apr,a+(Apr,)))
                new.append(Production(Apr,()))
            else:
                new.extend(Production(A,r) for r in prods)
        self.productions=new
        self.terminals={s for p in new for s in p.right if s not in self.nonterminals}
        return self

    # LL(1) cells are reported as conflicts when multiple productions map to one cell.
    def ll1_table(self):
        """Return an LL(1) parsing table and a list of conflicts."""
        first=self.first_sets(); follow=self.follow_sets()
        table={}
        conflicts=[]
        for p in self.productions:
            seq_first=self.first_of_sequence(p.right,first)
            targets=set(seq_first-{EPSILON})
            if EPSILON in seq_first:
                targets |= follow[p.left]
            for terminal in targets:
                key=(p.left,terminal)
                table.setdefault(key,[]).append(p)
                if len(table[key])>1:
                    conflicts.append(f"{p.left}, {terminal}: multiple productions")
        rendered={}
        for key,prods in table.items():
            rendered[key]=[f"{p.left} -> {EPSILON if not p.right else ' '.join(p.right)}" for p in prods]
        return rendered,conflicts

    # Repeated prefixes are extracted into helper nonterminals.
    def left_factor(self):
        """Apply simple repeated-prefix left factoring until no pair shares a prefix."""
        changed=True
        while changed:
            changed=False
            new=[]
            for A in list(self.nonterminals):
                prods=[p.right for p in self.productions if p.left==A]
                groups={}
                for r in prods:
                    if r: groups.setdefault(r[0],[]).append(r)
                factor=next(((sym,rs) for sym,rs in groups.items() if len(rs)>1),None)
                if not factor:
                    new.extend(Production(A,r) for r in prods); continue
                sym,rs=factor; idx=1; Apr=A+"F"
                while Apr in self.nonterminals: idx+=1; Apr=A+"F"*idx
                self.nonterminals.add(Apr)
                for r in prods:
                    if r in rs: continue
                    new.append(Production(A,r))
                new.append(Production(A,(sym,Apr)))
                for r in rs:new.append(Production(Apr,r[1:]))
                changed=True
            self.productions=new
        self.terminals={s for p in self.productions for s in p.right if s not in self.nonterminals}
        return self

    def text(self):
        groups=defaultdict(list)
        for p in self.productions: groups[p.left].append(EPSILON if not p.right else " ".join(p.right))
        return "\n".join(f"{a} -> " + " | ".join(v) for a,v in groups.items())
