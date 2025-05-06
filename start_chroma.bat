@echo off
REM ChromaDB startup script for Windows

SETLOCAL EnableDelayedExpansion

REM Function to check if docker compose command is available
call :check_docker_compose
if errorlevel 1 exit /b 1

REM Function to check for .env file and create from example if needed
call :setup_env_file

REM Parse command line arguments
set "DEV_MODE=false"
for %%a in (%*) do (
    if "%%a"=="--dev" set "DEV_MODE=true"
    if "%%a"=="-d" set "DEV_MODE=true"
)

REM Set default values
if not defined CHROMA_USERNAME (
    set "USERNAME=thinkAdmin"
) else (
    set "USERNAME=%CHROMA_USERNAME%"
)

REM Generate random password if not provided
if not defined CHROMA_PASSWORD (
    for /f "tokens=*" %%a in ('powershell -Command "[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(9))"') do set "PASSWORD=%%a"
) else (
    set "PASSWORD=%CHROMA_PASSWORD%"
)

if not defined CHROMA_HOST (
    set "CHROMA_HOST=chroma"
)

if not defined CHROMA_PORT (
    set "CHROMA_PORT=8000"
)

if not defined CHROMA_DEV_PORT (
    set "DEV_PORT=8001"
) else (
    set "DEV_PORT=%CHROMA_DEV_PORT%"
)

REM Display banner
echo =====================================
if "%DEV_MODE%"=="true" (
    echo  ChromaDB Development Server Setup  
) else (
    echo    ChromaDB Server Setup ^& Startup   
)
echo =====================================

REM Check if server.htpasswd exists
if not exist server.htpasswd (
    echo Generating htpasswd file with credentials...
    docker run --rm --entrypoint htpasswd httpd:2 -Bbn "%USERNAME%" "%PASSWORD%" > server.htpasswd
    echo Created server.htpasswd with username: %USERNAME%
    
    REM Update .env file with the credentials if it exists
    if exist .env (
        REM Check if CHROMA_CLIENT_AUTHN_CREDENTIALS already exists in .env
        findstr /C:"CHROMA_CLIENT_AUTHN_CREDENTIALS" .env > nul
        if not errorlevel 1 (
            REM Create temp file without the line
            type .env | findstr /V "CHROMA_CLIENT_AUTHN_CREDENTIALS" > .env.tmp
            REM Add updated line
            echo CHROMA_CLIENT_AUTHN_CREDENTIALS=%USERNAME%:%PASSWORD% >> .env.tmp
            move /Y .env.tmp .env > nul
        ) else (
            REM Add the line at the end of the file
            echo CHROMA_CLIENT_AUTHN_CREDENTIALS=%USERNAME%:%PASSWORD% >> .env
        )
        echo Updated .env file with credentials
    ) else (
        echo Warning: .env file not found. Please set CHROMA_CLIENT_AUTHN_CREDENTIALS=%USERNAME%:%PASSWORD% manually.
    )
) else (
    echo Using existing server.htpasswd file
)

REM Start ChromaDB using docker compose
echo Starting ChromaDB server...
set "CURRENT_DIR=%CD%"

REM Create development data directory if needed
if "%DEV_MODE%"=="true" (
    if not exist chroma-dev-data mkdir chroma-dev-data
    
    echo Starting ChromaDB in development mode...
    
    REM Stop any existing dev container to avoid conflicts
    docker stop chromadb-dev 2>nul
    
    echo Using directory: %CURRENT_DIR% for ChromaDB data
    echo Server htpasswd path: %CURRENT_DIR%\server.htpasswd
    
    REM Check if server.htpasswd exists before starting container
    if not exist "%CURRENT_DIR%\server.htpasswd" (
        echo Error: server.htpasswd file not found at %CURRENT_DIR%\server.htpasswd
        exit /b 1
    )
    
    REM Use a different port and directory for development mode
    echo Development ChromaDB instance running on port: %DEV_PORT%
    
    REM Update .env.dev file with the dev credentials
    echo Updating .env.dev file...
    
    REM Create a backup of existing .env.dev if it exists
    if exist .env.dev (
        copy .env.dev .env.dev.bak > nul
        echo Created backup of existing .env.dev as .env.dev.bak
    )
    
    if exist .env (
        REM Start with a copy of the main .env file
        copy .env .env.dev > nul
    ) else (
        REM Create new .env.dev file
        type nul > .env.dev
    )
    
    REM Update or add environment variables to .env.dev
    call :update_env_var "CHROMA_PORT" "%CHROMA_PORT%" ".env.dev"
    call :update_env_var "CHROMA_DEV_PORT" "%DEV_PORT%" ".env.dev"
    call :update_env_var "CHROMA_HOST" "chroma-dev" ".env.dev"
    call :update_env_var "CHROMA_CLIENT_AUTHN_CREDENTIALS" "%USERNAME%:%PASSWORD%" ".env.dev"
    
    echo Updated .env.dev file with development ChromaDB settings
    
    REM Check if docker-compose.dev.yml exists
    if exist "docker-compose.dev.yml" (
        echo Development environment setup complete. To start the server, run:
        echo %DOCKER_COMPOSE_CMD% -f docker-compose.dev.yml up -d
    ) else (
        echo docker-compose.dev.yml not found, setup complete. To start the server, run:
        echo docker run -d --name chromadb-dev ^
        echo   -v "%CURRENT_DIR%\chroma-dev-data:/chroma/chroma" ^
        echo   -v "%CURRENT_DIR%\server.htpasswd:/chroma/server.htpasswd:ro" ^
        echo   -p %DEV_PORT%:8000 ^
        echo   -e AUTH_CREDENTIALS_FILE=/chroma/server.htpasswd ^
        echo   -e AUTH_PROVIDER=basic ^
        echo   chromadb/chroma:latest
    )
) else (
    REM Check if docker-compose.yml exists in a chroma directory
    if exist "chroma\docker-compose.yml" (
        cd chroma
        echo ChromaDB setup complete. To start the server, run:
        echo %DOCKER_COMPOSE_CMD% up -d --build
    ) else (
        echo ChromaDB setup complete. Server not started.
        echo To start ChromaDB as a standalone container, run:
        
        echo docker run -d --name chromadb ^
        echo   -v "%CURRENT_DIR%\chroma:/chroma/chroma" ^
        echo   -v "%CURRENT_DIR%\server.htpasswd:/chroma/server.htpasswd:ro" ^
        echo   -p 8000:8000 ^
        echo   -e AUTH_CREDENTIALS_FILE=/chroma/server.htpasswd ^
        echo   -e AUTH_PROVIDER=basic ^
        echo   chromadb/chroma:latest
    )
)

echo =====================================
echo ChromaDB setup completed successfully.
if "%DEV_MODE%"=="true" (
    echo Development mode configuration ready.
    echo Host: localhost
    echo Port: %DEV_PORT%
) else (
    echo Host: %CHROMA_HOST%
    echo Port: %CHROMA_PORT%
)
echo Authentication: Basic auth with username: %USERNAME%
echo =====================================

goto :eof

:check_docker_compose
REM Function to check if docker compose command is available
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not available
    echo Please install Docker with Docker Compose support
    exit /b 1
)

docker compose version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Using docker compose command
    set "DOCKER_COMPOSE_CMD=docker compose"
) else (
    echo Error: Docker compose command is not available
    echo Please install Docker with Docker Compose support
    exit /b 1
)
exit /b 0

:setup_env_file
REM Function to check for .env file and create from example if needed
if not exist .env (
    if exist .env.example (
        echo No .env file found. Creating from .env.example...
        copy .env.example .env > nul
        echo Created .env file. Please edit it to add your credentials.
    ) else (
        echo Warning: Neither .env nor .env.example found. Environment configuration may be incomplete.
        type nul > .env
    )
) else (
    echo Found existing .env file.
)
exit /b 0

:update_env_var
REM Function to update environment variables in a file
REM Parameters: %1=variable name, %2=value, %3=file path
set "VAR_NAME=%~1"
set "VAR_VALUE=%~2"
set "FILE_PATH=%~3"

findstr /C:"%VAR_NAME%=" %FILE_PATH% > nul
if not errorlevel 1 (
    REM Create temp file without the line
    type %FILE_PATH% | findstr /V "%VAR_NAME%=" > %FILE_PATH%.tmp
    REM Add updated line
    echo %VAR_NAME%=%VAR_VALUE% >> %FILE_PATH%.tmp
    move /Y %FILE_PATH%.tmp %FILE_PATH% > nul
) else (
    REM Add the line at the end of the file
    echo %VAR_NAME%=%VAR_VALUE% >> %FILE_PATH%
)
exit /b 0