# Extrator Automático de ZIP

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?logo=windows&logoColor=white)
![Dependências](https://img.shields.io/badge/dependências-0-brightgreen)

> Automatize a organização dos arquivos ZIP baixados no Windows: o aplicativo monitora **Downloads**, detecta novos arquivos compactados e conduz a extração para uma estrutura organizada e segura.

## Por que este projeto existe?

Baixar um ZIP normalmente significa repetir a mesma sequência: localizar o arquivo, criar uma pasta, mover o original, extrair o conteúdo e conferir o resultado. O **Extrator Automático de ZIP** reduz esse trabalho manual mantendo o arquivo compactado e o conteúdo extraído separados.

- funciona em segundo plano;
- usa somente a biblioteca padrão do Python;
- não exige serviços externos;
- preserva o ZIP original;
- valida o conteúdo antes da extração;
- evita sobrescrever silenciosamente arquivos existentes.

## Demonstração

### 1. Organização do arquivo

Após detectar um novo ZIP, o aplicativo permite selecionar o local de destino, criar uma pasta com o nome original do arquivo ou informar um nome personalizado.

![Tela de organização do arquivo ZIP](docs/images/tela-organizacao.png)

### 2. Estrutura criada

O destino escolhido recebe pastas separadas para preservar o ZIP original e armazenar o conteúdo extraído.

![Estrutura das pastas Zipado e Extraido](docs/images/estrutura-pastas.png)

### 3. Conclusão da extração

Ao finalizar, o aplicativo informa a quantidade de arquivos processados e oferece a opção de abrir imediatamente a pasta extraída.

![Confirmação para abrir a pasta extraída](docs/images/confirmacao-extracao.png)

## Funcionalidades

| Recurso | O que faz |
| --- | --- |
| Monitoramento automático | Observa a pasta Downloads em segundo plano |
| Detecção rápida | Identifica novos ZIPs em aproximadamente 1–2 segundos |
| Download completo | Aguarda o arquivo terminar de ser gravado antes de processá-lo |
| Destino configurável | Permite escolher a pasta-base e criar uma nova pasta |
| Nome personalizável | Usa o nome do ZIP ou um nome informado pelo usuário |
| Preservação do original | Mantém o ZIP na estrutura `Zipado/` |
| Extração organizada | Coloca o conteúdo em `Extraido/` |
| Extração segura | Bloqueia path traversal, caminhos absolutos e links simbólicos |
| Proteção contra sobrescrita | Não substitui silenciosamente arquivos e pastas existentes |
| Processamento manual | Permite selecionar um ZIP diretamente pelo painel |
| Inicialização com Windows | Pode iniciar automaticamente junto com a sessão |

## Estrutura gerada

```text
Pasta escolhida ou criada/
├── Zipado/
│   └── arquivo.zip
└── Extraido/
    └── arquivo/
        └── conteúdo extraído
```

## Requisitos

- Windows 10 ou Windows 11
- Python 3.10 ou superior
- Testado com Python 3.12

O programa utiliza apenas módulos da biblioteca padrão do Python.

## Instalação rápida

1. Baixe ou clone este repositório.
2. Mantenha `INSTALAR_E_INICIAR.bat` e `extrator_automatico.py` na mesma pasta.
3. Execute `INSTALAR_E_INICIAR.bat`.
4. Aguarde a confirmação da instalação.
5. Reinicie o Windows caso uma versão anterior já esteja em execução.

O instalador procura automaticamente o Python 3.12. Caso não encontre, abre uma janela para selecionar manualmente o arquivo `python.exe`.

Um caminho comum é:

```text
C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python312\python.exe
```

## Como usar

Depois da instalação, baixe um novo arquivo `.zip`. Quando o download terminar, a tela de organização será aberta automaticamente.

Nela, você poderá:

1. selecionar o local-base;
2. usar diretamente esse local ou criar uma nova pasta;
3. usar o nome original do ZIP ou informar outro nome;
4. confirmar a organização;
5. abrir a pasta extraída ao finalizar.

> Arquivos ZIP que já estavam em Downloads antes da instalação são ignorados.

## Segurança

Antes da extração, o programa valida cada item do ZIP. Caminhos absolutos, tentativas de sair da pasta de destino e links simbólicos são bloqueados.

O aplicativo não exclui o ZIP baixado e não substitui silenciosamente pastas existentes.

## Desinstalação

Execute `DESINSTALAR.bat` e reinicie ou encerre a sessão do Windows.

## Contribuindo

Sugestões, correções e melhorias são bem-vindas. Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) antes de abrir um pull request.

Se o projeto resolveu um problema para você, uma ⭐ ajuda outras pessoas a encontrá-lo.

## Autoria

Desenvolvido por [Letícia Vitória](https://github.com/leticiazooe).
