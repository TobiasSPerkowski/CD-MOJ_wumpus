import sys
from pysat.solvers import Solver
from pysat.formula import IDPool


class WumpusKB:
    def __init__(self):
        self.vpool = IDPool()
        self.solver = Solver(name='glucose3')

    def pit(self, x,y):
        return self.vpool.id(f"P_{x}_{y}")

    def wumpus(self, x,y):
        return self.vpool.id(f"W_{x}_{y}")

    def add_clause(self, c):
        self.solver.add_clause(c)

    def no_pits(self, adj):
        for x,y in adj:
            self.add_clause([-self.pit(x,y)])

    def pits(self, adj):
        clause = [self.pit(x,y) for x,y in adj]
        if clause:
            self.add_clause(clause)

    def no_wumpuses(self, adj):
        for x,y in adj:
            self.add_clause([-self.wumpus(x,y)])

    def wumpuses(self, adj):
        clause = [self.wumpus(x,y) for x,y in adj]
        if clause:
            self.add_clause(clause)

    def is_safe(self, x,y):
        p = self.pit(x,y)
        w = self.wumpus(x,y)

        has_pit = self.solver.solve(assumptions=[p])
        has_wumpus = self.solver.solve(assumptions=[w])
        
        # soh eh safe se n tiver poco nem wumpus
        return not has_pit and not has_wumpus


DIRECTIONS = ["N", "E", "S", "W"]
MOVES = [
    ( 0, 1),  # N
    ( 1, 0),  # E
    ( 0,-1),  # S
    (-1, 0)   # W
]

class Agent:
    def __init__(self):
        self.pos = (0, 0)
        self.dir = 0
        self.target = None

        self.visited = set()
        self.safe = set()
        self.walls = set()
        self.path_stack = []

        self.kb = WumpusKB()

    def turn_left(self):
        self.dir = (self.dir - 1) % 4 
        return "l"

    def forward_pos(self):
        x,y = self.pos
        dx,dy = MOVES[self.dir]
        return (x + dx, y + dy)

    def adj(self, pos):
        x,y = pos
        # retornando na melhor ordem (evita giros desnecessarios)
        if self.dir == 0: #N
            return [(x, y+1), (x-1, y), (x, y-1), (x+1, y)]
        if self.dir == 1: #E
            return [(x+1, y), (x, y+1), (x-1, y), (x, y-1)]
        if self.dir == 2: #S
            return [(x, y-1), (x+1, y), (x, y+1), (x-1, y)]
        #W
        return [(x-1, y), (x, y-1), (x+1, y), (x, y+1)]

    def update(self, sensors):
        stench, breeze, glitter, bump, scream = sensors

        if bump == '1': # bateu em uma parede
            self.walls.add(self.pos)
            # informando kb q n tem pit nem wumpus
            no_pit = -self.kb.pit(self.pos[0], self.pos[1])
            no_wumpus = -self.kb.wumpus(self.pos[0], self.pos[1])
            self.kb.add_clause([no_pit])
            self.kb.add_clause([no_wumpus])
            # voltando p posicao anterior
            self.pos = self.path_stack.pop()
            self.target = None
        
        self.visited.add(self.pos)
        self.safe.add(self.pos)

        adj = [c for c in self.adj(self.pos) if c not in self.walls]

        if breeze == '1':
            self.kb.pits(adj)
        else:
            self.kb.no_pits(adj)

        if stench == '1':
            self.kb.wumpuses(adj)
        else:
            self.kb.no_wumpuses(adj)
        
        for c in adj:
            if c not in self.visited and c not in self.safe:
                if self.kb.is_safe(c[0], c[1]):
                    self.safe.add(c)


    def move_towards_target(self):
        if self.target is None: # n deve acontecer
            return "r" # vira pra direita (debugging)

        x,y = self.pos
        tx,ty = self.target
        dx,dy = tx - x, ty - y

        #encontrando a direcao do alvo
        target_dir = None
        for i, m in enumerate(MOVES):
            if m == (dx,dy):
                target_dir = i
                break

        if target_dir is None and self.pos != self.target: # n deve acontecer
            return "r" # vira pra direita (debugging)
        
        # se n estiver virado pro alvo, vira pra esquerda
        if self.dir != target_dir:
            return self.turn_left()

        # atualizando pilha do caminho
        if self.path_stack and self.target == self.path_stack[-1]:
            self.path_stack.pop() # backtracking
        else:
            self.path_stack.append(self.pos)

        self.pos = self.target

        return "m"
    

    def choose(self):
        # se jah tiver target, apenas move em direcao a ele
        if self.target and self.pos != self.target:
            return self.move_towards_target()

        # adjacente segura n visitada
        adj = [c for c in self.adj(self.pos) if c not in self.walls]
        for cell in adj:
            if cell in self.safe and cell not in self.visited:
                self.target = cell
                #print("pos: ", self.pos)
                #print("dir: ", self.dir)
                #print("target: ", self.target)
                return self.move_towards_target()
        
        # se n, backtracking
        if len(self.path_stack) > 0:
            self.target = self.path_stack[-1]
            return self.move_towards_target()
        
        # se n, desistir
        return "e"


agent = Agent()
print("l", flush=True)

while True:
    line = sys.stdin.readline()
    if not line:
        break

    sensors = line.strip()
    if len(sensors) != 5:
        continue

    # pegar ouro
    if sensors[2] == '1':
        print("p", flush=True)
        break

    agent.update(sensors)
    action = agent.choose()
    print(action, flush=True)
