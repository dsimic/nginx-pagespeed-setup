from fabric.api import env, run, sudo, put
from fabric.contrib.files import exists
from fabric.context_managers import cd

env.use_ssh_config = True


def setup_env():
    env.user_home = "/home/%s" % env.user
    # for nginx install from source with pagespeed mod
    env.nps_version = '1.9.32.2'
    env.pagespeed_module = 'ngx_pagespeed-release-%s-beta' % env.nps_version
    env.pagespeed_folder = env.pagespeed_module
    env.pagespeed_archive = 'release-%s-beta' % env.nps_version + '.zip'
    env.pagespeed_url = 'https://github.com/pagespeed/ngx_pagespeed/archive/' + \
        env.pagespeed_archive
    env.psol_folder = 'psol'
    env.psol_archive = '%s.tar.gz' % env.nps_version
    env.psol_url = 'https://dl.google.com/dl/page-speed/psol/' +\
        env.psol_archive
    env.nginx_version = '1.6.2'
    env.nginx_folder = 'nginx-%s' % env.nginx_version
    env.nginx_archive = env.nginx_folder + '.tar.gz'
    env.nginx_url = 'http://nginx.org/download/' + env.nginx_archive
    env.nginx_root = '/usr/local/nginx/'
    env.pagespeed_cache = '/var/ngx_pagespeed_cache/%s' % env.domain
    env.uwsgi_root = '/etc/uwsgi/'
    env.venv_root = env.user_home + "/Env/"


def nginx_install_from_source():
    # remove and apt-get installs
    sudo("apt-get -y remove nginx")
    sudo("apt-get -y autoremove")
    # remove and installs from source
    sudo("rm -rf /usr/local/nginx")
    sudo("rm -f /usr/local/sbin/nginx")
    sudo("rm -f /usr/sbin/nginx")
    if exists("/usr/sbin/nginx"):
        print "Warning a version of nginx appears to be installed. Aborting."

    def clean_up():
        cd("$HOME")
        run("rm -rf %s" % env.pagespeed_folder)
        run("rm -f %s" % env.pagespeed_archive)
        run("rm -f %s" % env.nginx_archive)
        run("rm -rf %s" % env.nginx_folder)
        sudo("rm -f /etc/init.d/nginx")

    clean_up()

    def install():
        sudo("apt-get -y install build-essential zlib1g-dev libpcre3 " +
             " libpcre3-dev libc6 libssl0.9.8 libssl-dev lsb-base unzip")
        with cd("$HOME"):
            run("wget %s" % env.pagespeed_url)
            run("unzip %s" % env.pagespeed_archive)
        with cd("$HOME/%s" % env.pagespeed_folder):
            run("wget %s" % env.psol_url)
            run("tar -xzf %s" % env.psol_archive)
        create_pagespeed_cache()
        with cd("$HOME"):
            run("wget %s" % env.nginx_url)
            run("tar -xzf %s" % env.nginx_archive)
        with cd("$HOME/%s" % env.nginx_folder):
            run("./configure --sbin-path=/usr/local/sbin " +
                " --with-http_ssl_module " +
                " --add-module=$HOME/%s " % env.pagespeed_module)
            run("make")
            sudo("make install")
        nginx_configure_from_source()
        # restart
        sudo("service nginx restart")

    install()


def create_pagespeed_cache():
    sudo('mkdir -p %s' % env.pagespeed_cache)
    sudo('chgrp www-data %s' % env.pagespeed_cache)


def nginx_configure_from_source():
    # setup init.d
    put("./nginx/init.d/nginx", "/etc/init.d/nginx", use_sudo=True)
    sudo("chmod +x /etc/init.d/nginx")
    # setup debian style layout
    sudo("mkdir -p /usr/local/nginx/sites-available")
    sudo("mkdir -p /usr/local/nginx/sites-enabled")
    # copy config
    put("./nginx/conf/nginx.conf", "%s/conf/nginx.conf" % env.nginx_root,
        use_sudo=True)
    put("./nginx/sites-available/default",
        "%s/sites-available/default" % env.nginx_root, use_sudo=True)
    sudo("ln -sf %s/sites-available/default %s/sites-enabled/default" %
         (env.nginx_root, env.nginx_root))


def nginx_start():
    sudo("service nginx start")


def nginx_stop():
    sudo("service nginx stop")


def nginx_restart():
    sudo("service nginx restart")


def pagespeed_flush_cache():
    sudo("rm -rf %s/*" % env.pagespeed_cache)
