# Skill: Simulacao + Visualizacao de Topologia de Circuito com AltDSS

## Objetivo
Criar uma pipeline completa que:
1. Executa simulação de circuito com AltDSS (com elementos dinâmicos: PV, baterias, cargas com LoadShape)
2. Captura a topologia **resultante** da simulação (não do .dss original)
3. Visualiza interativamente a topologia com coordenadas reais do circuito
4. Gera relatório automático

**Resultado esperado:** Um arquivo `.html` interativo mostrando o circuito com todos os elementos e um arquivo `.txt` com metadados.

---

## Arquitetura de 3 Camadas

```
┌─────────────────────────────────────────────────────┐
│ pipeline_simulacao_visualizacao.py                  │ ← Orquestração
│ (Executar simulação → Visualizar → Gerar relatório) │
└─────────────────────────────────────────────────────┘
         ↓ chama           ↓ chama           ↓ chama
┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
│ seu_experimento  │  │ visualizar_      │  │ Relatório    │
│ .py              │  │ topologia.py     │  │ .txt         │
│ (Simulação)      │  │ (Visualização)   │  │ (Metadados)  │
└──────────────────┘  └──────────────────┘  └──────────────┘
```

---

## 1. Script de Simulação (seu_experimento.py)

### Estrutura Mínima

```python
from altdss import AltDSS
from pathlib import Path

class ExperimentoSeuCaso:
    def __init__(self, dss_dir: Path):
        self.dss_dir = dss_dir
        self.altdss = AltDSS()
        
    def carregar_circuito(self):
        # CRÍTICO: Use circuito base correto
        circuito = self.dss_dir / "seu_circuito.dss"
        self.altdss(f"Redirect {circuito}")
        self.altdss.Compile()
        
    def criar_elementos_dinamicos(self):
        # Criar PVSystem, Storage, LoadShapes, etc.
        # IMPORTANTE: Tudo é criado em MEMÓRIA apenas
        # O arquivo .dss NUNCA é modificado
        pass
        
    def salvar_elementos_adicionais(self):
        # Salvar elementos criados em arquivo separado
        # Formato: elementos_fv_baterias.dss ou similar
        # Necessário para visualizador recriar em memória
        pass
        
    def executar_simulacao(self):
        self.carregar_circuito()
        self.criar_elementos_dinamicos()
        self.salvar_elementos_adicionais()
        # Rodar passo-a-passo ou profile
        self.altdss.Solution.SolveAll()
        
if __name__ == "__main__":
    dss_dir = Path(__file__).parent / "Rede34Barras"  # Ajuste conforme seu projeto
    exp = ExperimentoSeuCaso(dss_dir)
    exp.executar_simulacao()
```

### Componentes Essenciais

#### A. LoadShape para Cargas
Se suas cargas variam no tempo, crie um LoadShape:

```python
def criar_loadshape_demanda(self):
    DEMANDA_CARGAS = (0.84, 0.81, 0.78, ..., 0.88)  # 24 horas
    
    perfil = self.altdss.LoadShape.new("demandacargas")
    perfil.NPts = 24
    perfil.Interval = 1.0
    perfil.PMult = list(DEMANDA_CARGAS)
    perfil.end_edit()
    
    # Anexar às cargas
    for carga in self.altdss.Load:
        carga.Daily = "demandacargas"
```

#### B. Linhas de Conexão (em memória)
Se conecta PV/Baterias via barras virtuais, crie linhas em memória:

```python
def criar_linhas_conexao(self):
    conexoes = {
        "824pv": "824",
        "816pv": "816",
        "828pv": "828",
        "830pv": "830"
    }
    
    for nome_pv, barra in conexoes.items():
        nome_linha = f"L{nome_pv}"
        self.altdss(
            f"New Line.{nome_linha} "
            f"Phases=3 Bus1={barra}.1.2.3 Bus2={nome_pv}.1.2.3 "
            f"LineCode=301 Length=0.001 units=kft"
        )
```

#### C. Salvar Elementos para Visualizador
**CRÍTICO:** Salvar em ordem específica (XYCurves → LoadShapes → PVSystem/Storage):

```python
def salvar_elementos_adicionais(self):
    saida = Path("Resultados") / "elementos_fv_baterias.dss"
    saida.parent.mkdir(parents=True, exist_ok=True)
    
    with open(saida, 'w') as f:
        f.write("! Elementos criados automaticamente\n\n")
        
        # 1. Salvar XYCurves PRIMEIRO
        for curve in self.altdss.XYCurve:
            f.write(f"New XYcurve.{curve.Name}\n")
            f.write(f"  ~ NPts={curve.NPts}\n")
            f.write(f"  ~ XArray={list(curve.XArray)}\n")
            f.write(f"  ~ YArray={list(curve.YArray)}\n\n")
        
        # 2. Depois LoadShapes
        for ls in self.altdss.LoadShape:
            f.write(f"New LoadShape.{ls.Name}\n")
            f.write(f"  ~ NPts={ls.NPts}\n")
            f.write(f"  ~ PMult={list(ls.PMult)}\n\n")
        
        # 3. Por fim PVSystem e Storage
        for pv in self.altdss.PVSystem:
            f.write(f"New PVSystem.{pv.Name}\n")
            f.write(f"  ~ Bus1={pv.Bus1}\n")
            # ... mais parâmetros
            f.write("\n")
```

---

## 2. Visualizador (visualizar_topologia.py)

### Estrutura Genérica

```python
from altdss import AltDSS
from pathlib import Path
import pandas as pd
from pyvis.network import Network

class VisualizadorTopologia:
    def __init__(self, dss_dir: Path):
        self.dss_dir = dss_dir
        self.altdss = AltDSS()
        self.coordenadas = {}
        
    def carregar_circuito_base(self, circuito_dss: str):
        # Carregar .dss original
        self.altdss(f"Redirect {self.dss_dir / circuito_dss}")
        self.altdss.Compile()
        
    def recriar_elementos_dinamicos(self, arquivo_elementos: str):
        # Recriar linhas L*pv em memória (exatamente como na simulação)
        conexoes = {"824pv": "824", "816pv": "816", "828pv": "828", "830pv": "830"}
        linhas_existentes = {line.Name.lower() for line in self.altdss.Line}
        
        for nome_pv, barra in conexoes.items():
            nome_linha = f"L{nome_pv}"
            if nome_linha.lower() not in linhas_existentes:
                self.altdss(
                    f"New Line.{nome_linha} Phases=3 "
                    f"Bus1={barra}.1.2.3 Bus2={nome_pv}.1.2.3 "
                    f"LineCode=301 Length=0.001 units=kft"
                )
        
        # Carregar arquivo de elementos (PV, Baterias, LoadShapes)
        self.altdss(f"Redirect {self.dss_dir / arquivo_elementos}")
        
    def carregar_coordenadas(self, arquivo_xy: str = None):
        # Carregar X,Y reais do circuito (ex: IEEE34_BusXY.csv)
        if arquivo_xy is None:
            arquivo_xy = "IEEE34_BusXY.csv"  # Ajuste nome conforme circuito
            
        caminho = self.dss_dir / arquivo_xy
        if not caminho.exists():
            print(f"[AVISO] Arquivo de coordenadas nao encontrado: {arquivo_xy}")
            return
        
        df = pd.read_csv(caminho)
        for _, row in df.iterrows():
            barra = str(row['Bus']).strip()
            self.coordenadas[barra] = (float(row['X']), float(row['Y']))
    
    def extrair_topologia(self) -> dict:
        # Extrair barras, linhas, PV, Storage, Cargas, Capacitores
        dados = {
            'barras': [],
            'linhas': [],
            'pv': [],
            'baterias': [],
            'cargas': [],
            'capacitores': []
        }
        
        # Extrair barras
        for barra in self.altdss.Bus:
            dados['barras'].append(barra.Name)
        
        # Extrair linhas
        for linha in self.altdss.Line:
            dados['linhas'].append({
                'nome': linha.Name,
                'bus1': linha.Bus1,
                'bus2': linha.Bus2
            })
        
        # Extrair PV
        for pv in self.altdss.PVSystem:
            dados['pv'].append({
                'nome': pv.Name,
                'bus': pv.Bus1,
                'kva': pv.kVA
            })
        
        # Extrair Storage
        for bat in self.altdss.Storage:
            dados['baterias'].append({
                'nome': bat.Name,
                'bus': bat.Bus1,
                'kw': bat.kWRated
            })
        
        # Extrair Cargas
        for carga in self.altdss.Load:
            dados['cargas'].append({
                'nome': carga.Name,
                'bus': carga.Bus1,
                'kw': carga.kW
            })
        
        # Extrair Capacitores
        for cap in self.altdss.Capacitor:
            dados['capacitores'].append({
                'nome': cap.Name,
                'bus': cap.Bus1,
                'kvar': cap.kvar if hasattr(cap.kvar, '__len__') else cap.kvar
            })
        
        return dados
    
    def visualizar_pyvis(self, dados: dict, arquivo_saida: Path):
        net = Network(height="100%", width="100%", directed=False, physics=True)
        
        # Adicionar nós (barras)
        cores_barra = "#0066cc"  # Azul
        for barra in dados['barras']:
            x, y = self.coordenadas.get(barra, (None, None))
            net.add_node(barra, label=barra, color=cores_barra, x=x, y=y, physics=True)
        
        # Adicionar PV como nós
        for pv in dados['pv']:
            x, y = self.coordenadas.get(pv['bus'], (None, None))
            net.add_node(pv['bus'], label=f"{pv['nome']}\n{pv['kva']}kVA", 
                        color="#00cc00", x=x, y=y, physics=True)
        
        # Adicionar arestas (linhas)
        for linha in dados['linhas']:
            net.add_edge(linha['bus1'], linha['bus2'], 
                        label=linha['nome'], title=linha['nome'])
        
        # Salvar
        net.show(arquivo_saida)
        print(f"Visualizacao salva em: {arquivo_saida}")

if __name__ == "__main__":
    dss_dir = Path(__file__).parent / "Rede34Barras"
    
    viz = VisualizadorTopologia(dss_dir)
    viz.carregar_circuito_base("seu_circuito.dss")
    viz.recriar_elementos_dinamicos("elementos_fv_baterias.dss")
    viz.carregar_coordenadas("seu_circuito_BusXY.csv")
    
    dados = viz.extrair_topologia()
    viz.visualizar_pyvis(dados, Path("Resultados") / "topologia.html")
```

---

## 3. Pipeline (pipeline_simulacao_visualizacao.py)

```python
import subprocess
from pathlib import Path

def executar_pipeline(experimento_py: str, visualizador_py: str, dss_dir: Path):
    print("[1/3] Executando simulacao...")
    resultado1 = subprocess.run(["python", experimento_py], cwd=Path.cwd())
    if resultado1.returncode != 0:
        print("[ERRO] Simulacao falhou!")
        return
    
    print("[2/3] Gerando visualizacao...")
    resultado2 = subprocess.run(["python", visualizador_py], cwd=Path.cwd())
    if resultado2.returncode != 0:
        print("[ERRO] Visualizacao falhou!")
        return
    
    print("[3/3] Pipeline completado!")
    print(f"[OK] Abra 'Resultados/topologia.html' no navegador")

if __name__ == "__main__":
    dss_dir = Path(__file__).parent / "Rede34Barras"
    
    executar_pipeline(
        "seu_experimento.py",
        "visualizar_topologia.py",
        dss_dir
    )
```

---

## 4. Checklist de Adaptação para Novo Projeto

### Passo 1: Preparar Estrutura de Diretórios
```
seu_projeto/
├── seu_circuito.dss           # Circuito base (original)
├── seu_circuito_BusXY.csv     # Coordenadas reais (opcional, fallback automático)
├── seu_experimento.py          # Simulação
├── visualizar_topologia.py     # Visualizador (copiado e adaptado)
├── pipeline_simulacao_visualizacao.py
└── Rede34Barras/               # (ou seu_circuito_dir/)
    ├── seu_circuito.dss
    └── IEEELineCodes.dss       # Se necessário
```

### Passo 2: Modificar seu_experimento.py

- [ ] Mudar `circuito_base = "seu_circuito.dss"` (linha X)
- [ ] Ajustar DEMANDA_CARGAS conforme seu caso (alterar valores)
- [ ] Ajustar IRRADIANCIA se usar PV
- [ ] Mudar nomes de barras em `conexoes` se não for IEEE34
- [ ] Mudar capacidades de PV e baterias conforme seu caso
- [ ] Salvar elementos em arquivo separado (elemtos_seu_caso.dss)

### Passo 3: Modificar visualizar_topologia.py

- [ ] Mudar `dss_dir = Path(...) / "Rede34Barras"` para seu diretório
- [ ] Mudar `seu_circuito.dss` para seu arquivo base
- [ ] Mudar `elementos_fv_baterias.dss` para seu arquivo de elementos
- [ ] Mudar `IEEE34_BusXY.csv` para seu arquivo de coordenadas
- [ ] Se não tiver arquivo de coordenadas, deixar vazio (fallback automático)
- [ ] Ajustar cores e rótulos se desejar (cores_barra, cores_pv, etc.)

### Passo 4: Testar
```bash
# Terminal PowerShell/Bash
python seu_experimento.py         # Deve criar Resultados/elementos_*.dss
python visualizar_topologia.py    # Deve criar Resultados/topologia.html
python pipeline_simulacao_visualizacao.py  # Orquestra tudo
```

---

## 5. Troubleshooting Comum

### Erro: "DSSException: (#243) Redirect file not found"
**Causa:** Caminho relativo do .dss não encontrado  
**Solução:** Use Path absoluto: `self.altdss(f"Redirect {circuito.absolute()}")`

### Erro: "LoadShape object not found"
**Causa:** LoadShape não salvo antes de PVSystem  
**Solução:** Salvar em ordem: XYCurves → LoadShapes → PVSystem/Storage

### Erro: "'NoneType' object has no attribute 'render'"
**Causa:** `net.show()` falhou com renderização  
**Solução:** Use `net.write_html(arquivo, notebook=False)`

### Visualização sem coordenadas reais
**Esperado:** Pyvis gera layout físico automático  
**Se quiser reais:** Criar arquivo `.csv` com colunas `Bus,X,Y`

### Original .dss foi alterado
**Verificar:** Se arquivo `.dss` cresceu em tamanho  
**Solução:** Nunca fazer `self.altdss(f"Save Circuit ...")`, apenas salvar elementos em arquivo separado

---

## 6. Exemplo Prático: Adaptando para IEEE69

```python
# ieee69_experimento.py
from pathlib import Path
from altdss import AltDSS

class ExperimentoIEEE69:
    def __init__(self):
        self.altdss = AltDSS()
        self.dss_dir = Path(__file__).parent / "Rede69Barras"
    
    def executar(self):
        # Circuito base diferente
        self.altdss(f"Redirect {self.dss_dir / 'ieee69Mod.dss'}")
        
        # Cargas diferentes (ajustar DEMANDA para 69 barras)
        DEMANDA_69 = (0.70, 0.68, 0.65, ...)  # 24 horas
        
        # Baterias em barras diferentes
        conexoes_69 = {
            "1pv": "1",
            "10pv": "10",
            "25pv": "25",
            "50pv": "50"
        }
        
        # ... rest of implementation
        
        # Salvar elementos
        self.salvar_elementos_adicionais()  # → elementos_ieee69.dss

# visualizar_topologia.py (adaptado)
dss_dir = Path(__file__).parent / "Rede69Barras"
viz.carregar_circuito_base("ieee69Mod.dss")
viz.recriar_elementos_dinamicos("elementos_ieee69.dss")
viz.carregar_coordenadas("IEEE69_BusXY.csv")  # Se tiver
```

---

## 7. Resultado Final

Após executar:
```
Resultados/
├── topologia.html              # Visualizacao interativa Pyvis
├── topologia_circuito.txt      # Metadados (barras, linhas, elementos)
└── elementos_seu_caso.dss      # Elementos criados (backup)
```

**Abra `topologia.html` no navegador:**
- ✓ Drag para mover nós
- ✓ Zoom com scroll
- ✓ Click em nó = propriedades no painel direito
- ✓ Hover em nó = tooltip
- ✓ Legenda colorida no canto superior esquerdo

---

## 8. Arquivos de Referência

- Original: `2026_consenso_fv_baterias_altdss_com_loadshape.py`
- Original: `visualizar_topologia.py` (versão v2 com coordenadas reais)
- Original: `pipeline_simulacao_visualizacao.py`

Copie e adapte os padrões desses arquivos para seu experimento!

---

## Notas Finais

1. **Nunca modifique o `.dss` original** — tudo em memória
2. **Sempre salve elementos em arquivo separado** — necessário para visualizador
3. **Coordenadas são opcionais** — Pyvis faz fallback automático
4. **Nomes de barras devem ser únicos** — evite conflitos
5. **LoadShapes/XYCurves vêm ANTES de PVSystem** — ordem de salvamento crítica

Boa sorte com seus experimentos! 🚀
