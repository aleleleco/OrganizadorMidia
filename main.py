import json
import os
import re
import shutil
import logging
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from flask import Flask, render_template, request


app = Flask(__name__)

class Midia:
    
    def __init__(self, nome, origem, destino):
        """
        :param nome recebe nome
        """
        self.nome = nome
        self.origem = origem
        self.destino = destino
        self.copiada = None
        self.pasta_salvar = None
        self.exception = None
    
    def get_copiada(self):
        return self.copiada
    
    def set_copiada(self, copiada):
        self.copiada = copiada
    
    
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resultado')
def resultado():
    return render_template('resultado.html', )

@app.route('/le_multiplos_arquivos', methods=['POST'])
def le_multiplos_arquivos():
    """
    Descrição: Função principal recebe as informações do index.html e trata e acordo com a solicitação
    
    :param patch_origem : recebe o patch raiz de onde serão lidas os arquivos
    :param patch_destino : recebe o patch raiz de onde serão gravadas as informações
    :param deleta_copiados : recebe o flag para deletar arquivos depois da cópia
    :param tipo_arquivo : recebe qual o tipo de processamento que vai fazer na leitura 
            lendo do Properties do arquivo
            lendo informações do EXIF do arquivo
            Lendo informa de um JSON com os dados do arquivo
    :return passa os arquivos para pasta especifica gerando log e uma tela de finalização
    """
    
    #recebe os parametros dos forms
    extencoes = []
    patch_origem = request.form['patch'] #raiz dos arquivos a serem ccopiados
    patch_destino = request.form['patchDestino'] #raiz do destino dos arquivos
    deleta_copiados = request.form.get('deleta_copiados') #opção de deletar arquivos já lidos
    tipo_arquivo = request.form.get('tipo_busca') #tipo de arquivos que vai ler EXIF, JSON, PROPRIEDADES
    gera_logs('inicio', None , str(patch_destino)) 

    #Recebe os tipos de arquivos aque vai ler
    if request.form.get('png'):
        extencoes.append('png')
    if request.form.get('jpg'):
        extencoes.append('jpg')
    if request.form.get('heic'):
        extencoes.append('heic')
    if request.form.get('mp4'):
        extencoes.append('mp4')

    print(f'patch_origem : {patch_origem}')
    print(f'patch_destino : {patch_destino}')
    print(f'deleta_copiados : {deleta_copiados}')
    print(f'tipo_arquivo : {tipo_arquivo}')
    print(f'extencoes : {extencoes}')
    print(f'---------------------------')
    
    items = gera_arquivos(patch_origem) #busca todos os arquivos nas pastas
    arquivos = separaArquivos(items, tipo_arquivo, extencoes) #sera as extenções  que vai buscar
    midias = cria_midia(arquivos, patch_destino) #gera os arquivos com objeto de midia
    
    #faz a separação por tipos de buscas
    match tipo_arquivo:
        case 'json':
            for midia in midias:
                lejson(midia)
                gera_logs('processo', midia, str(midia.destino))
        case 'exif':
            for midia in midias:
                le_exif(midia)
                gera_logs('processo', midia, str(midia.destino))    
        case 'propriedades':
            for midia in midias:
                leImages(midia)
                gera_logs('processo', midia, str(midia.destino))
    
    #depois de copiados verifica pastas vazias para deletar
    deleta_pasta_vazia(patch_destino)
    
    #deleta os arquivos já lidos. 
    if deleta_copiados:
        print('deleta arquivos')
        arquivos_deletados=[]
        for midia in midias:
            if midia.get_copiada:
                print(f'{str(midia.origem)}')
                os.remove(f'{str(midia.origem)}')
                arquivos_deletados.append(midia)
        gera_logs('deletados',arquivos_deletados, str(patch_destino))
        
    
    #gera os logs      
    gera_logs('fim', None, str(patch_destino))
    
    #retorno e finaliza o processo
    patch_log = f'{str(patch_destino)}\\MidaOraganizada.log'
    print('fim')
    return render_template('RESULTADO.html')

def gera_arquivos(origem):
    """
        Recebe o patch para fazer a busca dos locais dos arquivos percorrendo toda a arvore de arquivos a partir do raiz
        
        :param origem patch raiz onde buscar os arquivos
        :return lista com o nome do arquivo e o caminho onde está
    """
    items = []
    for raiz, _, arquivos in os.walk(origem):
        for arquivo in arquivos:
            items.append([arquivo, f'{raiz}\\{arquivo}'])

    return items

def separaArquivos(lista_items, tipo, extencoes):
    """
    gera uma lista somente com os arquivos que seram trabalhados de acordo com as extencoes recebidas
    :param lista_items lista com todos os itens para filtrar
    :param tipo qual será a busca realizada, necessário para fazer busca diferenciada dos arquivos .XXXX.json
    :param extencoes extencoes que seram buscadas .jpg .mp4 etc
    """
    print('Lista arquivos')
    arquivos_separados = []
    if tipo == 'exif' or tipo == 'propriedades':
        print('Lista arquivos imagens-exif')
        padrao = '\\.('
        for i, extencao in enumerate(extencoes):
            padrao += extencao
            if i + 1 < len(extencoes):
                padrao += '|'
            else:
                padrao += ')$'
        print(f'Padrao de busca {padrao}')

        for item in lista_items:
            resultado = re.search(padrao, item[0], flags=re.IGNORECASE)
            if resultado:
                arquivos_separados.append(item)


    if tipo == 'json':
        print('Lista json')
        padrao = '\\.('
        for i, extencao in enumerate(extencoes):
            padrao += f'{extencao}.json'
            if i + 1 < len(extencoes):
                padrao += '|'
            else:
                padrao += ')$'
        print(f'Padrao de busca {padrao}')

    for item in lista_items:
            resultado = re.search(padrao, item[0], flags=re.IGNORECASE)
            if resultado:
                arquivos_separados.append(item)

    return(arquivos_separados)

def cria_midia(arquivos, destino):
    """
    criar os objetos de midias
    :param arquivos lista dos arquivos para criar lista contem [nome do arquivo, patch do arquivo]
    :param destino patch do destino para criar
    :return lista com objetos do tipo midia
    """
    midias = []
    for item in arquivos:
        midias.append(Midia(item[0], item[1], destino))
    print('objetos criados')

    return midias
    
def lejson(json_obj):
    """
    Faz o tratamento e copia nos arquivos ja separados, trata os arquivos com leitura do tipo json
    :param img_obj objeto do tipo midia
    
    """
    padrao = r"(?:\.jpg|\.png)$"
    print(f'patch do arquivo de imagem {json_obj.origem}')
    with open(json_obj.origem, "r") as arquivo:
        arquivo_json = json.load(arquivo)
        
def leImages(img_obj):
    """
    Faz o tratamento e copia nos arquivos ja separados, trata os arquivos com leitura do tipo configuracoes
    :param img_obj objeto do tipo midia
    
    """
    try:
        image = Image.open(img_obj.origem) # abre a imagem
        exifData = image.getexif() # converte o properties
        try:
            data_modificacao = os.path.getmtime(img_obj.origem)  # pega data
            img_obj.data_modificacao = datetime.fromtimestamp(data_modificacao)  # converte data
        except :
            img_obj.data_modificacao = None
        
        try:    
            captura = exifData.get(36864)  # Data e hora da captura da imagem (formato EXIF).
            img_obj.captura = datetime.fromtimestamp(captura)  # converte data
        except:
            img_obj.captura = None
        
        
        if img_obj.captura != None:
            img_obj.pasta_salvar = buscapasta(str(img_obj.captura), img_obj.destino) 
        else:
            img_obj.pasta_salvar = buscapasta(str(img_obj.data_modificacao), img_obj.destino) 
               
        dest = shutil.copy2(str(img_obj.origem), str(img_obj.pasta_salvar))
        img_obj.set_copiada(True)
    except Exception as e:
        img_obj.set_copiada(False)
        img_obj.exception = e
        print(f"Ocorreu um erro: {e}")    

def le_exif(img_obj):
    """
    Faz o tratamento e copia nos arquivos ja separados, trata os arquivos com leitura do tipo EXIF
    :param img_obj objeto do tipo midia
    
    """
    try:
        image = Image.open(img_obj.origem) # abre a imagem
        exif_data = image.getexif()
        for tag, valor in exif_data.items():
            tag_nome = TAGS.get(tag, tag)
            if tag_nome == 'DateTime':
                img_obj.pasta_salvar = buscapasta(str(valor), img_obj.destino)
                dest = shutil.copy2(str(img_obj.origem), str(img_obj.pasta_salvar))
                img_obj.copiada = True
    except Exception as e:
        img_obj.copiada = False
        img_obj.exception = e
        print(f"Ocorreu um erro: {e}")    

def buscapasta(dataArquivo, patchDestino):
    padrao = r"^(.{10})"
    dataCheia = re.search(padrao, dataArquivo)
    padrao = r"^(.{4})"
    dataAno = re.search(padrao, dataCheia.group(1))
    padrao = r"^.{5}(.{2})"
    dataMes = re.search(padrao, dataCheia.group(1))
    padrao = r".{2}$"
    datadia = re.search(padrao, dataCheia.group(1))
    caminho = str(patchDestino)
    pasta = os.path.join(os.getcwd(), caminho)
    if os.path.exists(pasta):
        pass
    else:
        os.mkdir(caminho)

    caminho = f'{caminho}\\{dataAno.group(1)}'
    pasta = os.path.join(os.getcwd(), caminho)
    if os.path.exists(pasta):
        # print(f'Pasta já existe')
        pass
    else:
        os.mkdir(caminho)
        #print(f'pasta criada {caminho}')

    caminho = f'{caminho}\\{dataMes.group(1)}'
    pasta = os.path.join(os.getcwd(), caminho)
    if os.path.exists(pasta):
        #print(f'Pasta já existe')
        pass
    else:
        os.mkdir(caminho)
        #print(f'pasta criada {caminho}')

    caminho = f'{caminho}\\{datadia.group(0)}'
    pasta = os.path.join(os.getcwd(), caminho)
    if os.path.exists(pasta):
        #print(f'Pasta já existe')
        pass
    else:
        os.mkdir(caminho)
        #print(f'pasta criada {caminho}')
    print(caminho)
    return caminho

def deleta_pasta_vazia(patch):
    """
    deleta pastas vazias depois de copiados os arquivos
    :param patch caminho raiz das pastas
    """
    for pasta, subpasta, arquivo in os.walk(patch):
        if not subpasta and not arquivo:
            os.rmdir(pasta)
            print(f'pasta {pasta} vazia !! Pasta Deletada !!!')

def busca_imagem_perdida(nome_imagem, patch_raiz):
    print(f' busca imagem {nome_imagem} no patch {patch_raiz}')
    for raiz, _, arquivos in os.walk(patch_raiz):
        #print(f'arquivos na busca do perdido {arquivos}')
        for arquivo in arquivos:
            if arquivo == nome_imagem:
                return (f'{raiz}\\{arquivo}')

def listar_arquivos(patch):
    """
    :param patch: Recebe pach para listar os arquivos na pasta especifica
    :return: Retorna uma lista com os arquivos nas pastas e subpastas
    """

    listaArquivos = []

    for raiz, _, arquivos in os.walk(patch):  # retorna lista dos arquivos de cada pasta
        #print(arquivos)
        for arquivo in arquivos:
            caminhoCompleto = os.path.join(raiz, arquivo)  # caminho completo de cada arquivo
            listaArquivos.append(caminhoCompleto)
    return listaArquivos

def gera_logs(tempo_exec, obj_img, patch_destino):
    logging.basicConfig(filename=f'{patch_destino}\\MidaOraganizada.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    match tempo_exec:
        case 'inicio':
            logging.info(f'Inicio do processamento as {datetime.now()}')
        case 'processo':
            if obj_img.get_copiada():
                logging.info(f'Arquivo  {obj_img.nome} DE {obj_img.origem} >> Para {obj_img.pasta_salvar}')
            else:
                logging.info(f'Arquivo  {obj_img.nome} erro: {obj_img.exception}')
        case 'fim':
            logging.info(f'Fim do processamento as {datetime.now()}')
        case 'deletados':
            logging.info(f'Arquivos deletados do processamento: {len(obj_img)}')
            for imagem in obj_img:
                logging.info(f'>> {imagem.nome}')
   
app.run(debug=True)