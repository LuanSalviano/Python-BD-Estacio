# Importações
from functools import wraps  # Importação os 'wraps' para preservar a identidade de funções decoradas.
from flask import Flask, render_template, request, flash  # Importação das classes e funções essenciais do Flask.
from flask import session, redirect, url_for  # Importação das funcionalidades para gerenciar sessões e redirecionamentos.
from flask_mysqldb import MySQL  # Importação da extensão MySQL para interagir com bancos de dados MySQL.

app = Flask(__name__)  # Inicialização da aplicação Flask com o nome do módulo.

# Configuração do banco de dados
app.config['MYSQL_HOST'] = 'localhost'  # Endereço do host do banco de dados.
app.config['MYSQL_USER'] = 'root'  # Usuário que terá acesso ao banco de dados.
app.config['MYSQL_PASSWORD'] = 'Abrac@2004'  # Senha para autenticação no banco de dados.
app.config['MYSQL_DB'] = 'SistemaComplexo'  # Nome do banco de dados a ser utilizado.

# Chave secreta para gerenciamento de sessões
app.secret_key = 'a7f041327602a31798cf2e790c1a20fb'  # Definição de uma chave secreta para proteger as sessões e cookies.

# Inicialização da conexão com o banco de dados
mysql = MySQL(app)  # Criação de uma instância do MySQL com a configuração do Flask.

@app.route('/')  # Definição a rota para a URL raiz.
def index():
    # Redirecionamento para a página de login
    return redirect(url_for('login'))  # Redireciona o usuário para a função 'login'

@app.route('/login', methods=['GET', 'POST'])  # Definição a rota '/login'
def login():
    # Se o método for POST, processa o login
    if request.method == 'POST':
        usuario = request.form['usuario']  # Obtém o nome de usuário do formulário.
        senha = request.form['senha']  # Obtém a senha do formulário.

        cur = mysql.connection.cursor()  # Criação de um cursor para interagir com o banco de dados.
        # Consulta no banco para verificar o usuário e senha
        cur.execute("SELECT * FROM trabalhadores WHERE usuario=%s AND senha=%s", (usuario, senha))
        user = cur.fetchone()  # Obtém o primeiro resultado da consulta.
        cur.close()  # Encerramento do cursor.

        if user:  # Se o usuário for encontrado
            session['usuario'] = user[1]  # Armazena o nome do usuário na sessão.
            flash('Login bem-sucedido!', 'success')  # Mensagem de sucesso para o usuário.
            return redirect(url_for('home'))  # Redireciona para a página home.
        else:  # Se o usuário não for encontrado
            flash('Usuário ou senha incorretos!', 'danger')  # Mensagem de erro para o usuário.

    return render_template('login.html')  # Renderiza o template de login.

# Decorador para proteger rotas que requerem login
def login_required(f):
    @wraps(f)  # Mantém as informações originais da função decorada.
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário está na sessão
        if 'usuario' not in session:
            # Se não estiver, redireciona para a página de login
            return redirect(url_for('login'))
        # Se estiver na sessão, chama a função original
        return f(*args, **kwargs)
    return decorated_function  # Retorna a função decorada.

@app.route('/logout', methods=['POST'])  # Definição a rota '/logout'
def logout():
    # Remove o usuário da sessão
    session.pop('usuario', None)  # Remove a chave 'usuario' da sessão, se existir.
    # Mensagem de sucesso informando que o logout foi realizado
    flash('Você saiu com sucesso!', 'success')  # Exibe uma mensagem de sucesso.
    # Redireciona para a página de login
    return redirect(url_for('login'))  # Redireciona o usuário para a página de login.

@app.route('/home')  # Definição a rota '/home'.
@login_required  # Protege a rota, requerendo login.
def home():
    # Renderiza a página inicial
    return render_template('home.html')  # Retorna o template da página inicial.

@app.route('/cadastro')  # Definição a rota '/cadastro'.
@login_required  # Protege a rota, requerendo login.
def cadastro():
    # Renderiza a página de cadastro
    return render_template('cadastro.html')  # Retorna o template da página de cadastro.

@app.route('/cadastrar', methods=['POST'])  # Definição a rota '/cadastrar'
@login_required  # Protege a rota, requerendo login.
def cadastrar():
    if request.method == 'POST':  # Verifica se o método é POST.
        # Captura os dados do formulário
        nome = request.form['nome']  # Captura o nome.
        endereco = request.form['endereco']  # Captura o endereço.
        idade = request.form['idade']  # Captura a idade.
        telefone = request.form['telefone']  # Captura o telefone.

        cur = mysql.connection.cursor()  # Criação de um cursor para interagir com o banco de dados.
        # Insere os dados no banco
        cur.execute("INSERT INTO moradores (nome, endereco, idade, telefone) VALUES (%s, %s, %s, %s)",
                    (nome, endereco, idade, telefone))
        mysql.connection.commit()  # Confirma a transação para salvar os dados.
        cur.close()  # Fecha o cursor após a operação.

        flash('Morador cadastrado com sucesso!', 'success')  # Mensagem de sucesso para o usuário.
        return redirect(url_for('home'))  # Redireciona para a página inicial.

@app.route('/listar')  # Definição a rota '/listar'.
@login_required  # Protege a rota, requerendo login.
def listar():
    search_query = request.args.get('search', '')  # Obtém a consulta de busca, padrão é vazio.
    search_by = request.args.get('searchBy', 'nome')  # Obtém o campo para busca, padrão é 'nome'.
    page = int(request.args.get('page', 1))  # Obtém a página atual, padrão é 1.
    limit = 15  # Limite de registros por página.
    offset = (page - 1) * limit  # Calcula o deslocamento para a consulta.

    cur = mysql.connection.cursor()  # Criação de um cursor para interagir com o banco de dados.

    # Adiciona lógica de busca para diferentes campos
    if search_query:
        if search_by == 'endereco':
            cur.execute("SELECT * FROM moradores WHERE endereco LIKE %s LIMIT %s OFFSET %s", ('%' + search_query + '%', limit, offset))
        elif search_by == 'telefone':
            cur.execute("SELECT * FROM moradores WHERE telefone LIKE %s LIMIT %s OFFSET %s", ('%' + search_query + '%', limit, offset))
        else:
            cur.execute("SELECT * FROM moradores WHERE nome LIKE %s LIMIT %s OFFSET %s", ('%' + search_query + '%', limit, offset))
    else:
        cur.execute("SELECT * FROM moradores LIMIT %s OFFSET %s", (limit, offset))  # Consulta padrão sem filtro.

    moradores = cur.fetchall()  # Obtém todos os registros retornados.

    # Obtém o total de registros para calcular o total de páginas
    cur.execute("SELECT COUNT(*) FROM moradores")  # Conta o total de moradores.
    total_records = cur.fetchone()[0]  # Obtém o total de registros.
    total_pages = (total_records + limit - 1) // limit  # Calcula o número total de páginas.

    cur.close()  # Fecha o cursor após a operação.

    return render_template('lista.html', moradores=moradores, search_query=search_query, search_by=search_by, page=page, total_pages=total_pages)  # Renderiza o template com os dados.


@app.route('/alteracoes')  # Definição a rota '/alteracoes'.
@login_required  # Protege a rota, requerendo login.
def alterar():
    search_query = request.args.get('search', '')  # Obtém a consulta de busca, padrão é vazio.
    search_by = request.args.get('searchBy', 'nome')  # Obtém o campo para busca, padrão é 'nome'.
    page = int(request.args.get('page', 1))  # Obtém a página atual, padrão é 1.
    limit = 15  # Limite de registros por página.
    offset = (page - 1) * limit  # Calcula o deslocamento para a consulta.

    cur = mysql.connection.cursor()  # Criação de um cursor para interagir com o banco de dados.

    # Adiciona lógica de busca para diferentes campos
    if search_query:
        if search_by == 'endereco':
            cur.execute("SELECT * FROM moradores WHERE endereco LIKE %s LIMIT %s OFFSET %s",
                        ('%' + search_query + '%', limit, offset))  # Busca por endereço.
        elif search_by == 'telefone':
            cur.execute("SELECT * FROM moradores WHERE telefone LIKE %s LIMIT %s OFFSET %s",
                        ('%' + search_query + '%', limit, offset))  # Busca por telefone.
        else:
            cur.execute("SELECT * FROM moradores WHERE nome LIKE %s LIMIT %s OFFSET %s",
                        ('%' + search_query + '%', limit, offset))  # Busca por nome.
    else:
        cur.execute("SELECT * FROM moradores LIMIT %s OFFSET %s", (limit, offset))  # Consulta padrão sem filtro.

    moradores = cur.fetchall()  # Obtém todos os registros retornados.

    # Obtém o total de registros para calcular o total de páginas
    cur.execute("SELECT COUNT(*) FROM moradores")  # Conta o total de moradores.
    total_records = cur.fetchone()[0]  # Obtém o total de registros.
    total_pages = (total_records + limit - 1) // limit  # Calcula o número total de páginas.

    cur.close()  # Fecha o cursor após a operação.

    return render_template('alteracoes.html', moradores=moradores, search_query=search_query, search_by=search_by, page=page,
                           total_pages=total_pages)  # Renderiza o template com os dados.


@app.route('/editar/<int:id>', methods=['GET', 'POST'])  # Definição a rota '/editar' que aceita um ID e os métodos GET e POST.
@login_required  # Protege a rota, requerendo login.
def editar(id):
    cur = mysql.connection.cursor()  # Criação de um cursor para interagir com o banco de dados.

    if request.method == 'POST':  # Se o método for POST, significa que o formulário foi enviado.
        # Captura os dados do formulário de edição
        nome = request.form['nome']  # Captura o nome.
        endereco = request.form['endereco']  # Captura o endereço.
        idade = request.form['idade']  # Captura a idade.
        telefone = request.form['telefone']  # Captura o telefone.

        # Atualiza os dados do morador pelo ID
        cur.execute("""
            UPDATE moradores 
            SET nome=%s, endereco=%s, idade=%s, telefone=%s 
            WHERE id=%s
        """, (nome, endereco, idade, telefone, id))  # Executa a atualização.
        mysql.connection.commit()  # Confirma a transação para salvar as alterações.
        cur.close()  # Fecha o cursor.

        # Mensagem de sucesso após a atualização
        flash('Dado atualizado com sucesso!', 'success')  # Mensagem de sucesso para o usuário.
        return redirect(url_for('alterar'))  # Redireciona para a página de alteração.

    # Se o método for GET, busca os dados do morador a ser editado
    cur.execute("SELECT * FROM moradores WHERE id=%s", (id,))  # Consulta para obter o morador pelo ID.
    morador = cur.fetchone()  # Obtém o morador a partir da consulta.
    cur.close()  # Fecha o cursor.

    # Renderiza a página de edição com os dados do morador
    return render_template('editar.html', morador=morador)  # Retorna o template de edição com os dados do morador.


@app.route('/excluir/<int:id>', methods=['POST'])  # Definição a rota '/excluir' que aceita um ID e o método POST.
@login_required  # Protege a rota, requerendo login.
def excluir(id):
    cur = mysql.connection.cursor()  # Criação de um cursor para interagir com o banco de dados.
    # Exclui o morador pelo ID
    cur.execute("DELETE FROM moradores WHERE id=%s", (id,))  # Executa a consulta para deletar o morador.
    mysql.connection.commit()  # Confirma a transação para aplicar a exclusão.
    cur.close()  # Fecha o cursor após a operação.

    flash('Usuário excluído com sucesso!', 'success')  # Mensagem de sucesso após exclusão.
    return redirect(url_for('alterar'))  # Redireciona para a página de alterações.

# Executa a aplicação em modo de depuração
if __name__ == '__main__':
    app.run(debug=True)  # Inicia o servidor em modo de depuração.

