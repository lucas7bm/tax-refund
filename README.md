# tax-refund

Esse é um protótipo de um webservice para recuperação de créditos fiscais.

Aqui ele está divido em três níveis:
 * refund-extractor-api, uma API desenvolvida em Python, utilizando Flask, que faz a mineração de todos os dados relevantes de extratos do PGDAS (Programa Gerador do Documento de Arrecadação do Simples Nacional). Esta API é focada apenas na extração dos extratos e no retorno estruturado dos mesmos. 
 * refund-backend, uma segunda API desenvolvida em NodeJS, que armazena os resultados provenientes da API de extração, resultados estes já devidamente filtrados à necessidade da API e ao foco na recuperação de crédito.
 * refund-frontend, um app em React que se comunica com o backend e em breve fará as solicitações à API de extração.
 
 A refund-extractor-api possui as seguintes dependências:
  - ghostscript
  - camelot-py[cv]
  - pdfplumber
  - xlsxwriter
 
O backend e o frontend são aplicações Node e React e basta instalar as dependências, migrar e inicializá-las.
