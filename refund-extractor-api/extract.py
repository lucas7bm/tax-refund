import os, re, sys, copy
from time import sleep
import camelot, ghostscript, pdfplumber
import xlsxwriter

value_regex = r'\d*\.?\d+,\d+'

def get_parcels(matrix):
    # VAMOS DEFINIR UMA CODIFICAÇÃO PARA AS POSSÍVEIS TRIBUTAÇÕES
    # 1 -> ST
    # 2 -> MONOFÁSICO
    # 3 -> ST MONOFÁSICO
    parcels = {
        1 : 0.00,
        2 : 0.00,
        3 : 0.00
    }
    offset = 0
    for row in matrix[offset:]:
        offset += 1
        if "parcela" in str(row).lower():
            value = re.findall(value_regex, row[0])[0]
            dict_index = 0
            taxes_string = matrix[offset][0].lower() + "\n" + matrix[offset+1][0].lower()
            if "subst" in taxes_string and "icms" in taxes_string:
                dict_index += 1
            if "monof" in taxes_string and ("cofins" in taxes_string or "pis" in taxes_string):
                dict_index += 2
            if "subst" in taxes_string and "pis" in taxes_string and "cofins" in taxes_string and "icms" in taxes_string:
                dict_index = 3
            try:
                value = float(value.replace(".", "").replace(",", "."))
                parcels[dict_index] = value
            except Exception as e:
                print("Erro ao converter valor de parcela. String: " + value)
                print(e)
        if re.findall(r'.*valor.*informado:.*', str(row).lower()):
            return parcels
        if re.findall(r'.*venda.*', str(row).lower()):
            return parcels
        if re.findall(r'.*revenda.*', str(row).lower()):
            return parcels
    return parcels

def get_taxed(matrix):
    offset = 0
    found = False
    for row in matrix:
        if re.findall(r'.*revenda.*sem substitui.*substituto.*', str(row).lower()):
            try:
                TOTAL_TRIB = float(re.findall(value_regex, str(row))[0].replace(".", "").replace(",", "."))
                found = True
            except Exception as e:
                print("Erro ao converter TOTAL_TRIB_REVENDA. String: " + TOTAL_TRIB)
                print(e)
        offset += 1
        if found:
            return matrix[offset:], TOTAL_TRIB
    if not found:
        return matrix, 0.00

def get_untaxed(matrix):
    offset = 0
    found = False
    for row in matrix:
        if re.findall(r'.*revenda.*com substitui.*substitu[i|í]do.*', str(row).lower()):
            try:
                TOTAL_ST = float(re.findall(value_regex, str(row))[0].replace(".", "").replace(",", "."))
                found = True
            except Exception as e:
                print("Erro ao converter TOTAL_ST_REVENDA. String: " + TOTAL_ST)
                print(e)
        offset += 1
        if found:
            return matrix[offset:], TOTAL_ST, get_parcels(matrix[offset:])
    if not found:
        return matrix, 0.00, {1:0.00, 2:0.00, 3:0.00}

def get_industrialized_taxed(matrix):
    offset = 0
    found = False
    for row in matrix:
        if re.findall(r'.*venda.*industri.*sem substitui.*substituto.*', str(row).lower()):
            try:
                TOTAL_IND_TRIB = float(re.findall(value_regex, str(row))[0].replace(".", "").replace(",", "."))
                found = True
            except Exception as e:
                print("Erro ao converter TOTAL_TRIB_VENDA. String: " + TOTAL_IND_TRIB)
                print(e)
        offset += 1
        if found:
            return matrix[offset:], TOTAL_IND_TRIB
    if not found:
        return matrix, 0.00

def get_industrialized_untaxed(matrix):
    offset = 0
    found = False
    for row in matrix:
        if re.findall(r'.*venda.*industri.*com substitui..*substitu[i|í]do.*', str(row).lower()):
            try:
                TOTAL_IND_ST = float(re.findall(value_regex, str(row))[0].replace(".", "").replace(",", "."))
                found = True
            except Exception as e:
                print("Erro ao converter TOTAL_ST_VENDA. String: " + TOTAL_IND_ST)
                print(e)
        offset += 1
        if found:
            return matrix[offset:], TOTAL_IND_ST, get_parcels(matrix[offset:])
    if not found:
        return matrix, 0.00, {1:0.00, 2:0.00, 3:0.00}

def from_pdf(filepath, filename):
    try:
        NOME_EMPRESA = ""
        COMPETENCIA = ""
        FATURAMENTO = 0
        TOTAL_TRIB_REVENDA = 0
        TOTAL_ST_REVENDA = 0
        TOTAL_TRIB_VENDA = 0
        TOTAL_ST_VENDA = 0
        PARCELAS_ST_REVENDA = []
        PARCELAS_ST_VENDA = []
        TOTAL_DEVIDO_DICT = []
        print("Lendo o arquivo " + filename + "...")
        with pdfplumber.open(filepath) as pdf:
            first_page = pdf.pages[0]
            plumber_text = first_page.extract_text()
            COMPETENCIA = re.findall(r'.*apuraç.*[0-1][0-9]\/[0-9]{4}', plumber_text.lower())[0]
            COMPETENCIA = re.findall(r'[0-1][0-9]\/[0-9]{4}', COMPETENCIA)[0]
        camelot_tables = camelot.read_pdf(filepath, pages="all", line_scale=40, strip_text='\n')
        # checking if the file is supported
        if not camelot_tables:
            print("Arquivo não contém tabelas: ", filename)
            print()
            return 0
        if not re.findall(r'.*extrato.*simples.*nacional.*', str(camelot_tables[0].data[0]).lower()):
            print("Arquivo não suportado: ", filename)
            print("Provavelmente não é um extrato. (PGDAS?)")
            print()
            return 0
        # construindo a versão serializada 2D das matrizes do camelot
        matrix = []
        for table in camelot_tables:
            for row in table.data:
                matrix.append(row)
        # Este offset serve para que não seja preciso percorrer o arquivo todo novamente
        # A informação que precisamos está serializada
        offset = 0
        # Primeiro extraímos o nome da empresa
        for row in matrix:
            found = False
            for field in row:
                try:
                    NOME_EMPRESA = field[field.lower().rindex("empresarial: ") + 13:]
                    found = True
                except: continue
            offset += 1
            if found: break
        matrix = matrix[offset:]
        # EXTRAÇÃO DE REVENDAS TRIBUTADAS
        matrix, TOTAL_TRIB_REVENDA = get_taxed(matrix)
        # EXTRAÇÃO DE REVENDAS ST
        matrix, TOTAL_ST_REVENDA, PARCELAS_ST_REVENDA = get_untaxed(matrix)
        # EXTRAÇÃO DE VENDAS TRIBUTADAS
        matrix, TOTAL_TRIB_VENDA = get_industrialized_taxed(matrix)
        # EXTRAÇÃO DE VENDAS ST
        matrix, TOTAL_ST_VENDA, PARCELAS_ST_VENDA = get_industrialized_untaxed(matrix)
        # APÓS OS DESMEMBRAMENTOS, ENCONTRAMOS O FATURAMENTO TOTAL
        offset = 0
        for row in matrix:
            found = False
            for field in row:
                if re.findall(r'.*valor.*informado:.*', str(row).lower()):
                    FATURAMENTO = float(re.findall(value_regex, str(row))[0].replace(".", "").replace(",", "."))
                    found = True
            offset += 1
            if found: break
        matrix = matrix[offset:]
        # O VALOR TOTAL PAGO É O EXTRAÍDO A SEGUIR
        offset = 0
        for row in matrix:
            offset += 1
            found = False
            for field in row:
                if re.findall(r'.*total.*d[e|é]bito.*declarado.*', str(row).lower()) or re.findall(r'.*total.*devido.*tributo.*', str(row).lower()):
                    keys = [str(k).lower().strip() for k in matrix[offset]]
                    values = [float(v.replace(".", "").replace(",", ".")) for v in re.findall(value_regex, str(matrix[offset+1]))]
                    TOTAL_DEVIDO_DICT = dict(zip(keys, values))
                    found = True
            if found: break
        matrix = matrix[offset:]
       
        TOTAL_MONO = PARCELAS_ST_REVENDA[2] + PARCELAS_ST_REVENDA[3] + PARCELAS_ST_VENDA[2] + PARCELAS_ST_VENDA[3]
        TOTAL_ST = PARCELAS_ST_REVENDA[1] + PARCELAS_ST_VENDA[1]
        MONO_RECALCULADO = FATURAMENTO * 0.8
        MONO_NAO_DECLARADO = MONO_RECALCULADO - TOTAL_MONO
        PISCOFINS_PAGO = TOTAL_DEVIDO_DICT["pis/pasep"] + TOTAL_DEVIDO_DICT["cofins"]
        ALIQUOTA = PISCOFINS_PAGO/TOTAL_ST
        A_RECUPERAR = MONO_NAO_DECLARADO * ALIQUOTA
        PISCOFINS_RECALCULADO = PISCOFINS_PAGO - A_RECUPERAR

        linha_detalhada = {
            "empresa" : NOME_EMPRESA,
            "competencia" : COMPETENCIA,
            "faturamento" : FATURAMENTO,
            "total_devido" : TOTAL_DEVIDO_DICT["total"],
            "total_trib_revenda" : TOTAL_TRIB_REVENDA,
            "total_st_revenda" : TOTAL_ST_REVENDA,
            "revenda_st" : PARCELAS_ST_REVENDA[1],
            "revenda_monofasica" : PARCELAS_ST_REVENDA[2],
            "revenda_st_monofasica" : PARCELAS_ST_REVENDA[3],
            "total_trib_venda" : TOTAL_TRIB_VENDA,
            "total_st_venda" : TOTAL_ST_VENDA,
            "venda_st" : PARCELAS_ST_VENDA[1],
            "venda_monofasica" : PARCELAS_ST_VENDA[2],
            "venda_st_monofasica" : PARCELAS_ST_VENDA[3],
            "pis" : TOTAL_DEVIDO_DICT["pis/pasep"],
            "cofins" : TOTAL_DEVIDO_DICT["cofins"],
            "ALIQ" : ALIQUOTA,
            "TOTAL_MONO" : TOTAL_MONO,
            "PISCOFINS_PAGO" : PISCOFINS_PAGO,
            "SALDO_A_RECUPERAR" : A_RECUPERAR,
            "MONO_NAO_DECLARADO" : MONO_NAO_DECLARADO,
            "PISCOFINS_RECALCULADO" : PISCOFINS_RECALCULADO
        }
        return linha_detalhada
    except Exception as e:
        print("Arquivo não pôde ser lido: " + filename)
        print(e)
        sleep(15)