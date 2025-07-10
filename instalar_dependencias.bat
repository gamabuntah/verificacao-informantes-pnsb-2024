@echo off
chcp 65001 > nul

echo Instalando dependencias do projeto...
echo.

:: Definir o caminho do projeto
set "PROJETO_DIR=C:\Users\ggmob\Cursor AI\Verificação Informantes PNSB"

:: Verificar se o diretório existe
if not exist "%PROJETO_DIR%" (
    echo Erro: Diretorio do projeto nao encontrado: %PROJETO_DIR%
    pause
    exit /b 1
)

:: Verificar se o ambiente virtual existe
if not exist "%PROJETO_DIR%\.venv" (
    echo Criando ambiente virtual...
    cd /d "%PROJETO_DIR%"
    python -m venv .venv
    if errorlevel 1 (
        echo Erro ao criar ambiente virtual!
        pause
        exit /b 1
    )
)

:: Ativar ambiente virtual
echo Ativando ambiente virtual...
cd /d "%PROJETO_DIR%"
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Erro ao ativar o ambiente virtual!
    pause
    exit /b 1
)

:: Atualizar o pip corretamente
echo Atualizando o pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

:: Atualizar typing_extensions e SQLAlchemy
echo Atualizando typing_extensions e SQLAlchemy...
pip install --upgrade typing_extensions
pip install --upgrade SQLAlchemy

:: Instalar dependências
echo Instalando pacotes necessarios...
pip install -r requirements.txt

echo.
echo Instalacao concluida!
echo Agora voce pode executar o projeto usando o arquivo executar_projeto.bat
echo.
pause 