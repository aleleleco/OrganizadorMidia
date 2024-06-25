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

arquivosErro = []
origemDestino = []

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/leArquivosExif', methods=['POST'])
def le_arquivos_exif():
    patch = request.form['patch']
    patch_destino = request.form['patchDestino']
    arquivos = listar_arquivos(patch)
    arquivos_imagens = separaArquivos(arquivos, 'imagens')
    le_exif(arquivos_imagens, patch_destino)

    deleta_pasta = request.form.get('deletaEZipa')

    if deleta_pasta:
        deletar_arquivos_lidos(origemDestino)

    deleta_pasta_vaza(str(patch_destino))

    return render_template('RESULTADO.html', erros=arquivosErro, copiados=origemDestino, qtdCopiados=len(origemDestino),
                           qtdErros=len(arquivosErro))


@app.route('/leArquivosJson', methods=['POST'])
def le_arquivos_json():
    inicio = datetime.now()
    patch = request.form['patch']
    patch_destino = request.form['patchDestino']
    arquivos = listar_arquivos(patch)
    arquivos_json = separaArquivos(arquivos, 'json')
    lejson(arquivos_json, patch_destino, patch)
    deleta_pasta = request.form.get('deletaEZipa')

    if deleta_pasta:
        deletar_arquivos_lidos(origemDestino)

    deleta_pasta_vaza(str(patch_destino))

    final = datetime.now()
    gera_logs(inicio, final, patch_destino)

    return render_template('RESULTADO.html', qtdCopiados=len(origemDestino), qtdErros=len(arquivosErro),
                           patchLog=f'{patch_destino}\\MidaOraganizada.log')


@app.route('/leArquivos', methods=['POST'])
def le_arquivos():
    inicio = datetime.now()
    patch = request.form['patch']
    patch_destino = request.form['patchDestino']

    arquivos = listar_arquivos(patch)

    arquivos_imagens = separaArquivos(arquivos, 'imagens')
    leImages(arquivos_imagens, patch_destino)

    deleta_pasta_vaza(str(patch_destino))
    final = datetime.now()
    gera_logs(inicio, final, patch_destino)
    return render_template('RESULTADO.html', erros=arquivosErro, copiados=origemDestino, qtdCopiados=len(origemDestino),
                           qtdErros=len(arquivosErro))


@app.route('/resultado')
def resultado():
    return render_template('resultado.html', )


def gera_logs(inicio, final, patch_destino):
    logging.basicConfig(filename=f'{patch_destino}\\MidaOraganizada.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f'Inicio do processamento as {inicio}')
    logging.info(f'Fim do processamento as {final}')
    logging.info(f'Quantidade de arquivos copiados  {len(origemDestino)}')
    logging.info(f'Quantidade de arquivos erro  {len(arquivosErro)}')
    logging.info(f'Arquivos copiados com sucesso ... ')
    logging.info(f'...')
    for arquivos_copiados in origemDestino:
        logging.info(f' De:  {arquivos_copiados[0]} >> para {arquivos_copiados[1]}')
    logging.info(f'Arquivos com erro ... ')
    logging.info(f'...')
    for arquivos_erro in arquivosErro:
        logging.info(f' De:  {arquivos_erro[0]} >> para {arquivos_erro[1]}')
    logging.info(
        f'------------------------------------------------------------------------------------------------------------')


def deletar_arquivos_lidos(lista_lidos):
    """
    Deleta arquivos lidos da origiem

    :param lista_lidos: Lista de arquivos lidos e importados

    """
    for listaArquivos in lista_lidos:
        os.remove(listaArquivos[0])
        os.remove(f'{str(listaArquivos[0])}.json')


def deleta_pasta_vaza(patch):
    """
     Deleta subpastas vazias

    :param patch: recebe o caminho para verificar e apagar subpastas vazias
    :return: None
    """
    for pasta, subpasta, arquivo in os.walk(patch):
        if not subpasta and not arquivo:
            os.rmdir(pasta)
            print(f'pasta {pasta} vazia !! Pasta Deletada !!!')

def lejson(arquivosJson, patchDestino, patch_raiz):
    """
        corrigir a busca dos arquivos com final jpg(1).jpg
        esta gerando erro e nao está copiando

        juntar todos os arquivos em uma mesma pasta antes para juntar todos os json e imagens na mesma pasta


    :param arquivosJson:
    :param patchDestino:
    :return:
    """
    padrao = r"(?:\.jpg|\.png|\.JPG|\.PNG)$"  #padrao para busca dos arquivos que sao png e jpg
    for patchArquivo in arquivosJson:
        try:
            print(f'patch do arquivo de imagem {patchArquivo}')
            with open(patchArquivo, "r") as arquivo:
                arquivoJson = json.load(arquivo)
                print(arquivoJson)
                resultado = re.search(padrao, arquivoJson['title'])
                if resultado:
                    arquivoImagem = patchArquivo[:-5]
                    # separar os arquivos e jogar nas pastas
                    #                        |STR| CONVERT PARA DATA   |INT| Data do arquivo json                    |
                    pastaGravar = buscapasta(str(datetime.fromtimestamp(int(arquivoJson['photoTakenTime']['timestamp']))),
                                             patchDestino)
                    #print(f'Local para gravar: {pastaGravar}')

                    print(f'origem  {arquivoImagem}')
                    try:
                        destinoImagem = f'{pastaGravar}\\{str(arquivoJson['title'])}'
                        print(f'destino {destinoImagem}')
                        dest = shutil.copy2(str(arquivoImagem), str(destinoImagem))
                        print(dest)
                        origemDestino.append([str(arquivoImagem), str(destinoImagem)])
                    except Exception as e:
                        """
                            Faz a busca das imagens que nao foram encontradas na mesma pasta que o arquivo json está
                            em todas as pastas desde a raiz
                        """
                        imagem_Encontrada = busca_imagem_perdida(str(arquivoJson['title']), patch_raiz)
                        if imagem_Encontrada:
                            try:
                                dest = shutil.copy2(str(imagem_Encontrada), str(destinoImagem))
                                origemDestino.append([str(arquivoImagem), str(destinoImagem)])
                            except Exception as e2:
                                arquivosErro.append([str(arquivoImagem), e2])
                        else:
                            arquivosErro.append([str(arquivoImagem),e])
                else:
                    print(f'nao é imagem')

        except Exception as e:
            arquivosErro.append(str(arquivoJson))

def le_exif(arquivo_imagem, patch_destino):

    for imagem in arquivo_imagem:
        try:
            image = Image.open(imagem)
            exif_data = image.getexif()
            for tag, valor in exif_data.items():
                tag_nome = TAGS.get(tag, tag)
                if tag_nome == 'DateTime':
                    pastaSalvar = buscapasta(str(valor), patch_destino)
                    dest = shutil.copy2(str(imagem), str(pastaSalvar))
                    origemDestino.append([str(imagem), str(pastaSalvar)])
        except Exception as e:
            arquivosErro.append(imagem)

def leImages(listaImagens, patchDestino):
    for imagem in listaImagens:
        try:
            image = Image.open(imagem)
            exifData = image.getexif()
            data_modificacao = os.path.getmtime(imagem)  # pega data
            data_modificacao = datetime.fromtimestamp(data_modificacao)  # converte data
            captura = exifData.get(36864)  # Data e hora da captura da imagem (formato EXIF).
            capturaDigitalizadas = exifData.get(31868)
            resoluH = exifData.get(282)  # Resolução horizontal da imagem (pixels por polegada).
            resoluv = exifData.get(283)  # Resolução vertical da imagem (pixels por polegada).
            pastaSalvar = buscapasta(str(data_modificacao), patchDestino)
            dest = shutil.copy2(str(imagem), str(pastaSalvar))
            origemDestino.append([str(imagem), str(pastaSalvar)])
            #print(origemDestino)
        except Exception as e:
            arquivosErro.append(imagem)
            #print(f"Ocorreu um erro: {e}")

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


def buscapasta(dataArquivo, patchDestino):
    padrao = r"^(.{10})"
    dataCheia = re.search(padrao, dataArquivo)
    #print(dataCheia.group(1))
    padrao = r"^(.{4})"
    dataAno = re.search(padrao, dataCheia.group(1))
    #print(dataAno.group(1))
    padrao = r"^.{5}(.{2})"
    dataMes = re.search(padrao, dataCheia.group(1))
    # print(dataMes.group(1))
    padrao = r".{2}$"
    datadia = re.search(padrao, dataCheia.group(1))
    #print(datadia.group(0))

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

    return caminho


def separaArquivos(listaArquivos, tipo):
    """

    :param listaArquivos: Recebe a lista de arquivos para processar
    :param tipo: o tipo do arquivo que vai separar para retornar possiveis:
                'imagens' - retorna arquivos jpg ou png
                'json' - retorna arquivos json
    :return: retorna uma lista com os arquivos listados
    """
    #retorna somente imagens
    print('Lista arquivos')
    arquivosSeparados = []
    if tipo == 'imagens':
        print('Lista arquivos imagens')
        for arquivo in listaArquivos:

            padro = r"(?:\.jpg|\.png|\.JPG|\.PNG)$"

            resultado = re.search(padro, arquivo)
            if resultado:
                arquivosSeparados.append(arquivo)
            else:
                pass

        return arquivosSeparados

    if tipo == 'json':
        print('Lista json')
        for arquivoJson in listaArquivos:
            padro = r"(?:\.json|\.JSON)$"
            resultado = re.search(padro, arquivoJson)
            if resultado:
                arquivosSeparados.append(arquivoJson)
            else:
                pass

        return arquivosSeparados


app.run(debug=True)