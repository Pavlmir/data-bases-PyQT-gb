import sys
from cx_Freeze import setup, Executable

build_exe_options = {
}
setup(
  name="myscript",
  version="1.0.0",
  description="SQL-test application!",
  options={
    "build_exe": build_exe_options
  },
  executables=[Executable('server_chat.server.py',
                          base='Win32GUI',
                          targetName='setup.exe',
                          )]
)