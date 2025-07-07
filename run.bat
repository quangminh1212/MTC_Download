@echo off
setlocal enabledelayedexpansion

REM Check input parameters
set "mode=%1"
if "%mode%"=="" set "mode=web"

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File .\run.ps1 -mode %mode% 
