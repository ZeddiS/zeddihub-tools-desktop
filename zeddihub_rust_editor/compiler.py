import os
import shutil
import urllib.request
import zipfile
import subprocess
import tempfile
import time
import glob
from .core import *

def update_oxide_compiler():
    print_header(); print("\n"*4 + YELLOW + center("KONTROLA OXIDE KNIHOVEN V COMPILER_REFS...") + RESET)
    needed_dlls = ["Oxide.Core.dll", "Assembly-CSharp.dll", "Newtonsoft.Json.dll", "Oxide.CSharp.dll"]
    missing = [dll for dll in needed_dlls if not os.path.exists(os.path.join(COMPILER_DIR, dll))]
    
    if not missing:
        # Zkontrolujeme, jestli máme dostatek dll, pokud ne, zjevně jsme je dřív nerozbalili všechny
        if len(glob.glob(os.path.join(COMPILER_DIR, "*.dll"))) > 50:
            return True
        
    print(center(CYAN + "Stahuji kompletní Oxide knihovny z uModu..." + RESET))
    url = "https://umod.org/games/rust/download"
    zip_path = os.path.join(COMPILER_DIR, "oxide_rust.zip")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                # Extrahujeme VŠECHNY DLL knihovny z balíčku Managed
                if file.endswith(".dll"):
                    filename = os.path.basename(file)
                    if filename:
                        with zip_ref.open(file) as source, open(os.path.join(COMPILER_DIR, filename), "wb") as target:
                            shutil.copyfileobj(source, target)
                        
        os.remove(zip_path)
        print(center(GREEN + "✅ Knihovny úspěšně aktualizovány!" + RESET)); time.sleep(2); return True
    except Exception as e:
        print(center(RED + f"Chyba při stahování Oxide: {e}" + RESET)); time.sleep(3); return False

def get_roslyn_compiler():
    roslyn_dir = os.path.join(COMPILER_DIR, "Roslyn")
    csc_exe = os.path.join(roslyn_dir, "tools", "csc.exe")
    
    if os.path.exists(csc_exe): return csc_exe
        
    print_header()
    print("\n"*4 + YELLOW + center("STAHUJI MODERNÍ C# KOMPILÁTOR (Roslyn)...") + RESET)
    print(center("Toto trvale vyřeší chybu s moderním C# (CS1056). Proběhne pouze jednou."))
    
    url = "https://www.nuget.org/api/v2/package/Microsoft.Net.Compilers/3.11.0"
    zip_path = os.path.join(COMPILER_DIR, "roslyn.zip")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(roslyn_dir)
            
        os.remove(zip_path)
        print(center(GREEN + "✅ Moderní kompilátor úspěšně nainstalován!" + RESET))
        time.sleep(2)
        return csc_exe
    except Exception as e:
        print(center(RED + f"Chyba při stahování kompilátoru Roslyn: {e}" + RESET))
        time.sleep(3)
        
        fallback_paths = [r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe", r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"]
        for p in fallback_paths:
            if os.path.exists(p): return p
        return None

def run_compiler_simulator(auto_mode=False):
    if platform.system() != "Windows":
        if not auto_mode:
            print_header(); print("\n"*4 + RED + center("Tato funkce je dostupná pouze na Windows.") + RESET); time.sleep(3)
        return
        
    csc_path = get_roslyn_compiler()
    if not csc_path:
        if not auto_mode:
            print_header(); print("\n"*4 + RED + center("Nepodařilo se najít žádný C# kompilátor.") + RESET); time.sleep(3)
        return
        
    update_oxide_compiler()
    
    work_dir = settings["target_dir"]
    if not auto_mode:
        sel_dir = 0
        opts_dir = [
            f"Zdrojová složka (Původní rozbité): {os.path.basename(settings['source_dir'])}",
            f"Cílová složka (Opravené z Fronty): {os.path.basename(settings['target_dir'])}"
        ]
        while True:
            render_menu("VÝBĚR SLOŽKY PRO KOMPILACI", opts_dir, sel_dir, footer="[W/S] Pohyb | [Enter] Vybrat | [A/Esc] Zpět")
            k = read_key()
            if k in ['a', 'esc', 'q']: return
            elif k == 'w' and sel_dir > 0: sel_dir -= 1
            elif k == 's' and sel_dir < len(opts_dir)-1: sel_dir += 1
            elif k in ['d', 'enter', 'space']:
                work_dir = settings["source_dir"] if sel_dir == 0 else settings["target_dir"]
                break
        
    if not os.path.exists(work_dir): return
    files = [f for f in os.listdir(work_dir) if f.endswith(".cs")]
    if not files:
        if not auto_mode:
            print_header(); print("\n"*4 + RED + center(f"Ve složce {work_dir} nejsou žádné soubory.") + RESET); time.sleep(2)
        return
        
    if auto_mode: 
        files_to_compile = files
    else:
        sel_flags = multi_select_menu("OXIDE COMPILER SIMULÁTOR", files, [True]*len(files), ["Zkompiluje plugin v paměti pro nalezení C# chyb."] * len(files), enable_x=True)
        if not sel_flags: return
        files_to_compile = [files[i] for i in range(len(files)) if sel_flags[i]]
        if not files_to_compile: return

    prog_win = ProgressWindow()
    prog_win.start("Kompilace Pluginů")
    
    for f_name in files_to_compile:
        src_path = os.path.join(work_dir, f_name)
        
        # Temp soubory aby to fungovalo
        temp_out = os.path.join(tempfile.gettempdir(), "temp_build_rust.dll")
        rsp_path = os.path.join(tempfile.gettempdir(), "compiler_args.rsp")
        
        # Filtrujeme SQLite atd., aby Windows compiler nenadával
        native_dlls = ["sqlite3.dll", "msvcr120.dll", "msvcp140.dll", "mono-2.0.dll", "steam_api64.dll", "rustnative.dll", "compiler.dll"]
        refs = [os.path.join(COMPILER_DIR, r) for r in os.listdir(COMPILER_DIR) if r.endswith(".dll") and r.lower() not in native_dlls]
        
        # Response file aby Windows cmd nepřetekl z délky textu
        with open(rsp_path, "w", encoding="utf-8") as rsp:
            rsp.write(f'/t:library\n')
            rsp.write(f'/nologo\n')
            rsp.write(f'/out:"{temp_out}"\n')
            for r in refs:
                rsp.write(f'/reference:"{r}"\n')
            rsp.write(f'"{src_path}"\n')
            
        cmd = f'"{csc_path}" @"{(rsp_path)}"'
        
        prog_win.log(f"\n{'='*60}\n=== SPUŠTĚNÍ C# KOMPILÁTORU: {f_name} ===\n")
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            stdout_bytes, _ = process.communicate()
            stdout = stdout_bytes.decode('cp852', errors='replace')
            
            if process.returncode == 0:
                prog_win.log("✅ KOMPILACE ÚSPĚŠNÁ! (Žádné syntax chyby C#)\n")
            else:
                prog_win.log("❌ CHYBA KOMPILACE:\n")
                prog_win.log(stdout)
                
            if os.path.exists(temp_out): os.remove(temp_out)
        except Exception as e:
            prog_win.log(f"Kritická chyba kompilátoru: {e}")

    prog_win.bring_to_front()