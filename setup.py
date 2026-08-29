from pathlib import Path
from setuptools import find_packages, setup
ROOT=Path(__file__).parent; PRODUCT=ROOT/'optional-tooling'/'python'
setup(name='novel-distiller',version='0.3.0',description='Optional local tooling for the Novel Distiller Skill',long_description=(PRODUCT/'README.md').read_text(encoding='utf-8'),long_description_content_type='text/markdown',package_dir={'':'optional-tooling/python'},packages=find_packages(where='optional-tooling/python',include=['novel_distiller','novel_distiller.*']),python_requires='>=3.9',install_requires=[x.strip() for x in (PRODUCT/'requirements.txt').read_text('ascii').splitlines() if x.strip() and not x.startswith('#')],entry_points={'console_scripts':['novel-distiller=novel_distiller.__main__:main']})
