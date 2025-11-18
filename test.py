# loja.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


# -------------------------
# Produtos
# -------------------------
@dataclass
class Produto:
    id: int
    nome: str
    quantidade: int
    categoria: str
    preco: float
    data_fabricacao: Optional[date] = None
    fabricante: Optional[str] = None
    NCM: Optional[str] = None

    def aplicar_desconto(self, pcnt: float) -> None:
        """Aplica desconto percentual (ex: pcnt=10 => 10%)."""
        if pcnt < 0 or pcnt > 100:
            raise ValueError("Percentual deve estar entre 0 e 100.")
        original = self.preco
        self.preco = self.preco * (1 - pcnt / 100)
        # Debug
        # print(f"[DEBUG] Desconto aplicado: {original} -> {self.preco}")

    def aplicar_acrescimo(self, pcnt: float) -> None:
        """Aplica acréscimo percentual."""
        if pcnt < 0:
            raise ValueError("Percentual não pode ser negativo.")
        original = self.preco
        self.preco = self.preco * (1 + pcnt / 100)
        # Debug
        # print(f"[DEBUG] Acréscimo aplicado: {original} -> {self.preco}")


@dataclass
class Alimento(Produto):
    data_validade: Optional[date] = None
    peso_kg: Optional[float] = None
    tipo: Optional[str] = None  # perecível / não perecível
    origem: Optional[str] = None  # nacional / importado
    info_nutricional: Optional[str] = None


@dataclass
class Roupa(Produto):
    tamanho: Optional[str] = None  # PP, P, M, G, GG
    cor: Optional[str] = None
    tecido: Optional[str] = None
    genero: Optional[str] = None  # masculino/feminino/unissex
    estampa: Optional[str] = None


@dataclass
class Eletronico(Produto):
    tensao: Optional[str] = None  # 110V / 220V / bivolt
    potencia_w: Optional[float] = None
    garantia_meses: Optional[int] = None
    consumo_kwh: Optional[float] = None
    conexoes: Optional[List[str]] = field(default_factory=list)


@dataclass
class Eletrodomestico(Produto):
    ano_lancamento: Optional[int] = None
    marca: Optional[str] = None
    funcao: Optional[str] = None
    tipos: Optional[str] = None


# -------------------------
# Usuários
# -------------------------
@dataclass
class Usuario:
    id: int
    nome: str
    data_nascimento: Optional[date] = None


@dataclass
class Cliente(Usuario):
    credito: float = 0.0
    historico_de_compra: List['Pedido'] = field(default_factory=list)

    def adicionar_credito(self, valor: float) -> None:
        if valor <= 0:
            raise ValueError("Valor de crédito deve ser positivo.")
        self.credito += valor


@dataclass
class Funcionario(Usuario):
    salario: float = 0.0
    cargo: Optional[str] = None

    def trabalhar(self) -> str:
        return f"{self.nome} está trabalhando como {self.cargo}."


# -------------------------
# Fornecedor
# -------------------------
@dataclass
class Fornecedor:
    id: int
    nome: str
    produtos: List[Produto] = field(default_factory=list)
    quantidade: int = 0
    quantidade_maxima: Optional[int] = None

    def armazenar(self, estoque: 'Estoque', item: Produto, qnt: int) -> int:
        """Fornece produtos ao estoque (retorna nova quantidade do item no estoque)."""
        estoque.armazenar(item, qnt)
        if item not in self.produtos:
            self.produtos.append(item)
        return estoque.obter_quantidade(item.id)


# -------------------------
# Estoque
# -------------------------
class Estoque:
    def __init__(self, quantidade_maxima: Optional[int] = None):
        self.produtos: dict[int, Produto] = {}   # id -> produto
        self.quantidades: dict[int, int] = {}    # id -> quantidade
        self.quantidade_maxima = quantidade_maxima

    def armazenar(self, item: Produto, qnt: int) -> int:
        if qnt <= 0:
            raise ValueError("Quantidade deve ser positiva.")
        current = self.quantidades.get(item.id, 0)
        new_total = current + qnt
        if self.quantidade_maxima is not None and new_total > self.quantidade_maxima:
            raise ValueError("Capacidade máxima do estoque excedida.")
        # Se produto novo, registra objeto (mantemos referência do produto)
        if item.id not in self.produtos:
            self.produtos[item.id] = item
        self.quantidades[item.id] = new_total
        return new_total

    def remover(self, produto_id: int, qnt: int) -> Produto:
        if produto_id not in self.produtos:
            raise KeyError("Produto não encontrado no estoque.")
        if qnt <= 0:
            raise ValueError("Quantidade deve ser positiva.")
        current = self.quantidades.get(produto_id, 0)
        if qnt > current:
            raise ValueError("Quantidade insuficiente no estoque.")
        self.quantidades[produto_id] = current - qnt
        produto = self.produtos[produto_id]
        return produto

    def obter_produto(self, produto_id: int) -> Produto:
        return self.produtos[produto_id]

    def obter_quantidade(self, produto_id: int) -> int:
        return self.quantidades.get(produto_id, 0)


# -------------------------
# Carrinho e Pedido
# -------------------------
@dataclass
class Carrinho:
    produtos: dict[int, int] = field(default_factory=dict)  # produto_id -> quantidade
    limite: Optional[int] = None

    def adicionar_produto(self, produto: Produto, qnt: int = 1) -> bool:
        if qnt <= 0:
            raise ValueError("Quantidade deve ser positiva.")
        atual = sum(self.produtos.values())
        if self.limite is not None and (atual + qnt) > self.limite:
            return False
        self.produtos[produto.id] = self.produtos.get(produto.id, 0) + qnt
        return True

    def remover_produto(self, produto_id: int, qnt: int = 1) -> bool:
        if produto_id not in self.produtos:
            return False
        if qnt <= 0:
            raise ValueError("Quantidade deve ser positiva.")
        atual = self.produtos[produto_id]
        if qnt >= atual:
            del self.produtos[produto_id]
        else:
            self.produtos[produto_id] = atual - qnt
        return True

    def limpar_carrinho(self) -> None:
        self.produtos.clear()

    def total(self, estoque: Estoque) -> float:
        s = 0.0
        for pid, q in self.produtos.items():
            produto = estoque.obter_produto(pid)
            s += produto.preco * q
        return s


@dataclass
class Pedido:
    id_pedido: int
    carrinho: Carrinho
    preco: float = 0.0
    pago: bool = False

    def calcular_preco(self, estoque: Estoque) -> float:
        self.preco = self.carrinho.total(estoque)
        return self.preco


# -------------------------
# Pagamento e Caixa
# -------------------------
@dataclass
class Pagamento:
    forma: str   # 'dinheiro', 'cartao', 'pix', etc.
    valor: float
    agencia: Optional[str] = None

    def realizar_pagamento(self) -> bool:
        # Aqui normalmente teríamos integração com gateway; simulamos sucesso para valores positivos.
        if self.valor <= 0:
            return False
        return True

@dataclass
class Caixa:
    funcionario: Optional[Funcionario] = None
    historico_pedidos: List[Pedido] = field(default_factory=list)
    troco: float = 0.0

    def processar_pagamento(self, pedido: Pedido, pagamento: Pagamento) -> bool:
        sucesso = pagamento.realizar_pagamento()
        if not sucesso:
            return False
        pedido.pago = True
        self.historico_pedidos.append(pedido)
        # Se pagamento em dinheiro e exceder valor, definir troco (simples)
        if pagamento.forma == 'dinheiro':
            self.troco = max(0.0, pagamento.valor - pedido.preco)
        return True


# -------------------------
# Exemplo de uso (teste)
# -------------------------
if __name__ == "__main__":
    # criar estoque
    estoque = Estoque(quantidade_maxima=1000)

    # criar produtos
    camiseta = Roupa(id=1, nome="Camiseta Algodão", quantidade=50, categoria="Roupas", preco=59.90, tamanho="M", cor="Branca", tecido="Algodão", genero="unissex")
    arroz = Alimento(id=2, nome="Arroz 1kg", quantidade=200, categoria="Alimentos", preco=6.50, data_validade=date(2026,1,1), peso_kg=1.0, tipo="não perecível")
    microondas = Eletrodomestico(id=3, nome="Microondas X", quantidade=10, categoria="Eletrodomésticos", preco=399.90, marca="MarcaX", ano_lancamento=2024)

    # armazenar no estoque
    estoque.armazenar(camiseta, 50)
    estoque.armazenar(arroz, 200)
    estoque.armazenar(microondas, 10)

    # criar cliente e funcionario
    cliente = Cliente(id=1, nome="Maria", data_nascimento=date(1990, 5, 14))
    funcionario = Funcionario(id=2, nome="João", cargo="Caixa", salario=1800.0)

    # cliente cria carrinho e adiciona produtos
    carrinho = Carrinho(limite=20)
    carrinho.adicionar_produto(camiseta, 2)
    carrinho.adicionar_produto(arroz, 5)

    # criar pedido
    pedido = Pedido(id_pedido=1001, carrinho=carrinho)
    preco_total = pedido.calcular_preco(estoque)
    print(f"Pedido #{pedido.id_pedido} - total: R$ {preco_total:.2f}")

    # processar pagamento
    pagamento = Pagamento(forma='dinheiro', valor=200.0)
    caixa = Caixa(funcionario=funcionario)
    sucesso = caixa.processar_pagamento(pedido, pagamento)
    print("Pagamento realizado com sucesso." if sucesso else "Falha no pagamento.")
    if sucesso:
        print(f"Troco: R$ {caixa.troco:.2f}")

    # reduzir quantidade do estoque (simular saída)
    estoque.remover(camiseta.id, 2)
    estoque.remover(arroz.id, 5)
    print("Quantidades restantes:", estoque.obter_quantidade(camiseta.id), estoque.obter_quantidade(arroz.id))
