# from setuptools import setup
import os
from cx_Freeze import setup, Executable

CURR_DIR = os.getcwd()

setup(
    name='package_messenger',
    version='0.1',
    author="Pavel",
    author_email="@gmail.com",
    description="Messenger",
    zip_safe=False,
    executables=[Executable(f'{CURR_DIR}/src/server_chat/server_gui.py'),
                 Executable(f'{CURR_DIR}/src/client_chat/client_gui.py')]
)
