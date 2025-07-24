#!/usr/bin/env python3
"""
OpenVPN Manager - Dependency Checker
Tests all required dependencies for the application
"""

import sys
import os

def test_dependency(module_name, package_hint=None):
    """Test if a Python module can be imported"""
    try:
        if module_name == "PyQt6.QtWidgets":
            from PyQt6.QtWidgets import QApplication
            print(f" {module_name} - OK")
            return True
        elif module_name == "PyQt6.QtCore":
            from PyQt6.QtCore import QTimer
            print(f" {module_name} - OK")
            return True
        elif module_name == "PyQt6.QtGui":
            from PyQt6.QtGui import QFont
            print(f" {module_name} - OK")
            return True
        elif module_name == "main":
            import main
            print(f" {module_name} - OK")
            return True
        elif module_name == "config":
            import config
            print(f" {module_name} - OK")
            return True
        else:
            __import__(module_name)
            print(f" {module_name} - OK")
            return True
    except ImportError as e:
        print(f" {module_name} - FALHOU: {e}")
        if package_hint:
            print(f"   Solução: {package_hint}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - ERRO: {e}")
        return False

def test_command(cmd_name, package_hint=None):
    """Test if a system command is available"""
    import subprocess
    try:
        result = subprocess.run([cmd_name, '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f" {cmd_name} - OK")
            return True
        else:
            print(f" {cmd_name} - comando existe mas retornou erro")
            return False
    except FileNotFoundError:
        print(f" {cmd_name} - COMANDO NÃO ENCONTRADO")
        if package_hint:
            print(f"   Solução: {package_hint}")
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠️  {cmd_name} - timeout (mas provavelmente OK)")
        return True
    except Exception as e:
        print(f" {cmd_name} - ERRO: {e}")
        return False

def main():
    print("=" * 60)
    print(" OpenVPN Manager - Verificador de Dependências")
    print("=" * 60)
    
    all_ok = True
    
    print("\n Testando dependências Python:")
    print("-" * 40)
    
    # Set PYTHONPATH if needed
    if "/usr/lib/python3.10/dist-packages" not in sys.path:
        sys.path.insert(0, "/usr/lib/python3.10/dist-packages")
        print(" PYTHONPATH ajustado para incluir pacotes do sistema")
    
    # Test Python modules
    deps = [
        ("sys", None),
        ("os", None),
        ("subprocess", None),
        ("json", None),
        ("time", None),
        ("pathlib", None),
        ("typing", None),
        ("datetime", None),
        ("re", None),
    ]
    
    for module, hint in deps:
        if not test_dependency(module, hint):
            all_ok = False
    
    print("\n🖥️  Testando dependências PyQt6:")
    print("-" * 40)
    
    pyqt_deps = [
        ("PyQt6.QtWidgets", "pip3 install PyQt6 ou sudo apt install python3-pyqt6"),
        ("PyQt6.QtCore", "pip3 install PyQt6 ou sudo apt install python3-pyqt6"),
        ("PyQt6.QtGui", "pip3 install PyQt6 ou sudo apt install python3-pyqt6"),
    ]
    
    for module, hint in pyqt_deps:
        if not test_dependency(module, hint):
            all_ok = False
    
    print("\n Testando módulos da aplicação:")
    print("-" * 40)
    
    app_deps = [
        ("config", "Verificar instalação do OpenVPN Manager"),
        ("main", "Verificar instalação do OpenVPN Manager"),
    ]
    
    for module, hint in app_deps:
        if not test_dependency(module, hint):
            all_ok = False
    
    print("\n  Testando comandos do sistema:")
    print("-" * 40)
    
    system_deps = [
        ("python3", "sudo apt install python3"),
        ("openvpn", "sudo apt install openvpn"),
        ("sudo", "sudo já deve estar instalado"),
        ("zenity", "sudo apt install zenity (para diálogos GUI)"),
    ]
    
    for cmd, hint in system_deps:
        if not test_command(cmd, hint):
            if cmd in ["python3", "openvpn", "sudo"]:
                all_ok = False
    
    print("\n" + "=" * 60)
    
    if all_ok:
        print(" TODAS AS DEPENDÊNCIAS ESSENCIAIS ESTÃO OK!")
        print(" OpenVPN Manager deve funcionar corretamente")
        
        # Test basic import
        print("\n🧪 Teste de importação básica:")
        try:
            os.environ['PYTHONPATH'] = "/usr/lib/python3.10/dist-packages:" + os.environ.get('PYTHONPATH', '')
            exec("import main; import config; from PyQt6.QtWidgets import QApplication")
            print(" Importação completa bem-sucedida!")
        except Exception as e:
            print(f" Falha na importação: {e}")
            all_ok = False
    else:
        print(" ALGUMAS DEPENDÊNCIAS ESTÃO FALTANDO!")
        print(" Instale as dependências indicadas acima")
        
    print("\n Resumo:")
    print(f"   • Python: {sys.version}")
    print(f"   • PYTHONPATH: {':'.join(sys.path[:3])}...")
    print(f"   • Diretório atual: {os.getcwd()}")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
