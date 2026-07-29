from __future__ import annotations
import argparse
import json
import os
import shutil
import stat
import sys
import threading
import time
import tkinter as tk
import zipfile
from pathlib import Path, PurePosixPath
from tkinter import Tk, filedialog, messagebox, ttk
NOME_APP = 'ExtratorAutomatico'
INTERVALO_SEGUNDOS = 0.5

def pasta_downloads() -> Path:
    if os.name == 'nt':
        try:
            import winreg
            chave = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders'
            guid_downloads = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chave) as registro:
                valor, _ = winreg.QueryValueEx(registro, guid_downloads)
                return Path(os.path.expandvars(valor)).expanduser()
        except (OSError, ImportError):
            pass
    return Path.home() / 'Downloads'

def pasta_dados_app() -> Path:
    base = os.environ.get('LOCALAPPDATA')
    return Path(base) / NOME_APP if base else Path.home() / f'.{NOME_APP}'

def arquivo_estado() -> Path:
    return pasta_dados_app() / 'estado.json'

def nome_disponivel(caminho: Path) -> Path:
    if not caminho.exists():
        return caminho
    contador = 2
    while True:
        candidato = caminho.with_name(f'{caminho.stem} ({contador}){caminho.suffix}')
        if not candidato.exists():
            return candidato
        contador += 1

def validar_item_zip(info: zipfile.ZipInfo, destino: Path) -> Path:
    relativo = PurePosixPath(info.filename.replace('\\', '/'))
    if relativo.is_absolute() or '..' in relativo.parts:
        raise ValueError(f'Caminho inseguro no ZIP: {info.filename}')
    if stat.S_ISLNK(info.external_attr >> 16):
        raise ValueError(f'Link simbólico não permitido: {info.filename}')
    alvo = (destino / Path(*relativo.parts)).resolve()
    raiz = destino.resolve()
    if alvo != raiz and raiz not in alvo.parents:
        raise ValueError(f'Arquivo fora da pasta de destino: {info.filename}')
    return alvo

def extrair_zip_seguro(zip_path: Path, destino: Path) -> int:
    quantidade = 0
    with zipfile.ZipFile(zip_path, 'r') as arquivo_zip:
        infos = arquivo_zip.infolist()
        for info in infos:
            validar_item_zip(info, destino)
        for info in infos:
            alvo = validar_item_zip(info, destino)
            if info.is_dir():
                alvo.mkdir(parents=True, exist_ok=True)
            else:
                alvo.parent.mkdir(parents=True, exist_ok=True)
                with arquivo_zip.open(info) as origem, alvo.open('wb') as saida:
                    shutil.copyfileobj(origem, saida)
                quantidade += 1
    return quantidade

def organizar_zip(original: Path, pasta_saida: Path) -> tuple[Path, Path, int]:
    original = original.resolve()
    if not original.is_file() or not zipfile.is_zipfile(original):
        raise ValueError('O download não é um arquivo ZIP válido.')
    pasta_zipado = pasta_saida / 'Zipado'
    pasta_descompactado = pasta_saida / 'Extraido'
    pasta_zipado.mkdir(parents=True, exist_ok=True)
    pasta_descompactado.mkdir(parents=True, exist_ok=True)
    copia = nome_disponivel(pasta_zipado / original.name)
    extraido = nome_disponivel(pasta_descompactado / original.stem)
    shutil.copy2(original, copia)
    extraido.mkdir(parents=True)
    try:
        quantidade = extrair_zip_seguro(copia, extraido)
    except Exception:
        shutil.rmtree(extraido, ignore_errors=True)
        copia.unlink(missing_ok=True)
        raise
    return (copia, extraido, quantidade)
NOMES_RESERVADOS_WINDOWS = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}

def validar_nome_pasta(nome: str) -> str:
    nome = nome.strip()
    if not nome:
        raise ValueError('Informe o nome da nova pasta.')
    if any((caractere in nome for caractere in '<>:"/\\|?*')):
        raise ValueError('O nome contém um caractere não permitido: < > : " / \\ | ? *')
    if nome.endswith((' ', '.')):
        raise ValueError('O nome não pode terminar com espaço ou ponto.')
    if nome.split('.')[0].upper() in NOMES_RESERVADOS_WINDOWS:
        raise ValueError('Esse nome é reservado pelo Windows.')
    return nome

class DialogoDestino:

    def __init__(self, parent: Tk, arquivo: Path, inicial: Path) -> None:
        self.parent = parent
        self.arquivo = arquivo
        self.resultado: Path | None = None
        self.criar_nova = tk.BooleanVar(value=True)
        self.tipo_nome = tk.StringVar(value='zip')
        self.nome_personalizado = tk.StringVar()
        self.local_base = tk.StringVar(value=str(inicial))
        self.janela = tk.Toplevel(parent)
        self.janela.title('Organizar arquivo ZIP')
        self.janela.geometry('650x480')
        self.janela.resizable(False, False)
        self.janela.transient(parent)
        self.janela.attributes('-topmost', True)
        self.janela.protocol('WM_DELETE_WINDOW', self.cancelar)
        quadro = ttk.Frame(self.janela, padding=24)
        quadro.pack(fill='both', expand=True)
        ttk.Label(quadro, text='Onde deseja organizar o ZIP?', font=('Segoe UI', 17, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Label(quadro, text=f'Arquivo detectado: {arquivo.name}', wraplength=590).grid(row=1, column=0, columnspan=3, sticky='w', pady=(5, 18))
        ttk.Label(quadro, text='Local onde será salvo:').grid(row=2, column=0, columnspan=3, sticky='w')
        ttk.Entry(quadro, textvariable=self.local_base, state='readonly').grid(row=3, column=0, columnspan=2, sticky='ew', pady=(5, 15))
        ttk.Button(quadro, text='Selecionar local', command=self.selecionar_local).grid(row=3, column=2, padx=(8, 0), pady=(5, 15))
        ttk.Checkbutton(quadro, text='Criar uma nova pasta neste local', variable=self.criar_nova, command=self.atualizar_campos).grid(row=4, column=0, columnspan=3, sticky='w', pady=(0, 12))
        self.radio_zip = ttk.Radiobutton(quadro, text=f'Usar o nome do ZIP: {arquivo.stem}', variable=self.tipo_nome, value='zip', command=self.atualizar_campos)
        self.radio_zip.grid(row=5, column=0, columnspan=3, sticky='w', padx=(22, 0))
        self.radio_novo = ttk.Radiobutton(quadro, text='Usar outro nome:', variable=self.tipo_nome, value='personalizado', command=self.atualizar_campos)
        self.radio_novo.grid(row=6, column=0, columnspan=3, sticky='w', padx=(22, 0), pady=(8, 4))
        self.entrada_nome = ttk.Entry(quadro, textvariable=self.nome_personalizado)
        self.entrada_nome.grid(row=7, column=0, columnspan=3, sticky='ew', padx=(42, 0))
        ttk.Separator(quadro).grid(row=8, column=0, columnspan=3, sticky='ew', pady=20)
        ttk.Label(quadro, text='O destino final terá sempre:\n• Zipado — cópia do ZIP original\n• Extraido — conteúdo descompactado', justify='left').grid(row=9, column=0, columnspan=3, sticky='w')
        botoes = ttk.Frame(quadro)
        botoes.grid(row=10, column=0, columnspan=3, sticky='e', pady=(22, 0))
        ttk.Button(botoes, text='Cancelar', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Continuar', command=self.confirmar).pack(side='left', padx=(8, 0))
        quadro.columnconfigure(0, weight=1)
        quadro.columnconfigure(1, weight=1)
        self.atualizar_campos()

    def selecionar_local(self) -> None:
        escolhido = filedialog.askdirectory(parent=self.janela, title='Selecione o local onde a pasta será salva', initialdir=self.local_base.get(), mustexist=True)
        if escolhido:
            self.local_base.set(escolhido)
            self.janela.lift()

    def atualizar_campos(self) -> None:
        criar = self.criar_nova.get()
        estado_radio = 'normal' if criar else 'disabled'
        self.radio_zip.config(state=estado_radio)
        self.radio_novo.config(state=estado_radio)
        habilitar_nome = criar and self.tipo_nome.get() == 'personalizado'
        self.entrada_nome.config(state='normal' if habilitar_nome else 'disabled')
        if habilitar_nome:
            self.entrada_nome.focus_set()

    def confirmar(self) -> None:
        try:
            base = Path(self.local_base.get()).expanduser()
            if not base.is_dir():
                raise ValueError('Selecione um local válido.')
            if self.criar_nova.get():
                nome = self.arquivo.stem if self.tipo_nome.get() == 'zip' else self.nome_personalizado.get()
                nome = validar_nome_pasta(nome)
                destino = nome_disponivel(base / nome)
                destino.mkdir(parents=False)
            else:
                destino = base
            self.resultado = destino
            self.janela.destroy()
        except (OSError, ValueError) as erro:
            messagebox.showerror('Destino inválido', str(erro), parent=self.janela)

    def cancelar(self) -> None:
        self.resultado = None
        self.janela.destroy()

    def mostrar(self) -> Path | None:
        self.janela.grab_set()
        self.janela.lift()
        self.janela.focus_force()
        self.parent.wait_window(self.janela)
        return self.resultado

def escolher_destino(parent: Tk, arquivo: Path, inicial: Path) -> Path | None:
    return DialogoDestino(parent, arquivo, inicial).mostrar()

def confirmar_e_abrir_pasta(parent: Tk, pasta: Path, quantidade: int) -> None:
    abrir = messagebox.askyesno('Extração concluída', f'{quantidade} arquivo(s) extraído(s) com sucesso.\n\nPasta:\n{pasta}\n\nDeseja abrir a pasta extraída?', parent=parent)
    if not abrir:
        return
    try:
        if os.name == 'nt':
            os.startfile(str(pasta))
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', str(pasta)])
        else:
            import subprocess
            subprocess.Popen(['xdg-open', str(pasta)])
    except Exception as erro:
        messagebox.showwarning('Não foi possível abrir a pasta', f'A extração foi concluída, mas a pasta não pôde ser aberta:\n\n{erro}', parent=parent)

def assinatura(arquivo: Path) -> str:
    dados = arquivo.stat()
    return f'{arquivo.resolve()}|{dados.st_size}|{dados.st_mtime_ns}'

def carregar_processados() -> set[str]:
    try:
        dados = json.loads(arquivo_estado().read_text(encoding='utf-8'))
        return set(dados.get('processados', []))
    except (OSError, ValueError, TypeError):
        return set()

def salvar_processados(processados: set[str]) -> None:
    pasta_dados_app().mkdir(parents=True, exist_ok=True)
    dados = {'processados': sorted(processados)[-2000:]}
    temporario = arquivo_estado().with_suffix('.tmp')
    temporario.write_text(json.dumps(dados, ensure_ascii=False), encoding='utf-8')
    temporario.replace(arquivo_estado())

def adquirir_instancia_unica() -> object | None:
    if os.name != 'nt':
        return object()
    import ctypes
    kernel32 = ctypes.windll.kernel32
    identificador = kernel32.CreateMutexW(None, False, f'Local\\{NOME_APP}_Monitor')
    if not identificador or kernel32.GetLastError() == 183:
        return None
    return identificador

class Monitor:

    def __init__(self) -> None:
        self.raiz = Tk()
        self.raiz.withdraw()
        self.downloads = pasta_downloads()
        self.processados = carregar_processados()
        self.observados: dict[Path, tuple[int, int]] = {}
        self.fila: list[Path] = []
        self.exibindo_pergunta = False

    def iniciar(self) -> None:
        self.raiz.after(1000, self.verificar)
        self.raiz.mainloop()

    def verificar(self) -> None:
        try:
            atuais = list(self.downloads.glob('*.zip')) if self.downloads.exists() else []
            caminhos_atuais = set(atuais)
            for caminho in list(self.observados):
                if caminho not in caminhos_atuais:
                    self.observados.pop(caminho, None)
            for arquivo in atuais:
                try:
                    chave = assinatura(arquivo)
                    tamanho = arquivo.stat().st_size
                except OSError:
                    continue
                if chave in self.processados or arquivo in self.fila:
                    continue
                tamanho_anterior, repeticoes = self.observados.get(arquivo, (-1, 0))
                repeticoes = repeticoes + 1 if tamanho == tamanho_anterior else 0
                self.observados[arquivo] = (tamanho, repeticoes)
                if repeticoes >= 1 and zipfile.is_zipfile(arquivo):
                    self.fila.append(arquivo)
                    self.observados.pop(arquivo, None)
            if self.fila and (not self.exibindo_pergunta):
                self.perguntar_destino(self.fila.pop(0))
        finally:
            self.raiz.after(int(INTERVALO_SEGUNDOS * 1000), self.verificar)

    def perguntar_destino(self, arquivo: Path) -> None:
        self.exibindo_pergunta = True
        try:
            self.raiz.deiconify()
            self.raiz.attributes('-topmost', True)
            self.raiz.update()
            destino = escolher_destino(self.raiz, arquivo, self.downloads)
            try:
                chave = assinatura(arquivo)
            except OSError:
                return
            if destino is not None:
                try:
                    _, pasta_extraida, quantidade = organizar_zip(arquivo, destino)
                    confirmar_e_abrir_pasta(self.raiz, pasta_extraida, quantidade)
                except Exception as erro:
                    messagebox.showerror('Não foi possível extrair', f'{arquivo.name}\n\n{erro}', parent=self.raiz)
            self.processados.add(chave)
            salvar_processados(self.processados)
        finally:
            self.raiz.withdraw()
            self.exibindo_pergunta = False

def caminhos_instalacao() -> tuple[Path, Path, Path]:
    app_dir = pasta_dados_app()
    programa = app_dir / 'extrator_automatico.pyw'
    startup = Path(os.environ['APPDATA']) / 'Microsoft\\Windows\\Start Menu\\Programs\\Startup\\ExtratorAutomatico.vbs'
    return (app_dir, programa, startup)

def registrar_zips_atuais() -> None:
    processados = carregar_processados()
    downloads = pasta_downloads()
    if downloads.exists():
        for arquivo in downloads.glob('*.zip'):
            try:
                processados.add(assinatura(arquivo))
            except OSError:
                continue
    salvar_processados(processados)

def instalar_inicializacao() -> None:
    if os.name != 'nt':
        raise OSError('A inicialização automática desta versão é própria para Windows.')
    app_dir, programa, startup = caminhos_instalacao()
    app_dir.mkdir(parents=True, exist_ok=True)
    registrar_zips_atuais()
    origem = Path(__file__).resolve()
    if origem != programa.resolve():
        shutil.copy2(origem, programa)
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    if not pythonw.exists():
        pythonw = Path(sys.executable)

    def vbs_texto(texto: str) -> str:
        return texto.replace('"', '""')
    comando = f'"{pythonw}" "{programa}" --monitor'
    conteudo = f'Set shell = CreateObject("WScript.Shell")\nshell.Run "{vbs_texto(comando)}", 0, False\n'
    startup.parent.mkdir(parents=True, exist_ok=True)
    startup.write_text(conteudo, encoding='utf-8')

def remover_inicializacao() -> None:
    if os.name != 'nt':
        return
    _, _, startup = caminhos_instalacao()
    startup.unlink(missing_ok=True)

def iniciar_monitor_instalado() -> None:
    if os.name != 'nt':
        threading.Thread(target=Monitor().iniciar, daemon=True).start()
        return
    import subprocess
    _, programa, _ = caminhos_instalacao()
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    executavel = pythonw if pythonw.exists() else Path(sys.executable)
    subprocess.Popen([str(executavel), str(programa), '--monitor'], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), close_fds=True)

class Painel:

    def __init__(self) -> None:
        self.raiz = Tk()
        self.raiz.title('Extrator Automático')
        self.raiz.geometry('620x390')
        self.raiz.resizable(False, False)
        quadro = ttk.Frame(self.raiz, padding=28)
        quadro.pack(fill='both', expand=True)
        ttk.Label(quadro, text='Extrator Automático de ZIP', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(quadro, text='Monitora sua pasta Downloads em segundo plano. Quando um ZIP novo terminar de baixar, o programa perguntará onde você deseja organizá-lo.', wraplength=550, justify='left').pack(anchor='w', pady=(10, 20))
        ttk.Label(quadro, text='Estrutura criada no destino:\n• Zipado → mantém uma cópia do ZIP\n• Extraido → recebe o conteúdo extraído', justify='left').pack(anchor='w', pady=(0, 22))
        ttk.Button(quadro, text='Ativar e iniciar com o Windows', command=self.ativar).pack(fill='x', ipady=6)
        ttk.Button(quadro, text='Desativar inicialização automática', command=self.desativar).pack(fill='x', pady=8, ipady=4)
        ttk.Button(quadro, text='Processar um ZIP agora', command=self.processar_agora).pack(fill='x', ipady=4)
        self.status = ttk.Label(quadro, text='')
        self.status.pack(anchor='w', pady=(15, 0))
        self.atualizar_status()

    def atualizar_status(self) -> None:
        ativo = False
        if os.name == 'nt':
            try:
                ativo = caminhos_instalacao()[2].exists()
            except KeyError:
                pass
        texto = 'Inicialização automática: ATIVA' if ativo else 'Inicialização automática: DESATIVADA'
        self.status.config(text=texto)

    def ativar(self) -> None:
        try:
            instalar_inicializacao()
            iniciar_monitor_instalado()
            self.atualizar_status()
            messagebox.showinfo('Ativado', 'Pronto! O monitor já está rodando e iniciará automaticamente quando você entrar no Windows.', parent=self.raiz)
        except Exception as erro:
            messagebox.showerror('Erro ao ativar', str(erro), parent=self.raiz)

    def desativar(self) -> None:
        try:
            remover_inicializacao()
            self.atualizar_status()
            messagebox.showinfo('Desativado', 'A inicialização automática foi removida. Se o monitor estiver rodando agora, ele encerrará quando você sair do Windows.', parent=self.raiz)
        except Exception as erro:
            messagebox.showerror('Erro ao desativar', str(erro), parent=self.raiz)

    def processar_agora(self) -> None:
        arquivo = filedialog.askopenfilename(parent=self.raiz, title='Selecione um arquivo ZIP', initialdir=str(pasta_downloads()), filetypes=[('Arquivos ZIP', '*.zip')])
        if not arquivo:
            return
        destino = escolher_destino(self.raiz, Path(arquivo), pasta_downloads())
        if destino is None:
            return
        try:
            _, extraido, quantidade = organizar_zip(Path(arquivo), destino)
            confirmar_e_abrir_pasta(self.raiz, extraido, quantidade)
        except Exception as erro:
            messagebox.showerror('Erro', str(erro), parent=self.raiz)

    def executar(self) -> None:
        self.raiz.mainloop()

def main() -> None:
    parser = argparse.ArgumentParser(description='Monitor automático de arquivos ZIP.')
    parser.add_argument('--monitor', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--instalar', action='store_true', help=argparse.SUPPRESS)
    argumentos = parser.parse_args()
    if argumentos.instalar:
        raiz = Tk()
        raiz.withdraw()
        try:
            instalar_inicializacao()
            iniciar_monitor_instalado()
            time.sleep(1)
            messagebox.showinfo('Extrator Automático instalado', 'Instalação concluída!\n\nO monitor está configurado para iniciar com o Windows.\nAgora baixe um NOVO arquivo ZIP e aguarde cerca de 1 a 2 segundos depois que o download terminar.', parent=raiz)
        except Exception as erro:
            messagebox.showerror('Falha na instalação', f'Não foi possível instalar o monitor:\n\n{erro}', parent=raiz)
            raise SystemExit(1)
        finally:
            raiz.destroy()
    elif argumentos.monitor:
        trava = adquirir_instancia_unica()
        if trava is None:
            return
        Monitor().iniciar()
    else:
        Painel().executar()
if __name__ == '__main__':
    main()
