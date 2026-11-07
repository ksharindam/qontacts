from setuptools import setup
import platform


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
    #cmdclass = {'bdist_wheel': BdistWheel, 'install': Install},
    include_package_data=True,
    zip_safe=False
    )
