from setuptools import setup, find_packages


setup(
    name='language_learner',
    version='0.0.1',
    description="Shiny language learning Telegram bot",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    keywords='Language',
    author='Omrigan',
    author_email='omrigann@gmail.com',
    url='https://github.com/Omrigan/shiny-language-learner',
    license='MIT',
    packages=find_packages(exclude=['language_learner_env', 'tests']),
    zip_safe=True,
    setup_requires=[
    ],
    install_requires=[
        'pymongo',
        'flask',
        'requests',
        'bs4',
        'nltk',
        'apscheduler',
        'Celery',
        'schedule',
        #'lxml',
    ]
)
