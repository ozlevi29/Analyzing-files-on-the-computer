@echo off
chcp 65001 >nul
title CleanWhy
where python >nul 2>nul || (echo Python is not installed. Download it from https://www.python.org/downloads/ & pause & exit /b 1)
python "%~dp0app\main.py"
if errorlevel 1 pause
