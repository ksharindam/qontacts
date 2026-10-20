from setuptools import setup
from setuptools.command.install import install
try:
    from setuptools.command.bdist_wheel import bdist_wheel
except:
    from wheel.bdist_wheel import bdist_wheel
from subprocess import check_call
import platform

# allows to run commands before 'setup.py install' (used by dh-python)
class Install(install):
    def run(self):
        check_call("pyrcc5 -o ./qontacts/resources_rc.py ./data/resources.qrc".split())
        install.run(self)

# allows to run commands before building wheel
class BdistWheel(bdist_wheel):
    def finalize_options(self):
        check_call("pyrcc5 -o ./qontacts/resources_rc.py ./data/resources.qrc".split())
        bdist_wheel.finalize_options(self)


if platform.system()=='Linux':
    data_files = [('share/applications', ['data/qontacts.desktop']),
                ('share/icons/hicolor/scalable/apps', ['data/icons/qontacts.png'])]
else:
    data_files = []

setup(
    name='qontacts',
    #version="0.1",
    packages=['qontacts'],
    entry_points={
      'gui_scripts': ['qontacts=qontacts.main:main'],
    },
    data_files = data_files,
    cmdclass = {'bdist_wheel': BdistWheel, 'install': Install},
    include_package_data=True,
    zip_safe=False
    )
