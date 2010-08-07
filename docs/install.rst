How to install Devmason Server
==============================

Devmason is easy to install. It comes with a setup.py, so you can easily
install it:


    virtualenv devmason
    cd devmason/
    . bin/activate
    pip install -e git://github.com/ericholscher/devmason-server.git#egg=devmason-server
    cd src/devmason-server
    pip install -r pip_requirements.txt
    cd test_project
    ./manage.py syncdb --noinput
    ./manage.py loaddata devmason_server_test_data.json
    ./manage.py runserver


That's all that it takes to get a running server up. Look at the test_project for examples on how to set up your urls and settings.
